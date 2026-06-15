from typing import ClassVar, Type, cast

from src.auth import Entity
from src.command.commands.users import (
    User,
    UserCreateWithConfirmPassword,
    UserDelete,
    UserGetByID,
    UserGetByIDQuery,
    VerifiedUserCreate,
)
from src.command.repositories.users import UserRepository
from src.command.services.base import BaseService
from src.core.security.password import PasswordHasher
from src.exceptions import (
    EntityNotFoundError,
    PasswordMismatchError,
    UserAlreadyExistsError,
    UserNotFoundError,
)


class UserService(BaseService[User]):
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = UserNotFoundError
    _entity: ClassVar[Entity] = Entity.USER

    def __init__(self, repo: UserRepository, password_hasher: PasswordHasher) -> None:

        self.repo = repo
        self.password_hasher = password_hasher

    async def create(self, cmd: UserCreateWithConfirmPassword) -> User:

        # Check for the password match.
        if cmd.password != cmd.confirm_password:
            raise PasswordMismatchError()

        # Check for the duplicate email.
        if await self.repo.exists_by(email=cmd.email):
            raise UserAlreadyExistsError(value=cmd.email, identifier="email")

        hashed_password = self.password_hasher.hash_password(cmd.password)
        user = await self.repo.add(
            VerifiedUserCreate(
                username=cmd.username,
                email=cmd.email,
                role=cmd.role,
                password=hashed_password,
                created_by=cmd.created_by,
            )
        )

        return cast(User, user)

    async def delete(self, cmd: UserDelete) -> User:
        user = await self.repo.delete(cmd)
        return self._require_entity(user, value=cmd.id)

    async def get(self, query: UserGetByIDQuery) -> User:

        user = await self.repo.get(UserGetByID(id=query.id))

        return self._require_entity(user, value=query.id)

    async def update(self, cmd): ...
