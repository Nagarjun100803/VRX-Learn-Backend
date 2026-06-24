from typing import Any, ClassVar, Optional, cast, override

from asyncpg import Connection, Record
from pydantic import BaseModel
from pypika import Criterion, Parameter, Table, functions
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
from src.command.commands.media import MediableType
from src.command.repositories.base import BaseRepository
from src.database import ExecutableSQL
from src.query_builder import (
    assignment_submission_table,
    assignment_table,
    course_table,
    enrollment_table,
    lesson_table,
    media_asset_table,
    module_table,
)


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

    async def _delete_enrollments(
        self, cmd: CourseDelete, connection: Optional[Connection] = None
    ) -> None:
        sql = (
            PostgreSQLQuery.update(enrollment_table)
            .set(enrollment_table.deleted_at, functions.Now())
            .set(enrollment_table.deleted_by, Parameter("$2"))
            .where(enrollment_table.course_id == Parameter("$1"))
        ).get_sql()

        executable = ExecutableSQL(sql, values=(cmd.id, cmd.deleted_by))

        await self.db.execute(executable, fetch_returns="none", connection=connection)

    async def _delete_modules(
        self, cmd: CourseDelete, connection: Optional[Connection] = None
    ) -> None:

        sql = (
            PostgreSQLQuery.update(module_table)
            .set(module_table.deleted_at, functions.Now())
            .set(module_table.deleted_by, Parameter("$2"))
            .where(module_table.course_id == Parameter("$1"))
        ).get_sql()

        executable = ExecutableSQL(sql, values=(cmd.id, cmd.deleted_by))

        await self.db.execute(executable, fetch_returns="none", connection=connection)

    async def _delete_lessons(
        self, cmd: CourseDelete, connection: Optional[Connection] = None
    ) -> None:

        module_ids_subquery = (
            PostgreSQLQuery.from_(module_table)
            .select(module_table.id)
            .where(module_table.course_id == Parameter("$1"))
        )

        lesson_ids_subquery = (
            PostgreSQLQuery.from_(lesson_table)
            .where(lesson_table.module_id.isin(module_ids_subquery))
            .select(lesson_table.id)
        )

        lesson_delete_sql = (
            PostgreSQLQuery.update(lesson_table)
            .set(lesson_table.deleted_at, functions.Now())
            .set(lesson_table.deleted_by, Parameter("$2"))
            .where(lesson_table.module_id.isin(module_ids_subquery))
        )

        lesson_media_delete_sql = (
            PostgreSQLQuery.update(media_asset_table)
            .set(media_asset_table.deleted_at, functions.Now())
            .set(media_asset_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_type == Parameter("$3"),
                        media_asset_table.mediable_id.isin(lesson_ids_subquery),
                    ]
                )
            )
        ).get_sql()

        executable1 = ExecutableSQL(
            lesson_delete_sql.get_sql(), values=(cmd.id, cmd.deleted_by)
        )
        executable2 = ExecutableSQL(
            lesson_media_delete_sql,
            values=(cmd.id, cmd.deleted_by, MediableType.LESSON),
        )

        await self.db.execute(executable1, fetch_returns="none", connection=connection)
        await self.db.execute(executable2, fetch_returns="none", connection=connection)

    async def _delete_assignments(
        self, cmd: CourseDelete, connection: Optional[Connection] = None
    ) -> None:

        assignment_ids_subquery = (
            PostgreSQLQuery.from_(assignment_table)
            .where(assignment_table.course_id == Parameter("$1"))
            .select(assignment_table.id)
        )

        assignment_delete_sql = (
            PostgreSQLQuery.update(assignment_table)
            .set(assignment_table.deleted_at, functions.Now())
            .set(assignment_table.deleted_by, Parameter("$2"))
            .where(assignment_table.course_id == Parameter("$1"))
        ).get_sql()

        assignment_media_delete_sql = (
            PostgreSQLQuery.update(media_asset_table)
            .set(media_asset_table.deleted_at, functions.Now())
            .set(media_asset_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_type == Parameter("$3"),
                        media_asset_table.mediable_id.isin(assignment_ids_subquery),
                    ]
                )
            )
        ).get_sql()

        executable1 = ExecutableSQL(
            assignment_delete_sql, values=(cmd.id, cmd.deleted_by)
        )
        executable2 = ExecutableSQL(
            assignment_media_delete_sql,
            values=(cmd.id, cmd.deleted_by, MediableType.ASSIGNMENT),
        )

        await self.db.execute(executable1, fetch_returns="none", connection=connection)
        await self.db.execute(executable2, fetch_returns="none", connection=connection)

    async def _delete_assignment_submissions(
        self, cmd: CourseDelete, connection: Optional[Connection] = None
    ) -> None:

        assignment_ids_subquery = (
            PostgreSQLQuery.from_(assignment_table)
            .select(assignment_table.id)
            .where(assignment_table.course_id == Parameter("$1"))
        )

        assignment_submission_ids_subquery = (
            PostgreSQLQuery.from_(assignment_submission_table)
            .where(
                assignment_submission_table.assignment_id.isin(assignment_ids_subquery)
            )
            .select(assignment_submission_table.id)
        )

        assignment_submission_delete_sql = (
            PostgreSQLQuery.update(assignment_submission_table)
            .set(assignment_submission_table.deleted_at, functions.Now())
            .set(assignment_submission_table.deleted_by, Parameter("$2"))
            .where(
                assignment_submission_table.assignment_id.isin(assignment_ids_subquery)
            )
            .get_sql()
        )

        assignment_submission_media_delete_sql = (
            PostgreSQLQuery.update(media_asset_table)
            .set(media_asset_table.deleted_at, functions.Now())
            .set(media_asset_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_id.isin(
                            assignment_submission_ids_subquery
                        ),
                        media_asset_table.mediable_type == Parameter("$3"),
                    ]
                )
            )
        ).get_sql()

        executable1 = ExecutableSQL(
            sql=assignment_submission_delete_sql, values=(cmd.id, cmd.deleted_by)
        )
        executable2 = ExecutableSQL(
            sql=assignment_submission_media_delete_sql,
            values=(cmd.id, cmd.deleted_by, MediableType.ASSIGNMENT_SUBMISSION),
        )

        await self.db.execute(executable1, fetch_returns="none", connection=connection)
        await self.db.execute(executable2, fetch_returns="none", connection=connection)

    async def _delete_course(
        self, cmd: CourseDelete, connection: Optional[Connection] = None
    ) -> Optional[Course]:

        update_query = (
            PostgreSQLQuery.update(course_table)
            .set(course_table.deleted_at, functions.Now())
            .set(course_table.deleted_by, Parameter("$2"))
            .where(
                Criterion.all(
                    terms=[
                        course_table.id == Parameter("$1"),
                        course_table.deleted_at.isnull(),
                    ]
                )
            )
        )

        update_query: Any = update_query.returning("*")  # type: ignore

        sql: str = update_query.get_sql()

        executable = ExecutableSQL(sql, values=(cmd.id, cmd.deleted_by))

        result = await self.db.execute(
            executable, fetch_returns="one", connection=connection
        )

        return self._to_domain(result)

    @override
    async def delete(
        self, cmd: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Course]:

        cmd = self._normalize(cmd, CourseDelete)

        async with self.db.transaction() as connection:
            await self._delete_enrollments(cmd, connection=connection)
            await self._delete_assignment_submissions(cmd, connection=connection)
            await self._delete_assignments(cmd, connection=connection)
            await self._delete_lessons(cmd, connection=connection)
            await self._delete_modules(cmd, connection=connection)

            deleted_course = await self._delete_course(cmd, connection=connection)

            return deleted_course

    async def get(
        self, query: BaseModel, connection: Optional[Connection] = None
    ) -> Optional[Course]:
        query = self._normalize(query, CourseGet)
        return await super().get(query, connection=connection)
