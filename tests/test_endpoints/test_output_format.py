import pytest
import logging
import csv
from httpx import AsyncClient
from main import app

log = logging.getLogger(__name__)

# ENDPOINT_ROUTER = '/api/admin1'
# endpoint_data = endpoint_data[ENDPOINT_ROUTER]
# query_parameters = endpoint_data['query_parameters']
# expected_fields = endpoint_data['expected_fields']
ENDPOINT_ROUTER_LIST = [
    '/api/v1/admin1',
    '/api/v1/admin2',
    '/api/v1/age_range',
    '/api/v1/dataset',
    '/api/v1/gender',
    '/api/v1/location',
    '/api/v1/themes/3W',
    '/api/v1/org',
    '/api/v1/org_type',
    '/api/v1/themes/population',
    '/api/v1/population_group',
    '/api/v1/population_status',
    '/api/v1/themes/food_security',
    '/api/v1/themes/national_risk',
    '/api/v1/themes/humanitarian_needs',
    '/api/v1/resource',
    '/api/v1/sector',
]


@pytest.mark.parametrize('endpoint_router', ENDPOINT_ROUTER_LIST)
@pytest.mark.asyncio
async def test_output_format(event_loop, refresh_db, endpoint_router):
    log.info('started ' + endpoint_router)
    # JSON by default
    async with AsyncClient(app=app, base_url='http://test') as ac:
        response = await ac.get(endpoint_router)
    assert response.status_code == 200
    assert response.headers.get('content-type') == 'application/json', 'The output should be in json format'
    no_rows_json = len(response.json())
    assert no_rows_json > 0

    # CSV
    async with AsyncClient(app=app, base_url='http://test', params={'output_format': 'csv'}) as ac:
        response = await ac.get(endpoint_router)
    assert response.status_code == 200
    assert response.headers.get('content-type') == 'text/csv; charset=utf-8', 'The output should be in csv format'
    csv_dictreader = csv.DictReader(response.text.split('\r\n'))
    no_rows_csv = 0
    for item in csv_dictreader:
        no_rows_csv = no_rows_csv + 1

    assert no_rows_csv == no_rows_json, 'The number of rows are different csv vs json for ' + endpoint_router