from src.auth import Action, AuthService, Entity, require_authorization
from src.cache import CacheKey, CacheService, CacheTag
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
    LessonDetail,
    ModuleDetail,
    TraineeDetail,
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
        cache_service: CacheService,
    ) -> None:

        self.entity_list_query_repo = entity_list_query_repo
        self.auth_service = auth_service
        self.cache_service = cache_service

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.MODULE,
        user_id_field="viewer_id",
        parent_id_field="course_id",
        object_name="query",
    )
    async def list_modules(self, query: CourseViewRequestSchema) -> list[ModuleDetail]:

        return await self.cache_service.get_or_set(
            key=CacheKey.LIST_MODULES.format(course_id=query.course_id),
            model=list[ModuleDetail],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.entity_list_query_repo.modules(
                course_id=query.course_id
            ),
            tags={CacheTag.LIST_MODULES.format(course_id=query.course_id)},
        )

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.LESSON,
        user_id_field="viewer_id",
        parent_id_field="module_id",
        object_name="query",
    )
    async def list_lessons(self, query: ModuleViewRequestSchema) -> list[LessonDetail]:

        return await self.cache_service.get_or_set(
            key=CacheKey.LIST_LESSONS.format(module_id=query.module_id),
            model=list[LessonDetail],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.entity_list_query_repo.lessons(
                module_id=query.module_id
            ),
            tags={CacheTag.LIST_LESSONS.format(module_id=query.module_id)},
        )

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
    ) -> Paginated[TraineeDetail]:

        key = CacheKey.LIST_TRAINEES.format(
            course_id=query.course_id,
            name=filters.name,
            role=filters.role,
            sort_by_enrollment_date=filters.sort_by_enrollment_date,
            sort_by_username=filters.sort_by_username,
            page=page_meta.page,
            limit=page_meta.limit,
        )

        return await self.cache_service.get_or_set(
            key=key,
            model=Paginated[TraineeDetail],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.entity_list_query_repo.trainees(
                course_id=query.course_id, filters=filters, page_meta=page_meta
            ),
            tags={CacheTag.LIST_TRAINEES.format(course_id=query.course_id)},
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
    def __init__(
        self,
        entity_list_query_repo: EntityListQueryRepository,
        cache_service: CacheService,
    ) -> None:

        self.entity_list_query_repo = entity_list_query_repo
        self.cache_service = cache_service

    async def list_users(
        self, filters: UserFilters, page_meta: PageMeta
    ) -> Paginated[UserDetail]:

        key = CacheKey.LIST_USERS.format(
            name_or_email=filters.name_or_email,
            role=filters.role,
            sort_by_created_at=filters.sort_by_created_at,
            sort_by_username=filters.sort_by_username,
            page=page_meta.page,
            limit=page_meta.limit,
        )

        return await self.cache_service.get_or_set(
            key=key,
            model=Paginated[UserDetail],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.entity_list_query_repo.users(
                filters=filters, page_meta=page_meta
            ),
            tags={CacheTag.LIST_USERS},
        )

    async def list_courses(
        self, filters: CourseFilters, page_meta: PageMeta
    ) -> Paginated[CourseDetail]:

        key = CacheKey.LIST_COURSES.format(
            course_name_or_trainer_name=filters.course_name_or_trainer_name,
            sort_by_course_name=filters.sort_by_course_name,
            sort_by_created_at=filters.sort_by_created_at,
            sort_by_no_of_trainees=filters.sort_by_no_of_trainees,
            page=page_meta.page,
            limit=page_meta.limit,
        )

        return await self.cache_service.get_or_set(
            key=key,
            model=Paginated[CourseDetail],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.entity_list_query_repo.courses(
                filters=filters, page_meta=page_meta
            ),
            tags={CacheTag.LIST_COURSES},
        )

    async def list_enrollments(
        self, filters: EnrollmentFilters, page_meta: PageMeta
    ) -> Paginated[EnrollmentDetail]:

        key = CacheKey.LIST_ENROLLMENTS.format(
            name_or_email=filters.name_or_email,
            status=filters.status,
            role=filters.role,
            sort_by_enrollment_date=filters.sort_by_enrollment_date,
            sort_by_course_name=filters.sort_by_course_name,
            page=page_meta.page,
            limit=page_meta.limit,
        )

        return await self.cache_service.get_or_set(
            key=key,
            model=Paginated[EnrollmentDetail],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.entity_list_query_repo.enrollments(
                filters=filters, page_meta=page_meta
            ),
            tags={CacheTag.LIST_ENROLLMENTS},
        )

    async def list_trainees(
        self, course_id: int, filters: TraineeFilters, page_meta: PageMeta
    ) -> Paginated[TraineeDetail]:

        key = CacheKey.LIST_TRAINEES.format(
            course_id=course_id,
            name=filters.name,
            role=filters.role,
            sort_by_enrollment_date=filters.sort_by_enrollment_date,
            sort_by_username=filters.sort_by_username,
            page=page_meta.page,
            limit=page_meta.limit,
        )

        return await self.cache_service.get_or_set(
            key=key,
            model=Paginated[TraineeDetail],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.entity_list_query_repo.trainees(
                course_id=course_id, filters=filters, page_meta=page_meta
            ),
            tags={CacheTag.LIST_TRAINEES.format(course_id=course_id)},
        )

    async def search_users(
        self, username_or_email: str, role: tuple[UserRole, ...] = ()
    ) -> list[UserSearchDetail]:

        return await self.cache_service.get_or_set(
            key=CacheKey.SEARCH_USERS.format(
                username_or_email=username_or_email, role=role
            ),
            model=list[UserSearchDetail],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.entity_list_query_repo.search_users(
                username_or_email=username_or_email, role=role
            ),
            tags={CacheTag.SEARCH_USERS},
        )

    async def search_course(self, course_name: str) -> list[CourseSearchDetail]:

        return await self.cache_service.get_or_set(
            key=CacheKey.SEARCH_COURSES.format(course_name=course_name),
            model=list[CourseSearchDetail],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.entity_list_query_repo.search_courses(
                course_name=course_name
            ),
            tags={CacheTag.SEARCH_COURSES},
        )
