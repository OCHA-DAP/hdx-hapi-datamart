import os
import pandas
from hdx_hapi.datamart.datamart_data import parse_data_filter

FIXTURE_DIRECTORY = os.path.join(os.path.dirname(__file__), 'fixtures')

BLANK_FIRST_LINE_SPREADSHEET = os.path.join(FIXTURE_DIRECTORY, 'blank_first_line.xlsx')


def test_parse_data_filter():
    field_, value_ = parse_data_filter('field_name:field_value')

    assert field_ == 'field_name'
    assert value_ == 'field_value'


def test_parse_data_filter_with_spaces():
    field_, value_ = parse_data_filter(' field_name: field_value ')
    assert field_ == 'field_name'
    assert value_ == 'field_value'


def test_data_content():
    dataframe = pandas.read_excel(BLANK_FIRST_LINE_SPREADSHEET)
    dataframe = dataframe.astype(str)
    results = dataframe.to_dict('records')

    print(results, flush=True)

    assert results == [
        {'Unnamed: 0': 'Alpha', 'Unnamed: 1': 'Beta', 'Unnamed: 2': 'Delta'},
        {'Unnamed: 0': '1', 'Unnamed: 1': '5', 'Unnamed: 2': '3'},
    ]

    n_unnamed = sum([1 for x in results[0].keys() if 'unnamed' in x.lower()])

    assert n_unnamed == 3
