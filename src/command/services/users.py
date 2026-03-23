from passlib.hash import argon2
from typing import ClassVar, Type, override
from src.command.repositories.users import UserRespository
from src.command.services.base import BaseService
from src.exceptions import EntityNotFoundError, UnAuthenticated, UserNotFoundError, UserAlreadyExistsError, PasswordMismatchError
from src.command.commands.users import (
    User, UserCreate, UserDelete, PasswordUpdate,
    UserCreateWithConfirmPassword, UserGetByIDQuery, 
    UserGetByID, UserAuth, UserGetByEmail
)
from src.auth import AuthService, Entity, Action, require_authorization


class PasswordHandler:
    "Helper class to perfrom the password hashing and verifying."
    def hash_password(self, raw_password: str) -> str:
        return argon2.hash(raw_password)
        

    def verify_password(self, raw_password: str, hashed_password: str) -> bool:
        return argon2.verify(raw_password, hashed_password)
        
    
class UserService(BaseService[User]):
    
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = UserNotFoundError
    _entity: ClassVar[Entity] = Entity.USER 
    
    def __init__(
        self,
        repo: UserRespository,
        password_handler: PasswordHandler,
        auth_service: AuthService
    ) -> None:
        
        self.repo = repo
        self.password_handler = password_handler
        self.auth_service = auth_service


    @require_authorization(
        action=Action.CREATE,
        entity=Entity.USER,
        user_id_field="created_by",
        parent_id_field=None, #Explicitly set None, because it is root.
        object_name="cmd"
    )
    @override
    async def create(self, cmd: UserCreateWithConfirmPassword) -> User:
        
        # Check for the password match.
        if cmd.password != cmd.confirm_password:
            raise PasswordMismatchError()
        
        # Check for the duplicate email.
        if await self.repo.exists_by(email=cmd.email):
            raise UserAlreadyExistsError(
                value=cmd.email, identifier="email"
            )
    
        hashed_password = self.password_handler.hash_password(cmd.password)
        user = await self.repo.add(
            UserCreate(
                username=cmd.username,
                email=cmd.email,
                role=cmd.role,
                password=hashed_password,
                created_by=cmd.created_by
            ) 
        )
        
        return user

    
    
    @override
    async def update(self, cmd: PasswordUpdate) -> User:
        # Check user found with the email.
        if not await self.repo.exists_by(email=cmd.email):
            raise UserNotFoundError(
                value=cmd.email, 
                identifier="email"
            )
        hashed_password = self.password_handler.hash_password(cmd.new_password)
        user = await self.repo.update(
            PasswordUpdate(
                email=cmd.email, 
                new_password=hashed_password
            )
        )
        return self._require_entity(user)
        
    
    @require_authorization(
        action=Action.DELETE,
        entity=Entity.USER,
        user_id_field="deleted_by",
        entity_id_field="id",
        object_name="cmd"
    )
    @override
    async def delete(self, cmd: UserDelete) -> User:
        user = await self.repo.delete(cmd)
        return self._require_entity(user, value=cmd.id)
    
    
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.USER,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query"
    )
    @override
    async def get(self, query: UserGetByIDQuery) -> User:
        user = await self.repo.get(UserGetByID(id=query.id))
        return self._require_entity(user, value=query.id)
           
        
    async def authenticate(self, auth: UserAuth) -> User:
        user = await self.repo.get(UserGetByEmail(email=auth.email))
        if user is None or \
            not self.password_handler.verify_password(
                auth.password, user.password
            ):
            raise UnAuthenticated("Invalid email or password.")
        return user
    
if __name__ == "__main__":
    password_handler = PasswordHandler()
    hash = "$argon2id$v=19$m=65536,t=3,p=4$PWfM+b+3tjZGKOUcwxgDwA$ElbUpsAGrjxIRjdx/ECUdnTJUxUH7xbsYuAtPAcxVK0"
    print(password_handler.verify_password("123",  hash))
    