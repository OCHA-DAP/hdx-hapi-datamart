from typing import Annotated, Optional

from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict


_LIMIT_DESCRIPTION = 'Maximum number of dataset to return. The system will not return more than 100 records.'
_OFFSET_DESCRIPTION = (
    'Number of records to skip in the response. Use in conjunction with the limit parameter to paginate.'
)
_APP_IDENTIFIER_DESCRIPTION = (
    'base64 encoded application name and email, as in `base64("app_name:email")`. '
    'This value can also be passed in the `X-HDX-HAPI-APP-IDENTIFIER` header. '
    'See the *encoded_app_identifier* endpoint.'
)

app_name_identifier_query = Query(max_length=512, min_length=4, description='A name for the calling application.')
email_identifier_query = Query(max_length=512, description='An email address.')

search_pagination_limit_query = Query(ge=0, le=100, example=5, description=_LIMIT_DESCRIPTION)
pagination_offset_query = Query(ge=0, description=_OFFSET_DESCRIPTION)
common_app_identifier_query = Query(max_length=512, description=_APP_IDENTIFIER_DESCRIPTION)


class SearchPaginationParams(BaseModel):
    offset: int = pagination_offset_query
    limit: int = search_pagination_limit_query

    model_config = ConfigDict(frozen=True)


class SearchCommonEndpointParams(SearchPaginationParams):
    app_identifier: Optional[str] = common_app_identifier_query


async def search_pagination_parameters(
    limit: Annotated[int, search_pagination_limit_query] = 10000,
    offset: Annotated[int, pagination_offset_query] = 0,
) -> SearchPaginationParams:
    return SearchPaginationParams(offset=offset, limit=limit)


async def search_common_endpoint_parameters(
    search_pagination_parameters: Annotated[SearchPaginationParams, Depends(search_pagination_parameters)],
    app_identifier: Annotated[Optional[str], common_app_identifier_query] = None,
) -> SearchCommonEndpointParams:
    return SearchCommonEndpointParams(**search_pagination_parameters.model_dump(), app_identifier=app_identifier)


def calculate_paging_metadata(pagination_parameters, decorated_results, total_rows):
    if isinstance(decorated_results, list):
        returned_rows = len(decorated_results)
    else:
        returned_rows = decorated_results

    if returned_rows < pagination_parameters.limit:
        next_offset = None
    else:
        next_offset = pagination_parameters.offset + pagination_parameters.limit
    paging_metadata = {
        'total_rows': total_rows,
        'returned_rows': returned_rows,
        'current_offset': pagination_parameters.offset,
        'next_offset': next_offset,
    }
    return paging_metadata
