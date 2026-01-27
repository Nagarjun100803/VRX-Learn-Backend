from typing import Annotated
from fastapi import Depends

# Base Dependency
from src.database import async_db_manager

# User Dependency.
from src.commands.base import UserID
from src.service.users import UserService, PasswordHandler
from src.repository.users import UserRespository
from src.service.permission_policy import PermissionPolicy

# Course Dependency.
from src.repository.courses import CourseRepository
from src.service.course import CourseService


# Module Dependency.
from src.repository.modules import ModuleRepository
from src.service.modules import ModuleService

# DB Connection
db = async_db_manager

# Repositories
user_repository = UserRespository(db=db)
course_reposiory = CourseRepository(db=db)
module_repository = ModuleRepository(db=db)


# Helper classes
permission_policy = PermissionPolicy()
password_handler = PasswordHandler()



def get_user_service() -> UserService:
    """
        Helper function used to build a UserService used
        for Depedency Injection.
    """
    return UserService(
        user_repo=user_repository,
        permission_policy=permission_policy,
        password_handler=password_handler,
        repo=user_repository
    )
  

def get_course_service() -> CourseService:
    return CourseService(
        user_repo=user_repository,
        permission_policy=permission_policy,
        repo=course_reposiory
    )  
    

def get_module_service() -> ModuleService:
    return ModuleService(
        user_repo=user_repository,
        permission_policy=permission_policy,
        repo=module_repository
    )

UserServiceDependency = Annotated[UserService, Depends(get_user_service)]  
CourseServiceDependency = Annotated[CourseService, Depends(get_course_service)]
ModuleServiceDependency = Annotated[ModuleService, Depends(get_module_service)]



def sample_get_current_user() -> UserID:
    "This is sample need to implement using JWT"
    return "U-1"


CurrentUser = Annotated[UserID, Depends(sample_get_current_user)]


