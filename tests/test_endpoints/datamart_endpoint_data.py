from hdx_hapi.datamart.datamart_responses import ListTypeEnum

datamart_endpoint_data = {
    '/api/v1/datamart/list': {
        'query_parameters': {
            'list_type': ListTypeEnum.ISO3_COUNTRY_CODES.value,
        },
        'expected_fields': [
            'value',
            'description',
        ],
    }
}
