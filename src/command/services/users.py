from typing import ClassVar, Optional, Type, Union, cast

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from passlib.hash import argon2  # type: ignore

from src.auth import Action, AuthService, Entity, require_authorization
from src.command.commands.users import (
    ForgetPassword,
    RequestResetPassword,
    ResetPassword,
    User,
    UserAuth,
    UserCreate,
    UserCreateWithConfirmPassword,
    UserDelete,
    UserGetByEmail,
    UserGetByID,
    UserGetByIDQuery,
)
from src.command.repositories.users import UserRepository
from src.command.services.base import BaseService
from src.exceptions import (
    EntityNotFoundError,
    InvalidPasswordResetTokenError,
    PasswordMismatchError,
    PasswordResetTokenExpiredError,
    UnAuthenticated,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.settings import settings

_serializer = URLSafeTimedSerializer(
    secret_key=settings.password_reset.secret_key.get_secret_value(),
    salt=settings.password_reset.salt.get_secret_value(),
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
        repo: UserRepository,
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

    async def _update_password(self, cmd: ResetPassword) -> Optional[User]:

        if not await self.repo.exists_by(id=cmd.id):
            raise UserNotFoundError(value=cmd.id)

        hashed_password = self.password_handler.hash_password(cmd.password)

        return await self.repo.update(
            cmd=ResetPassword(id=cmd.id, password=hashed_password)
        )

    async def _update_password_by_owner(
        self, cmd: RequestResetPassword
    ) -> Optional[User]:

        try:
            payload = _serializer.loads(
                cmd.token, max_age=settings.password_reset.token_expire_seconds
            )
            email = payload["email"]
            user = await self.repo.get(UserGetByEmail(email=email))

            if user is None:
                raise UserNotFoundError(value=email, identifier="email")

            hashed_password = self.password_handler.hash_password(cmd.password)

            return await self.repo.update(
                cmd=ResetPassword(id=user.id, password=hashed_password)
            )

        except SignatureExpired:
            raise PasswordResetTokenExpiredError()
        except BadSignature:
            raise InvalidPasswordResetTokenError()

    async def update(self, cmd: Union[ResetPassword, RequestResetPassword]) -> User:

        if isinstance(cmd, ResetPassword):
            updated_user = await self._update_password(cmd=cmd)
        else:
            updated_user = await self._update_password_by_owner(cmd=cmd)

        return self._require_entity(updated_user)

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

    async def request_password_reset(self, cmd: ForgetPassword) -> tuple[User, str]:
        user = await self.repo.get(UserGetByEmail(email=cmd.email))
        if user is None:
            raise UserNotFoundError(value=cmd.email, identifier="email")

        token = _serializer.dumps({"email": cmd.email})

        return (user, token)
