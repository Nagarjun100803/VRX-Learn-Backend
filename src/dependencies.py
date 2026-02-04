# Database initalization.
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

# Repositories.
user_repository = UserRespository(db=db)
course_repository = CourseRepository(db=db)
module_repository = ModuleRepository(db=db)
media_repository = MediaRepository(db=db)
lesson_repository = LessonRepository(db=db)


# Service Imports.
from src.service.users import UserService, PasswordHandler
from src.service.course import CourseService
from src.service.modules import ModuleService
from src.service.media import MediaService
from src.service.lessons import LessonService
from src.service.files import S3, get_session
from src.service.permission_policy import PermissionPolicy

# Helper classes.
password_handler = PasswordHandler()
permission_policy = PermissionPolicy()

# Services.
user_service = UserService(
    user_repo=user_repository,
    permission_policy=permission_policy,
    repo=user_repository,
    password_handler=password_handler
)

course_service = CourseService(
    user_repo=user_repository,
    permission_policy=permission_policy,
    repo=course_repository
)

module_service = ModuleService(
    user_repo=user_repository,
    permission_policy=permission_policy,
    course_repo=course_repository,
    repo=module_repository
)

session = get_session()
file_service = S3(bucket="vrx-learn", session=session)

media_service = MediaService(
    file_service=file_service,
    repo=media_repository
)

lesson_service = LessonService(
    user_repo=user_repository,
    permission_policy=permission_policy,
    repo=lesson_repository,
    module_repo=module_repository,
    media_service=media_service
)






