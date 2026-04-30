from enum import Enum
from typing import TypedDict, Union


class EndpointDoc(TypedDict, total=False):
    summary: str
    description: str
    response_description: str
    responses: dict[Union[int, str], dict]
    deprecated: bool
    openapi_extra: dict
    tags: list[Union[str, Enum]]
