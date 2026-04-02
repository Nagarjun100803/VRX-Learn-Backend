from datetime import datetime
from functools import partial
from typing import Annotated, ClassVar, Optional, Type, Union

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    TypeAdapter,
    field_serializer,
    field_validator,
)
from pydantic.alias_generators import to_camel

ID = Union[int, str]


def to_internal_id(id: ID, cls: Type["EntityBase"]) -> int:
    """
    Helper function that takes EntityBase object and
    converts that as integer.

    e.g., id U-1 becomes 1
    """
    return cls(id=id).id  # type: ignore


def to_external_id(id: ID, cls: Type["EntityBase"]) -> str:
    """
    Helper function that takes EntityBase object and
    converts that as string with prefix.

    e.g., id 1 becomes U-1
    """
    obj = cls(id=id)  # type: ignore
    return f"{cls.PREFIX}-{obj.id}"


class BaseCmd(BaseModel):
    """
        Base Command Model for API requests and command payloads on the write side.

        This model provides a centralized configuration for all Commands used in
        the application's write layer (CQRS command side). It standardizes naming
        conventions and validation behavior across all derived Command classes.

        Key behaviors:
        - Accepts both Python `snake_case` and `camelCase` field names during
          validation. This allows flexibility for API clients sending write
          operation payloads.
        - Allows models to be constructed directly from objects using attribute
          access (useful for internal command creation).
        - Ignores extra fields that may appear in request payloads to provide
          forward compatibility with client versions.
        - Does NOT convert field names in API responses (responses use snake_case
          internally for write operations).

        Configuration:
        - `validate_by_name=True`
            Allows validation using the original snake_case field names.

        - `validate_by_alias=True`
            Allows validation using camelCase aliases (auto-generated).

        - `alias_generator=to_camel`
            Automatically generates camelCase aliases for all fields, enabling
            camelCase input without explicit alias definitions.

        - `from_attributes=True`
            Enables model creation from objects with attributes (e.g. for internal
            command construction or data transfer objects).

        - `extra="ignore"`
            Ignores unknown fields instead of raising validation errors. This
            provides forward compatibility when API clients send additional fields.

        Example
        -------
    ```python
        class CreateCourseCmd(BaseCmd):
            title: str
            description: str
            trainer_id: int
            is_active: bool = True
    ```

        Input payloads accepted:

        snake_case:
    ```json
        {
            "title": "Advanced FastAPI",
            "description": "Build production APIs",
            "trainer_id": 5,
            "is_active": true
        }
    ```

        camelCase:
    ```json
        {
            "title": "Advanced FastAPI",
            "description": "Build production APIs",
            "trainerId": 5,
            "isActive": true
        }
    ```

        Both payloads create identical command objects:
    ```python
        CreateCourseCmd(
            title="Advanced FastAPI",
            description="Build production APIs",
            trainer_id=5,
            is_active=True
        )
    ```

        Usage in API write operations:
    ```python
        @router.post("/courses")
        async def create_course(cmd: CreateCourseCmd):
            # cmd accepts both snake_case and camelCase from request body
            # Internally uses snake_case field names
            return await course_service.create(cmd)
    ```

        Notes
        -----
        All Commands in the write layer should inherit from this class to ensure
        consistent validation behavior and support both naming conventions for API
        requests. Commands represent write operations (CREATE, UPDATE, DELETE) and
        focus on input validation rather than response serialization.
    """

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
        from_attributes=True,
        extra="ignore",
    )


class EntityBase(BaseCmd):
    PREFIX: ClassVar[str] = "B"
    id: int

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value: Union[str, int]):

        # Case 0: Already an int.
        if isinstance(value, int):
            return value

        # Case 1: Prefixed String. eg. 'B-123' or 'b-123'
        value = str(value).strip()
        if (
            value.upper().startswith(f"{cls.PREFIX}-")
            and value[len(cls.PREFIX) + 1 :].isdigit()
        ):
            return int(value.split("-")[-1])

        # Case 2: Plain Number String.
        if value.isdigit():
            return int(value)

        raise ValueError(
            (
                f"Invalid id format: {value!r}. "
                f"Expected {cls.PREFIX}-<number> or just a number."
                "eg. 'B-123' or 'b-123' or '123' or 123"
            )
        )

    @field_serializer("id", when_used="json")
    def serialize_id(self, value: int) -> str:
        return f"{self.PREFIX}-{value}"


class CourseBase(EntityBase):
    PREFIX: ClassVar[str] = "C"


class UserBase(EntityBase):
    PREFIX: ClassVar[str] = "U"


class ModuleBase(EntityBase):
    PREFIX: ClassVar[str] = "M"


class AssignmentBase(EntityBase):
    PREFIX: ClassVar[str] = "A"


class EnrollmentBase(EntityBase):
    PREFIX: ClassVar[str] = "E"


class MediaBase(EntityBase):
    PREFIX: ClassVar[str] = "ME"


class LessonBase(EntityBase):
    PREFIX: ClassVar[str] = "L"


class AssignmentSubmissionBase(EntityBase):
    PREFIX: ClassVar[str] = "AS"


BaseID = Annotated[
    int,
    BeforeValidator(partial(to_internal_id, cls=EntityBase)),
    PlainSerializer(partial(to_external_id, cls=EntityBase)),
]


UserID = Annotated[
    int,
    BeforeValidator(partial(to_internal_id, cls=UserBase)),
    PlainSerializer(partial(to_external_id, cls=UserBase), when_used="json"),
]


CourseID = Annotated[
    int,
    BeforeValidator(partial(to_internal_id, cls=CourseBase)),
    PlainSerializer(partial(to_external_id, cls=CourseBase), when_used="json"),
]


ModuleID = Annotated[
    int,
    BeforeValidator(partial(to_internal_id, cls=ModuleBase)),
    PlainSerializer(partial(to_external_id, cls=ModuleBase), when_used="json"),
]


LessonID = Annotated[
    int,
    BeforeValidator(partial(to_internal_id, cls=LessonBase)),
    PlainSerializer(partial(to_external_id, cls=LessonBase), when_used="json"),
]


AssignmentID = Annotated[
    int,
    BeforeValidator(partial(to_internal_id, cls=AssignmentBase)),
    PlainSerializer(partial(to_external_id, cls=AssignmentBase), when_used="json"),
]


EnrollmentID = Annotated[
    int,
    BeforeValidator(partial(to_internal_id, cls=EnrollmentBase)),
    PlainSerializer(partial(to_external_id, cls=EnrollmentBase), when_used="json"),
]


MediaID = Annotated[
    int,
    BeforeValidator(partial(to_internal_id, cls=MediaBase)),
    PlainSerializer(partial(to_external_id, cls=MediaBase), when_used="json"),
]


AssignmentSubmissionID = Annotated[
    int,
    BeforeValidator(partial(to_internal_id, cls=AssignmentSubmissionBase)),
    PlainSerializer(
        partial(to_external_id, cls=AssignmentSubmissionBase), when_used="json"
    ),
]


any_id_adaptor = TypeAdapter(ID)


class CreateAuditFields(BaseCmd):
    created_at: Optional[datetime] = None
    created_by: Optional[UserID] = None


class UpdateAuditFields(BaseCmd):
    updated_at: Optional[datetime] = None
    updated_by: Optional[UserID] = None


class DeleteAuditField(BaseCmd):
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UserID] = None


class AuditFields(DeleteAuditField, UpdateAuditFields, CreateAuditFields):
    """Helper class define the audit of the action."""


NullField = Field(default=None, examples=[None])
