import pytest
import logging

from httpx import AsyncClient
from main import app

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
