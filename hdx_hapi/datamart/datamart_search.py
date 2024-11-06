import random
import time
import httpx

from random import randrange
from typing import Optional
from httpx import AsyncClient
from hdx_hapi.endpoints.util.util import PaginationParams

from hdx_hapi.config.config import get_config

CONFIG = get_config()

PACKAGE_SEARCH_ENDPOINT = '/api/action/package_search'
RESOURCE_SHOW_ENDPOINT = '/api/action/resource_show'


async def datamart_search(
    pagination_params: PaginationParams,
    filter_query: Optional[str],
    main_query: Optional[str],
    resource_id: Optional[str] = None,
    lucky_dip: Optional[bool] = None,
):
    results = []

    if resource_id is not None:
        params = {'id': resource_id}
        url = f'{CONFIG.HDX_DOMAIN}{RESOURCE_SHOW_ENDPOINT}'
        response_items = await call_ckan_api(params, url)

        if 'result' in response_items:
            resource = select_resource_fields(response_items['result'])
            params = {'fq': f'id:{resource["dataset_hdx_id"]}'}
            url = f'{CONFIG.HDX_DOMAIN}{PACKAGE_SEARCH_ENDPOINT}'
            response_items = await call_ckan_api(params, url)
            resource = decorate_with_dataset_metadata(response_items['result']['results'][0], resource)
            results.append(resource)
    elif filter_query is not None or main_query is not None:
        params = {}
        if filter_query is not None:
            params['fq'] = filter_query
        if main_query is not None:
            params['q'] = main_query

        url = f'{CONFIG.HDX_DOMAIN}{PACKAGE_SEARCH_ENDPOINT}'
        response_items = await call_ckan_api(params, url)
        # Extract resources from response:
        if 'result' in response_items:
            for dataset in response_items['result']['results']:
                for original_resource in dataset['resources']:
                    resource = select_resource_fields(original_resource)
                    resource = decorate_with_dataset_metadata(dataset, resource)

                    results.append(resource)
    elif lucky_dip:
        # Call package search to get a number of datasets (we could hard code this) - filter to
        url = f'{CONFIG.HDX_DOMAIN}{PACKAGE_SEARCH_ENDPOINT}'
        params = {'fq': 'res_format:(CSV and XLS)'}
        response_items = await call_ckan_api(params, url)
        n_datasets = response_items['result']['count']

        # Make a random offset in the range 0, n datasets
        random_start = randrange(0, n_datasets)
        # query with offset (start) = random, limit (rows) = 1
        params['start'] = random_start
        params['rows'] = 1
        random_item = await call_ckan_api(params, url)
        # Pick first resource?
        if 'result' in random_item:
            dataset = random_item['result']['results'][0]
            selected_resource = dataset['resources'][randrange(0, len(dataset['resources']))]
            resource = select_resource_fields(selected_resource)
            resource = decorate_with_dataset_metadata(dataset, resource)

            results.append(resource)

    return results


async def call_ckan_api(params: dict, url: str) -> dict:
    t0 = time.time()
    try:
        async with AsyncClient() as ac:
            response = await ac.get(url, params=params, timeout=60)
        response.raise_for_status()
    except httpx.ConnectTimeout:
        print(f'**Timeout in {time.time() - t0:0.2f} seconds')
        response = None

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
    return resource
