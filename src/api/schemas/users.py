from pydantic import BaseModel, ConfigDict, StringConstraints
from typing import Annotated
from src.command.commands.users import UserRole, Email
from src.command.commands.base import UserID



class UserCreateSchema(BaseModel):
    username: Annotated[str, StringConstraints(min_length=5)]
    email: Email
    password: str
    confirm_password: str
    role: UserRole = UserRole.TRAINEE
    model_config = ConfigDict(str_strip_whitespace=True, str_to_lower=True)
    

 
class UserOutSchema(BaseModel):
    id: UserID
    email: Email
    role: UserRole
    

class LoginSchema(BaseModel):
    email: Email
    password: str
    