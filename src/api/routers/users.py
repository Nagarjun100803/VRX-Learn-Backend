from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.api.dependencies import (
    CurrentUser,
    JWTServiceDependency,
    UserContextDependency,
    UserServiceDependency,
)
from src.api.jwt import JWTPayloadCreate
from src.api.schemas.users import LoginSchema, UserCreateSchema, UserOutSchema
from src.command.commands.base import UserID
from src.command.commands.users import (
    UserAuth,
    UserCreateWithConfirmPassword,
    UserDelete,
    UserGetByIDQuery,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/login")
async def login(
    login_details: LoginSchema,
    user_service: UserServiceDependency,
    jwt_service: JWTServiceDependency,
):

    # Get user.
    user = await user_service.authenticate(
        UserAuth(email=login_details.email, password=login_details.password)
    )

    # Add a token in cookie and return.
    token = jwt_service.create_jwt_token(
        payload=JWTPayloadCreate(user_id=user.id, role=user.role)
    )
    response = JSONResponse(content={"message": "Logged in successfully"})
    response.set_cookie(
        key="access_token", value=token, samesite="none", httponly=True, secure=True
    )
    return response


@router.post("/logout")
async def logout():
    response = JSONResponse(content={"message": "Logged out successfully."})
    response.delete_cookie(
        key="access_token", httponly=True, samesite="none", secure=True
    )
    return response


@router.get("/me")
async def me(user_context: UserContextDependency):
    return user_context


@router.get("/{user_id}", response_model=UserOutSchema)
async def get_user(
    user_id: UserID, user_service: UserServiceDependency, current_user: CurrentUser
):
    return await user_service.get(UserGetByIDQuery(id=user_id, viewer_id=current_user))


@router.post("/", response_model=UserOutSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreateSchema,
    user_service: UserServiceDependency,
    current_user: CurrentUser,
):

    return await user_service.create(
        UserCreateWithConfirmPassword(**user.model_dump(), created_by=current_user)
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UserID, user_service: UserServiceDependency, current_user: CurrentUser
):
    await user_service.delete(UserDelete(id=user_id, deleted_by=current_user))
