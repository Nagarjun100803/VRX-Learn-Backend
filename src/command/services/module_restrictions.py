from typing import Optional

from asyncpg import Connection
from pypika import Parameter, PostgreSQLQuery, Table
from pypika.terms import Criterion, ValueWrapper

from src.command.commands.module_restrictions import (
    ModuleRestrictionCreate,
    ModuleRestrictionDelete,
    ModuleRestrictionSync,
)
from src.command.repositories import (
    EnrollmentRepository,
    ModuleRepository,
    ModuleRestrictionRepository,
)
from src.database import ExecutableSQL
from src.exceptions import (
    CourseModuleNotFoundError,
    EnrollmentNotFoundError,
    ModuleAccessRestrictedError,
)


class ModuleAccessResolver:
    def __init__(
        self, repo: ModuleRestrictionRepository, enrollment_repo: EnrollmentRepository
    ) -> None:
        self.repo = repo
        self.enrollment_repo = enrollment_repo

    async def is_restricted(self, user_id: int, module_id: int) -> bool:

        # Tables
        table = Table(self.repo.tablename)
        enrollment_table = Table(self.enrollment_repo.tablename)

        enrollment_ids_query = (
            PostgreSQLQuery.from_(enrollment_table)
            .where(
                Criterion.all(
                    terms=[
                        enrollment_table.user_id == Parameter("$1"),
                        enrollment_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(enrollment_table.id)
        )

        sql = (
            PostgreSQLQuery.from_(table)
            .where(
                Criterion.all(
                    terms=[
                        table.module_id == Parameter("$2"),
                        table.enrollment_id.isin(enrollment_ids_query),
                    ]
                )
            )
            .select(ValueWrapper(1))
            .limit(1)
            .get_sql()
        )
        # Add limit due to module_id and enrollment_id is a unique pair.
        # We get same result regardless of the limit.
        # But we use limit to avoid fetching all rows and for our understanding.

        executable = ExecutableSQL(sql=sql, values=(user_id, module_id))

        result = await self.repo.db.execute(executable, fetch_returns="one")

        return result is not None


class ModuleAccessService:
    def __init__(
        self,
        repo: ModuleRestrictionRepository,
        module_repo: ModuleRepository,
        enrollment_repo: EnrollmentRepository,
        module_access_resolver: ModuleAccessResolver,
    ) -> None:
        self.repo = repo
        self.module_repo = module_repo
        self.enrollment_repo = enrollment_repo
        self.module_access_resolver = module_access_resolver

    async def validate_access(self, user_id: int, module_id: int) -> None:
        if await self.module_access_resolver.is_restricted(
            user_id=user_id, module_id=module_id
        ):
            raise ModuleAccessRestrictedError()

    async def _validate_module_ids(self, module_ids: set[int], course_id: int) -> None:
        modules = await self.module_repo.pick(
            columns=["id", "course_id"], course_id=course_id, fetch_all=True
        )
        existed_module_ids: set[int] = {module["id"] for module in modules}

        if set(module_ids) - existed_module_ids:
            raise CourseModuleNotFoundError(
                message=f"Module(s) {set(module_ids) - existed_module_ids} not found in course {course_id}."
            )

    async def _validate(
        self, cmd: ModuleRestrictionSync, connection: Optional[Connection] = None
    ) -> None:
        enrollment_detail = await self.enrollment_repo.pick(
            columns=["id", "course_id"],
            fetch_all=False,
            connection=connection,
            id=cmd.enrollment_id,
        )
        if enrollment_detail is None:
            raise EnrollmentNotFoundError(value=cmd.enrollment_id)

        await self._validate_module_ids(
            module_ids=cmd.module_ids, course_id=enrollment_detail["course_id"]
        )

    async def sync_restriction(
        self, cmd: ModuleRestrictionSync, connection: Optional[Connection] = None
    ) -> None:
        # validate enrollment and module ids.
        await self._validate(cmd=cmd, connection=connection)

        # Get previous restrictions.
        restricted_module_ids = await self.repo.get_module_restrictions(
            enrollment_id=cmd.enrollment_id
        )

        module_ids_to_add = cmd.module_ids - restricted_module_ids
        module_ids_to_delete = restricted_module_ids - cmd.module_ids

        print(
            f"Module ids to add: {module_ids_to_add}, to delete: {module_ids_to_delete}"
        )

        async with self.repo.db.scoped_transaction(connection) as tconn:
            if module_ids_to_add:
                await self.repo.create(
                    cmd=ModuleRestrictionCreate(
                        enrollment_id=cmd.enrollment_id,
                        module_ids=module_ids_to_add,
                        created_by=cmd.by,
                    ),
                    connection=tconn,
                )

            if module_ids_to_delete:
                await self.repo.delete(
                    cmd=ModuleRestrictionDelete(
                        enrollment_id=cmd.enrollment_id,
                        module_ids=module_ids_to_delete,
                        deleted_by=cmd.by,
                    ),
                    connection=tconn,
                )
