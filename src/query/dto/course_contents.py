from typing import Optional

from src.command.commands.assignments import AssignmentTitle
from src.command.commands.base import (
    AssignmentID,
    CourseID,
    LessonID,
    MediaID,
    ModuleID,
    UserID,
)
from src.command.commands.courses import (
    CourseLongDescription,
    CourseShortDescription,
    CourseTitle,
)
from src.command.commands.lessons import LessonDescription, LessonTitle
from src.command.commands.media import AllowedContentTypes
from src.command.commands.modules import ModuleDescription, ModuleTitile
from src.query.dto.base import BaseDTO


class LessonDetail(BaseDTO):
    id: LessonID
    title: LessonTitle
    description: Optional[LessonDescription] = None
    media_id: MediaID
    mime_type: AllowedContentTypes
    filename: str


class BaseModuleDetail(BaseDTO):
    id: ModuleID
    title: ModuleTitile
    description: Optional[ModuleDescription] = None


class TrainerModuleDetail(BaseModuleDetail): ...


class TraineeModuleDetail(BaseModuleDetail):
    restricted: bool
    lessons: list[LessonDetail]


class TraineeCourseDetail(BaseDTO):
    id: CourseID
    title: CourseTitle
    short_description: Optional[CourseShortDescription] = None


class TrainerCourseDetail(TraineeCourseDetail):
    long_description: Optional[CourseLongDescription] = None
    trainer_id: UserID
    trainer_name: str


class AssignmentDetail(BaseDTO):
    id: AssignmentID
    title: AssignmentTitle


class TraineeCourseContent(BaseDTO):
    course: TraineeCourseDetail
    modules: list[TraineeModuleDetail]


class TrainerCourseContent(BaseDTO):
    course: TrainerCourseDetail
    modules: list[TrainerModuleDetail]
    assignments: list[AssignmentDetail]


class CourseContentRequestSchema(BaseDTO):
    course_id: CourseID
    viewer_id: UserID
