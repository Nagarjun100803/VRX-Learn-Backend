from fastapi import APIRouter
from src.api.routers.users import router as UserAPIRouter
from src.api.routers.courses import router as CourseAPIRouter
from src.api.routers.enrollments import router as EnrollmentAPIRouter
from src.api.routers.modules import router as ModuleAPIRouter
from src.api.routers.lessons import router as LessonAPIRouter
from src.api.routers.media import router as MediaAPIRouter
from src.api.routers.assignments import router as AssignmentAPIRouter
from src.api.routers.assignment_submissions import router as AssignmentSubmissionAPIRouter

from src.api.routers.dashboards import (
    admin_router as AdminDashboardAPIRouter,
    trainee_router as TraineeDashboardAPIRouter,
    trainer_router as TrainerDashboardAPIRouter
)
from src.api.routers.course_contents import (
    trainee_router as TraineeCourseContentAPIRouter,
    trainer_router as TrainerCourseContentAPIRouter
)
from src.api.routers.entity_list import (
    admin_router as AdminEntityListAPIRouter,
    trainee_router as TraineeEntityListAPIRouter,
    trainer_router as TrainerEntityListAPIRouter
)
from src.api.routers.assignment_contents import (
    trainee_router as TraineeAssignmentContentAPIRouter, 
    trainer_router as TrainerAssignmentContentAPIRouter
)

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
    TraineeEntityListAPIRouter,
    TrainerEntityListAPIRouter,
    TraineeAssignmentContentAPIRouter,
    TrainerAssignmentContentAPIRouter
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
    "TraineeEntityListAPIRouter",
    "TrainerEntityListAPIRouter",
    "TraineeAssignmentContentAPIRouter",
    "TrainerAssignmentContentAPIRouter"
]
