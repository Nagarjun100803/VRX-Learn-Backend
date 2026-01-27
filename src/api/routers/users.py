from fastapi import APIRouter, status
from src.commands.base import UserID
from src.commands.users import UserGetByIDQuery, UserCreateWithConfirmPassword, UserDelete
from src.api.dependencies import UserServiceDependency, CurrentUser
from src.api.schemas.users import UserCreateSchema, UserOutSchema


user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get("/{user_id}", response_model=UserOutSchema)
async def get_user(
    user_id: UserID,
    user_service: UserServiceDependency,
    current_user: CurrentUser
):
    return await user_service.get(        
        UserGetByIDQuery(
            id=user_id,
            viewer_id=current_user
        )
    )
    


@user_router.post("/", response_model=UserOutSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreateSchema,
    user_service: UserServiceDependency,
    current_user: CurrentUser
):
    
    return await user_service.create(
        UserCreateWithConfirmPassword(
            **user.model_dump(),
            created_by=current_user
        )
    )



@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UserID,
    user_service: UserServiceDependency,
    current_user: CurrentUser
):
    await user_service.delete(
        UserDelete(
            id=user_id,
            deleted_by=current_user
        )
    )
    