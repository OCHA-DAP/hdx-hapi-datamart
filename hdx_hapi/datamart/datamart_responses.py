from enum import Enum
from pydantic import ConfigDict, Field
from hdx_hapi.endpoints.models.base import HapiBaseModel


class DatamartListResponse(HapiBaseModel):
    value: str = Field(max_length=512, description='List entry value')
    description: str = Field(max_length=512, description='List entry description')

    model_config = ConfigDict(from_attributes=True)


class DatamartSearchResponse(HapiBaseModel):
    placeholder: str = Field(max_length=512, description='Datamart Search Placeholder Response')

    model_config = ConfigDict(from_attributes=True)


class DatamartDataResponse(HapiBaseModel):
    placeholder: str = Field(max_length=512, description='Datamart Data Placeholder Response')

    model_config = ConfigDict(from_attributes=True)


class ListTypeEnum(str, Enum):
    TAGS = 'tags'
    ISO3_COUNTRY_CODES = 'country_codes'
    DATASERIES = 'dataseries'
    HAPI_RESOURCES = 'hapi_resources'
