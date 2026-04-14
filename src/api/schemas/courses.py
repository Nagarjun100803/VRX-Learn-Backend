from typing import Optional

from src.command.commands.base import BaseCmd, CourseID, UserID
from src.command.commands.courses import (
    CourseCreateCore,
    CourseInfoUpdateCore,
    CourseLongDescription,
    CourseShortDescription,
    RecordedCourseDetailsUpdateCore,
)


class CourseCreateSchema(CourseCreateCore): ...


class CourseOutSchema(BaseCmd):
    id: CourseID
    title: str
    slug: str
    short_description: Optional[CourseShortDescription] = None
    long_description: Optional[CourseLongDescription] = None
    trainer_id: UserID
    created_by: UserID


class CourseInfoUpdateSchema(CourseInfoUpdateCore): ...


class RecordedCourseDetailsUpdateSchema(RecordedCourseDetailsUpdateCore): ...
