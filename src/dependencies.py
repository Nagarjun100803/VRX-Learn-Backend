# Database initalization.
from src.auth.auth import AuthService

# Repository Imports.
from src.command.repositories import (
    AssignmentRepository,
    AssignmentSubmissionRepository,
    AuthenticationRepository,
    CourseRepository,
    EnrollmentRepository,
    IssueRepository,
    LessonRepository,
    MediaRepository,
    ModuleRepository,
    UserRepository,
)

# Service Imports.
from src.command.services import (
    AssignmentService,
    AssignmentSubmissionService,
    AuthenticationService,
    CourseService,
    EnrollmentService,
    IssueService,
    LessonService,
    MediaService,
    ModuleService,
    PositioningService,
    UserOnboardService,
    UserService,
)
from src.command.services.media import AttachmentResolver
from src.core.security.jwt import JWTHandler
from src.core.security.password import PasswordHasher
from src.core.storage.files import S3Bucket
from src.core.storage.files import get_session as get_s3_session
from src.database import AsyncPgDBManager
from src.notifications import SES, EmailTemplates, NotificationSender
from src.notifications import get_session as get_ses_session

# Query Repository imports.
from src.query.repositories import (
    AdminDashboardQueryRepository,
    EntityListQueryRepository,
    IssueQueryRepository,
    TraineeAssignmentContentQueryRepository,
    TraineeCourseContentQueryRepository,
    TraineeCourseOverviewQueryRepository,
    TraineeDashboardQueryRepository,
    TrainerAssignmentContentQueryRepository,
    TrainerCourseContentQueryRepository,
    TrainerCourseOverviewQueryRepository,
    TrainerDashboardQueryRepository,
)

# Query Service imports.
from src.query.services import (
    AdminDashboardQueryService,
    AdminEntityListQueryService,
    IssueQueryService,
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
)

db = AsyncPgDBManager()


# Command Repositories.

authentication_repository = AuthenticationRepository(db=db)
user_repository = UserRepository(db=db)
course_repository = CourseRepository(db=db)
module_repository = ModuleRepository(db=db)
media_repository = MediaRepository(db=db)
lesson_repository = LessonRepository(db=db)
assignment_repository = AssignmentRepository(db=db)
enrollment_repository = EnrollmentRepository(db=db)
assignment_submission_repository = AssignmentSubmissionRepository(db=db)
issue_repository = IssueRepository(db=db)


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

trainee_course_overview_query_repository = TraineeCourseOverviewQueryRepository(db=db)
trainer_course_overview_query_repository = TrainerCourseOverviewQueryRepository(db=db)
issue_query_repository = IssueQueryRepository(db=db)

# Helper classes.

# Core
jwt_handler = JWTHandler()
password_hasher = PasswordHasher()

# Services.

auth_service = AuthService(user_repo=user_repository, db=db)

authentication_service = AuthenticationService(
    repo=authentication_repository,
    user_repo=user_repository,
    password_hasher=password_hasher,
    jwt_handler=jwt_handler,
)

positioning_service = PositioningService(db=db)

user_service = UserService(
    repo=user_repository, password_hasher=password_hasher, auth_service=auth_service
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

session = get_s3_session()
ses_session = get_ses_session()

file_service = S3Bucket(bucket_name="vrx-learn", session=session)

media_service = MediaService(repo=media_repository)

email_service = SES(session=ses_session)
email_templates = EmailTemplates()
notification_service = NotificationSender(
    provider=email_service, template=email_templates
)

attachment_resolver = AttachmentResolver(
    media_service=media_service, file_service=file_service
)


lesson_service = LessonService(
    repo=lesson_repository,
    module_repo=module_repository,
    media_service=media_service,
    auth_service=auth_service,
    file_service=file_service,
    positioning_service=positioning_service,
    attachment_resolver=attachment_resolver,
)

assignment_service = AssignmentService(
    repo=assignment_repository,
    course_repo=course_repository,
    media_service=media_service,
    auth_service=auth_service,
    file_service=file_service,
    attachment_resolver=attachment_resolver,
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

issue_service = IssueService(
    repo=issue_repository, auth_service=auth_service, media_service=media_service
)

user_onboard_service = UserOnboardService(enrollment_service=enrollment_service)


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

trainee_course_overview_query_service = TraineeCourseOverviewQueryService(
    trainee_course_overview_query_repo=trainee_course_overview_query_repository,
    auth_service=auth_service,
)

trainer_course_overview_query_service = TrainerCourseOverviewQueryService(
    trainer_course_overview_query_repo=trainer_course_overview_query_repository,
    auth_service=auth_service,
)

issue_query_service = IssueQueryService(issue_query_repo=issue_query_repository)
