from typing import ClassVar, Type, cast

from passlib.hash import argon2

from src.auth import Action, AuthService, Entity, require_authorization
from src.command.commands.users import (
    PasswordUpdate,
    User,
    UserAuth,
    UserCreate,
    UserCreateWithConfirmPassword,
    UserDelete,
    UserGetByEmail,
    UserGetByID,
    UserGetByIDQuery,
)
from src.command.repositories.users import UserRespository
from src.command.services.base import BaseService
from src.exceptions import (
    EntityNotFoundError,
    PasswordMismatchError,
    UnAuthenticated,
    UserAlreadyExistsError,
    UserNotFoundError,
)


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
        auth_service: AuthService,
    ) -> None:

        self.repo = repo
        self.password_handler = password_handler
        self.auth_service = auth_service

    @require_authorization(
        action=Action.CREATE,
        entity=Entity.USER,
        user_id_field="created_by",
        parent_id_field=None,  # Explicitly set None, because it is root.
        object_name="cmd",
    )
    async def create(self, cmd: UserCreateWithConfirmPassword) -> User:

        # Check for the password match.
        if cmd.password != cmd.confirm_password:
            raise PasswordMismatchError()

        # Check for the duplicate email.
        if await self.repo.exists_by(email=cmd.email):
            raise UserAlreadyExistsError(value=cmd.email, identifier="email")

        hashed_password = self.password_handler.hash_password(cmd.password)
        user = await self.repo.add(
            UserCreate(
                username=cmd.username,
                email=cmd.email,
                role=cmd.role,
                password=hashed_password,
                created_by=cmd.created_by,
            )
        )

        return cast(User, user)

    async def update(self, cmd: PasswordUpdate) -> User:
        # Check user found with the email.
        if not await self.repo.exists_by(email=cmd.email):
            raise UserNotFoundError(value=cmd.email, identifier="email")

        hashed_password = self.password_handler.hash_password(cmd.new_password)

        user = await self.repo.update(
            PasswordUpdate(email=cmd.email, new_password=hashed_password)
        )

        return self._require_entity(user)

    @require_authorization(
        action=Action.DELETE,
        entity=Entity.USER,
        user_id_field="deleted_by",
        entity_id_field="id",
        object_name="cmd",
    )
    async def delete(self, cmd: UserDelete) -> User:
        user = await self.repo.delete(cmd)
        return self._require_entity(user, value=cmd.id)

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.USER,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query",
    )
    async def get(self, query: UserGetByIDQuery) -> User:

        user = await self.repo.get(UserGetByID(id=query.id))

        return self._require_entity(user, value=query.id)

    async def authenticate(self, auth: UserAuth) -> User:
        user = await self.repo.get(UserGetByEmail(email=auth.email))
        if user is None or not self.password_handler.verify_password(
            auth.password, user.password
        ):
            raise UnAuthenticated("Invalid email or password.")

        await self.repo.update_last_login(user_id=user.id)

        return user
