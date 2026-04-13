from enum import StrEnum
from typing import Annotated, Literal, Optional, Union

from pydantic import Field, StringConstraints

from src.command.commands.base import (
    AuditFields,
    BaseCmd,
    CourseBase,
    NullField,
    UserID,
)
from src.command.commands.validator import UpdateValidatorMixin


class CourseType(StrEnum):
    PRE_RECORDED = "pre-recorded"
    LIVE = "live"


class LiveCourseDetails(BaseCmd):
    type: Literal[CourseType.LIVE] = CourseType.LIVE
    # We can add more fields, if we want.


CourseTitle = Annotated[
    str,
    StringConstraints(
        to_upper=True, min_length=1, strip_whitespace=True, max_length=200
    ),
]
CourseShortDescription = Annotated[str, StringConstraints(max_length=600)]
CourseLongDescription = Annotated[str, StringConstraints(max_length=5000)]
Price = Annotated[float, Field(gt=1000)]


class RecordedCourseDetails(BaseCmd):
    type: Literal[CourseType.PRE_RECORDED] = CourseType.PRE_RECORDED
    total_hours: Annotated[float, Field(gt=0)]
    price: Price


class CourseCreateCore(BaseCmd):
    title: CourseTitle
    short_description: Optional[CourseShortDescription] = None
    long_description: Optional[CourseLongDescription] = None
    thumbnail: Optional[str] = None
    details: Union[RecordedCourseDetails, LiveCourseDetails] = Field(
        discriminator="type"
    )
    trainer_id: UserID


class CourseCreate(CourseCreateCore):
    created_by: UserID

    def get_slug(self) -> str:
        return self.title.lower().strip().replace(" ", "-")


class CourseDelete(CourseBase):
    deleted_by: UserID


class CourseInfoUpdateCore(UpdateValidatorMixin, BaseCmd):
    title: Annotated[Optional[CourseTitle], NullField]
    short_description: Annotated[Optional[CourseShortDescription], NullField]
    long_description: Annotated[Optional[CourseLongDescription], NullField]
    thumbnail: Annotated[Optional[str], NullField]
    trainer_id: Annotated[Optional[UserID], NullField]


class CourseInfoUpdate(CourseInfoUpdateCore, CourseBase):
    updated_by: UserID


class RecordedCourseDetailsUpdateCore(UpdateValidatorMixin, BaseCmd):
    total_hours: Annotated[Optional[float], NullField]
    price: Annotated[Optional[Price], NullField]


class RecordedCourseDetailsUpdate(RecordedCourseDetailsUpdateCore, CourseBase):
    updated_by: UserID


class CourseGet(CourseBase): ...


class CourseGetByIDQuery(CourseGet):
    viewer_id: UserID


class Course(AuditFields, CourseCreateCore, CourseBase):
    slug: Annotated[Optional[str], NullField]
