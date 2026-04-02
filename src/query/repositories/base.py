from typing import (
    Any,
    Callable,
    Coroutine,
    Literal,
    Optional,
    ParamSpec,
    Type,
    TypeVar,
    Union,
    overload,
)

from pydantic import BaseModel

from src.database import AsyncPgDBManager


class BaseQueryRepository:
    def __init__(self, db: AsyncPgDBManager) -> None:
        self.db = db


BT = TypeVar("BT", bound=BaseModel)
P = ParamSpec("P")  # Preserve the original function signature.


@overload
def map_to_dto(
    dto: Type[BT], dto_mode: Literal["single"]
) -> Callable[[Callable[P, Any]], Callable[P, Coroutine[Any, Any, Optional[BT]]]]: ...


@overload
def map_to_dto(
    dto: Type[BT], dto_mode: Literal["list"]
) -> Callable[[Callable[P, Any]], Callable[P, Coroutine[Any, Any, list[BT]]]]: ...


def map_to_dto(
    dto: Type[BT], dto_mode: Literal["single", "list"]
) -> Callable[
    [Callable[P, Any]], Callable[P, Coroutine[Any, Any, Union[Optional[BT], list[BT]]]]
]:
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

        >>> @map_to_dto(dto=CourseCard, dto_mode="list")
        ... async def get_courses(self) -> list[CourseCard]:
        ...     pass
    """

    def decorator(
        fn: Callable[P, Any],
    ) -> Callable[P, Coroutine[Any, Any, Union[Optional[BT], list[BT]]]]:

        async def wrapper(
            *args: P.args, **kwargs: P.kwargs
        ) -> Union[Optional[BT], list[BT]]:
            result = await fn(*args, **kwargs)
            if dto_mode == "single":
                return dto.model_validate(dict(result)) if result else None
            return [dto.model_validate(dict(item)) for item in result]

        return wrapper

    return decorator
