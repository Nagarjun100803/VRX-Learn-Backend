from typing import Optional

from src.command.commands.assignments import AssignmentInstruction
from src.command.commands.courses import CourseShortDescription, CourseTitle
from src.command.commands.modules import ModuleDescription, ModuleTitile
from src.command.commands.base import AssignmentID, CourseID, LessonID, MediaID, ModuleID, UserID
from src.command.commands.lessons import LessonTitle
from src.query.dto.base import BaseDTO


class LessonDetail(BaseDTO):
    id: LessonID
    title: LessonTitle
    media_id: MediaID
    filename: str
    

class ModuleDetail(BaseDTO):
    id: ModuleID
    title: ModuleTitile
    description: Optional[ModuleDescription] = None
    lessons: list[LessonDetail]
    

class CourseDetail(BaseDTO):
    id: CourseID
    title: CourseTitle
    short_description: Optional[CourseShortDescription] = None


class AssignmentDetail(BaseDTO):
    id: AssignmentID
    instruction: Optional[AssignmentInstruction] = None 
    media_id: Optional[MediaID]
    filename: Optional[str] = None
    

class TraineeCourseContent(BaseDTO):
    course: CourseDetail
    module: list[ModuleDetail]


class TrainerCourseContent(BaseDTO):
    course: CourseDetail
    module: list[ModuleDetail]
    assignment: list[AssignmentDetail]


class CourseContentRequestSchema(BaseDTO):
    course_id: CourseID
    viewer_id: UserID