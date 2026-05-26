from fastapi import APIRouter, status

from src.api.dependencies import CurrentUser, UserServiceDependency
from src.api.docs.users import CREATE_USER, DELETE_USER, GET_USER
from src.api.schemas.users import UserCreateSchema, UserOutSchema
from src.command.commands.base import UserID
from src.command.commands.users import (
    UserCreateWithConfirmPassword,
    UserDelete,
    UserGetByIDQuery,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}", response_model=UserOutSchema, **GET_USER)
async def get_user(
    user_id: UserID, user_service: UserServiceDependency, current_user: CurrentUser
):
    return await user_service.get(UserGetByIDQuery(id=user_id, viewer_id=current_user))


@router.post(
    "/",
    response_model=UserOutSchema,
    status_code=status.HTTP_201_CREATED,
    **CREATE_USER,
)
async def create_user(
    user: UserCreateSchema,
    user_service: UserServiceDependency,
    current_user: CurrentUser,
):

    return await user_service.create(
        UserCreateWithConfirmPassword(**user.model_dump(), created_by=current_user)
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, **DELETE_USER)
async def delete_user(
    user_id: UserID, user_service: UserServiceDependency, current_user: CurrentUser
):
    await user_service.delete(UserDelete(id=user_id, deleted_by=current_user))
