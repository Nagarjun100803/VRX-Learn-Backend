from functools import wraps
from typing import Callable, Literal, Type, TypeVar, Union, overload

from asyncpg import Record
from pydantic import BaseModel

from src.database import AsyncPgDBManager


class BaseQueryRepository:
    
    def __init__(self, db: AsyncPgDBManager) -> None:
        self.db = db
    


BT = TypeVar("BT", bound=BaseModel)


@overload
def map_to_dto(dto: Type[BT], dto_mode: Literal["single"]) -> Callable[[Callable], Callable[..., BT]]: ...

@overload
def map_to_dto(dto: Type[BT], dto_mode: Literal["list"]) -> Callable[[Callable], Callable[..., list[BT]]]: ...


def map_to_dto(dto: Type[BT], dto_mode: Literal["single", "list"]):
    """
    Decorator to map asyncpg Record(s) to Pydantic DTO(s).
    
    Args:
        dto: Pydantic DTO model class
        result_type: Literal["single", "list"]
    
    Returns:
        Decorated function that returns DTO(s)
    
    Example:
        >>> @map_to_dto(dto=CourseCard, dto_mode="single")
        ... async def get_course(self, course_id: int) -> Optional[CourseCard]:
        ...     pass
    """
    
    def decorator(fn: Callable) -> Callable:
        
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            result: Union[Record, list[Record]] = await fn(*args, **kwargs)
            
            if dto_mode == "single":
                if result is not None:
                    return dto.model_validate(dict(result))
                else:
                    return None
            return [dto.model_validate(dict(res))for res in result]

        return wrapper
    
    return decorator
