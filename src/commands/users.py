from pydantic import EmailStr, BaseModel, StringConstraints
from typing import Annotated
from src.commands.base import UserBase, UserID, AuditFields
from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    SUBADMIN = "subadmin"
    TRAINER = "trainer"
    TRAINEE = "trainee"


Email = Annotated[EmailStr, StringConstraints(to_lower=True, strip_whitespace=True)]    
    
class UserCreate(BaseModel):
    username: Annotated[str, StringConstraints(min_length=5)]
    email: Email
    password: str
    role: "UserRole" = "trainee" # Add explicit value, due to circular import issue.
    created_by: UserID



class UserCreateWithConfirmPassword(UserCreate):
    confirm_password: str
    

class PasswordUpdate(BaseModel):
    email: EmailStr
    new_password: str
    

    
class UserGetByID(UserBase): ...


class UserGetByIDQuery(UserBase):
    viewer_id: UserID
    
    
class UserGetByEmail(BaseModel): 
    email: EmailStr


class UserDelete(UserBase):
    deleted_by: UserID
    

class UserAuth(BaseModel):
    email: EmailStr
    password: str
    

class User(AuditFields, UserCreate, UserBase): 
    ...
