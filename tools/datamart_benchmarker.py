import csv
import json
import datetime
import logging
import logging.config
import os
import sys
import time

from httpx import Client

logging.config.fileConfig(os.getenv('LOGGING_CONF_FILE', 'logging.conf'))

log = logging.getLogger(__name__)

LOCAL_DATAMART_ROOT_URL = 'http://localhost:8844'
DEV_DATAMART_ROOT_URL = 'https://dev.hapi-humdata-org.ahconu.org'

APP_IDENTIFIER = 'SERYSU5URVJOQUxfZG9jc191aV9paDppYW4uaG9wa2luc29uQGh1bWRhdGEub3Jn'

RESULT_TEMPLATE = {
    'datetime': None,
    'server': None,
    'resource_id': None,
    'resource_name': None,
    'download_url': None,
    'status_code': None,
    'file_format': None,
    'has_fs_check_info': None,
    'size': None,
    'returned_row_count': None,
    'query_time': None,
    'success': None,
}


def get_app_identifier(
    email_address: str = 'ian.hopkinson%40humdata.org',
    app_name: str = 'HDXINTERNAL_datamart_benchmarker',
    root_url: str = LOCAL_DATAMART_ROOT_URL,
) -> str:
    app_identifier_url = f'{root_url}/api/v1/encode_app_identifier?application={app_name}&email={email_address}'
    with Client() as ac:
        response = ac.get(app_identifier_url, timeout=60)

    response.raise_for_status()
    app_identifier = response.json()['encoded_app_identifier']
    return app_identifier


def benchmark(filename, query, server):
    log.info(f'Started datamart benchmarking: {filename}')
    root_url = None
    run_start_time = time.time()
    if server == 'local':
        root_url = LOCAL_DATAMART_ROOT_URL
    elif server == 'dev':
        root_url = DEV_DATAMART_ROOT_URL

    app_identifier = get_app_identifier(root_url=root_url)

    # Setup output file
    output_filepath = os.path.join(os.path.dirname(__file__), 'benchmark-results', filename)
    already_done_set = set()
    if not os.path.exists(output_filepath):
        with open(
            output_filepath,
            'w',
            encoding='utf-8',
        ) as output_file:
            fieldnames = RESULT_TEMPLATE.keys()
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()
    else:
        with open(output_filepath, 'r', encoding='utf-8') as output_file:
            rows = list(csv.DictReader(output_file))

            if len(rows) != 0:
                already_done_set = {x['resource_id'] for x in rows}
            else:
                already_done_set = set()

    params = query
    params['app_identifier'] = app_identifier
    params['limit'] = 20

    # Do the search
    try:
        with Client(base_url=root_url, params=params, timeout=60) as ac:
            response = ac.get('/api/v1/datamart/search')

        response.raise_for_status()
    except Exception as exc:
        log.info(f'Failed on search with query params {params}, error {str(exc)}')
        raise

    # Generate results for each result
    results = []
    n_downloads = 0
    for i, record in enumerate(response.json()['data'], start=1):
        if record['resource_hdx_id'] in already_done_set:
            print(f"{i}, {record['resource_name']} - already done", flush=True)
            continue
        n_downloads += 1
        # if n_downloads > 5:
        #     break

        t0 = time.time()
        print(i, record['resource_name'], record['size'], flush=True)
        params = {
            'download_url': record['download_url'],
            'app_identifier': app_identifier,
        }
        result_row = RESULT_TEMPLATE.copy()
        result_row['datetime'] = datetime.datetime.now().isoformat()
        result_row['server'] = server
        result_row['resource_id'] = record['resource_hdx_id']
        result_row['resource_name'] = record['resource_name']
        result_row['download_url'] = record['download_url']
        result_row['size'] = record['size']

        try:
            with Client(base_url=root_url, params=params, timeout=60) as ac:
                response = ac.get('/api/v1/datamart/data')
            result_row['status_code'] = response.status_code
            response.raise_for_status()
            query_time = f'{time.time() - t0:0.2f}'
            print(f'{query_time}, {len(response.json()['data'])}', flush=True)
            result_row['returned_row_count'] = len(response.json()['data'])
            result_row['query_time'] = query_time
            result_row['success'] = True
            result_row['file_format'] = response.json()['resource_metadata']['format']
            # print(json.dumps(response.json()['resource_metadata'], indent=4), flush=True)
            has_fs_check_info = 'True'
            if response.json()['resource_metadata']['sheets'][0]['sheet_name'] is None:
                #    print('Found fs_check_info', flush=True)
                has_fs_check_info = 'False'
            result_row['has_fs_check_info'] = has_fs_check_info
        except Exception as exc:
            result_row['status_code'] = response.status_code
            query_time = f'{time.time() - t0:0.2f}'
            print(f'{query_time}, failed with {exc}', flush=True)
            result_row['returned_row_count'] = None
            result_row['query_time'] = query_time
            result_row['success'] = False

        with open(output_filepath, 'a', encoding='utf-8') as output_file:
            writer = csv.DictWriter(output_file, fieldnames=result_row.keys())
            writer.writerow(result_row)
        results.append(result_row)
        log.info('Waiting for 2 seconds')
        time.sleep(2)

    print(f'\nDid {n_downloads} tests in {time.time() - run_start_time:0.2f} seconds', flush=True)


if __name__ == '__main__':
    target = None
    server = 'local'
    date_ = datetime.datetime.now().isoformat()[0:10]
    if len(sys.argv) > 1:
        target = sys.argv[1]
    if len(sys.argv) > 2:
        server = sys.argv[2]

    if target is None:
        print('Target must be specified on commandline, one of climada|insecurity-insight|lucky_dip', flush=True)
    if target == 'climada':
        filename = f'{date_}-climada-benchmark-{server}.csv'
        query = {'filter_query': r'dataset_source:ETH\ Zurich\ Climada'}
        benchmark(filename, query, server)
    elif target == 'insecurity-insight':
        filename = f'{date_}-insecurity-insight-benchmark-{server}.csv'
        query = {'filter_query': r'dataset_source:Insecurity\ Insight'}
        benchmark(filename, query, server)
    elif target == 'lucky_dip':
        filename = f'{date_}-lucky-dip-csv-xls-{server}.csv'
        while True:
            query = {'lucky_dip': True}
            benchmark(filename, query, server)
