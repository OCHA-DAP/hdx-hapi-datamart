import json
import os

from hdx_hapi.datamart.datamart_search import (
    select_resource_fields,
    decorate_with_dataset_metadata,
    decorate_with_fs_check_info,
)

FIXTURE_DIRECTORY = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_decorate_with_fs_check_info():
    # search_records_filepath = os.path.join(FIXTURE_DIRECTORY, '2024-11-12-gibraltar-healthsites.json')
    # search_records_filepath = os.path.join(FIXTURE_DIRECTORY, '2024-11-12-climada.json')
    search_records_filepath = os.path.join(FIXTURE_DIRECTORY, '2024-11-12-insecurity-insight.json')

    with open(search_records_filepath, encoding='UTF-8') as search_records_file:
        search_response = json.load(search_records_file)

    results = []
    for dataset in search_response['result']['results']:
        for original_resource in dataset['resources']:
            selected_resource = select_resource_fields(original_resource)
            selected_resource = decorate_with_dataset_metadata(dataset, selected_resource)
            selected_resource = decorate_with_fs_check_info(original_resource, selected_resource)

            print(json.dumps(selected_resource, indent=4), flush=True)
            results.append(selected_resource)

    assert False
