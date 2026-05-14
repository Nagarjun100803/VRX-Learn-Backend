from typing import Annotated, Optional

from fastapi import Cookie, Depends

from src.api.auth import AuthenticationService, UnAuthenticated, UserContext
from src.api.jwt import JWTHandler
from src.command.commands.base import UserID
from src.command.commands.users import UserRole

# Query Dependencies.
from src.dependencies import (
    AdminDashboardQueryService,
    AdminEntityListQueryService,
    AssignmentService,
    AssignmentSubmissionService,
    CourseService,
    EnrollmentService,
    IssueQueryService,
    IssueService,
    LessonService,
    MediaService,
    ModuleService,
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
    course_service,
    enrollment_service,
    issue_query_service,
    issue_service,
    jwt_handler,
    lesson_service,
    media_service,
    module_service,
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
    user_repository,
    user_service,
)
from src.exceptions import UnauthorizedError

# # Helper functions to build a Services used for Depedency Injection.


def get_user_service() -> UserService:
    return user_service


def get_course_service() -> CourseService:
    return course_service


def get_module_service() -> ModuleService:
    return module_service


def get_lesson_service() -> LessonService:
    return lesson_service


def get_jwt_handler() -> JWTHandler:
    return jwt_handler


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


UserServiceDependency = Annotated[UserService, Depends(get_user_service)]
CourseServiceDependency = Annotated[CourseService, Depends(get_course_service)]
ModuleServiceDependency = Annotated[ModuleService, Depends(get_module_service)]
LessonServiceDependency = Annotated[LessonService, Depends(get_lesson_service)]
JWTServiceDependency = Annotated[JWTHandler, Depends(get_jwt_handler)]
AssignmentServiceDependency = Annotated[
    AssignmentService, Depends(get_assignment_service)
]
MediaServiceDependency = Annotated[MediaService, Depends(get_media_service)]
EnrollmentServiceDependency = Annotated[
    EnrollmentService, Depends(get_enrollment_service)
]
AssignmentSubmissionServiceDependency = Annotated[
    AssignmentSubmissionService, Depends(get_assignment_submission_service)
]

IssueServiceDependency = Annotated[IssueService, Depends(get_issue_service)]


authentication_service = AuthenticationService(
    user_repo=user_repository, jwt_handler=jwt_handler
)


async def get_current_user_context(
    access_token: Annotated[Optional[str], Cookie()] = None,
) -> UserContext:
    if access_token is None:
        raise UnAuthenticated(message="No access token provided.")
    user_context = await authentication_service.authenticate(token=access_token)
    return user_context


AdminDashboardQueryServiceDependency = Annotated[
    AdminDashboardQueryService, Depends(get_admin_dashboard_query_service)
]
TraineeDashboardQueryServiceDependency = Annotated[
    TraineeDashboardQueryService, Depends(get_trainee_dashboard_query_service)
]
TrainerDashboardQueryServiceDependency = Annotated[
    TrainerDashboardQueryService, Depends(get_trainer_dashboard_query_service)
]

TraineeCourseContentQueryServiceDependency = Annotated[
    TraineeCourseContentQueryService, Depends(get_trainee_course_content_query_service)
]
TrainerCourseContentQueryServiceDependency = Annotated[
    TrainerCourseContentQueryService, Depends(get_trainer_course_content_query_service)
]

AdminEntityListQueryServiceDependency = Annotated[
    AdminEntityListQueryService, Depends(get_admin_entity_list_query_service)
]
TraineeEntityListQueryServiceDependency = Annotated[
    TraineeEntityListQueryService, Depends(get_trainee_entity_list_query_service)
]
TrainerEntityListQueryServiceDependency = Annotated[
    TrainerEntityListQueryService, Depends(get_trainer_entity_list_query_service)
]

TraineeAssignmentContentQueryServiceDependency = Annotated[
    TraineeAssignmentContentQueryService,
    Depends(get_trainee_assignment_content_query_service),
]
TrainerAssignmentContentQueryServiceDependency = Annotated[
    TrainerAssignmentContentQueryService,
    Depends(get_trainer_assignment_content_query_service),
]

TraineeCourseOverviewQueryServiceDependency = Annotated[
    TraineeCourseOverviewQueryService,
    Depends(get_trainee_course_overview_query_service),
]

TrainerCourseOverviewQueryServiceDependency = Annotated[
    TrainerCourseOverviewQueryService,
    Depends(get_trainer_course_overview_query_service),
]

IssueQueryServiceDependency = Annotated[
    IssueQueryService, Depends(get_issue_query_service)
]

UserContextDependency = Annotated[UserContext, Depends(get_current_user_context)]


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
        raise UnauthorizedError(
            message=f"Permission Denied: '{UserRole.ADMIN.value}' or '{UserRole.TRAINER.value}' required."
        )
    return user_context.user_id


async def get_current_trainee_or_trainer(user_context: UserContextDependency) -> UserID:
    if not (
        user_context.role == UserRole.TRAINEE.value
        or user_context.role == UserRole.TRAINER.value
    ):
        raise UnauthorizedError(
            message=f"Permission Denied: '{UserRole.TRAINEE.value}' or '{UserRole.TRAINER.value}' required."
        )
    return user_context.user_id


CurrentUser = Annotated[UserID, Depends(get_current_user)]
CurrentTrainee = Annotated[UserID, Depends(get_current_trainee)]
CurrentTrainer = Annotated[UserID, Depends(get_current_trainer)]
CurrentAdmin = Annotated[UserID, Depends(get_current_admin)]
CurrentAdminOrTrainer = Annotated[UserID, Depends(get_current_admin_or_trainer)]
CurrentTraineeOrTrainer = Annotated[UserID, Depends(get_current_trainee_or_trainer)]
