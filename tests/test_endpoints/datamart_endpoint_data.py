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
    },
    '/api/v1/datamart/search': {
        'query_parameters': {
            'resource_hdx_id': '96b24403-0de4-4652-bb76-f585c04b5e6d',
        },
        'expected_fields': [
            'resource_name',
            'dataset_hdx_id',
            'resource_hdx_id',
            'format',
            'download_url',
        ],
    },
}
