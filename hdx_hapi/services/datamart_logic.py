from typing import Optional

from hdx_hapi.endpoints.util.util import PaginationParams


async def get_list_search_srv(
    pagination_parameters: PaginationParams,
):
    return [{'placeholder': 'hello'}]


async def get_datamart_search_srv(
    pagination_parameters: PaginationParams,
):
    return [{'placeholder': 'hello'}]


async def get_datamart_data_srv(
    pagination_parameters: PaginationParams,
):
    return [{'placeholder': 'hello'}]
