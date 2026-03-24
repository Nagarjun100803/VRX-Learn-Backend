from enum import StrEnum
from typing import Annotated

from pydantic import EmailStr, StringConstraints

from src.command.commands.base import BaseCmd, UserBase, UserID, AuditFields


class UserRole(StrEnum):
    ADMIN = "admin"
    SUBADMIN = "subadmin"
    TRAINER = "trainer"
    TRAINEE = "trainee"


Email = Annotated[EmailStr, StringConstraints(to_lower=True, strip_whitespace=True)]    
    
class UserCreate(BaseCmd):
    username: Annotated[str, StringConstraints(min_length=5)]
    email: Email
    password: str
    role: UserRole = UserRole.TRAINEE
    created_by: UserID



class UserCreateWithConfirmPassword(UserCreate):
    confirm_password: str
    

class PasswordUpdate(BaseCmd):
    email: EmailStr
    new_password: str
    

    
class UserGetByID(UserBase): ...


class UserGetByIDQuery(UserBase):
    viewer_id: UserID
    
    
class UserGetByEmail(BaseCmd): 
    email: EmailStr


class UserDelete(UserBase):
    deleted_by: UserID
    

class UserAuth(BaseCmd):
    email: EmailStr
    password: str
    

class User(AuditFields, UserCreate, UserBase): 
    
    def is_manager(self) -> bool:
        return self.role in {UserRole.SUBADMIN, UserRole.TRAINER}
        
