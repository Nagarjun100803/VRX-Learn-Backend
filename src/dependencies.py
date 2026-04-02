# Database initalization.
from src.api.jwt import JWTHandler
from src.auth.auth import AuthService

# Repository Imports.
from src.command.repositories import (
    AssignmentRepository,
    AssignmentSubmissionRepository,
    CourseRepository,
    EnrollmentRepository,
    LessonRepository,
    MediaRepository,
    ModuleRepository,
    UserRepository,
)

# Service Imports.
from src.command.services import (
    S3,
    AssignmentService,
    AssignmentSubmissionService,
    CourseService,
    EnrollmentService,
    LessonService,
    MediaService,
    ModuleService,
    PositioningService,
    UserService,
)
from src.command.services.files import get_session
from src.command.services.users import PasswordHandler
from src.database import AsyncPgDBManager

# Query Repository imports.
from src.query.repositories import (
    AdminDashboardQueryRepository,
    EntityListQueryRepository,
    TraineeAssignmentContentQueryRepository,
    TraineeCourseContentQueryRepository,
    TraineeDashboardQueryRepository,
    TrainerAssignmentContentQueryRepository,
    TrainerCourseContentQueryRepository,
    TrainerDashboardQueryRepository,
)

# Query Service imports.
from src.query.services import (
    AdminDashboardQueryService,
    AdminEntityListQueryService,
    TraineeAssignmentContentQueryService,
    TraineeCourseContentQueryService,
    TraineeDashboardQueryService,
    TraineeEntityListQueryService,
    TrainerAssignmentContentQueryService,
    TrainerCourseContentQueryService,
    TrainerDashboardQueryService,
    TrainerEntityListQueryService,
)

db = AsyncPgDBManager()


# Command Repositories.
user_repository = UserRepository(db=db)
course_repository = CourseRepository(db=db)
module_repository = ModuleRepository(db=db)
media_repository = MediaRepository(db=db)
lesson_repository = LessonRepository(db=db)
assignment_repository = AssignmentRepository(db=db)
enrollment_repository = EnrollmentRepository(db=db)
assignment_submission_repository = AssignmentSubmissionRepository(db=db)


# Query Repositories.
admin_dashboard_query_repository = AdminDashboardQueryRepository(db=db)
trainee_dashboard_query_repository = TraineeDashboardQueryRepository(db=db)
trainer_dashboard_query_repository = TrainerDashboardQueryRepository(db=db)

trainee_course_content_query_repository = TraineeCourseContentQueryRepository(db=db)
trainer_course_content_query_repository = TrainerCourseContentQueryRepository(db=db)

entity_list_query_repository = EntityListQueryRepository(db=db)

trainee_assignment_content_query_repository = TraineeAssignmentContentQueryRepository(
    db=db
)
trainer_assignment_content_query_repository = TrainerAssignmentContentQueryRepository(
    db=db
)


# Helper classes.
password_handler = PasswordHandler()
jwt_handler = JWTHandler()

# Services.

auth_service = AuthService(user_repo=user_repository, db=db)

positioning_service = PositioningService(db=db)

user_service = UserService(
    repo=user_repository, password_handler=password_handler, auth_service=auth_service
)

course_service = CourseService(
    user_repo=user_repository, repo=course_repository, auth_service=auth_service
)

module_service = ModuleService(
    course_repo=course_repository,
    repo=module_repository,
    auth_service=auth_service,
    positioning_service=positioning_service,
)

session = get_session()
file_service = S3(bucket="vrx-learn", session=session)

media_service = MediaService(file_service=file_service, repo=media_repository)

lesson_service = LessonService(
    repo=lesson_repository,
    module_repo=module_repository,
    media_service=media_service,
    auth_service=auth_service,
    positioning_service=positioning_service,
)

assignment_service = AssignmentService(
    repo=assignment_repository,
    course_repo=course_repository,
    media_service=media_service,
    auth_service=auth_service,
)

enrollment_service = EnrollmentService(
    user_repo=user_repository,
    repo=enrollment_repository,
    course_repo=course_repository,
    auth_service=auth_service,
)

assignment_submission_service = AssignmentSubmissionService(
    repo=assignment_submission_repository,
    assignment_repo=assignment_repository,
    media_service=media_service,
    auth_service=auth_service,
)


# Query services.
admin_dashboard_query_service = AdminDashboardQueryService(
    admin_dashboard_query_repo=admin_dashboard_query_repository
)

trainee_dashboard_query_service = TraineeDashboardQueryService(
    trainee_dashboard_query_repo=trainee_dashboard_query_repository
)

trainer_dashboard_query_service = TrainerDashboardQueryService(
    trainer_dashboard_query_repo=trainer_dashboard_query_repository
)

trainee_course_content_query_service = TraineeCourseContentQueryService(
    trainee_course_content_repo=trainee_course_content_query_repository,
    auth_service=auth_service,
)

trainer_course_content_query_service = TrainerCourseContentQueryService(
    trainer_course_content_repo=trainer_course_content_query_repository,
    auth_service=auth_service,
)

admin_entity_list_query_service = AdminEntityListQueryService(
    entity_list_query_repo=entity_list_query_repository
)

trainee_entity_list_query_service = TraineeEntityListQueryService(
    entity_list_query_repo=entity_list_query_repository, auth_service=auth_service
)

trainer_entity_list_query_service = TrainerEntityListQueryService(
    entity_list_query_repo=entity_list_query_repository, auth_service=auth_service
)


trainee_assignment_content_query_service = TraineeAssignmentContentQueryService(
    trainee_assignment_query_repo=trainee_assignment_content_query_repository,
    auth_service=auth_service,
)

trainer_assignment_content_query_service = TrainerAssignmentContentQueryService(
    trainer_assignment_content_repo=trainer_assignment_content_query_repository,
    entity_list_query_repo=entity_list_query_repository,
    auth_service=auth_service,
)
