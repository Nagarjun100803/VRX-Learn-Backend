from typing import Annotated, Optional

from pydantic import Field, computed_field

from src.command.commands.base import CourseID, LessonID, ModuleID
from src.command.commands.courses import CourseShortDescription, CourseTitle
from src.command.commands.lessons import (
    AllowedLessonAttachmentContentTypes,
    LessonTitle,
)
from src.command.commands.modules import ModuleTitle
from src.query.dto.base import BaseDTO

NonNegativeInt = Annotated[int, Field(ge=0)]


class BaseCourseOverview(BaseDTO):
    course_id: CourseID
    title: CourseTitle
    short_description: Optional[str] = None
    trainer_name: str
    no_of_modules: NonNegativeInt
    no_of_lessons: NonNegativeInt
    no_of_assignments: NonNegativeInt


class TraineeCourseOverview(BaseCourseOverview): ...


class TrainerCourseOverview(BaseCourseOverview):
    no_of_trainees: NonNegativeInt


class AdminCourseOverview(TrainerCourseOverview): ...


class CoursePreviewCourseDetail(BaseDTO):
    id: CourseID
    title: CourseTitle
    description: Optional[CourseShortDescription] = None
    trainer: str


class CoursePreviewLessonDetail(BaseDTO):
    id: LessonID
    title: LessonTitle
    is_preview: bool
    mime_type: AllowedLessonAttachmentContentTypes


class CoursePreviewModuleDetail(BaseDTO):
    id: ModuleID
    title: ModuleTitle
    lessons: list[CoursePreviewLessonDetail]

    @computed_field
    def number_of_lessons(self) -> int:
        return len(self.lessons)


class CoursePreview(BaseDTO):
    course: CoursePreviewCourseDetail
    modules: list[CoursePreviewModuleDetail]
