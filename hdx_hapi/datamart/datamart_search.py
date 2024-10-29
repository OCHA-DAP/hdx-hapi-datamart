from typing import Optional
from httpx import AsyncClient
from hdx_hapi.endpoints.util.util import PaginationParams

from hdx_hapi.config.config import get_config

CONFIG = get_config()

PACKAGE_SEARCH_ENDPOINT = '/api/action/package_search'
RESOURCE_SHOW_ENDPOINT = '/api/action/resource_show'


async def datamart_search(pagination_params: PaginationParams, fq: Optional[str], resource_id: Optional[str] = None):
    results = []

    # if fq is not None:
    #     params = {'fq': fq, 'start': pagination_parameters.offset, 'rows': pagination_parameters.limit}
    #     async with AsyncClient(app=app, base_url=CONFIG.HDX_DOMAIN, params=params) as ac:
    #         response = await ac.get(PACKAGE_SEARCH_ENDPOINT)
    if resource_id is not None:
        params = {'id': resource_id}
        async with AsyncClient() as ac:
            url = f'{CONFIG.HDX_DOMAIN}{RESOURCE_SHOW_ENDPOINT}'
            response = await ac.get(url, params=params)
        response.raise_for_status()
        response_items = response.json()

        if 'result' in response_items:
            resource = {
                'resource_name': response_items['result']['name'],
                'dataset_hdx_id': response_items['result']['package_id'],
                'resource_hdx_id': response_items['result']['id'],
                'format': response_items['result']['format'],
                'download_url': response_items['result']['download_url'],
            }

            results.append(resource)

    return results
