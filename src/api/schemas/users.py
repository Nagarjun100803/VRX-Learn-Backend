from pydantic import BaseModel, ConfigDict, StringConstraints, EmailStr
from typing import Annotated
from src.commands.users import UserRole
from src.commands.base import UserID



class UserCreateSchema(BaseModel):
    username: Annotated[str, StringConstraints(min_length=5)]
    email: EmailStr
    password: str
    confirm_password: str
    role: UserRole = UserRole.TRAINEE
    model_config = ConfigDict(str_strip_whitespace=True, str_to_lower=True)
    

 
class UserOutSchema(BaseModel):
    id: UserID
    email: EmailStr
    role: UserRole
    



    