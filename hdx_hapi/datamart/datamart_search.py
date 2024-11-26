import datetime
import json
import logging
import logging.config
import os

import time
import httpx

from fastapi import HTTPException
from random import randrange
from typing import Optional
from httpx import AsyncClient
from hdx_hapi.datamart.datamart_util import SearchPaginationParams, calculate_paging_metadata

from hdx_hapi.config.config import get_config

logging.config.fileConfig(os.getenv('LOGGING_CONF_FILE', 'logging.conf'))

log = logging.getLogger(__name__)

CONFIG = get_config()

PACKAGE_SEARCH_ENDPOINT = '/api/action/package_search'
RESOURCE_SHOW_ENDPOINT = '/api/action/resource_show'


async def datamart_search(
    search_pagination_params: SearchPaginationParams,
    query: Optional[str] = None,
    resource_id: Optional[str] = None,
    lucky_dip: Optional[bool] = None,
):
    results = []
    log.info(f'Query parameters: {locals()}')
    total_rows = None
    search_type = None
    n_rows_returned = None
    if resource_id is not None:
        resource = await search_by_resource_id(resource_id)
        results.append(resource)
        total_rows = 1
        search_type = 'resource_id'
    elif query is not None:
        results, total_rows, n_rows_returned = await search_by_query(
            query=query, search_pagination_params=search_pagination_params
        )
        search_type = 'filter query'
    elif lucky_dip:
        resource = await search_by_lucky_dip()
        results.append(resource)
        total_rows = 1
        search_type = 'lucky dip'
    else:
        log.info('No valid query parameters provided')
        search_type = 'No valid query parameters provided'

    resource_metadata = {
        'search_type': search_type,
        'total_datasets': total_rows,
        'n_resources': len(results),
        'help': 'https://docs.google.com/document/d/10Rkr0VxrGu2XuPjwtGhxTrDorGfXb6c8LqEWqlohtTo/edit?usp=sharing',
    }
    # Make paging_metadata
    if search_type == 'filter query':
        paging_metadata = calculate_paging_metadata(search_pagination_params, n_rows_returned, total_rows)
    else:
        paging_metadata = calculate_paging_metadata(search_pagination_params, results, total_rows)

    # Attach the resource_metadata to the results here
    results_dictionary = {
        'resource_metadata': resource_metadata,
        'paging_metadata': paging_metadata,
        'data': results,
    }

    return results_dictionary


async def search_by_query(
    query: Optional[str], search_pagination_params: SearchPaginationParams
) -> tuple[list[dict], Optional[int], Optional[int]]:
    results = []
    params = {}
    if query is not None:
        query = query.replace('tags:', 'vocab_Topics:')
        query = query.replace('countries:', 'groups:')
        log.info(f'query with query={query} - going to fq parameter in CKAN')
        params['fq'] = query

    params['start'] = search_pagination_params.offset
    params['rows'] = search_pagination_params.limit

    url = f'{CONFIG.HDX_DOMAIN}{PACKAGE_SEARCH_ENDPOINT}'
    response_items = await call_ckan_api(params, url)
    # Extract resources from response:
    total_rows = None
    n_results_returned = None
    if 'result' in response_items:
        n_results_returned = len(response_items['result']['results'])
        for dataset in response_items['result']['results']:
            for original_resource in dataset['resources']:
                resource = select_resource_fields(original_resource)
                resource = decorate_with_dataset_metadata(dataset, resource)
                resource = decorate_with_fs_check_info(original_resource, resource)

                results.append(resource)
        total_rows = response_items['result']['count']
    return results, total_rows, n_results_returned


async def call_ckan_api(params: dict, url: str) -> dict:
    t0 = time.time()
    log.info(f'Calling {url} with {params}')
    try:
        async with AsyncClient() as ac:
            response = await ac.get(url, params=params, timeout=60)
        # response.raise_for_status()
    except httpx.ConnectTimeout:
        log.info(f'**Timeout in {time.time() - t0:0.2f} seconds')
        response = None
    except Exception as exc:
        log.info(f'{exc}')
        raise exc

    if response is None:
        raise HTTPException(status_code=404, detail=f'Empty response from querying {url} with {params}')

    response_items = response.json()
    return response_items


def select_resource_fields(original_resource_record: dict) -> dict:
    selected_resource = {
        'resource_name': original_resource_record['name'],
        'dataset_hdx_id': original_resource_record['package_id'],
        'resource_hdx_id': original_resource_record['id'],
        'format': original_resource_record['format'],
        'download_url': original_resource_record['download_url'],
        'created': original_resource_record['created'],
        'last_modified': original_resource_record['last_modified'],
        'metadata_modified': original_resource_record['metadata_modified'],
        'position': original_resource_record['position'],
        'size': original_resource_record['size'],
    }

    return selected_resource


