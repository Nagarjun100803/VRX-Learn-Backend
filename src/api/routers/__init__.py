from fastapi import APIRouter
from src.api.routers.users import router as UserAPIRouter
from src.api.routers.courses import router as CourseAPIRouter
from src.api.routers.enrollments import router as EnrollmentAPIRouter
from src.api.routers.modules import router as ModuleAPIRouter
from src.api.routers.lessons import router as LessonAPIRouter
from src.api.routers.media import router as MediaAPIRouter
from src.api.routers.assignments import router as AssignmentAPIRouter
from src.api.routers.assignment_submissions import router as AssignmentSubmissionAPIRouter


ROUTERS: list[APIRouter] = [
    UserAPIRouter,
    CourseAPIRouter,
    EnrollmentAPIRouter,
    ModuleAPIRouter,
    LessonAPIRouter,
    MediaAPIRouter,
    AssignmentAPIRouter,
    AssignmentSubmissionAPIRouter
]

__all__ = [
    "UserAPIRouter",
    "CourseAPIRouter",
    "EnrollmentAPIRouter",
    "ModuleAPIRouter",
    "LessonAPIRouter",
    "MediaAPIRouter",
    "AssignmentAPIRouter",
    "AssignmentSubmissionAPIRouter"
]
