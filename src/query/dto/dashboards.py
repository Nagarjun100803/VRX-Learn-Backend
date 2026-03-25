from typing import Annotated, Optional

from pydantic import StringConstraints

from src.query.dto.base import BaseDTO
from src.command.commands.base import CourseID
from src.command.commands.courses import CourseTitle


class CourseCard(BaseDTO):
    course_id: CourseID
    course_name: CourseTitle
    trainer_name: Annotated[str, StringConstraints(to_upper=True)]
    thumbnail_url: Optional[str] = None


class TrainerKPI(BaseDTO):
    assigned_courses: int
    total_learners: int
    

class AssignedCourse(BaseDTO):
    course_id: CourseID
    course_name: CourseTitle
    total_trainees: int
    thumbnail_url: Optional[str] = None
    

class AdminKPI(BaseDTO):
    total_users: int
    total_courses: int
    total_enrollments: int


class AdminCourseCard(BaseDTO):
    id: CourseID
    course_name: CourseTitle
    trainer_name: str
    total_trainees: int
    
