from typing import ClassVar, Optional

from asyncpg import Connection, Record
from pydantic import BaseModel
from pypika import Case, Criterion, Parameter, PostgreSQLQuery, Table, functions
from pypika.terms import LiteralValue

from src.command.commands.enrollments import (
    Enrollment,
    EnrollmentAuditUpdate,
    EnrollmentCreate,
    EnrollmentDelete,
    EnrollmentGet,
    EnrollmentUpdate,
    EnrollmentWithRestriction,
)
from src.command.repositories.base import BaseRepository
from src.database import ExecutableSQL
from src.query_builder import (
    JsonbAgg,
    JsonbBuildObject,
    PGSqlTypes,
    course_table,
    enrollment_table,
    module_restriction_table,
    module_table,
    user_table,
)


class EnrollmentRepository(BaseRepository[Enrollment]):
    tablename: ClassVar[str] = "enrollments"

    def _to_domain(self, row: Optional[Record]) -> Optional[Enrollment]:
        if row is None:
            return None
        return Enrollment.model_validate(dict(row))

    async def add(self, cmd: BaseModel, connection: Optional[Connection] = None):
        cmd = self._normalize(cmd, EnrollmentCreate)
        return await super().add(cmd, connection)

    async def update(self, cmd: BaseModel, connection: Optional[Connection] = None):
        cmd = self._normalize(cmd, EnrollmentUpdate)
        return await super().update(cmd, connection)

    async def delete(self, cmd: BaseModel, connection: Optional[Connection] = None):
        cmd = self._normalize(cmd, EnrollmentDelete)
        return await super().delete(cmd, connection)

    async def get(self, query: BaseModel, connection: Optional[Connection] = None):
        query = self._normalize(query, EnrollmentGet)
        return await super().get(query, connection)

    async def update_audit_field(
        self, cmd: EnrollmentAuditUpdate, connection: Optional[Connection] = None
    ) -> None:
        table = Table(self.tablename)

        sql = (
            (
                PostgreSQLQuery.update(table)
                .set(table.updated_by, Parameter("$1"))
                .set(table.updated_at, functions.Now())
            )
            .where(
                Criterion.all(
                    terms=[table.id == Parameter("$2"), table.deleted_at.isnull()]
                )
            )
            .get_sql()
        )
        executable = ExecutableSQL(sql=sql, values=(cmd.updated_by, cmd.id))

        await self.db.execute(executable, fetch_returns="none", connection=connection)

    async def get_enrollment_with_module_restriction(
        self, id: int, connection: Optional[Connection] = None
    ) -> Optional[EnrollmentWithRestriction]:

        enrolled_users_table = Table("users").as_("enrolled_users")

        modules_subquery = (
            PostgreSQLQuery.from_(module_table)
            .left_join(module_restriction_table)
            .on(
                Criterion.all(
                    terms=[
                        module_restriction_table.module_id == module_table.id,
                        module_restriction_table.enrollment_id
                        == LiteralValue('"enrollments"."id"'),
                    ]
                )
            )
            .where(
                Criterion.all(
                    terms=[
                        module_table.deleted_at.isnull(),
                        module_table.course_id == course_table.id,
                    ]
                )
            )
            .select(
                functions.Coalesce(
                    JsonbAgg(
                        JsonbBuildObject(
                            "id",
                            module_table.id,
                            "title",
                            module_table.title,
                            "restricted",
                            Case()
                            .when(module_restriction_table.module_id.isnull(), False)
                            .else_(True),
                        )
                    ).orderby(module_table.position_string),
                    functions.Cast("[]", PGSqlTypes.JSONB),
                ).as_("modules")
            )
        )

        sql = (
            PostgreSQLQuery.from_(enrollment_table)
            .join(course_table)
            .on(course_table.id == enrollment_table.course_id)
            .join(enrolled_users_table)
            .on(enrolled_users_table.id == enrollment_table.user_id)
            .left_join(user_table)
            .on(user_table.id == enrollment_table.updated_by)
            .where(
                Criterion.all(
                    terms=[
                        enrollment_table.id == Parameter("$1"),
                        enrollment_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(
                enrollment_table.id,
                enrollment_table.user_id,
                enrolled_users_table.username,
                enrollment_table.course_id,
                course_table.title.as_("course_title"),
                enrollment_table.status,
                enrollment_table.expire_at,
                user_table.username.as_("updated_by"),
                enrollment_table.updated_at,
                modules_subquery,
            )
        ).get_sql()

        executable = ExecutableSQL(sql=sql, values=(id,))

        result = await self.db.execute(
            executable, fetch_returns="one", connection=connection
        )

        return (
            EnrollmentWithRestriction.model_validate(dict(result)) if result else None
        )
