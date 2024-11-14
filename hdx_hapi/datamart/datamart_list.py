import csv
import os

from typing import Optional
from httpx import Client
from hdx_hapi.datamart.datamart_responses import ListTypeEnum
from hdx_hapi.endpoints.util.util import PaginationParams

DATAFILE_ROOT = os.path.join(os.path.dirname(__file__), 'list-data')

"""
Sources for the list data:
1.	tags - from this file: https://docs.google.com/spreadsheets/d/e/2PACX-1vQD3ba751XbWS5GVwdJmzOF9mc7dnm56hE2U8di12JnpYkdseILmjfGSn1W7UVQzmHKSd6p8FWaXdFL/pub?gid=1768359211&single=true&output=csv - DONE 
2.	ISO-3 country codes - from this file: https://github.com/OCHA-DAP/hdx-python-country/blob/main/src/hdx/location/Countries%20%26%20Territories%20Taxonomy%20MVP%20-%20C%26T%20Taxonomy%20with%20HXL%20Tags.csv - DONE
3.	dataseries - from this file: https://github.com/OCHA-DAP/HDX_data_series/blob/main/23-11-dataseries_summary.csv  - DONE
4.	HAPI_resources (the existing endpoints) - from this file: https://hapi.humdata.org/openapi.json - DONE
5.	solr_query fields - from this file: https://docs.google.com/spreadsheets/d/1OzDQrnUZXiI1RuveE0HWVgbHDkohyJToRJnraDZMJOI/edit?pli=1&gid=0#gid=0 - DONE
6.	organizations – there is an organization list query with CKAN https://data.humdata.org/api/action/organization_list?all_fields=True - DONE

"""  # noqa


async def datamart_list(pagination_parameters: PaginationParams, list_type: Optional[ListTypeEnum]):
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
    elif list_type == ListTypeEnum.DATASERIES:
        with open(os.path.join(DATAFILE_ROOT, '2023-11-dataseries_summary.csv'), encoding='utf-8') as dataseries_file:
            rows = list(csv.DictReader(dataseries_file))

        results = [{'value': x['Data series name'], 'description': ''} for x in rows]
    elif list_type == ListTypeEnum.TAGS:
        with open(os.path.join(DATAFILE_ROOT, '2024-10-hdx-accepted-tags.csv'), encoding='utf-8') as tags_file:
            rows = list(csv.DictReader(tags_file))

        results = [{'value': x['tag'], 'description': x['description']} for x in rows]
    elif list_type == ListTypeEnum.HAPI_RESOURCES:
        openapi_url = 'https://hapi.humdata.org/openapi.json'
        with Client() as ac:
            response = ac.get(openapi_url)

        response.raise_for_status()

        results = []
        records = response.json()['paths']
        for path_ in records.keys():
            try:
                description = records[path_]['get']['description']
            except KeyError:
                description = ''
            row = {'value': path_, 'description': description}
            results.append(row)
    elif list_type == ListTypeEnum.ORGANIZATIONS:
        organisation_list_url = 'https://data.humdata.org/api/action/organization_list?all_fields=True'
        with Client() as ac:
            response = ac.get(organisation_list_url, timeout=60)

        response.raise_for_status()

        results = []
        records = response.json()['result']
        for record in records:
            row = {'value': record['name'], 'description': record['description']}
            results.append(row)
    elif list_type == ListTypeEnum.SOLR_QUERY_FIELDS:
        with open(
            os.path.join(DATAFILE_ROOT, '2024-11-08-hdx-fields-in-solr.csv'), encoding='utf-8'
        ) as query_fields_file:
            rows = list(csv.DictReader(query_fields_file))[1:]

        results = [
            {'value': x['Field Name'], 'description': x['Example (package_search)']}
            for x in rows
            if x['Queryable'].lower() == 'yes'
        ]

    try:
        results = results[pagination_parameters.offset : (pagination_parameters.offset + pagination_parameters.limit)]
    except IndexError:
        results = results

    return results
