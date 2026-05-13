from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode, urljoin

from fastapi import APIRouter, BackgroundTasks, status
from starlette.responses import JSONResponse

from src.api.dependencies import (
    JWTServiceDependency,
    NotificationServiceDependency,
    UserContextDependency,
    UserServiceDependency,
)
from src.api.docs.users import LOGIN, LOGOUT, ME
from src.api.jwt import JWTPayloadCreate
from src.api.schemas.users import LoginSchema, ResetPasswordSchema, UserOutSchema
from src.command.commands.users import ForgetPassword, RequestResetPassword, UserAuth
from src.settings import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", **LOGIN, response_class=JSONResponse)
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


@router.post("/logout", **LOGOUT)
async def logout():
    response = JSONResponse(content={"message": "Logged out successfully."})
    response.delete_cookie(
        key="access_token", httponly=True, samesite="none", secure=True
    )
    return response


@router.post("/forget-password", status_code=status.HTTP_204_NO_CONTENT)
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


@router.patch("/reset-password", response_model=UserOutSchema)
async def reset_password(
    token: str, reset_password: ResetPasswordSchema, user_service: UserServiceDependency
):
    return await user_service.update(
        cmd=RequestResetPassword(token=token, password=reset_password.password)
    )


@router.get("/me", **ME)
async def me(user_context: UserContextDependency):
    return user_context
