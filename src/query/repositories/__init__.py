from src.query.repositories.assignment_contents import TraineeAssignmentContentQueryRepository, TrainerAssignmentContentQueryRepository
from src.query.repositories.course_contents import TraineeCourseContentQueryRepository, TrainerCourseContentQueryRepository
from src.query.repositories.dashboards import TrainerDashboardQueryReository, TraineeDashboardQueryRepository
from src.query.repositories.entity_list import EntityListQueryRepository

__all__ = [
    "TraineeDashboardQueryRepository",
    "TrainerDashboardQueryReository",
    "TraineeCourseContentQueryRepository",
    "TrainerCourseContentQueryRepository",
    "EntityListQueryRepository",
    "TraineeAssignmentContentQueryRepository",
    "TrainerAssignmentContentQueryRepository"
]