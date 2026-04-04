from typing import Annotated

from pydantic import Field

from src.command.commands.base import CourseID
from src.command.commands.courses import CourseTitle
from src.query.dto.base import BaseDTO

NonNegativeInt = Annotated[int, Field(ge=0)]


class BaseCourseOverview(BaseDTO):
    course_id: CourseID
    title: CourseTitle
    short_description: str
    trainer_name: str
    no_of_modules: NonNegativeInt
    no_of_lessons: NonNegativeInt
    no_of_assignments: NonNegativeInt


class TraineeCourseOverview(BaseCourseOverview): ...


class TrainerCourseOverview(BaseCourseOverview):
    no_of_trainees: NonNegativeInt


class AdminCourseOverview(TrainerCourseOverview): ...
