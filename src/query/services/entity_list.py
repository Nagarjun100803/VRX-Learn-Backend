from typing_extensions import AsyncGenerator

from src.command.commands.users import UserRole
from src.query.dto.base import PageMeta, Paginated
from src.query.dto.entity_list import (
    AssignmentDetail,
    AssignmentDetailWithDue,
    CourseDetail,
    CourseFilters,
    CourseSearchDetail,
    EnrollmentDetail,
    EnrollmentFilters,
    IssueDetail,
    IssueFilters,
    LessonDetail,
    ModuleDetail,
    TraineeFilters,
    UserDetail,
    UserFilters,
    UserSearchDetail,
)
from src.query.dto.request_schemas import (
    CourseViewRequestSchema,
    ModuleViewRequestSchema,
)
from src.query.repositories.entity_list import EntityListQueryRepository


# NOTE: This class is not used in API Layer, It has only one method which is
# list_assignments that returns the list of assignment to trainee view.
# But this is functionality also defined in `TraineeAssignmentContentQueryService`.
class TraineeEntityListQueryService:
    def __init__(self, entity_list_query_repo: EntityListQueryRepository) -> None:

        self.entity_list_query_repo = entity_list_query_repo

    async def list_assignments(
        self, query: CourseViewRequestSchema
    ) -> list[AssignmentDetail]:
        assignments: list[
            AssignmentDetailWithDue
        ] = await self.entity_list_query_repo.assignments(course_id=query.course_id)
        return [
            AssignmentDetail(id=assignment.id, title=assignment.title)
            for assignment in assignments
        ]


class TrainerEntityListQueryService:
    def __init__(self, entity_list_query_repo: EntityListQueryRepository) -> None:

        self.entity_list_query_repo = entity_list_query_repo

    async def list_modules(self, query: CourseViewRequestSchema) -> list[ModuleDetail]:
        return await self.entity_list_query_repo.modules(course_id=query.course_id)

    async def list_lessons(self, query: ModuleViewRequestSchema) -> list[LessonDetail]:
        return await self.entity_list_query_repo.lessons(module_id=query.module_id)

    async def list_trainees(
        self,
        query: CourseViewRequestSchema,
        filters: TraineeFilters,
        page_meta: PageMeta,
    ):
        return await self.entity_list_query_repo.trainees(
            course_id=query.course_id, filters=filters, page_meta=page_meta
        )

    # NOTE: This method is not used in API Layer.
    # list_assignments() for Trainer View also defined in
    # TrainerAssignmentContentQueryService. Will be removed later.
    async def list_assignments(
        self, query: CourseViewRequestSchema
    ) -> list[AssignmentDetailWithDue]:
        return await self.entity_list_query_repo.assignments(course_id=query.course_id)


class AdminEntityListQueryService:
    def __init__(self, entity_list_query_repo: EntityListQueryRepository) -> None:
        self.entity_list_query_repo = entity_list_query_repo

    async def list_users(
        self, filters: UserFilters, page_meta: PageMeta
    ) -> Paginated[UserDetail]:

        return await self.entity_list_query_repo.users(
            filters=filters, page_meta=page_meta
        )

    def export_users(self, filters: UserFilters) -> AsyncGenerator[bytes, None]:
        return self.entity_list_query_repo.export_users(filters=filters)

    async def list_courses(
        self, filters: CourseFilters, page_meta: PageMeta
    ) -> Paginated[CourseDetail]:

        return await self.entity_list_query_repo.courses(
            filters=filters, page_meta=page_meta
        )

    def export_courses(self, filters: CourseFilters) -> AsyncGenerator[bytes, None]:
        return self.entity_list_query_repo.export_courses(filters=filters)

    async def list_enrollments(
        self, filters: EnrollmentFilters, page_meta: PageMeta
    ) -> Paginated[EnrollmentDetail]:

        return await self.entity_list_query_repo.enrollments(
            filters=filters, page_meta=page_meta
        )

    def export_enrollments(
        self, filters: EnrollmentFilters
    ) -> AsyncGenerator[bytes, None]:
        return self.entity_list_query_repo.export_enrollments(filters=filters)

    async def list_trainees(
        self, course_id: int, filters: TraineeFilters, page_meta: PageMeta
    ):

        return await self.entity_list_query_repo.trainees(
            course_id=course_id, filters=filters, page_meta=page_meta
        )

    def export_trainees(
        self, course_id: int, filters: TraineeFilters
    ) -> AsyncGenerator[bytes, None]:
        return self.entity_list_query_repo.export_trainees(
            course_id=course_id, filters=filters
        )

    async def search_users(
        self, username_or_email: str, role: tuple[UserRole, ...] = ()
    ) -> list[UserSearchDetail]:

        return await self.entity_list_query_repo.search_users(
            username_or_email=username_or_email, role=role
        )

    async def search_course(self, course_name: str) -> list[CourseSearchDetail]:

        return await self.entity_list_query_repo.search_courses(course_name=course_name)

    async def list_issues(
        self, filters: IssueFilters, page_meta: PageMeta
    ) -> Paginated[IssueDetail]:
        return await self.entity_list_query_repo.issues(
            filters=filters, page_meta=page_meta
        )
