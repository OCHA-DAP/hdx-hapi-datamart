from enum import Enum
from pydantic import ConfigDict, Field, HttpUrl
from hdx_hapi.config.doc_snippets import (
    DOC_HDX_DATASET_ID,
    DOC_HDX_RESOURCE_FORMAT,
    DOC_HDX_RESOURCE_ID,
    truncate_query_description,
)
from hdx_hapi.endpoints.models.base import HapiBaseModel


class DatamartListResponse(HapiBaseModel):
    value: str = Field(max_length=512, description='List entry value')
    description: str = Field(max_length=512, description='List entry description')

    model_config = ConfigDict(from_attributes=True)


# Should we just use the ResourceResponse here?
class DatamartSearchResponse(HapiBaseModel):
    resource_name: str = Field(
        max_length=256,
        description=(
            'The resource name on HDX. In combination with the dataset UUIDs'
            'from the `dataset_hdx_id` and `resource_hdx_id` fields respectively, it can be used to '
            'construct a URL to download the resource: '
            '`https://data.humdata.org/dataset/[dataset_hdx_id]/resource/[resource_hdx_id]/download/[name]`, '
            'which can be found in the `download_url` field.'
        ),
    )
    dataset_hdx_id: str = Field(max_length=36, description=truncate_query_description(DOC_HDX_DATASET_ID))
    resource_hdx_id: str = Field(max_length=36, description=truncate_query_description(DOC_HDX_RESOURCE_ID))
    format: str = Field(max_length=32, description=truncate_query_description(DOC_HDX_RESOURCE_FORMAT))
    download_url: HttpUrl = Field(
        description='A URL to directly download the resource file from HDX, in the format '
        'specified in the `format` field.'
    )

    model_config = ConfigDict(from_attributes=True)


class DatamartDataResponse(HapiBaseModel):
    placeholder: str = Field(max_length=512, description='Datamart Data Placeholder Response')

    model_config = ConfigDict(from_attributes=True)


class ListTypeEnum(str, Enum):
    TAGS = 'tags'
    ISO3_COUNTRY_CODES = 'country_codes'
    DATASERIES = 'dataseries'
    HAPI_RESOURCES = 'hapi_resources'
    SOLR_QUERY_FIELDS = 'solr_query_fields'
