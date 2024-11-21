import logging
import logging.config
import os
import time
import httpx
import pandas


from typing import Optional
from httpx import Client
from fastapi import HTTPException
from hdx_hapi.datamart.datamart_responses import BackendEnum
from hdx_hapi.datamart.datamart_search import search_by_resource_id, search_by_query, search_by_lucky_dip
from hdx_hapi.datamart.datamart_util import SearchPaginationParams
from hdx_hapi.endpoints.util.util import PaginationParams

from hdx_hapi.config.config import get_config

logging.config.fileConfig(os.getenv('LOGGING_CONF_FILE', 'logging.conf'))

log = logging.getLogger(__name__)

CONFIG = get_config()

PACKAGE_SEARCH_ENDPOINT = '/api/action/package_search'
RESOURCE_SHOW_ENDPOINT = '/api/action/resource_show'
HXL_PROXY_DATA_PREVIEW_ENDPOINT = 'https://proxy.hxlstandard.org/api/data-preview.json'


async def datamart_data(
    pagination_parameters: PaginationParams,
    download_url: Optional[str],
    resource_hdx_id: Optional[str],
    dataset_hdx_stub: Optional[str],
    resource_hdx_stub: Optional[str],
    lucky_dip: Optional[bool],
    sheet_name: Optional[str],
    data_filter: Optional[str],
    backend: Optional[BackendEnum],
):
    resource_metadata = {}
    # get a download URL if it is not provided
    if download_url is None:
        if lucky_dip:
            resource_metadata = await search_by_lucky_dip()
            if 'download_url' in resource_metadata:
                download_url = resource_metadata['download_url']
        if resource_hdx_id:
            resource_metadata = await search_by_resource_id(resource_id=resource_hdx_id)
            if 'download_url' in resource_metadata:
                download_url = resource_metadata['download_url']
        if dataset_hdx_stub and resource_hdx_stub:
            dataset_resource_pagination = SearchPaginationParams(limit=5, offset=0)
            results = await search_by_query(
                f'name:{dataset_hdx_stub}',
                None,
                search_pagination_params=dataset_resource_pagination,
            )
            for resource_metadata in results:
                if resource_metadata['resource_name'] == resource_hdx_stub:
                    download_url = resource_metadata['download_url']
                    break
    # This gets resource metadata for the download_url
    else:
        log.info(f'{download_url}')
        try:
            parts = download_url.split('/resource/')
            resource_id = parts[1].split('/download/')[0]
            resource_metadata = await search_by_resource_id(resource_id=resource_id)
            log.info(f'{resource_id}')
        except IndexError:
            log.info(f'{download_url} is not an HDX format download_url')
            raise HTTPException(
                status_code=204,
                detail=(f'{download_url} is not an HDX format download_url, no data returned'),
            )

    log.info(resource_metadata)
    # Error on resource not found
    if download_url is None:
        log.info(
            f'Resource not found for dataset_hdx_stub= {dataset_hdx_stub}, '
            f'resource_hdx_stub= {resource_hdx_stub}, resource_hdx_id={resource_hdx_id}'
        )
        raise HTTPException(
            status_code=204,
            detail=(
                f'Resource not found for dataset_hdx_stub= {dataset_hdx_stub}, '
                f'resource_hdx_stub= {resource_hdx_stub}, resource_hdx_id={resource_hdx_id}'
            ),
        )

    results_from_backend = None
    if backend == BackendEnum.PANDAS:
        results_from_backend = pandas_backend(resource_metadata, sheet_name=sheet_name)
    elif backend == BackendEnum.HXL_PROXY:
        results_from_backend = hxl_proxy_backend(resource_metadata, sheet_name=sheet_name)
    elif backend == BackendEnum.DATASTORE:
        raise NotImplementedError

    assert results_from_backend is not None
    # Pop hxl row, if required
    results_from_backend = remove_hxl_row(results_from_backend, resource_metadata, sheet_name=sheet_name)
    # Apply data filter
    if data_filter:
        results_from_backend = filter_data(results_from_backend, data_filter)
    total_rows = len(results_from_backend)
    # Apply pagination
    try:
        results_from_backend = results_from_backend[
            pagination_parameters.offset : (pagination_parameters.offset + pagination_parameters.limit)
        ]
    except IndexError:
        results_from_backend = results_from_backend

    # Make paging_metadata
    paging_metadata = calculate_paging_metadata(pagination_parameters, results_from_backend, total_rows)

    # Attach the resource_metadata to the results here
    result = {
        'resource_metadata': resource_metadata,
        'paging_metadata': paging_metadata,
        'data': results_from_backend,
    }

    return result


