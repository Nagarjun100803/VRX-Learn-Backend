from math import ceil
from typing import Annotated, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator
from pydantic.alias_generators import to_camel


class BaseDTO(BaseModel):
    """
    Base Data Transfer Object (DTO) for API responses and request payloads.

    This model provides a centralized configuration for all DTOs used in the
    application's read layer (CQRS query side) and API schemas. It standardizes
    naming conventions and validation behavior across all derived DTO classes.

    Key behaviors:
    - Converts Python `snake_case` field names to `camelCase` when serialized
      in API responses.
    - Accepts both `snake_case` and `camelCase` field names during validation.
      This allows flexibility for clients sending payloads.
    - Allows models to be constructed directly from objects or database rows
      using attribute access.
    - Ignores extra fields that may appear in SQL query results (for example
      when using joins in query repositories).

    Configuration:
    - `alias_generator=to_camel`
        Automatically generates camelCase aliases for all fields.

    - `validate_by_name=True`
        Allows validation using the original snake_case field names.

    - `validate_by_alias=True`
        Allows validation using the generated camelCase aliases.

    - `from_attributes=True`
        Enables model creation from objects with attributes (e.g. ORM objects
        or database record objects).

    - `extra="ignore"`
        Ignores unknown fields instead of raising validation errors. This is
        useful when mapping SQL query results containing additional columns.

    Example
    -------
    ```python
    class CourseCardDTO(BaseDTO):
        course_id: int
        course_name: str
        trainer_name: str
    ```

    Input payloads accepted:

    snake_case:
    ```json
    {
        "course_id": 1,
        "course_name": "Advanced FastAPI",
        "trainer_name": "Nagarjun"
    }
    ```

    camelCase:
    ```json
    {
        "courseId": 1,
        "courseName": "Advanced FastAPI",
        "trainerName": "Nagarjun"
    }
    ```

    API response serialization:

    ```json
    {
        "courseId": 1,
        "courseName": "Advanced FastAPI",
        "trainerName": "Nagarjun"
    }
    ```

    Notes
    -----
    All DTOs in the API layer should inherit from this class to ensure
    consistent serialization behavior and reduce repeated configuration.
    """
    
    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
        from_attributes=True,
        extra="ignore"
    )




class PageMeta(BaseDTO):
    page: Annotated[int, Field(ge=1)]
    limit: Literal[10, 15, 20, 25] = 10
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


T = TypeVar("T", bound=BaseDTO)

class Paginated[T](BaseDTO):
    data: list[T]
    page: int
    limit: int
    total_items: int
    
    @computed_field
    @property
    def total_pages(self) -> int:
        return ceil(self.total_items / self.limit) if self.total_items > 0 else 0 