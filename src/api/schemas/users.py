from typing import Annotated

from pydantic import ConfigDict, StringConstraints

from src.command.commands.base import BaseCmd, UserID
from src.command.commands.users import Email, UserRole


class UserCreateSchema(BaseCmd):
    username: Annotated[str, StringConstraints(min_length=5)]
    email: Email
    password: str
    confirm_password: str
    role: UserRole = UserRole.TRAINEE
    model_config = ConfigDict(str_strip_whitespace=True, str_to_lower=True)


class UserOutSchema(BaseCmd):
    id: UserID
    username: str
    email: Email
    role: UserRole


class LoginSchema(BaseCmd):
    email: Email
    password: str
