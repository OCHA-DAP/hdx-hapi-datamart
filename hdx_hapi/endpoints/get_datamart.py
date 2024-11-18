from typing import Annotated, Optional
from fastapi import Depends, Query, APIRouter

from hdx_hapi.config.doc_snippets import (
    DOC_HDX_RESOURCE_ID,
    DOC_HDX_DATASET_IN_RESOURCE_NAME,
    DOC_SEE_DATASET,
    DOC_HDX_RESOURCE_STUB,
)
from hdx_hapi.endpoints.models.base import HapiGenericResponse
from hdx_hapi.datamart.datamart_responses import (
    DatamartSearchResponse,
    DatamartDataResponse,
    DatamartListResponse,
    ListTypeEnum,
    BackendEnum,
)
from hdx_hapi.endpoints.util.util import (
    CommonEndpointParams,
    OutputFormat,
    common_endpoint_parameters,
)
from hdx_hapi.services.csv_transform_logic import transform_result_to_csv_stream_if_requested

from hdx_hapi.datamart.datamart_logic import get_datamart_search_srv, get_datamart_data_srv, get_datamart_list_srv


router = APIRouter(
    tags=['Datamart'],
)


@router.get(
    '/api/datamart/list',
    response_model=HapiGenericResponse[DatamartListResponse],
    summary='Get lists of entities available to query the HAPI datamart i.e. tags, country codes, dataseries names',
    include_in_schema=False,
)
@router.get(
    '/api/v1/datamart/list',
    response_model=HapiGenericResponse[DatamartListResponse],
    summary='Get lists of entities available to query the HAPI datamart i.e. tags, country codes, dataseries names',
)
async def get_datamart_list(
    common_parameters: Annotated[CommonEndpointParams, Depends(common_endpoint_parameters)],
    list_type: Annotated[
        Optional[ListTypeEnum], Query(max_length=32, description='The required list name')
    ] = ListTypeEnum.ISO3_COUNTRY_CODES,
    output_format: OutputFormat = OutputFormat.JSON,
):
    """
    Provide a facility to retreive lists of entities such as tags, country codes, HAPI resources and dataseries names
    for use with the search and data endpoints
    """
    result = await get_datamart_list_srv(pagination_parameters=common_parameters, list_type=list_type)
    return transform_result_to_csv_stream_if_requested(result, output_format, DatamartListResponse)


@router.get(
    '/api/datamart/search',
    response_model=HapiGenericResponse[DatamartSearchResponse],
    summary='Get information about resources in the HAPI datamart which come from HDX',
    include_in_schema=False,
)
@router.get(
    '/api/v1/datamart/search',
    response_model=HapiGenericResponse[DatamartSearchResponse],
    summary='Get information about resources in the HAPI datamart which come from HDX',
)
async def get_datamart_search(
    common_parameters: Annotated[CommonEndpointParams, Depends(common_endpoint_parameters)],
    resource_hdx_id: Annotated[Optional[str], Query(max_length=36, description=f'{DOC_HDX_RESOURCE_ID}')] = None,
    main_query: Annotated[
        Optional[str], Query(max_length=1024, description='Search HDX using a Solr main query expression')
    ] = None,
    filter_query: Annotated[
        Optional[str], Query(max_length=1024, description='Search HDX using a Solr filter query expression')
    ] = None,
    lucky_dip: Annotated[Optional[bool], Query(description='Return a random resource record from HDX')] = None,
    output_format: OutputFormat = OutputFormat.JSON,
):
    """
    Provide a search facility to retreive metadata from HDX for use in the datamart /data endpoint
    """
    result = await get_datamart_search_srv(
        pagination_parameters=common_parameters,
        resource_hdx_id=resource_hdx_id,
        main_query=main_query,
        filter_query=filter_query,
        lucky_dip=lucky_dip,
    )

    return transform_result_to_csv_stream_if_requested(result, output_format, DatamartSearchResponse)


@router.get(
    '/api/datamart/data',
    response_model=None,  # HapiGenericResponse[DatamartSearchResponse],
    summary='Get data from the HAPI datamart which come from HDX',
    include_in_schema=False,
)
@router.get(
    '/api/v1/datamart/data',
    response_model=None,  # HapiGenericResponse[DatamartSearchResponse],
    summary='Get data from the HAPI datamart which come from HDX',
)
async def get_datamart_data(
    common_parameters: Annotated[CommonEndpointParams, Depends(common_endpoint_parameters)],
    download_url: Annotated[Optional[str], Query(max_length=2048, description='A direct download_url for HDX')] = None,
    resource_hdx_id: Annotated[Optional[str], Query(max_length=36, description=f'{DOC_HDX_RESOURCE_ID}')] = None,
    dataset_hdx_stub: Annotated[
        Optional[str], Query(max_length=128, description=f'{DOC_HDX_DATASET_IN_RESOURCE_NAME} {DOC_SEE_DATASET}')
    ] = None,
    resource_hdx_stub: Annotated[Optional[str], Query(max_length=128, description=f'{DOC_HDX_RESOURCE_STUB}')] = None,
    lucky_dip: Annotated[Optional[bool], Query(description='Return a random data file from HDX')] = None,
    sheet_name: Annotated[
        Optional[str], Query(max_length=36, description='The name or index of the required sheet in a spreadsheet')
    ] = None,
    data_filter: Annotated[
        Optional[str], Query(max_length=512, description='A filter definition like fieldname:value')
    ] = None,
    backend: Annotated[
        Optional[BackendEnum], Query(max_length=32, description='The backend, for development purposes')
    ] = BackendEnum.PANDAS,
    output_format: OutputFormat = OutputFormat.JSON,
):
    """
    Provide a access to data in the HAPI datamart
    """
    result = await get_datamart_data_srv(
        pagination_parameters=common_parameters,
        download_url=download_url,
        resource_hdx_id=resource_hdx_id,
        dataset_hdx_stub=dataset_hdx_stub,
        resource_hdx_stub=resource_hdx_stub,
        lucky_dip=lucky_dip,
        sheet_name=sheet_name,
        data_filter=data_filter,
        backend=backend,
    )

    formatted_data = transform_result_to_csv_stream_if_requested(result['data'], output_format, DatamartDataResponse)

    response = None
    if isinstance(formatted_data, dict):
        response = {}
        response['data'] = formatted_data['data']
        response['resource_metadata'] = result['resource_metadata']
        response['paging_metadata'] = result['paging_metadata']
    else:
        response = formatted_data

    return response
