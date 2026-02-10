from typing import Annotated, Optional
from fastapi import Depends, Cookie
from src.api.jwt import JWTHandler, JWTPayload
from src.commands.base import UserID
from src.dependencies import (
    user_service, course_service, module_service, 
    lesson_service, media_service
)
from src.dependencies import (
    UserService, CourseService, ModuleService,
    LessonService, MediaService
)
from src.exceptions import UnAuthenticated


# Helper functions to build a Services used for Depedency Injection.

def get_user_service() -> UserService:
    return user_service

def get_course_service() -> CourseService:
    return course_service 
    

def get_module_service() -> ModuleService:
    return module_service

def get_lesson_service() -> LessonService:
    return lesson_service

def get_jwt_handler() -> JWTHandler:
    return JWTHandler()


UserServiceDependency = Annotated[UserService, Depends(get_user_service)]  
CourseServiceDependency = Annotated[CourseService, Depends(get_course_service)]
ModuleServiceDependency = Annotated[ModuleService, Depends(get_module_service)]
LessonServiceDependency = Annotated[LessonService, Depends(get_lesson_service)]
JWTServiceDependency = Annotated[JWTHandler, Depends(get_jwt_handler)]



async def get_current_user(
    jwt_handler: Annotated[JWTHandler, Depends(get_jwt_handler)],
    access_token: Annotated[Optional[str], Cookie()] = None,
) -> JWTPayload:
    
    if access_token is None:
        raise UnAuthenticated(message="Missing access token.")
    
    try:
        payload = jwt_handler.decode_jwt_token(access_token)
        return payload.user_id
    
    except Exception:
        raise UnAuthenticated(message="Invalid or Expired token.")
    


CurrentUser = Annotated[UserID, Depends(get_current_user)]


