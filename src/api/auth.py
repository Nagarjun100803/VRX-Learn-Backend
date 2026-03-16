from dataclasses import dataclass
from typing import Self

from src.api.jwt import JWTHandler
from src.command.commands.base import UserID
from src.command.commands.users import UserGetByID, UserRole
from src.command.repositories.users import UserRespository
from src.exceptions import UnAuthenticated, UnauthorizedError



@dataclass
class UserContext:
    user_id: UserID
    role: UserRole
    
    def validate_role(self, role: UserRole) -> Self:
        if self.role != UserRole(role).value:
            raise UnauthorizedError(
                message=f"Permission Denied: '{role.value}' only."
            )
        return self


class AuthenticationService:
    
    def __init__(
        self,
        user_repo: UserRespository,
        jwt_handler: JWTHandler
    ) -> None:
        
        self.user_repo = user_repo
        self.jwt_handler = jwt_handler

    
    async def authenticate(self, token: str) -> UserContext:
        jwt_payload = self.jwt_handler.decode_jwt_token(token=token)
        # Get user from the user id.
        user = await self.user_repo.get(UserGetByID(id=jwt_payload.user_id))
        
        if user is None:
            raise UnAuthenticated(message=f"No user found with this user id: {jwt_payload.user_id}")
        
        return UserContext(user_id=jwt_payload.user_id, role=jwt_payload.role)
 
