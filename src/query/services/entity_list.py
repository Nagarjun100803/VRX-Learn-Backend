from src.auth import Action, AuthService, Entity, require_authorization
from src.query.dto.base import PageMeta, Paginated
from src.query.dto.entity_list import (
    AssignmentDetail,
    AssignmentDetailWithDue,
    CourseDetail,
    CourseFilters,
    CourseSearchDetail,
    EnrollmentDetail,
    EnrollmentFilters,
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
    def __init__(
        self,
        entity_list_query_repo: EntityListQueryRepository,
        auth_service: AuthService,
    ) -> None:

        self.entity_list_query_repo = entity_list_query_repo
        self.auth_service = auth_service

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        parent_id_field="course_id",
        object_name="query",
    )
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
    def __init__(
        self,
        entity_list_query_repo: EntityListQueryRepository,
        auth_service: AuthService,
    ) -> None:

        self.entity_list_query_repo = entity_list_query_repo
        self.auth_service = auth_service

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.MODULE,
        user_id_field="viewer_id",
        parent_id_field="course_id",
        object_name="query",
    )
    async def list_modules(self, query: CourseViewRequestSchema) -> list[ModuleDetail]:
        return await self.entity_list_query_repo.modules(course_id=query.course_id)

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.LESSON,
        user_id_field="viewer_id",
        parent_id_field="module_id",
        object_name="query",
    )
    async def list_lessons(self, query: ModuleViewRequestSchema) -> list[LessonDetail]:
        return await self.entity_list_query_repo.lessons(module_id=query.module_id)

    # NOTE: Passed `entity=Entity.COURSE even though we get all trainees in a course.
    # CourseAccessSpec will be executed to check the relationship between the user and course.
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.COURSE,
        user_id_field="viewer_id",
        entity_id_field="course_id",
        object_name="query",
    )
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
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        parent_id_field="course_id",
        object_name="query",
    )
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

    async def list_courses(
        self, filters: CourseFilters, page_meta: PageMeta
    ) -> Paginated[CourseDetail]:

        return await self.entity_list_query_repo.courses(
            filters=filters, page_meta=page_meta
        )

    async def list_enrollments(
        self, filters: EnrollmentFilters, page_meta: PageMeta
    ) -> Paginated[EnrollmentDetail]:

        return await self.entity_list_query_repo.enrollments(
            filters=filters, page_meta=page_meta
        )

    async def list_trainees(
        self, course_id: int, filters: TraineeFilters, page_meta: PageMeta
    ):

        return await self.entity_list_query_repo.trainees(
            course_id=course_id, filters=filters, page_meta=page_meta
        )

    async def search_users(self, username_or_email: str) -> list[UserSearchDetail]:

        return await self.entity_list_query_repo.search_users(
            username_or_email=username_or_email
        )

    async def search_course(self, course_name: str) -> list[CourseSearchDetail]:

        return await self.entity_list_query_repo.search_courses(course_name=course_name)
