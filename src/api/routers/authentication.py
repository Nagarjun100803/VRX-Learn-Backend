from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode, urljoin

from fastapi import APIRouter, BackgroundTasks, status
from fastapi.responses import JSONResponse

from src.api.dependencies import (
    AuthenticationServiceDependency,
    NotificationServiceDependency,
    UserContextDependency,
    UserOnboardServiceDependency,
)
from src.api.docs.users import LOGIN, LOGOUT, ME
from src.command.commands.authentication import (
    ForgetPassword,
    Login,
    ResetPassword,
    ResetPasswordByToken,
    ResetPasswordContext,
    SignUp,
    VerifyEmailByToken,
)
from src.settings import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_class=JSONResponse)
async def signup(
    signup_details: SignUp,
    authentication_service: AuthenticationServiceDependency,
    notification_service: NotificationServiceDependency,
    background_tasks: BackgroundTasks,
):
    user = await authentication_service.signup(signup_details)
    email_verification_token = authentication_service.generate_email_verification_token(
        user.email
    )
    params = urlencode({"token": email_verification_token})
    url = urljoin(settings.frontend.base_url, settings.email_verification.path)
    verify_link = f"{url}?{params}"

    # Send the verification email in the background.
    kwargs = {"to": user.email, "username": user.username, "verify_link": verify_link}

    background_tasks.add_task(notification_service.send_verify_email, **kwargs)

    return JSONResponse(content={"message": "User signed up successfully"})


@router.post("/verify-email", response_class=JSONResponse)
async def verify_email(
    token: str,
    authentication_service: AuthenticationServiceDependency,
    user_onboard_service: UserOnboardServiceDependency,
    background_tasks: BackgroundTasks,
):
    context = await authentication_service.verify_email(VerifyEmailByToken(token=token))
    response = JSONResponse(content={"message": "Email verified successfully"})
    response.set_cookie(
        key="access_token",
        value=context.jwt_token,
        samesite="none",
        httponly=True,
        secure=True,
        expires=datetime.now(tz=UTC) + timedelta(days=2),
    )

    background_tasks.add_task(user_onboard_service.onboard_user, context.user.id)

    return response


@router.post("/login", **LOGIN, response_class=JSONResponse)
async def login(
    login_details: Login, authentication_service: AuthenticationServiceDependency
):

    access_token = await authentication_service.login(login_details)

    response = JSONResponse(content={"message": "Logged in successfully"})
    response.set_cookie(
        key="access_token",
        value=access_token,
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
    authentication_service: AuthenticationServiceDependency,
    notification_service: NotificationServiceDependency,
    background_tasks: BackgroundTasks,
):

    context: ResetPasswordContext = await authentication_service.forget_password(
        cmd=forget_password
    )
    params = urlencode(query={"token": context.token})
    url = urljoin(settings.frontend.base_url, settings.password_reset.path)
    final_url = f"{url}?{params}"

    # Send reset password email using background tasks.
    kwargs = {
        "username": context.username,
        "to": forget_password.email,
        "reset_link": final_url,
    }

    background_tasks.add_task(
        func=notification_service.send_reset_password_email, **kwargs
    )


@router.patch("/reset-password", response_class=JSONResponse)
async def reset_password(
    token: str,
    reset_password: ResetPassword,
    authentication_service: AuthenticationServiceDependency,
):
    await authentication_service.reset_password(
        cmd=ResetPasswordByToken(
            token=token,
            new_password=reset_password.new_password,
            new_confirm_password=reset_password.new_confirm_password,
        )
    )

    return JSONResponse(content={"message": "Password reset successfully"})


@router.get("/me", **ME)
async def me(user_context: UserContextDependency):
    return user_context
