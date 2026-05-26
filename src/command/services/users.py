from typing import ClassVar, Type, cast

from src.auth import Action, AuthService, Entity, require_authorization
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

    def __init__(
        self,
        repo: UserRepository,
        password_hasher: PasswordHasher,
        auth_service: AuthService,
    ) -> None:

        self.repo = repo
        self.password_hasher = password_hasher
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

    async def update(self, cmd): ...