def pandas_backend(resource_metadata: dict, sheet_name: Optional[str]) -> list[dict]:
    download_url = resource_metadata['download_url']
    file_format = resource_metadata['format']
    results = []
    try:
        if file_format.upper() in ['XLS', 'XLSX']:
            if sheet_name is None:
                dataframe = pandas.read_excel(download_url)
            else:
                dataframe = pandas.read_excel(download_url, sheet_name=sheet_name)
        elif file_format == 'CSV':
            dataframe = pandas.read_csv(download_url)
        else:
            raise HTTPException(status_code=501, detail=f'Data in file format {file_format} not supported')
        dataframe = dataframe.astype(str)
        results = dataframe.to_dict('records')

    except FileNotFoundError:
        raise HTTPException(status_code=204, detail=f'Resource not found for URL {download_url}')
    except pandas.errors.ParserError:
        raise HTTPException(status_code=422, detail=f'Resource could not be parsed for URL {download_url}')

    return results


def hxl_proxy_backend(resource_metadata: dict, sheet_name: Optional[str]) -> list[dict]:
    download_url = resource_metadata['download_url']

    params = {}
    params['url'] = download_url
    if sheet_name:
        try:
            params['sheet'] = int(sheet_name)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f'Requested HXL proxy backend requires an integer sheet index, not {sheet_name}'
            )

    t0 = time.time()
    log.info(f'Calling {HXL_PROXY_DATA_PREVIEW_ENDPOINT} with {params}')
    try:
        with Client() as ac:
            response = ac.get(HXL_PROXY_DATA_PREVIEW_ENDPOINT, params=params, timeout=60)
        response.raise_for_status()
    except httpx.ConnectTimeout:
        log.info(f'**Timeout in {time.time() - t0:0.2f} seconds')
        raise HTTPException(
            status_code=504,
            detail=f'Request to {HXL_PROXY_DATA_PREVIEW_ENDPOINT} timed out after {time.time() - t0:0.2f} seconds',
        )

    except Exception as exc:
        log.info(f'{exc}')
        raise exc

    results = response.json()

    # results is a list of lists, we need to convert to a list of dicts
    headers = results[0]
    decorated_results = []
    for result in results[1:]:
        decorated_row = zip(headers, result)
        decorated_results.append(decorated_row)

    return decorated_results


def remove_hxl_row(
    decorated_results: list[dict], resource_metadata: dict, sheet_name: Optional[str] = None
) -> list[dict]:
    is_hxlated = None
    if not sheet_name:
        is_hxlated = resource_metadata['sheets'][0]['is_hxlated']
    else:
        try:
            is_hxlated = resource_metadata['sheets'][int(sheet_name)]['is_hxlated']
        except ValueError:
            for sheet in resource_metadata['sheets']:
                if sheet_name == sheet['sheet_name']:
                    is_hxlated = sheet['is_hxlated']
                    break
        except IndexError:
            is_hxlated = None

    # is_hxlated detection would go here:
    if is_hxlated is None:
        n_hashes = 0
        for k, v in decorated_results[0].items():
            if '#' in v:
                n_hashes += 1
        if n_hashes > 3:
            is_hxlated = True
        else:
            is_hxlated = False
    # Pop HXL row if it exists
    if is_hxlated:
        decorated_results = decorated_results[1:]
    return decorated_results


def calculate_paging_metadata(pagination_parameters, decorated_results, total_rows):
    returned_rows = len(decorated_results)

    if returned_rows < pagination_parameters.limit:
        next_offset = None
    else:
        next_offset = pagination_parameters.offset + pagination_parameters.limit
    paging_metadata = {
        'total_rows': total_rows,
        'returned_rows': returned_rows,
        'current_offset': pagination_parameters.offset,
        'next_offset': next_offset,
    }
    log.info(paging_metadata)
    return paging_metadata


def filter_data(rows: list[dict], data_filter: str) -> list[dict]:
    filtered_data = []
    #
    try:
        field_, value_ = parse_data_filter(data_filter)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f'{data_filter} is not a valid data_filter, it should be of the form fieldname:value',
        )

    if field_ not in rows[0]:
        raise HTTPException(
            status_code=400,
            detail=f'{field_} is not a field in the data provided',
        )
    for row in rows:
        if value_ in row[field_]:
            filtered_data.append(row)

    return filtered_data


def parse_data_filter(data_filter: str) -> tuple[str, str]:
    field_ = None
    value_ = None

    field_, value_ = data_filter.split(':')

    return field_.strip(), value_.strip()
