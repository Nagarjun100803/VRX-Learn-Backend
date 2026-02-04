from typing import Annotated
from fastapi import Depends
from src.commands.base import UserID
from src.dependencies import (
    user_service, course_service, module_service, 
    lesson_service, media_service
)
from src.dependencies import (
    UserService, CourseService, ModuleService,
    LessonService, MediaService
)



# Helper functions to build a Services used for Depedency Injection.

def get_user_service() -> UserService:
    return user_service

def get_course_service() -> CourseService:
    return course_service 
    

def get_module_service() -> ModuleService:
    return module_service

def get_lesson_service() -> LessonService:
    return lesson_service

UserServiceDependency = Annotated[UserService, Depends(get_user_service)]  
CourseServiceDependency = Annotated[CourseService, Depends(get_course_service)]
ModuleServiceDependency = Annotated[ModuleService, Depends(get_module_service)]
LessonServiceDependency = Annotated[LessonService, Depends(get_lesson_service)]


def sample_get_current_user() -> UserID:
    "This is sample need to implement using JWT"
    return "U-1"


CurrentUser = Annotated[UserID, Depends(sample_get_current_user)]


