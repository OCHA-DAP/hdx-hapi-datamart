import pytest
import logging

from httpx import AsyncClient
from sqlalchemy import True_
from hdx_hapi.datamart.datamart_responses import ListTypeEnum
from main import app
from tests.test_endpoints.datamart_endpoint_data import datamart_endpoint_data

log = logging.getLogger(__name__)

DATAMART_ENDPOINTS = ['/api/v1/datamart/list', '/api/v1/datamart/search', '/api/v1/datamart/data']


@pytest.mark.parametrize(
    'endpoint',
    DATAMART_ENDPOINTS,
)
@pytest.mark.asyncio
async def test_get_with_query_params(event_loop, endpoint):
    log.info(f'started {endpoint}')
    if endpoint in datamart_endpoint_data:
        endpoint_data = datamart_endpoint_data[endpoint]
    else:
        return
    query_parameters = endpoint_data['query_parameters']
    expected_fields = endpoint_data['expected_fields']
    for param_name, param_value in query_parameters.items():
        log.info(f'Testing with parameter: {param_name}={param_value}')
        if endpoint == '/api/v1/datamart/search':
            params = {param_name: param_value, 'limit': 5}
        else:
            params = {param_name: param_value}
        async with AsyncClient(app=app, base_url='http://test', params=params) as ac:
            response = await ac.get(endpoint)

        assert response.status_code == 200, f'Failed for {param_name}={param_value}'

        assert len(response.json()['data']) > 0, (
            f'There should be at least one entry for parameter "{param_name}" with value "{param_value}" '
            'in the database'
        )

        for field in expected_fields:
            assert field in response.json()['data'][0], f'Field "{field}" not found in the response'

        assert len(response.json()['data'][0]) == len(
            expected_fields
        ), 'Response has a different number of fields than expected'


@pytest.mark.asyncio
async def test_get_search(event_loop):
    log.info('started datamart search test')
    params = {'query': r'dataset_source:ETH\ Zurich\ Climada', 'limit': 10}
    async with AsyncClient(app=app, base_url='http://test', params=params) as ac:
        response = await ac.get('/api/v1/datamart/search')

    assert response.status_code == 200
    assert len(response.json()['data']) == 157


@pytest.mark.asyncio
async def test_get_search_lucky_dip(event_loop):
    log.info('Started datamart lucky dip search test')
    params = {'lucky_dip': True, 'limit': 10}
    async with AsyncClient(app=app, base_url='http://test', params=params) as ac:
        response = await ac.get('/api/v1/datamart/search')

    assert response.status_code == 200
    assert len(response.json()['data']) == 1


@pytest.mark.asyncio
async def test_get_data_file_not_found(event_loop):
    log.info('Started datamart file not found test')
    params = {'download_url': "i don't exist.csv"}
    async with AsyncClient(app=app, base_url='http://test', params=params) as ac:
        response = await ac.get('/api/v1/datamart/data')

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_data_by_resource_and_dataset_name(event_loop):
    log.info('Started datamart data by resource and dataset name ')
    params = {'dataset_hdx_stub': 'climada-litpop-dataset', 'resource_hdx_stub': 'admin1-summaries-litpop.csv'}
    async with AsyncClient(app=app, base_url='http://test', params=params) as ac:
        response = await ac.get('/api/v1/datamart/data')

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_paging(event_loop):
    log.info('Started datamart data by resource and dataset name ')
    params = {'list_type': ListTypeEnum.ISO3_COUNTRY_CODES.value, 'limit': 300}
    async with AsyncClient(app=app, base_url='http://test', params=params) as ac:
        single_page_response = await ac.get('/api/v1/datamart/list')
    assert single_page_response.status_code == 200

    assert len(single_page_response.json()['data']) == 249

    offset = 0
    composite = []
    while True:
        params = {'list_type': ListTypeEnum.ISO3_COUNTRY_CODES.value, 'limit': 50, 'offset': offset}
        async with AsyncClient(app=app, base_url='http://test', params=params) as ac:
            print(params, flush=True)
            page_response = await ac.get('/api/v1/datamart/list')
        assert page_response.status_code == 200
        composite.extend(page_response.json()['data'])
        offset = page_response.json()['paging_metadata']['next_offset']

        if offset is None:
            break

    assert len(single_page_response.json()['data']) == len(composite)
