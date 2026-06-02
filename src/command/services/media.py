from typing import Optional, cast

from asyncpg import Connection

from src.command.commands.media import (
    Media,
    MediableType,
    MediaCreate,
    MediaDelete,
    MediaGet,
    MediaStatusUpdate,
    MediaStatusUpdateByMediable,
)
from src.command.repositories import MediaRepository
from src.exceptions import MediaAlreadyExistsError, MediaNotFoundError


class MediaService:
    def __init__(self, repo: MediaRepository) -> None:
        self.repo = repo

    def _require_entity(self, entity: Optional[Media], **error_kwargs) -> Media:
        if entity is None:
            raise MediaNotFoundError(**error_kwargs)
        return entity

    async def create(
        self, cmd: MediaCreate, connection: Optional[Connection] = None
    ) -> Media:
        if await self.repo.exists_by(key=cmd.key):
            raise MediaAlreadyExistsError(cmd.key, identifier="key")
        return cast(Media, await self.repo.add(cmd, connection=connection))

    async def update(
        self, cmd: MediaStatusUpdateByMediable, connection: Optional[Connection] = None
    ) -> Media:

        media = await self.get_by_mediable(
            mediable_id=cmd.mediable_id,
            mediable_type=cmd.mediable_type,
            connection=connection,
        )

        return self._require_entity(
            await self.repo.update(
                cmd=MediaStatusUpdate(
                    id=media.id, status=cmd.status, updated_by=cmd.updated_by
                ),
                connection=connection,
            ),
            value=cmd.mediable_id,
            alias=cmd.mediable_type.title(),
        )

    async def delete(
        self, cmd: MediaDelete, connection: Optional[Connection] = None
    ) -> Media:
        return self._require_entity(
            await self.repo.delete(cmd, connection=connection), value=cmd.id
        )

    async def get(
        self, query: MediaGet, connection: Optional[Connection] = None
    ) -> Media:
        return self._require_entity(
            await self.repo.get(query, connection=connection), value=query.id
        )

    async def get_by_mediable(
        self,
        mediable_id: int,
        mediable_type: MediableType,
        connection: Optional[Connection] = None,
    ) -> Media:

        media = await self.repo.get_by_mediable(
            mediable_id=mediable_id, mediable_type=mediable_type, connection=connection
        )

        return self._require_entity(
            media, value=mediable_id, alias=mediable_type.title()
        )
