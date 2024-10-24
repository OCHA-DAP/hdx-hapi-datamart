import pytest

from inspect import signature
from hdx_hapi.endpoints.get_idps import get_idps
from hdx_hapi.endpoints.get_affected_people import get_humanitarian_needs
from hdx_hapi.endpoints.get_operational_presence import get_operational_presence
from hdx_hapi.endpoints.get_conflict_events import get_conflict_event
from hdx_hapi.endpoints.get_food_security import get_food_security
from hdx_hapi.endpoints.get_population import get_population
from hdx_hapi.endpoints.get_wfp_market import get_wfp_market
from hdx_hapi.endpoints.get_population import get_poverty_rate
from hdx_hapi.endpoints.get_food_price import get_food_price

from hdx_hapi.services.poverty_rate_logic import get_poverty_rates_srv
from hdx_hapi.db.dao.poverty_rate_dao import poverty_rates_view_list


GEOGRAPHIC_PARAMETERS = {
    'location_ref',
    'location_code',
    'location_name',
    'admin1_ref',
    'admin1_code',
    'admin1_name',
    'provider_admin1_name',
    'admin2_ref',
    'admin2_code',
    'admin2_name',
    'provider_admin2_name',
    'has_hrp',
    'in_gho',
}

ENDPOINT_FUNCTION_LIST = [
    get_idps,
    get_humanitarian_needs,
    get_operational_presence,
    get_conflict_event,
    get_food_security,
    get_population,
    get_wfp_market,
    get_food_price,
]


@pytest.mark.parametrize(
    'endpoint_function',
    ENDPOINT_FUNCTION_LIST,
)
def test_call_signatures_parametrically(endpoint_function):
    function_signature = signature(endpoint_function)

    query_parameters_set = {x for x, _ in function_signature.parameters.items()}

    print(f'{GEOGRAPHIC_PARAMETERS.difference(query_parameters_set)}', flush=True)
    assert GEOGRAPHIC_PARAMETERS.issubset(query_parameters_set)


def test_poverty_rate_call_signature():
    router_function_signature = signature(get_poverty_rate)
    service_function_signature = signature(get_poverty_rates_srv)
    list_function_signature = signature(poverty_rates_view_list)

    router_parameters_set = {x for x, _ in router_function_signature.parameters.items()}
    service_parameters_set = {x for x, _ in service_function_signature.parameters.items()}
    list_parameters_set = {x for x, _ in list_function_signature.parameters.items()}

    assert 'provider_admin1_name' in router_parameters_set

    assert router_parameters_set - set(['common_parameters', 'output_format']) == service_parameters_set - set(
        ['pagination_parameters', 'ref_period_parameters']
    )
    assert service_parameters_set == list_parameters_set
