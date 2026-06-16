from typing import Any, ClassVar, Optional

from asyncpg import Connection, Record
from pydantic import BaseModel
from pypika import PostgreSQLQuery, functions
from pypika.terms import Criterion, Parameter

from src.command.commands.lessons import (
    Lesson,
    LessonCreateWithPosition,
    LessonDelete,
    LessonGet,
    LessonUpdate,
    LessonWithMedia,
)
from src.command.commands.media import MediableType, MediaStatus
from src.command.repositories.base import BaseRepository
from src.database import ExecutableSQL
from src.query_builder import lesson_table, media_asset_table


class LessonRepository(BaseRepository[Lesson]):
    tablename: ClassVar[str] = "lessons"

    def _to_domain(self, row: Optional[Record]) -> Optional[Lesson]:
        if row is None:
            return None
        return Lesson.model_validate(dict(row))

    async def add(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Lesson:
        cmd = self._normalize(cmd, LessonCreateWithPosition)
        return await super().add(cmd, connection=connection)

    async def update(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Lesson]:
        cmd = self._normalize(cmd, LessonUpdate)
        return await super().update(cmd, connection=connection)

    async def _delete_lesson(
        self, cmd: LessonDelete, connection: Optional[Connection] = None
    ) -> Optional[Lesson]:

        # Delete the lesson.
        delete_lesson_query = (
            PostgreSQLQuery.update(lesson_table)
            .set(lesson_table.deleted_at, functions.Now())
            .set(lesson_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        lesson_table.id == Parameter("$1"),
                        lesson_table.deleted_at.isnull(),
                    ]
                )
            )
        )

        # Delete media associated with that lesson.
        delete_lesson_media_sql = (
            PostgreSQLQuery.update(media_asset_table)
            .set(media_asset_table.deleted_at, functions.Now())
            .set(media_asset_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_id == Parameter("$1"),
                        media_asset_table.mediable_type == Parameter("$3"),
                    ]
                )
            )
        ).get_sql()

        delete_lesson_query: Any = delete_lesson_query.returning("*")  # type: ignore
        delete_lesson_sql: str = delete_lesson_query.get_sql()

        executable1 = ExecutableSQL(
            sql=delete_lesson_sql, values=(cmd.id, cmd.deleted_by)
        )
        executable2 = ExecutableSQL(
            sql=delete_lesson_media_sql,
            values=(cmd.id, cmd.deleted_by, MediableType.LESSON),
        )

        async with self.db.transaction() as connection:
            await self.db.execute(
                executable2, fetch_returns="none", connection=connection
            )
            deleted_lesson = await self.db.execute(
                executable1, fetch_returns="one", connection=connection
            )

            return self._to_domain(deleted_lesson)

    async def delete(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Lesson]:

        cmd = self._normalize(cmd, LessonDelete)
        return await self._delete_lesson(cmd, connection=connection)

    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Lesson]:
        query = self._normalize(query, LessonGet)
        return await super().get(query, connection=connection)

    async def get_with_media(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[LessonWithMedia]:

        query = self._normalize(query, LessonGet)

        sql = (
            PostgreSQLQuery.from_(lesson_table)
            .join(media_asset_table)
            .on(
                Criterion.all(
                    terms=[
                        lesson_table.id == media_asset_table.mediable_id,
                        media_asset_table.status == Parameter("$1"),
                        media_asset_table.mediable_type == Parameter("$2"),
                    ]
                )
            )
            .where(
                Criterion.all(
                    terms=[
                        lesson_table.deleted_at.isnull(),
                        media_asset_table.deleted_at.isnull(),
                        lesson_table.id == Parameter("$3"),
                    ]
                )
            )
            .select(
                lesson_table.id,
                lesson_table.title,
                lesson_table.description,
                media_asset_table.id.as_("media_id"),
                media_asset_table.mime_type,
            )
        ).get_sql()

        executable = ExecutableSQL(
            sql=sql, values=(MediaStatus.UPLOADED, MediableType.LESSON, query.id)
        )

        lesson = await self.db.execute(executable, fetch_returns="one")

        if lesson is not None:
            return LessonWithMedia.model_validate(dict(lesson))

        return lesson
