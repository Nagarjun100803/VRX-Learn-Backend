from src.query.services.assignment_contents import TraineeAssignmentContentQueryService, TrainerAssignmentContentQueryService
from src.query.services.dashboards import TraineeDashboardQueryService, TrainerDashboardQueryService
from src.query.services.course_contents import TraineeCourseContentQueryService, TrainerCourseContentQueryService
from src.query.services.entity_list import TraineeEntityListQueryService, TrainerEntityListQueryService

__all__ = [
    "TraineeDashboardQueryService",
    "TrainerDashboardQueryService",
    "TraineeCourseContentQueryService",
    "TrainerCourseContentQueryService",
    "TraineeEntityListQueryService",
    "TrainerEntityListQueryService",
    "TraineeAssignmentContentQueryService",
    "TrainerAssignmentContentQueryService"
]