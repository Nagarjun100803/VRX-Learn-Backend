# Database initalization.
from src.api.jwt import JWTHandler
from src.database import AsyncPgDBManager
from src.query_builder.asyncpg import AsyncPgQueryBuilder

query_builder = AsyncPgQueryBuilder()
db = AsyncPgDBManager(query_builder=query_builder)


# Repository Imports.
from src.repository.users import UserRespository
from src.repository.courses import CourseRepository
from src.repository.modules import ModuleRepository
from src.repository.media import MediaRepository
from src.repository.lessons import LessonRepository
from src.repository.assignments import AssignmentRepository
from src.repository.enrollments import EnrollmentRepository

# Repositories.
user_repository = UserRespository(db=db)
course_repository = CourseRepository(db=db)
module_repository = ModuleRepository(db=db)
media_repository = MediaRepository(db=db)
lesson_repository = LessonRepository(db=db)
assignment_repository = AssignmentRepository(db=db)
enrollment_repository = EnrollmentRepository(db=db)


# Service Imports.

from src.auth.auth import AuthService # Authorization Layer.
from src.service.users import UserService, PasswordHandler
from src.service.course import CourseService
from src.service.modules import ModuleService
from src.service.media import MediaService
from src.service.lessons import LessonService
from src.service.assignments import AssignmentService
from src.service.enrollments import EnrollmentService
from src.service.files import S3, get_session
from src.service.permission_policy import PermissionPolicy

# Helper classes.
password_handler = PasswordHandler()
permission_policy = PermissionPolicy()
jwt_handler = JWTHandler()

# Services.

auth_service = AuthService(
    user_repo=user_repository,
    db=db
)

user_service = UserService(
    user_repo=user_repository,
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
    user_repo=user_repository,
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
    user_repo=user_repository,
    repo=lesson_repository,
    module_repo=module_repository,
    media_service=media_service,
    auth_service=auth_service
)

assignment_service = AssignmentService(
    user_repo=user_repository,
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



