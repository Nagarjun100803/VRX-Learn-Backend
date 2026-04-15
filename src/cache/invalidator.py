import asyncio
from enum import StrEnum
from typing import Union

from pypika import Parameter
from pypika.dialects import PostgreSQLQuery
from pypika.terms import Criterion

from src.cache import CacheService, CacheTag
from src.database import AsyncPgDBManager, ExecutableSQL
from src.events.events import (
    AssignmentCreatedEvent,
    AssignmentDeletedEvent,
    AssignmentSubmissionCreatedEvent,
    AssignmentUpdatedEvent,
    CourseCreatedEvent,
    CourseDeletedEvent,
    CourseUpdatedEvent,
    EnrollmentCreatedEvent,
    EnrollmentDeletedEvent,
    EnrollmentUpdatedEvent,
    LessonCreatedEvent,
    LessonDeletedEvent,
    LessonReorderedEvent,
    LessonUpdatedEvent,
    ModuleCreatedEvent,
    ModuleDeletedEvent,
    ModuleReorderedEvent,
    ModuleUpdatedEvent,
    UserCreatedEvent,
    UserDeletedEvent,
)
from src.pypika_query_builder import (
    assignment_table,
    course_table,
    lesson_table,
    module_table,
)


class _TagResolver:
    """
    Helper class used to fetch db to get some piece of data
    to format a `CacheTag` to invalidate.
    Don't use it directly.
    """

    def __init__(self, db: AsyncPgDBManager) -> None:
        self.db = db

    async def get_module_ids_by_course_id(self, course_id: int) -> list[int]:
        sql = (
            PostgreSQLQuery.from_(module_table)
            .where(
                Criterion.all(
                    terms=[
                        module_table.course_id == Parameter("$1"),
                        module_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(module_table.id)
        ).get_sql()

        executable = ExecutableSQL(sql=sql, values=(course_id,))

        module_ids = await self.db.execute(executable, fetch_returns="all")

        return [module_id["id"] for module_id in module_ids]

    async def get_assignment_ids_by_course_id(self, course_id: int) -> list[int]:
        sql = (
            PostgreSQLQuery.from_(assignment_table)
            .where(
                Criterion.all(
                    terms=[
                        assignment_table.course_id == Parameter("$1"),
                        assignment_table.deleted_at.isnull(),
                    ]
                )
            )
            .select(assignment_table.id)
        ).get_sql()

        executable = ExecutableSQL(sql=sql, values=(course_id,))

        assignment_ids = await self.db.execute(executable, fetch_returns="all")

        return [assignment_id["id"] for assignment_id in assignment_ids]

    async def get_trainer_id_course_id(self, course_id: int) -> int:
        sql = (
            PostgreSQLQuery.from_(course_table)
            .where(course_table.id == Parameter("$1"))
            .select(course_table.trainer_id)
        ).get_sql()

        executable = ExecutableSQL(sql=sql, values=(course_id,))

        result = await self.db.execute(executable, fetch_returns="one")

        return result["trainer_id"] if result is not None else 0

    async def get_course_id_by_module_id(self, module_id: int) -> int:

        sql = (
            PostgreSQLQuery.from_(module_table)
            .join(course_table)
            .on(course_table.id == module_table.course_id)
            .where(module_table.id == Parameter("$1"))
            .select(module_table.course_id)
        ).get_sql()

        executable = ExecutableSQL(sql=sql, values=(module_id,))

        result = await self.db.execute(executable, fetch_returns="one")

        return result["course_id"] if result is not None else 0

    async def get_module_id_and_course_id_by_lesson_id(
        self, lesson_id: int
    ) -> tuple[int, int]:
        sql = (
            PostgreSQLQuery.from_(lesson_table)
            .join(module_table)
            .on(module_table.id == lesson_table.module_id)
            .where(lesson_table.id == Parameter("$1"))
            .select(module_table.id, module_table.course_id)
        ).get_sql()

        executable = ExecutableSQL(sql=sql, values=(lesson_id,))

        result = await self.db.execute(executable, fetch_returns="one")

        return (result["id"], result["course_id"]) if result is not None else (0, 0)


class CacheInvalidator:
    def __init__(self, cache_service: CacheService, resolver: _TagResolver) -> None:
        self.cache_service = cache_service
        self.resolver = resolver

    async def on_user_created(self, event: UserCreatedEvent):
        tags = [CacheTag.LIST_USERS, CacheTag.ADMIN_KPIS, CacheTag.SEARCH_USERS]
        await self.cache_service.invalidate_tags(tags)

    async def on_user_deleted(self, event: UserDeletedEvent):
        tags = [CacheTag.LIST_USERS, CacheTag.ADMIN_KPIS, CacheTag.SEARCH_USERS]
        await self.cache_service.invalidate_tags(tags)

    async def on_course_created(self, event: CourseCreatedEvent):
        tags = [
            CacheTag.LIST_COURSES,
            CacheTag.ADMIN_KPIS,
            CacheTag.SEARCH_COURSES,
            CacheTag.TRAINEE_TOP_NEW_COURSES,
        ]
        await self.cache_service.invalidate_tags(tags)

    async def on_course_updated(self, event: CourseUpdatedEvent):
        tags = [
            CacheTag.LIST_COURSES,
            CacheTag.SEARCH_COURSES,
            CacheTag.TRAINER_ASSIGNED_COURSES.format(trainer_id=event.trainer_id),
            CacheTag.TRAINEE_COURSE_OVERVIEW.format(course_id=event.id),
            CacheTag.TRAINER_COURSE_OVERVIEW.format(course_id=event.id),
            CacheTag.TRAINEE_COURSE_CONTENTS.format(course_id=event.id),
            CacheTag.TRAINER_COURSE_CONTENTS.format(course_id=event.id),
        ]

        await self.cache_service.invalidate_tags(tags)

    async def on_course_deleted(self, event: CourseDeletedEvent):

        module_ids, assignment_ids = await asyncio.gather(
            self.resolver.get_module_ids_by_course_id(event.id),
            self.resolver.get_assignment_ids_by_course_id(event.id),
        )

        tags: list[Union[str, StrEnum]] = [
            CacheTag.LIST_COURSES,
            CacheTag.ADMIN_KPIS,
            CacheTag.SEARCH_COURSES,
            CacheTag.TRAINER_ASSIGNED_COURSES.format(trainer_id=event.trainer_id),
            CacheTag.TRAINEE_COURSE_OVERVIEW.format(course_id=event.id),
            CacheTag.TRAINER_COURSE_OVERVIEW.format(course_id=event.id),
            CacheTag.TRAINEE_COURSE_CONTENTS.format(course_id=event.id),
            CacheTag.TRAINER_COURSE_CONTENTS.format(course_id=event.id),
            CacheTag.LIST_MODULES.format(course_id=event.id),
            CacheTag.TRAINER_LIST_ASSIGNMENTS.format(course_id=event.id),
            CacheTag.LIST_TRAINEES.format(course_id=event.id),
            *[
                CacheTag.LIST_LESSONS.format(module_id=module_id)
                for module_id in module_ids
            ],
            *[
                CacheTag.LIST_ASSIGNMENT_SUBMISSIONS.format(assignment_id=assignment_id)
                for assignment_id in assignment_ids
            ],
        ]

        await self.cache_service.invalidate_tags(tags)

    async def on_enrollment_created(self, event: EnrollmentCreatedEvent):
        trainer_id = await self.resolver.get_trainer_id_course_id(event.course_id)
        tags = [
            CacheTag.ADMIN_KPIS,
            CacheTag.ADMIN_TOP_ENROLLED_COURSES.format(course_id=event.course_id),
            CacheTag.TRAINEE_ENROLLED_COURSES.format(trainee_id=event.user_id),
            CacheTag.TRAINEE_CURRENT_COURSE.format(trainee_id=event.user_id),
            CacheTag.TRAINER_COURSE_OVERVIEW.format(course_id=event.course_id),
            CacheTag.LIST_TRAINEES.format(course_id=event.course_id),
            CacheTag.LIST_ENROLLMENTS,
            CacheTag.TRAINER_KPIS.format(trainer_id=trainer_id),
        ]

        await self.cache_service.invalidate_tags(tags)

    async def on_enrollment_updated(self, event: EnrollmentUpdatedEvent): ...

    async def on_enrollment_deleted(self, event: EnrollmentDeletedEvent):
        trainer_id = await self.resolver.get_trainer_id_course_id(event.course_id)
        tags = [
            CacheTag.ADMIN_KPIS,
            CacheTag.ADMIN_TOP_ENROLLED_COURSES.format(course_id=event.course_id),
            CacheTag.TRAINEE_ENROLLED_COURSES.format(trainee_id=event.user_id),
            CacheTag.TRAINEE_CURRENT_COURSE.format(trainee_id=event.user_id),
            CacheTag.TRAINER_KPIS.format(trainer_id=trainer_id),
            CacheTag.TRAINER_COURSE_OVERVIEW.format(course_id=event.course_id),
            CacheTag.LIST_TRAINEES.format(course_id=event.course_id),
            CacheTag.LIST_ENROLLMENTS,
        ]

        await self.cache_service.invalidate_tags(tags)

    async def on_module_created(self, event: ModuleCreatedEvent):
        tags = [
            CacheTag.LIST_MODULES.format(course_id=event.course_id),
            CacheTag.TRAINEE_COURSE_OVERVIEW.format(course_id=event.course_id),
            CacheTag.TRAINER_COURSE_OVERVIEW.format(course_id=event.course_id),
            CacheTag.TRAINEE_COURSE_CONTENTS.format(course_id=event.course_id),
            CacheTag.TRAINER_COURSE_CONTENTS.format(course_id=event.course_id),
        ]

        await self.cache_service.invalidate_tags(tags)

    async def on_module_updated(self, event: ModuleUpdatedEvent):
        tags = [
            CacheTag.LIST_MODULES.format(course_id=event.course_id),
            CacheTag.TRAINEE_COURSE_CONTENTS.format(course_id=event.course_id),
            CacheTag.TRAINER_COURSE_CONTENTS.format(course_id=event.course_id),
        ]
        await self.cache_service.invalidate_tags(tags)

    async def on_module_reordered(self, event: ModuleReorderedEvent):
        course_id = await self.resolver.get_course_id_by_module_id(event.id)
        tags = [
            CacheTag.LIST_MODULES.format(course_id=course_id),
            CacheTag.TRAINEE_COURSE_CONTENTS.format(course_id=course_id),
            CacheTag.TRAINER_COURSE_CONTENTS.format(course_id=course_id),
        ]
        await self.cache_service.invalidate_tags(tags)

    async def on_module_deleted(self, event: ModuleDeletedEvent):
        tags = [
            CacheTag.LIST_MODULES.format(course_id=event.course_id),
            CacheTag.TRAINEE_COURSE_OVERVIEW.format(course_id=event.course_id),
            CacheTag.TRAINER_COURSE_OVERVIEW.format(course_id=event.course_id),
            CacheTag.TRAINEE_COURSE_CONTENTS.format(course_id=event.course_id),
            CacheTag.TRAINER_COURSE_CONTENTS.format(course_id=event.course_id),
        ]
        await self.cache_service.invalidate_tags(tags)

    async def on_lesson_created(self, event: LessonCreatedEvent):
        course_id = await self.resolver.get_course_id_by_module_id(event.module_id)

        tags = [
            CacheTag.LIST_LESSONS.format(module_id=event.module_id),
            CacheTag.TRAINEE_COURSE_OVERVIEW.format(course_id=course_id),
            CacheTag.TRAINER_COURSE_OVERVIEW.format(course_id=course_id),
            CacheTag.TRAINEE_COURSE_CONTENTS.format(course_id=course_id),
        ]

        await self.cache_service.invalidate_tags(tags)

    async def on_lesson_updated(self, event: LessonUpdatedEvent):
        course_id = await self.resolver.get_course_id_by_module_id(event.module_id)

        tags = [
            CacheTag.LIST_LESSONS.format(module_id=event.module_id),
            CacheTag.TRAINEE_COURSE_CONTENTS.format(course_id=course_id),
        ]

        await self.cache_service.invalidate_tags(tags)

    async def on_lesson_reordered(self, event: LessonReorderedEvent):
        (
            module_id,
            course_id,
        ) = await self.resolver.get_module_id_and_course_id_by_lesson_id(event.id)
        tags = [
            CacheTag.LIST_LESSONS.format(module_id=module_id),
            CacheTag.TRAINEE_COURSE_CONTENTS.format(course_id=course_id),
        ]
        await self.cache_service.invalidate_tags(tags)

    async def on_lesson_deleted(self, event: LessonDeletedEvent):
        course_id = await self.resolver.get_course_id_by_module_id(event.module_id)

        tags = [
            CacheTag.LIST_LESSONS.format(module_id=event.module_id),
            CacheTag.TRAINEE_COURSE_OVERVIEW.format(course_id=course_id),
            CacheTag.TRAINER_COURSE_OVERVIEW.format(course_id=course_id),
            CacheTag.TRAINEE_COURSE_CONTENTS.format(course_id=course_id),
        ]

        await self.cache_service.invalidate_tags(tags)

    async def on_assignment_created(self, event: AssignmentCreatedEvent):
        tags = [
            CacheTag.TRAINER_LIST_ASSIGNMENTS.format(course_id=event.course_id),
            CacheTag.TRAINEE_COURSE_OVERVIEW.format(course_id=event.course_id),
            CacheTag.TRAINER_COURSE_OVERVIEW.format(course_id=event.course_id),
            CacheTag.TRAINER_COURSE_CONTENTS.format(course_id=event.course_id),
        ]

        await self.cache_service.invalidate_tags(tags)

    async def on_assignment_updated(self, event: AssignmentUpdatedEvent):
        tags = [
            CacheTag.TRAINER_LIST_ASSIGNMENTS.format(course_id=event.course_id),
            CacheTag.TRAINER_COURSE_CONTENTS.format(course_id=event.course_id),
        ]

        await self.cache_service.invalidate_tags(tags)

    async def on_assignment_deleted(self, event: AssignmentDeletedEvent):
        tags = [
            CacheTag.TRAINER_LIST_ASSIGNMENTS.format(course_id=event.course_id),
            CacheTag.TRAINEE_COURSE_OVERVIEW.format(course_id=event.course_id),
            CacheTag.TRAINER_COURSE_OVERVIEW.format(course_id=event.course_id),
            CacheTag.TRAINER_COURSE_CONTENTS.format(course_id=event.course_id),
            CacheTag.LIST_ASSIGNMENT_SUBMISSIONS.format(assignment_id=event.id),
        ]

        await self.cache_service.invalidate_tags(tags)

    async def on_assignment_submission_created(
        self, event: AssignmentSubmissionCreatedEvent
    ):

        tags = [CacheTag.LIST_ASSIGNMENT_SUBMISSIONS.format(assignment_id=event.id)]

        await self.cache_service.invalidate_tags(tags)
