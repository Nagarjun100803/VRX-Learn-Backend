from fastapi import APIRouter

from src.api.routers.assignment_contents import (
    trainee_router as TraineeAssignmentContentAPIRouter,
)
from src.api.routers.assignment_contents import (
    trainer_router as TrainerAssignmentContentAPIRouter,
)
from src.api.routers.assignment_submissions import (
    router as AssignmentSubmissionAPIRouter,
)
from src.api.routers.assignments import router as AssignmentAPIRouter
from src.api.routers.course_contents import (
    trainee_router as TraineeCourseContentAPIRouter,
)
from src.api.routers.course_contents import (
    trainer_router as TrainerCourseContentAPIRouter,
)
from src.api.routers.courses import router as CourseAPIRouter
from src.api.routers.dashboards import admin_router as AdminDashboardAPIRouter
from src.api.routers.dashboards import trainee_router as TraineeDashboardAPIRouter
from src.api.routers.dashboards import trainer_router as TrainerDashboardAPIRouter
from src.api.routers.enrollments import router as EnrollmentAPIRouter
from src.api.routers.entity_list import admin_router as AdminEntityListAPIRouter
from src.api.routers.entity_list import (
    admin_search_router as AdminEntitySearchAPIRouter,
)
from src.api.routers.entity_list import trainee_router as TraineeEntityListAPIRouter
from src.api.routers.entity_list import trainer_router as TrainerEntityListAPIRouter
from src.api.routers.lessons import router as LessonAPIRouter
from src.api.routers.media import router as MediaAPIRouter
from src.api.routers.modules import router as ModuleAPIRouter
from src.api.routers.users import router as UserAPIRouter

ROUTERS: list[APIRouter] = [
    # Write routers.
    UserAPIRouter,
    CourseAPIRouter,
    EnrollmentAPIRouter,
    ModuleAPIRouter,
    LessonAPIRouter,
    MediaAPIRouter,
    AssignmentAPIRouter,
    AssignmentSubmissionAPIRouter,
    # Read Routers.
    AdminDashboardAPIRouter,
    TraineeDashboardAPIRouter,
    TrainerDashboardAPIRouter,
    TraineeCourseContentAPIRouter,
    TrainerCourseContentAPIRouter,
    AdminEntityListAPIRouter,
    AdminEntitySearchAPIRouter,
    TraineeEntityListAPIRouter,
    TrainerEntityListAPIRouter,
    TraineeAssignmentContentAPIRouter,
    TrainerAssignmentContentAPIRouter,
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
    "AdminDashboardAPIRouter",
    "TraineeDashboardAPIRouter",
    "TrainerDashboardAPIRouter",
    "TraineeCourseContentAPIRouter",
    "TrainerCourseContentAPIRouter",
    "AdminEntityListAPIRouter",
    "AdminEntitySearchAPIRouter",
    "TraineeEntityListAPIRouter",
    "TrainerEntityListAPIRouter",
    "TraineeAssignmentContentAPIRouter",
    "TrainerAssignmentContentAPIRouter",
]
