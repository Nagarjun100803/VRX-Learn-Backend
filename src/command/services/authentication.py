from typing import Any, Optional

from itsdangerous import BadSignature, SignatureExpired

from src.command.commands.authentication import (
    ForgetPassword,
    JWTToken,
    Login,
    PasswordReset,
    ResetPasswordByToken,
    ResetPasswordContext,
    SignUp,
    UserContext,
    VerifyEmailByToken,
    VerifyEmailContext,
)
from src.command.commands.users import User, UserCreate, UserGetByEmail, UserGetByID
from src.command.repositories import AuthenticationRepository, UserRepository
from src.core.security.jwt import JWTHandler, JWTPayloadCreate
from src.core.security.password import PasswordHasher
from src.core.security.serializer import (
    reset_password_serializer,
    verify_email_serializer,
)
from src.exceptions import (
    EmailNotVerifiedError,
    ExpiredEmailVerificationTokenError,
    ExpiredPasswordResetTokenError,
    InvalidEmailVerificationTokenError,
    InvalidPasswordResetTokenError,
    UnAuthenticated,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.settings import settings


class AuthenticationService:
    def __init__(
        self,
        repo: AuthenticationRepository,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        jwt_handler: JWTHandler,
    ) -> None:

        self.repo = repo
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.jwt_handler = jwt_handler

    def _require_entity(self, record: Optional[User], **kwargs: Any) -> User:
        if record is None:
            raise UserNotFoundError(**kwargs)
        return record

    async def signup(self, cmd: SignUp) -> User:
        if await self.user_repo.get(UserGetByEmail(email=cmd.email)):
            raise UserAlreadyExistsError(value=cmd.email, identifier="email")

        hashed_password = self.password_hasher.hash_password(cmd.password)
        return await self.user_repo.add(
            UserCreate(username=cmd.username, email=cmd.email, password=hashed_password)
        )

    async def login(self, cmd: Login) -> str:
        user = await self.user_repo.get(UserGetByEmail(email=cmd.email))

        if user is None or not self.password_hasher.verify_password(
            raw_password=cmd.password, hashed_password=user.password
        ):
            raise UnAuthenticated("Incorrect Email or Password.")

        if not user.email_verified:
            raise EmailNotVerifiedError()

        # Encode the JWT token and return it.
        await self.repo.update_last_login(user_id=user.id)

        return self.jwt_handler.create_jwt_token(
            payload=JWTPayloadCreate(user_id=user.id, role=user.role)
        )

    async def forget_password(self, cmd: ForgetPassword) -> ResetPasswordContext:

        user = await self.user_repo.get(UserGetByEmail(email=cmd.email))

        if user is None:
            raise UserNotFoundError(value=cmd.email, identifier="email")

        if not user.email_verified:
            raise EmailNotVerifiedError("Email not verified.")

        token = reset_password_serializer.dumps({"email": cmd.email})

        return ResetPasswordContext(username=user.username, token=token)

    async def reset_password(self, cmd: ResetPasswordByToken) -> User:
        # Verify the token.
        try:
            payload = reset_password_serializer.loads(
                cmd.token, max_age=settings.password_reset.token_expire_seconds
            )
            user = await self.user_repo.get(UserGetByEmail(email=payload.get("email")))
            if user is None:
                raise UserNotFoundError(value=payload.get("email"), identifier="email")

            hashed_password = self.password_hasher.hash_password(cmd.new_password)
            updated_user = await self.repo.reset_password(
                PasswordReset(id=user.id, password=hashed_password)
            )

            return self._require_entity(updated_user, value=user.id)

        except SignatureExpired:
            raise ExpiredPasswordResetTokenError()

        except BadSignature:
            raise InvalidPasswordResetTokenError()

    def generate_email_verification_token(self, email: str) -> str:
        return verify_email_serializer.dumps({"email": email})

    async def verify_email(self, cmd: VerifyEmailByToken) -> VerifyEmailContext:

        try:
            payload = verify_email_serializer.loads(
                cmd.token, max_age=settings.email_verification.token_expire_seconds
            )
            user = await self.user_repo.get(UserGetByEmail(email=payload.get("email")))

            if user is None:
                raise UserNotFoundError(value=payload.get("email"), identifier="email")

            # If already verified.
            if not user.email_verified:
                await self.repo.update_email_verified(user_id=user.id)

            await self.repo.update_last_login(user_id=user.id)

            jwt_token = self.jwt_handler.create_jwt_token(
                payload=JWTPayloadCreate(user_id=user.id, role=user.role)
            )

            return VerifyEmailContext(jwt_token=jwt_token, user=user)

        except SignatureExpired:
            raise ExpiredEmailVerificationTokenError()
        except BadSignature:
            raise InvalidEmailVerificationTokenError()

    async def me(self, token: JWTToken) -> UserContext:

        payload = self.jwt_handler.decode_jwt_token(token=token.token)
        user = await self.user_repo.get(UserGetByID(id=payload.user_id))

        if user is None:
            raise UserNotFoundError(value=payload.user_id)

        return UserContext(
            user_id=user.id, username=user.username, email=user.email, role=user.role
        )
