import csv
import datetime
import logging
import logging.config
import os
import time

from httpx import Client

logging.config.fileConfig(os.getenv('LOGGING_CONF_FILE', 'logging.conf'))

log = logging.getLogger(__name__)

DATAMART_ROOT_URL = 'http://localhost:8844'
APP_IDENTIFIER = 'SERYSU5URVJOQUxfZG9jc191aV9paDppYW4uaG9wa2luc29uQGh1bWRhdGEub3Jn'

RESULT_TEMPLATE = {
    'datetime': None,
    'resource_id': None,
    'resource_name': None,
    'download_url': None,
    'size': None,
    'returned_row_count': None,
    'query_time': None,
    'success': None,
}


def get_app_identifier(
    email_address: str = 'ian.hopkinson%40humdata.org',
    app_name='HDXINTERNAL_datamart_benchmarker',
) -> str:
    app_identifier_url = (
        f'{DATAMART_ROOT_URL}/api/v1/encode_app_identifier?application={app_name}&email={email_address}'
    )
    with Client() as ac:
        response = ac.get(app_identifier_url)

    response.raise_for_status()
    app_identifier = response.json()['encoded_app_identifier']
    return app_identifier


def climada_benchmark():
    log.info('started datamart benchmark test')
    app_identifier = get_app_identifier()

    output_filepath = os.path.join(os.path.dirname(__file__), 'benchmark-results', 'climada-benchmark.csv')
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

    print(already_done_set, flush=True)
    params = {'filter_query': r'dataset_source:ETH\ Zurich\ Climada', 'app_identifier': app_identifier}
    with Client(base_url=DATAMART_ROOT_URL, params=params) as ac:
        response = ac.get('/api/v1/datamart/search')

    response.raise_for_status()

    results = []
    for i, record in enumerate(response.json()['data'], start=1):
        if i > 5:
            break
        if record['resource_hdx_id'] in already_done_set:
            print(f"{i}, {record['resource_name']} - already done", flush=True)
            continue

        t0 = time.time()
        print(i, record['resource_name'], record['size'], flush=True)
        params = {
            'download_url': record['download_url'],
            'app_identifier': app_identifier,
        }
        with Client(base_url=DATAMART_ROOT_URL, params=params) as ac:
            response = ac.get('/api/v1/datamart/data')
        response.raise_for_status()
        query_time = f'{time.time() - t0:0.2f}'
        print(f'{time.time() - t0:0.2f}, {len(response.json()["data"])}', flush=True)

        result_row = RESULT_TEMPLATE.copy()
        result_row['datetime'] = datetime.datetime.now().isoformat()
        result_row['resource_id'] = record['resource_hdx_id']
        result_row['resource_name'] = record['resource_name']
        result_row['download_url'] = record['download_url']
        result_row['size'] = record['size']
        result_row['returned_row_count'] = len(response.json()['data'])
        result_row['query_time'] = query_time
        result_row['success'] = True
        with open(output_filepath, 'a', encoding='utf-8') as output_file:
            writer = csv.DictWriter(output_file, fieldnames=result_row.keys())
            writer.writerow(result_row)
        results.append(result_row)


if __name__ == '__main__':
    climada_benchmark()
