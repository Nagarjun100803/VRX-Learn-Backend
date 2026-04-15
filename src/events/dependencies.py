from typing import Annotated

from fastapi import Depends

from src.cache import CacheInvalidator
from src.dependencies import cache_invalidator


def get_cache_invalidtor_service() -> CacheInvalidator:
    return cache_invalidator


CacheInvalidatorServiceDependency = Annotated[
    CacheInvalidator, Depends(get_cache_invalidtor_service)
]
