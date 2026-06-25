from typing import Optional, cast

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
        self, trainee_assignment_query_repo: TraineeAssignmentContentQueryRepository
    ) -> None:

        self.trainee_assignment_query_repo = trainee_assignment_query_repo

    async def list_assignments(
        self, query: CourseViewRequestSchema
    ) -> list[TraineeAssignmentCore]:
        return await self.trainee_assignment_query_repo.assignments(
            course_id=query.course_id, trainee_id=query.viewer_id
        )

    async def get_assignment_contents(
        self, query: AssignmentViewRequestSchema
    ) -> Optional[TraineeAssignmentContent]:
        return await self.trainee_assignment_query_repo.assignment_contents(
            assignment_id=query.assignment_id, trainee_id=query.viewer_id
        )


class TrainerAssignmentContentQueryService:
    def __init__(
        self,
        trainer_assignment_content_repo: TrainerAssignmentContentQueryRepository,
        entity_list_query_repo: EntityListQueryRepository,
    ) -> None:

        self.trainer_assignment_content_repo = trainer_assignment_content_repo
        self.entity_list_query_repo = entity_list_query_repo

    async def list_assignments(
        self, query: CourseViewRequestSchema
    ) -> list[TrainerAssignmentCore]:
        return await self.trainer_assignment_content_repo.assignments(
            course_id=query.course_id
        )

    async def get_assignment_contents(
        self, query: AssignmentViewRequestSchema
    ) -> Optional[TrainerAssignmentContent]:
        return await self.trainer_assignment_content_repo.assignment_contents(
            assignment_id=query.assignment_id
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

        return cast(
            Paginated[TrainerSubmissionDetail],
            await self.entity_list_query_repo.assignment_submissions(
                assignment_id=query.assignment_id, filters=filters, page_meta=page_meta
            ),
        )
