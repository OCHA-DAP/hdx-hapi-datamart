import csv
import os

from hdx_hapi.datamart.datamart_responses import ListTypeEnum
from hdx_hapi.endpoints.util.util import PaginationParams

DATAFILE_ROOT = os.path.join(os.path.dirname(__file__), 'list-data')


async def datamart_list(pagination_parameters: PaginationParams, list_type: ListTypeEnum):
    results = []
    if list_type == ListTypeEnum.ISO3_COUNTRY_CODES:
        with open(
            os.path.join(DATAFILE_ROOT, '2024-10-23-countries-and-territories-taxonomy-hxl-tags.csv'), encoding='utf-8'
        ) as countries_file:
            # Pop off the HXL row
            rows = list(csv.DictReader(countries_file))[1:]

        results = [
            {'value': x['ISO 3166-1 Alpha 3-Codes'], 'description': x['Preferred Term']}
            for x in rows
            if len(x['ISO 3166-1 Alpha 3-Codes']) == 3
        ]

    try:
        results = results[pagination_parameters.offset : (pagination_parameters.offset + pagination_parameters.limit)]
    except IndexError:
        results = results

    return results
