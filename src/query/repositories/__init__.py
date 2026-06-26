from src.query.repositories.assignment_contents import (
    TraineeAssignmentContentQueryRepository,
    TrainerAssignmentContentQueryRepository,
)
from src.query.repositories.course_contents import (
    TraineeCourseContentQueryRepository,
    TrainerCourseContentQueryRepository,
)
from src.query.repositories.course_overview import (
    TraineeCourseOverviewQueryRepository,
    TraineeCoursePreviewQueryRepository,
    TrainerCourseOverviewQueryRepository,
)
from src.query.repositories.dashboards import (
    AdminDashboardQueryRepository,
    TraineeDashboardQueryRepository,
    TrainerDashboardQueryRepository,
)
from src.query.repositories.entity_list import EntityListQueryRepository
from src.query.repositories.issues import IssueQueryRepository

__all__ = [
    "AdminDashboardQueryRepository",
    "TraineeDashboardQueryRepository",
    "TrainerDashboardQueryRepository",
    "TraineeCourseContentQueryRepository",
    "TrainerCourseContentQueryRepository",
    "EntityListQueryRepository",
    "TraineeAssignmentContentQueryRepository",
    "TrainerAssignmentContentQueryRepository",
    "TraineeCoursePreviewQueryRepository",
    "TraineeCourseOverviewQueryRepository",
    "TrainerCourseOverviewQueryRepository",
    "IssueQueryRepository",
]
