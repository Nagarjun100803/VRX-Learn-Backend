from typing import Optional, cast

from src.auth import Action, AuthService, Entity, require_authorization
from src.cache import CacheKey, CacheService, CacheTag
from src.query.dto.assignment_contents import (
    AssignmentSubmissionFilters,
    TraineeAssignmentContent,
    TraineeAssignmentCore,
    TrainerAssignmentContent,
    TrainerAssignmentCore,
    TrainerSubmissionDetail,
)
from src.query.dto.base import PageMeta, Paginated
from src.query.dto.request_schemas import (
    AssignmentViewRequestSchema,
    CourseViewRequestSchema,
)
from src.query.repositories.assignment_contents import (
    TraineeAssignmentContentQueryRepository,
    TrainerAssignmentContentQueryRepository,
)
from src.query.repositories.entity_list import EntityListQueryRepository


class TraineeAssignmentContentQueryService:
    def __init__(
        self,
        trainee_assignment_query_repo: TraineeAssignmentContentQueryRepository,
        auth_service: AuthService,
        cache_service: CacheService,
    ) -> None:

        self.trainee_assignment_query_repo = trainee_assignment_query_repo
        self.auth_service = auth_service
        self.cache_service = cache_service

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        parent_id_field="course_id",
        object_name="query",
    )
    async def list_assignments(
        self, query: CourseViewRequestSchema
    ) -> list[TraineeAssignmentCore]:

        return await self.cache_service.get_or_set(
            key=CacheKey.TRAINEE_LIST_ASSIGNMENTS.format(
                course_id=query.course_id, trainee_id=query.viewer_id
            ),
            model=list[TraineeAssignmentCore],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.trainee_assignment_query_repo.assignments(
                course_id=query.course_id, trainee_id=query.viewer_id
            ),
            tags={
                CacheTag.TRAINEE_LIST_ASSIGNMENTS.format(
                    course_id=query.course_id, trainee_id=query.viewer_id
                ),
                # Note: Add list assignments tag, because we cannot get all the students
                # enrolled in that course and invalidate if some mutation happens. So we use
                # this to invalidate easily.
                CacheTag.TRAINER_LIST_ASSIGNMENTS.format(course_id=query.course_id),
            },
        )

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        entity_id_field="assignment_id",
        object_name="query",
    )
    async def get_assignment_contents(
        self, query: AssignmentViewRequestSchema
    ) -> Optional[TraineeAssignmentContent]:

        return await self.cache_service.get_or_set(
            key=CacheKey.TRAINEE_ASSIGNMENT_CONTENTS.format(
                assignment_id=query.assignment_id, trainee_id=query.viewer_id
            ),
            model=Optional[TraineeAssignmentContent],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.trainee_assignment_query_repo.assignment_contents(
                assignment_id=query.assignment_id, trainee_id=query.viewer_id
            ),
            tags={
                CacheTag.TRAINEE_ASSIGNMENT_CONTENTS.format(
                    assignment_id=query.assignment_id, trainee_id=query.viewer_id
                )
            },
        )


class TrainerAssignmentContentQueryService:
    def __init__(
        self,
        trainer_assignment_content_repo: TrainerAssignmentContentQueryRepository,
        entity_list_query_repo: EntityListQueryRepository,
        auth_service: AuthService,
        cache_service: CacheService,
    ) -> None:

        self.trainer_assignment_content_repo = trainer_assignment_content_repo
        self.entity_list_query_repo = entity_list_query_repo
        self.auth_service = auth_service
        self.cache_service = cache_service

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        parent_id_field="course_id",
        object_name="query",
    )
    async def list_assignments(
        self, query: CourseViewRequestSchema
    ) -> list[TrainerAssignmentCore]:

        return await self.cache_service.get_or_set(
            key=CacheKey.TRAINER_LIST_ASSIGNMENTS.format(course_id=query.course_id),
            model=list[TrainerAssignmentCore],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.trainer_assignment_content_repo.assignments(
                course_id=query.course_id
            ),
            tags={CacheTag.TRAINER_LIST_ASSIGNMENTS.format(course_id=query.course_id)},
        )

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        entity_id_field="assignment_id",
        object_name="query",
    )
    async def get_assignment_contents(
        self, query: AssignmentViewRequestSchema
    ) -> Optional[TrainerAssignmentContent]:

        return await self.cache_service.get_or_set(
            key=CacheKey.TRAINER_ASSIGNMENT_CONTENTS.format(
                assignment_id=query.assignment_id
            ),
            model=Optional[TrainerAssignmentContent],
            ttl=600,
            negative_ttl=120,
            fetch_func=lambda: self.trainer_assignment_content_repo.assignment_contents(
                assignment_id=query.assignment_id
            ),
            tags={
                CacheTag.TRAINER_ASSIGNMENT_CONTENTS.format(
                    assignment_id=query.assignment_id
                )
            },
        )

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT_SUBMISSION,
        user_id_field="viewer_id",
        parent_id_field="assignment_id",
        object_name="query",
    )
    async def list_submissions(
        self,
        query: AssignmentViewRequestSchema,
        filters: AssignmentSubmissionFilters,
        page_meta: PageMeta,
    ) -> Paginated[TrainerSubmissionDetail]:

        # NOTE: assignment_submission() returns Paginated[AssignmentSubmissionDetail]
        # But we Annotate the return type as Paginated[TrainerSubmissionDetail]
        # Because `class TrainerSubmissionDetail(AssignmentSubmissionDetail): ...`

        key = CacheKey.TRAINER_LIST_ASSIGNMENT_SUBMISSIONS.format(
            assignment_id=query.assignment_id,
            from_date=str(filters.from_date),
            to_date=str(filters.to_date),
            status=filters.status,
            sort_by_grade=filters.sort_by_grade,
            page=page_meta.page,
            limit=page_meta.limit,
        )

        return cast(
            Paginated[TrainerSubmissionDetail],
            await self.cache_service.get_or_set(
                key=key,
                model=Paginated[TrainerSubmissionDetail],
                ttl=600,
                negative_ttl=120,
                fetch_func=lambda: self.entity_list_query_repo.assignment_submissions(
                    assignment_id=query.assignment_id,
                    filters=filters,
                    page_meta=page_meta,
                ),
                tags={
                    CacheTag.LIST_ASSIGNMENT_SUBMISSIONS.format(
                        assignment_id=query.assignment_id
                    )
                },
            ),
        )
