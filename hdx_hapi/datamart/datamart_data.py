import logging
import logging.config
import os
import pandas

from typing import Optional
from fastapi import HTTPException
from hdx_hapi.datamart.datamart_responses import BackendEnum
from hdx_hapi.datamart.datamart_search import search_by_resource_id, search_by_query, search_by_lucky_dip
from hdx_hapi.endpoints.util.util import PaginationParams

from hdx_hapi.config.config import get_config

logging.config.fileConfig(os.getenv('LOGGING_CONF_FILE', 'logging.conf'))

log = logging.getLogger(__name__)

CONFIG = get_config()

PACKAGE_SEARCH_ENDPOINT = '/api/action/package_search'
RESOURCE_SHOW_ENDPOINT = '/api/action/resource_show'


async def datamart_data(
    pagination_parameters: PaginationParams,
    download_url: Optional[str],
    resource_hdx_id: Optional[str],
    dataset_hdx_stub: Optional[str],
    resource_hdx_stub: Optional[str],
    lucky_dip: Optional[str],
    sheet_name: Optional[str],
    data_filter: Optional[str],
    backend: Optional[BackendEnum],
):
    results = []

    # get a download URL if it is not provided
    if download_url is None:
        if lucky_dip:
            result = await search_by_lucky_dip()
            if 'download_url' in result:
                download_url = result['download_url']
        if resource_hdx_id:
            result = await search_by_resource_id(resource_id=resource_hdx_id)
            if 'download_url' in result:
                download_url = result['download_url']
        if dataset_hdx_stub and resource_hdx_stub:
            results = await search_by_query(f'name:{dataset_hdx_stub}', None)
            for result in results:
                if result['resource_name'] == resource_hdx_stub:
                    download_url = result['download_url']
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

    if backend == BackendEnum.PANDAS:
        results = pandas_backend(download_url, pagination_parameters, sheet_name=sheet_name)
    elif backend == BackendEnum.HXL_PROXY:
        raise NotImplementedError
    elif backend == BackendEnum.DATASTORE:
        raise NotImplementedError

    return results


def pandas_backend(download_url: str, pagination_parameters: PaginationParams, sheet_name: Optional[str]):
    try:
        if download_url.lower().endswith('.xls') or download_url.lower().endswith('.xlsx'):
            if sheet_name is None:
                dataframe = pandas.read_excel(download_url)
            else:
                dataframe = pandas.read_excel(download_url, sheet_name=sheet_name)
        else:
            dataframe = pandas.read_csv(download_url)
        dataframe = dataframe.astype(str)
        results = dataframe.to_dict('records')
    except FileNotFoundError:
        raise HTTPException(status_code=204, detail=f'Resource not found for URL {download_url}')
    except pandas.errors.ParserError:
        raise HTTPException(status_code=422, detail=f'Resource could not be parsed for URL {download_url}')

    # Pop HXL row if it exists - not yet implemented - you can set offset=1 if you know it's HXL-ated
    try:
        results = results[pagination_parameters.offset : (pagination_parameters.offset + pagination_parameters.limit)]
    except IndexError:
        results = results

    return results
