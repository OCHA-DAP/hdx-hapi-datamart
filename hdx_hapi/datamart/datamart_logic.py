from typing import Optional

from hdx_hapi.datamart.datamart_list import datamart_list
from hdx_hapi.datamart.datamart_responses import ListTypeEnum
from hdx_hapi.endpoints.util.util import PaginationParams


# Data sources for the list endpoint:
# Dataseries: https://raw.githubusercontent.com/OCHA-DAP/HDX_data_series/refs/heads/main/23-11-dataseries_summary.csv
# Tags: https://docs.google.com/spreadsheets/d/e/2PACX-1vQD3ba751XbWS5GVwdJmzOF9mc7dnm56hE2U8di12JnpYkdseILmjfGSn1W7UVQzmHKSd6p8FWaXdFL/pub?gid=1768359211&single=true&output=csv
# country codes: https://raw.githubusercontent.com/OCHA-DAP/hdx-python-country/refs/heads/main/src/hdx/location/Countries%20%26%20Territories%20Taxonomy%20MVP%20-%20C%26T%20Taxonomy%20with%20HXL%20Tags.csv
# HAPI resources: https://hapi.humdata.org/openapi.json
async def get_datamart_list_srv(pagination_parameters: PaginationParams, list_type: ListTypeEnum):
    results = await datamart_list(pagination_parameters, list_type)
    return results


async def get_datamart_search_srv(
    pagination_parameters: PaginationParams,
):
    return [{'placeholder': 'hello'}]


async def get_datamart_data_srv(
    pagination_parameters: PaginationParams,
):
    return [{'placeholder': 'hello'}]
