# Database initalization.
from src.api.jwt import JWTHandler
from src.database import AsyncPgDBManager
from src.query_builder.asyncpg import AsyncPgQueryBuilder

query_builder = AsyncPgQueryBuilder()
db = AsyncPgDBManager(query_builder=query_builder)


# Repository Imports.
from src.repository import (
    UserRespository, CourseRepository, ModuleRepository,
    EnrollmentRepository, LessonRepository, MediaRepository,
    AssignmentRepository, AssignmentSubmissionRepository
)

# Repositories.
user_repository = UserRespository(db=db)
course_repository = CourseRepository(db=db)
module_repository = ModuleRepository(db=db)
media_repository = MediaRepository(db=db)
lesson_repository = LessonRepository(db=db)
assignment_repository = AssignmentRepository(db=db)
enrollment_repository = EnrollmentRepository(db=db)
assignment_submission_repository = AssignmentSubmissionRepository(db=db)

# Service Imports.
from src.service import (
    UserService, CourseService, ModuleService, 
    LessonService, EnrollmentService, AssignmentService,
    MediaService, S3, AssignmentSubmissionService
)
from src.service.files import get_session
from src.service.users import PasswordHandler
from src.auth.auth import AuthService

# Helper classes.
password_handler = PasswordHandler()
jwt_handler = JWTHandler()

# Services.

auth_service = AuthService(
    user_repo=user_repository,
    db=db
)

user_service = UserService(
    repo=user_repository,
    password_handler=password_handler,
    auth_service=auth_service
)

course_service = CourseService(
    user_repo=user_repository,
    repo=course_repository,
    auth_service=auth_service
)

module_service = ModuleService(
    course_repo=course_repository,
    repo=module_repository,
    auth_service=auth_service
)

session = get_session()
file_service = S3(bucket="vrx-learn", session=session)

media_service = MediaService(
    file_service=file_service,
    repo=media_repository
)

lesson_service = LessonService(
    repo=lesson_repository,
    module_repo=module_repository,
    media_service=media_service,
    auth_service=auth_service
)

assignment_service = AssignmentService(
    repo=assignment_repository,
    course_repo=course_repository,
    media_service=media_service,
    auth_service=auth_service
)

enrollment_service = EnrollmentService(
    user_repo=user_repository,
    repo=enrollment_repository,
    course_repo=course_repository,
    auth_service=auth_service
)

assignment_submission_service = AssignmentSubmissionService(
    repo=assignment_submission_repository,
    assignment_repo=assignment_repository,
    media_service=media_service,
    auth_service=auth_service
)

