from passlib.hash import argon2
from typing import ClassVar, Type, override
from src.repository.users import UserRespository
from src.service.base import BaseService, require_access
from src.service.permission_policy import Entity
from src.exceptions import EntityNotFoundError, UnAuthenticated, UserNotFoundError, UserAlreadyExistsError, PasswordMismatchError
from src.commands.users import (
    User, UserCreate, UserDelete, PasswordUpdate,
    UserCreateWithConfirmPassword, UserGetByIDQuery, 
    UserGetByID, UserAuth, UserGetByEmail
)
from src.commands.base import UserID
from dataclasses import dataclass



class PasswordHandler:
    "Helper class to perfrom the password hashing and verifying."
    def hash_password(self, raw_password: str) -> str:
        return argon2.hash(raw_password)
        

    def verify_password(self, raw_password: str, hashed_password: str) -> bool:
        res = argon2.verify(raw_password, hashed_password)
        print(F"Verification is {res}")
        return res
    
@dataclass(kw_only=True)
class UserService(BaseService[User]):
    
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = UserNotFoundError
    _entity: ClassVar[Entity] = Entity.USER 
    
    repo: UserRespository
    password_handler: PasswordHandler


    @require_access(action="create", user_id_alias="created_by", obj_name="cmd")
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
        user = await self.user_repo.add(
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
        if not await self.user_repo.exists_by(email=cmd.email):
            raise UserNotFoundError(
                value=cmd.email, 
                identifier="email"
            )
        hashed_password = self.password_handler.hash_password(cmd.new_password)
        user = await self.user_repo.update(
            PasswordUpdate(
                email=cmd.email, 
                new_password=hashed_password
            )
        )
        return self._require_entity(user)
        
    
    @require_access(action="delete", user_id_alias="deleted_by", entity_id_alias="id")
    @override
    async def delete(self, cmd: UserDelete) -> User:
        user = await self.user_repo.delete(cmd)
        return self._require_entity(user, value=cmd.id)
    
    
    @require_access(action="view", user_id_alias="viewer_id",  entity_id_alias="id", obj_name="query")
    @override
    async def get(self, query: UserGetByIDQuery) -> User:
        user = await self.user_repo.get(UserGetByID(id=query.id))
        return self._require_entity(user, value=query.id)
           
        
    async def authenticate(self, auth: UserAuth) -> User:
        user = await self.repo.get(UserGetByEmail(email=auth.email))
        if user is None or \
            not self.password_handler.verify_password(
                auth.password, user.password
            ):
            raise UnAuthenticated("Invalid email or password.")
        return user
    
