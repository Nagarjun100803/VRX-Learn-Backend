from typing import Annotated, Self

from pydantic import Field, StringConstraints, model_validator

from src.command.commands.base import BaseCmd, UserID
from src.command.commands.users import Email, UserRole
from src.exceptions import UnAuthorizedError


class SignUp(BaseCmd):
    """Payload for signing up a new user."""

    username: Annotated[
        str, StringConstraints(min_length=3), Field(description="Username")
    ]
    email: Annotated[Email, Field(description="Email address")]
    password: Annotated[str, Field(description="Password")]
    confirm_password: Annotated[str, Field(description="Confirm password")]

    @model_validator(mode="after")
    def validate_password(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Password and Confirm password should match.")
        return self


class Login(BaseCmd):
    """Payload for logging in."""

    email: Annotated[Email, Field(description="Email address")]
    password: Annotated[str, Field(description="Password")]


class ForgetPassword(BaseCmd):
    """Request reset password by email."""

    email: Annotated[Email, Field(description="Email address")]


class ResetPasswordContext(BaseCmd):
    """Context used by notifications to reset password."""

    username: Annotated[
        str, Field(description="Name of the user to be used in the email.")
    ]
    token: Annotated[str, Field(description="Reset password token, send via email.")]


class ResetPassword(BaseCmd):
    """Payload for requesting reset password. Used by API layer."""

    new_password: Annotated[str, Field(description="New password")]
    new_confirm_password: Annotated[str, Field(description="Confirm new password")]

    @model_validator(mode="after")
    def validate_password(self) -> Self:
        if self.new_password != self.new_confirm_password:
            raise ValueError("Password and Confirm password should match.")
        return self


class ResetPasswordByToken(ResetPassword):  # Action + Entity + Optional Context
    """Payload for resetting password with the token and new password."""

    token: Annotated[
        str, Field(description="Token received back from the email to reset password.")
    ]


class PasswordReset(BaseCmd):  # Entity + Action.
    """Payload for resetting password, Used by Repository layer."""

    id: Annotated[UserID, Field(description="User ID")]
    password: Annotated[str, Field(description="New password")]


class VerifyEmail(BaseCmd):
    """Payload for verifying email"""

    email: Annotated[Email, Field(description="Email address to verify")]


class VerifyEmailByToken(BaseCmd):
    """Verify email by token"""

    token: Annotated[str, Field(description="Verification token")]


class JWTToken(BaseCmd):
    """Token used for authentication"""

    token: Annotated[
        str, Field(description="JWT token that is used for authentication")
    ]


class UserContext(BaseCmd):
    """Context of the authenticated user"""

    user_id: Annotated[UserID, Field(description="User ID")]
    username: Annotated[str, Field(description="Username")]
    email: Annotated[Email, Field(description="Email address")]
    role: Annotated[UserRole, Field(description="User role")]

    def validate_role(self, role: UserRole) -> Self:
        if self.role != UserRole(role).value:
            raise UnAuthorizedError(message=f"Permission Denied: '{role.value}' only.")
        return self
