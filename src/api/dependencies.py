from typing import Annotated, Optional

from fastapi import Cookie, Depends

from src.command.commands.authentication import JWTToken, UserContext
from src.command.commands.base import UserID
from src.command.commands.users import UserRole

# Query Dependencies.
from src.dependencies import (
    AdminDashboardQueryService,
    AdminEntityListQueryService,
    AssignmentService,
    AssignmentSubmissionService,
    AuthenticationService,
    CourseService,
    EnrollmentService,
    IssueQueryService,
    IssueService,
    LessonService,
    MediaService,
    ModuleService,
    NotificationSender,
    TraineeAssignmentContentQueryService,
    TraineeCourseContentQueryService,
    TraineeCourseOverviewQueryService,
    TraineeDashboardQueryService,
    TraineeEntityListQueryService,
    TrainerAssignmentContentQueryService,
    TrainerCourseContentQueryService,
    TrainerCourseOverviewQueryService,
    TrainerDashboardQueryService,
    TrainerEntityListQueryService,
    UserService,
    admin_dashboard_query_service,
    admin_entity_list_query_service,
    assignment_service,
    assignment_submission_service,
    authentication_service,
    course_service,
    enrollment_service,
    issue_query_service,
    issue_service,
    lesson_service,
    media_service,
    module_service,
    notification_service,
    trainee_assignment_content_query_service,
    trainee_course_content_query_service,
    trainee_course_overview_query_service,
    trainee_dashboard_query_service,
    trainee_entity_list_query_service,
    trainer_assignment_content_query_service,
    trainer_course_content_query_service,
    trainer_course_overview_query_service,
    trainer_dashboard_query_service,
    trainer_entity_list_query_service,
    user_service,
)
from src.exceptions import UnAuthenticated, UnAuthorizedError

# # Helper functions to build a Services used for Depedency Injection.


def get_authentication_service() -> AuthenticationService:
    return authentication_service


def get_user_service() -> UserService:
    return user_service


def get_course_service() -> CourseService:
    return course_service


def get_module_service() -> ModuleService:
    return module_service


def get_lesson_service() -> LessonService:
    return lesson_service


def get_notification_service() -> NotificationSender:
    return notification_service


def get_assignment_service() -> AssignmentService:
    return assignment_service


def get_media_service() -> MediaService:
    return media_service


def get_enrollment_service() -> EnrollmentService:
    return enrollment_service


def get_assignment_submission_service() -> AssignmentSubmissionService:
    return assignment_submission_service


def get_issue_service() -> IssueService:
    return issue_service


def get_admin_dashboard_query_service() -> AdminDashboardQueryService:
    return admin_dashboard_query_service


def get_trainee_dashboard_query_service() -> TraineeDashboardQueryService:
    return trainee_dashboard_query_service


def get_trainer_dashboard_query_service() -> TrainerDashboardQueryService:
    return trainer_dashboard_query_service


def get_trainee_course_content_query_service() -> TraineeCourseContentQueryService:
    return trainee_course_content_query_service


def get_trainer_course_content_query_service() -> TrainerCourseContentQueryService:
    return trainer_course_content_query_service


def get_trainee_entity_list_query_service() -> TraineeEntityListQueryService:
    return trainee_entity_list_query_service


def get_admin_entity_list_query_service() -> AdminEntityListQueryService:
    return admin_entity_list_query_service


def get_trainer_entity_list_query_service() -> TrainerEntityListQueryService:
    return trainer_entity_list_query_service


def get_trainee_assignment_content_query_service() -> (
    TraineeAssignmentContentQueryService
):
    return trainee_assignment_content_query_service


def get_trainer_assignment_content_query_service() -> (
    TrainerAssignmentContentQueryService
):
    return trainer_assignment_content_query_service


def get_trainee_course_overview_query_service() -> TraineeCourseOverviewQueryService:
    return trainee_course_overview_query_service


def get_trainer_course_overview_query_service() -> TrainerCourseOverviewQueryService:
    return trainer_course_overview_query_service


def get_issue_query_service() -> IssueQueryService:
    return issue_query_service


type AuthenticationServiceDependency = Annotated[
    AuthenticationService, Depends(get_authentication_service)
]
type UserServiceDependency = Annotated[UserService, Depends(get_user_service)]
type CourseServiceDependency = Annotated[CourseService, Depends(get_course_service)]
type ModuleServiceDependency = Annotated[ModuleService, Depends(get_module_service)]
type LessonServiceDependency = Annotated[LessonService, Depends(get_lesson_service)]
type AssignmentServiceDependency = Annotated[
    AssignmentService, Depends(get_assignment_service)
]
type MediaServiceDependency = Annotated[MediaService, Depends(get_media_service)]
type EnrollmentServiceDependency = Annotated[
    EnrollmentService, Depends(get_enrollment_service)
]
type AssignmentSubmissionServiceDependency = Annotated[
    AssignmentSubmissionService, Depends(get_assignment_submission_service)
]

