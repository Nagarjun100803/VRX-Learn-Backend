from enum import StrEnum
from typing import Annotated, Optional

from pydantic import EmailStr, StringConstraints

from src.command.commands.base import AuditFields, BaseCmd, UserBase, UserID


class UserRole(StrEnum):
    ADMIN = "admin"
    SUBADMIN = "subadmin"
    TRAINER = "trainer"
    TRAINEE = "trainee"


Email = Annotated[EmailStr, StringConstraints(to_lower=True, strip_whitespace=True)]


class UserCreateCore(BaseCmd):
    username: Annotated[str, StringConstraints(min_length=4)]
    email: Email
    password: str
    role: UserRole = UserRole.TRAINEE


class UserCreate(UserCreateCore):
    created_by: Optional[UserID] = None


class UserCreateWithConfirmPassword(UserCreate):
    confirm_password: str


class VerifiedUserCreate(UserCreate):
    email_verified: bool = True


class UserGetByID(UserBase): ...


class UserGetByIDQuery(UserBase):
    viewer_id: UserID


class UserGetByEmail(BaseCmd):
    email: EmailStr


class UserDelete(UserBase):
    deleted_by: UserID


class User(AuditFields, UserCreateCore, UserBase):
    email_verified: bool = False

    def is_manager(self) -> bool:
        return self.role in {UserRole.SUBADMIN, UserRole.TRAINER}
