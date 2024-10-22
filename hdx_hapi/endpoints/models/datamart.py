from pydantic import ConfigDict, Field
from hdx_hapi.endpoints.models.base import HapiBaseModel


class DatamartListResponse(HapiBaseModel):
    placeholder: str = Field(max_length=512, description='Datamart List Placeholder Response')

    model_config = ConfigDict(from_attributes=True)


class DatamartSearchResponse(HapiBaseModel):
    placeholder: str = Field(max_length=512, description='Datamart Search Placeholder Response')

    model_config = ConfigDict(from_attributes=True)


class DatamartDataResponse(HapiBaseModel):
    placeholder: str = Field(max_length=512, description='Datamart Data Placeholder Response')

    model_config = ConfigDict(from_attributes=True)