type NotificationServiceDependency = Annotated[
    NotificationSender, Depends(get_notification_service)
]
type IssueServiceDependency = Annotated[IssueService, Depends(get_issue_service)]


async def get_current_user_context(
    access_token: Annotated[Optional[str], Cookie()] = None,
) -> UserContext:
    if access_token is None:
        raise UnAuthenticated(message="No access token provided.")
    user_context = await authentication_service.me(token=JWTToken(token=access_token))
    return user_context


type AdminDashboardQueryServiceDependency = Annotated[
    AdminDashboardQueryService, Depends(get_admin_dashboard_query_service)
]
type TraineeDashboardQueryServiceDependency = Annotated[
    TraineeDashboardQueryService, Depends(get_trainee_dashboard_query_service)
]
type TrainerDashboardQueryServiceDependency = Annotated[
    TrainerDashboardQueryService, Depends(get_trainer_dashboard_query_service)
]

type TraineeCourseContentQueryServiceDependency = Annotated[
    TraineeCourseContentQueryService, Depends(get_trainee_course_content_query_service)
]
type TrainerCourseContentQueryServiceDependency = Annotated[
    TrainerCourseContentQueryService, Depends(get_trainer_course_content_query_service)
]

type AdminEntityListQueryServiceDependency = Annotated[
    AdminEntityListQueryService, Depends(get_admin_entity_list_query_service)
]
type TraineeEntityListQueryServiceDependency = Annotated[
    TraineeEntityListQueryService, Depends(get_trainee_entity_list_query_service)
]
type TrainerEntityListQueryServiceDependency = Annotated[
    TrainerEntityListQueryService, Depends(get_trainer_entity_list_query_service)
]

type TraineeAssignmentContentQueryServiceDependency = Annotated[
    TraineeAssignmentContentQueryService,
    Depends(get_trainee_assignment_content_query_service),
]
type TrainerAssignmentContentQueryServiceDependency = Annotated[
    TrainerAssignmentContentQueryService,
    Depends(get_trainer_assignment_content_query_service),
]

type TraineeCourseOverviewQueryServiceDependency = Annotated[
    TraineeCourseOverviewQueryService,
    Depends(get_trainee_course_overview_query_service),
]

type TrainerCourseOverviewQueryServiceDependency = Annotated[
    TrainerCourseOverviewQueryService,
    Depends(get_trainer_course_overview_query_service),
]

type IssueQueryServiceDependency = Annotated[
    IssueQueryService, Depends(get_issue_query_service)
]

type UserContextDependency = Annotated[UserContext, Depends(get_current_user_context)]


async def get_current_user(user_context: UserContextDependency) -> UserID:
    return user_context.user_id


async def get_current_trainee(user_context: UserContextDependency) -> UserID:
    return user_context.validate_role(UserRole.TRAINEE).user_id


async def get_current_trainer(user_context: UserContextDependency) -> UserID:
    return user_context.validate_role(UserRole.TRAINER).user_id


async def get_current_admin(user_context: UserContextDependency) -> UserID:
    return user_context.validate_role(UserRole.ADMIN).user_id


async def get_current_admin_or_trainer(user_context: UserContextDependency) -> UserID:
    if not (
        user_context.role == UserRole.ADMIN or user_context.role == UserRole.TRAINER
    ):
        raise UnAuthorizedError(
            message=f"Permission Denied: '{UserRole.ADMIN.value}' or '{UserRole.TRAINER.value}' required."
        )
    return user_context.user_id


async def get_current_trainee_or_trainer(user_context: UserContextDependency) -> UserID:
    if not (
        user_context.role == UserRole.TRAINEE.value
        or user_context.role == UserRole.TRAINER.value
    ):
        raise UnAuthorizedError(
            message=f"Permission Denied: '{UserRole.TRAINEE.value}' or '{UserRole.TRAINER.value}' required."
        )
    return user_context.user_id


type CurrentUser = Annotated[UserID, Depends(get_current_user)]
type CurrentTrainee = Annotated[UserID, Depends(get_current_trainee)]
type CurrentTrainer = Annotated[UserID, Depends(get_current_trainer)]
type CurrentAdmin = Annotated[UserID, Depends(get_current_admin)]
type CurrentAdminOrTrainer = Annotated[UserID, Depends(get_current_admin_or_trainer)]
type CurrentTraineeOrTrainer = Annotated[
    UserID, Depends(get_current_trainee_or_trainer)
]
