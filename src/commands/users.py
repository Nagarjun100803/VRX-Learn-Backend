from pydantic import EmailStr, BaseModel, StringConstraints, ConfigDict
from enum import StrEnum
from typing import Annotated
from src.commands.base import UserBase, UserID, AuditFields


class UserRole(StrEnum):
    ADMIN = "admin"
    SUBADMIN = "subadmin"
    TRAINER = "trainer"
    TRAINEE = "trainee"
    
    
    
class UserCreate(BaseModel):
    username: Annotated[str, StringConstraints(min_length=5)]
    email: EmailStr
    password: str
    role: UserRole = UserRole.TRAINEE
    created_by: UserID
    model_config = ConfigDict(str_strip_whitespace=True, str_to_lower=True)



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
