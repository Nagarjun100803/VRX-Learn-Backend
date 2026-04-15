import hashlib
from typing import Self

from src.api.jwt import JWTHandler
from src.cache import CacheKey, CacheService, CacheTag
from src.command.commands.base import BaseCmd, UserID
from src.command.commands.users import UserGetByID, UserRole
from src.command.repositories.users import UserRepository
from src.exceptions import UnAuthenticated, UnauthorizedError


class UserContext(BaseCmd):
    user_id: UserID
    role: UserRole
    username: str

    def validate_role(self, role: UserRole) -> Self:
        if self.role != UserRole(role).value:
            raise UnauthorizedError(message=f"Permission Denied: '{role.value}' only.")
        return self


class AuthenticationService:
    def __init__(
        self,
        user_repo: UserRepository,
        jwt_handler: JWTHandler,
        cache_service: CacheService,
    ) -> None:

        self.user_repo = user_repo
        self.jwt_handler = jwt_handler
        self.cache_service = cache_service

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def _get_user_context(self, token: str) -> UserContext:

        jwt_payload = self.jwt_handler.decode_jwt_token(token=token)

        # Get user from the user id.
        user = await self.user_repo.get(UserGetByID(id=jwt_payload.user_id))

        if user is None:
            raise UnAuthenticated(
                message=f"No user found with this user id: {jwt_payload.user_id}"
            )

        return UserContext(user_id=user.id, role=user.role, username=user.username)

    async def authenticate(self, token: str) -> UserContext:

        hashed_token = self._hash_token(token=token)

        key = CacheKey.USER_CONTEXT.format(token=hashed_token)

        return await self.cache_service.get_or_set(
            key=key,
            model=UserContext,
            fetch_func=lambda: self._get_user_context(token=token),
            tags={CacheTag.USER_CONTEXT.format(token=hashed_token)},
            ttl=5 * 60,  # 5 minutes,
            negative_ttl=1 * 60,  # 1 minute
        )
