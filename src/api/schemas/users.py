from datetime import datetime
from typing import Self

from pydantic import model_validator

from src.command.commands.base import BaseCmd, UserID
from src.command.commands.users import Email, UserCreateCore, UserRole


class UserCreateSchema(UserCreateCore):
    confirm_password: str


class UserOutSchema(BaseCmd):
    id: UserID
    username: str
    email: Email
    role: UserRole
    status: str = "active"
    created_at: datetime


class LoginSchema(BaseCmd):
    email: Email
    password: str


class ResetPasswordSchema(BaseCmd):
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self
