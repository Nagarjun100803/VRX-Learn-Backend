from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode, urljoin

from fastapi import APIRouter, status
from fastapi.background import BackgroundTasks
from fastapi.responses import JSONResponse

from src.api.dependencies import (
    CurrentAdmin,
    CurrentUser,
    JWTServiceDependency,
    NotificationServiceDependency,
    UserContextDependency,
    UserServiceDependency,
)
from src.api.docs.users import CREATE_USER, DELETE_USER, GET_USER, LOGIN, LOGOUT, ME
from src.api.jwt import JWTPayloadCreate
from src.api.schemas.users import (
    LoginSchema,
    ResetPasswordSchema,
    UserCreateSchema,
    UserOutSchema,
)
from src.command.commands.base import UserID
from src.command.commands.users import (
    ForgetPassword,
    RequestResetPassword,
    ResetPassword,
    UserAuth,
    UserCreateWithConfirmPassword,
    UserDelete,
    UserGetByIDQuery,
)
from src.settings import settings

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/login", deprecated=True, **LOGIN)
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
        key="access_token",
        value=token,
        samesite="none",
        httponly=True,
        secure=True,
        expires=datetime.now(tz=UTC) + timedelta(days=2),
    )
    return response


@router.post("/logout", deprecated=True, **LOGOUT)
async def logout():
    response = JSONResponse(content={"message": "Logged out successfully."})
    response.delete_cookie(
        key="access_token", httponly=True, samesite="none", secure=True
    )
    return response


@router.get("/me", deprecated=True, **ME)
async def me(user_context: UserContextDependency):
    return user_context


@router.post(
    "/forget-password", status_code=status.HTTP_204_NO_CONTENT, deprecated=True
)
async def forget_password(
    forget_password: ForgetPassword,
    user_service: UserServiceDependency,
    notification_service: NotificationServiceDependency,
    background_tasks: BackgroundTasks,
):
    user, token = await user_service.request_password_reset(cmd=forget_password)
    params = urlencode(query={"token": token})
    url = urljoin(
        settings.password_reset.frontend_base_url, settings.password_reset.reset_path
    )
    final_url = f"{url}?{params}"

    # Send email using background tasks.
    kwargs = {"username": user.username, "to": user.email, "reset_link": final_url}

    background_tasks.add_task(
        func=notification_service.send_reset_password_email, **kwargs
    )


@router.patch("/reset-password", response_model=UserOutSchema, deprecated=True)
async def reset_password(
    token: str, reset_password: ResetPasswordSchema, user_service: UserServiceDependency
):
    return await user_service.update(
        cmd=RequestResetPassword(token=token, password=reset_password.password)
    )


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


@router.patch("/{user_id}/update-password", response_model=UserOutSchema)
async def update_password(
    user_id: UserID,
    password: str,
    user_service: UserServiceDependency,
    current_user: CurrentAdmin,
):
    return await user_service.update(ResetPassword(id=user_id, password=password))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, **DELETE_USER)
async def delete_user(
    user_id: UserID, user_service: UserServiceDependency, current_user: CurrentUser
):
    await user_service.delete(UserDelete(id=user_id, deleted_by=current_user))
