import pytest
import logging

from httpx import AsyncClient
from main import app
from tests.test_endpoints.datamart_endpoint_data import datamart_endpoint_data

log = logging.getLogger(__name__)

DATAMART_ENDPOINTS = ['/api/v1/datamart/list', '/api/v1/datamart/search', '/api/v1/datamart/data']


@pytest.mark.parametrize(
    'endpoint',
    DATAMART_ENDPOINTS,
)
@pytest.mark.asyncio
async def test_get_datamart_endpoints(event_loop, endpoint):
    log.info('started test_get_datamart_list')
    async with AsyncClient(app=app, base_url='http://test') as ac:
        response = await ac.get(endpoint)
    assert response.status_code == 200
    response_items = response.json()['data']
    assert len(response_items) > 0, 'There should be at least one entry in the response'


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
        print(param_name, param_value, flush=True)
        async with AsyncClient(app=app, base_url='http://test', params={param_name: param_value}) as ac:
            response = await ac.get(endpoint)

        assert response.status_code == 200
        assert len(response.json()['data']) > 0, (
            f'There should be at least one entry for parameter "{param_name}" with value "{param_value}" '
            'in the database'
        )