def decorate_with_dataset_metadata(dataset_metadata: dict, resource: dict) -> dict:
    resource['dataset_title'] = dataset_metadata.get('title', '')
    resource['dataset_name'] = dataset_metadata.get('name', '')
    resource['dataset_notes'] = dataset_metadata.get('notes', '')
    resource['dataset_subnational'] = dataset_metadata.get('subnational', '')
    resource['dataset_updated_by_script'] = dataset_metadata.get('updated_by_script', '')
    try:
        resource['dataset_organization'] = dataset_metadata['organization']['title']
    except KeyError:
        resource['dataset_organization'] = ''
    # License information
    license_title = dataset_metadata.get('license_title', '')
    license_source = dataset_metadata.get('dataset_source', '')
    license_year = datetime.datetime.now().isoformat()[0:4]
    license_str = f'Data by {license_source} ({license_year}). Licensed under {license_title}.'
    resource['dataset_license_and_attribution'] = license_str

    return resource


def decorate_with_fs_check_info(original_resource: dict, selected_resource: dict) -> dict:
    log.info(f"\n{original_resource.get('url', 'No URL')}, {original_resource.get('format', 'No format')}")
    selected_resource['n_sheets'] = 1
    selected_resource['sheet_names'] = []
    selected_resource['sheets'] = []
    if 'fs_check_info' in original_resource.keys():
        fs_check_info_dict = json.loads(original_resource['fs_check_info'])
        if isinstance(fs_check_info_dict, dict):
            log.info(f'fs_check_info was a dictionary: {fs_check_info_dict}')
            sheet_record = {}
            sheet_record['sheet_name'] = None
            sheet_record['ncols'] = None
            sheet_record['nrows'] = None
            sheet_record['headers'] = []
            sheet_record['hxl_headers'] = []
            sheet_record['is_hxlated'] = None
            selected_resource['sheets'].append(sheet_record)

            return selected_resource

        log.info(f'Number of fs_check_info_entries {len(fs_check_info_dict)}')
        fs_check_info_dict.reverse()  # This makes sure we get the most recent file structure check
        for entry in fs_check_info_dict:
            if (
                'File structure check completed' in entry['message']
                and 'error' not in entry['hxl_proxy_response'].keys()
            ):
                if len(entry['sheet_changes']) != 0:
                    log.info(entry['sheet_changes'])
                selected_resource['n_sheets'] = len(entry['hxl_proxy_response']['sheets'])
                number_of_sheets = len(entry['hxl_proxy_response']['sheets'])

                log.info(f'{number_of_sheets} sheets found in resource')
                for sheet in entry['hxl_proxy_response']['sheets']:
                    log.info(sheet['name'])
                    sheet_record = {}
                    selected_resource['sheet_names'].append(sheet['name'])
                    sheet_record['sheet_name'] = sheet['name']
                    sheet_record['ncols'] = sheet['ncols']
                    sheet_record['nrows'] = sheet['nrows']
                    sheet_record['headers'] = sheet.get('headers', '')
                    sheet_record['hxl_headers'] = sheet.get('hxl_headers', '')
                    sheet_record['is_hxlated'] = sheet.get('is_hxlated', '')
                    selected_resource['sheets'].append(sheet_record)
                break

    else:
        log.info('No fs_check_info key found')
        sheet_record = {}
        sheet_record['sheet_name'] = None
        sheet_record['ncols'] = None
        sheet_record['nrows'] = None
        sheet_record['headers'] = []
        sheet_record['hxl_headers'] = []
        sheet_record['is_hxlated'] = None
        selected_resource['sheets'].append(sheet_record)

    return selected_resource


async def search_by_resource_id(resource_id: str) -> dict:
    log.info('Resource_id query')
    params = {'id': resource_id}
    url = f'{CONFIG.HDX_DOMAIN}{RESOURCE_SHOW_ENDPOINT}'
    resource_response_items = await call_ckan_api(params, url)
    resource = {}
    if 'result' in resource_response_items:
        resource = select_resource_fields(resource_response_items['result'])
        params = {'fq': f'id:{resource["dataset_hdx_id"]}'}
        url = f'{CONFIG.HDX_DOMAIN}{PACKAGE_SEARCH_ENDPOINT}'
        response_items = await call_ckan_api(params, url)
        resource = decorate_with_dataset_metadata(response_items['result']['results'][0], resource)
        resource = decorate_with_fs_check_info(resource_response_items['result'], resource)

    return resource


async def search_by_lucky_dip() -> dict:
    log.info('Lucky dip query')
    # Call package search to get a number of datasets (we could hard code this) - filter to
    url = f'{CONFIG.HDX_DOMAIN}{PACKAGE_SEARCH_ENDPOINT}'
    count_params = {'fq': 'res_format:(CSV and XLS and XLSX)'}
    response_items = await call_ckan_api(count_params, url)
    n_datasets = response_items['result']['count']

    # Now do a second query with a random start, using the first to get the range of offsets possible
    # Make a random offset in the range 0, n datasets
    random_start = randrange(0, n_datasets)
    # query with offset (start) = random, limit (rows) = 1
    random_offset_params = {'fq': 'res_format:(CSV and XLS and XLSX)', 'start': random_start, 'rows': 1}
    random_item = await call_ckan_api(random_offset_params, url)
    # Pick first resource?
    resource = {}
    if 'result' in random_item:
        dataset = random_item['result']['results'][0]
        selected_resource = dataset['resources'][randrange(0, len(dataset['resources']))]
        resource = select_resource_fields(selected_resource)
        resource = decorate_with_dataset_metadata(dataset, resource)
        resource = decorate_with_fs_check_info(selected_resource, resource)

    log.info(json.dumps(resource))
    return resource
