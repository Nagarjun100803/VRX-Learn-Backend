from fastapi import APIRouter
from src.api.routers.users import router as UserAPIRouter
from src.api.routers.courses import router as CourseAPIRouter
from src.api.routers.enrollments import router as EnrollmentAPIRouter
from src.api.routers.modules import router as ModuleAPIRouter
from src.api.routers.lessons import router as LessonAPIRouter
from src.api.routers.media import router as MediaAPIRouter
from src.api.routers.assignments import router as AssignmentAPIRouter
from src.api.routers.assignment_submissions import router as AssignmentSubmissionAPIRouter

from src.api.routers.dashboards import trainee_router as TraineeDashboardAPIRouter
from src.api.routers.dashboards import trainer_router as TrainerDashboardAPIRouter
from src.api.routers.course_contents import trainee_router as TraineeCourseContentAPIRouter
from src.api.routers.course_contents import trainer_router as TrainerCourseContentAPIRouter
from src.api.routers.entity_list import trainee_router as TraineeEntityListAPIRouter
from src.api.routers.entity_list import trainer_router as TrainerEntityListAPIRouter


ROUTERS: list[APIRouter] = [
    UserAPIRouter,
    CourseAPIRouter,
    EnrollmentAPIRouter,
    ModuleAPIRouter,
    LessonAPIRouter,
    MediaAPIRouter,
    AssignmentAPIRouter,
    AssignmentSubmissionAPIRouter,
    TraineeDashboardAPIRouter,
    TrainerDashboardAPIRouter,
    TraineeCourseContentAPIRouter,
    TrainerCourseContentAPIRouter,
    TraineeEntityListAPIRouter,
    TrainerEntityListAPIRouter
]

__all__ = [
    "UserAPIRouter",
    "CourseAPIRouter",
    "EnrollmentAPIRouter",
    "ModuleAPIRouter",
    "LessonAPIRouter",
    "MediaAPIRouter",
    "AssignmentAPIRouter",
    "AssignmentSubmissionAPIRouter",
    "TraineeDashboardAPIRouter",
    "TrainerDashboardAPIRouter",
    "TraineeCourseContentAPIRouter",
    "TrainerCourseContentAPIRouter",
    "TraineeEntityListAPIRouter",
    "TrainerEntityListAPIRouter"
]
