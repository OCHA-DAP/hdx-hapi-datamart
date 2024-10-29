import pandas
from typing import Optional
from hdx_hapi.endpoints.util.util import PaginationParams

from hdx_hapi.config.config import get_config

CONFIG = get_config()

PACKAGE_SEARCH_ENDPOINT = '/api/action/package_search'
RESOURCE_SHOW_ENDPOINT = '/api/action/resource_show'


async def datamart_data(pagination_parameters: PaginationParams, download_url: Optional[str]):
    results = []

    if download_url is not None:
        dataframe = pandas.read_csv(download_url)
        dataframe = dataframe.astype(str)
        results = dataframe.to_dict('records')
        # Pop HXL row if it exists - not yet implemented - you can set offset=1 if you know it's HXL-ated
        try:
            results = results[
                pagination_parameters.offset : (pagination_parameters.offset + pagination_parameters.limit)
            ]
        except IndexError:
            results = results

    return results
