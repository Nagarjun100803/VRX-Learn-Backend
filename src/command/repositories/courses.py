from typing import Any, ClassVar, Optional, cast, override

from asyncpg import Connection, Record
from pydantic import BaseModel
from pypika import Parameter, Table
from pypika.dialects import PostgreSQLQuery

from src.command.commands.courses import (
    Course,
    CourseCreate,
    CourseDelete,
    CourseGet,
    CourseInfoUpdate,
    CourseType,
    LiveCourseDetails,
    RecordedCourseDetails,
    RecordedCourseDetailsUpdate,
)
from src.command.repositories.base import BaseRepository
from src.database import ExecutableSQL


class CourseRepository(BaseRepository[Course]):
    tablename: ClassVar[str] = "courses"

    @override
    def _to_domain(self, row: Optional[Record]) -> Optional[Course]:

        if row is None:
            return None

        course = dict(row)
        print(course)

        if course["type"] == CourseType.PRE_RECORDED:
            detail_columns = ["type", "price", "total_hours"]
            details = {key: course[key] for key in detail_columns}
            details = RecordedCourseDetails.model_validate(details)
            return Course(details=details, **course)

        details = LiveCourseDetails.model_validate({"type": CourseType.LIVE})
        return Course(details=details, **course)

    async def add(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Course:

        cmd = self._normalize(cmd, CourseCreate)

        data = cmd.model_dump(exclude_none=True, exclude={"details", "trainer_id"})
        data.update(cmd.details.model_dump())
        data.update({"slug": cmd.get_slug(), "trainer_id": cmd.trainer_id})

        table = Table(self.tablename)

        insert_query = PostgreSQLQuery.into(table).columns(*data.keys())
        insert_query = insert_query.insert(
            *[Parameter(f"${idx}") for idx, _ in enumerate(data.values(), start=1)]
        )

        insert_query: Any = insert_query.returning("*")
        sql: str = insert_query.get_sql()

        executable = ExecutableSQL(sql, tuple(data.values()))
        course = cast(
            Record,
            await self.db.execute(
                executable, fetch_returns="one", connection=connection
            ),
        )

        return cast(Course, self._to_domain(course))

    async def update(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Course]:

        cmd = self._normalize_one_of(
            cmd, [CourseInfoUpdate, RecordedCourseDetailsUpdate]
        )
        return await super().update(cmd, connection=connection)

    @override
    async def delete(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Course]:

        cmd = self._normalize(cmd, CourseDelete)

        # TODO: Soft delete all the related records.
        return await super().delete(cmd, connection=connection)

    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Course]:
        query = self._normalize(query, CourseGet)
        return await super().get(query, connection=connection)
