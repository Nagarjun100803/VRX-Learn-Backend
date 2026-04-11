from typing import Annotated, Optional

from fastapi import APIRouter, Depends

from src.api.dependencies import (
    CurrentAdminOrTrainer,
    CurrentTraineeOrTrainer,
    TraineeAssignmentContentQueryServiceDependency,
    TrainerAssignmentContentQueryServiceDependency,
)
from src.command.commands.base import AssignmentID, CourseID
from src.query.dto.assignment_contents import (
    AssignmentSubmissionFilters,
    AssignmentSubmissionQuerySchema,
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

trainee_router = APIRouter(
    prefix="/assignment-contents/trainee",
    tags=["Assignment Contents", "Trainee Assignment Contents"],
)


@trainee_router.get(
    "/assignments/{course_id}", response_model=list[TraineeAssignmentCore]
)
async def trainee_view_list_assignments(
    course_id: CourseID,
    query_service: TraineeAssignmentContentQueryServiceDependency,
    current_user: CurrentTraineeOrTrainer,
):
    return await query_service.list_assignments(
        CourseViewRequestSchema(course_id=course_id, viewer_id=current_user)
    )


@trainee_router.get(
    "/contents/{assignment_id}", response_model=Optional[TraineeAssignmentContent]
)
async def get_assignment_contents(
    assignment_id: AssignmentID,
    query_service: TraineeAssignmentContentQueryServiceDependency,
    current_user: CurrentTraineeOrTrainer,
):
    return await query_service.get_assignment_contents(
        AssignmentViewRequestSchema(assignment_id=assignment_id, viewer_id=current_user)
    )


trainer_router = APIRouter(
    prefix="/assignment-contents/trainer",
    tags=["Assignment Contents", "Trainer Assignment Contents"],
)


@trainer_router.get(
    "/assignments/{course_id}", response_model=list[TrainerAssignmentCore]
)
async def trainer_view_list_assignments(
    course_id: CourseID,
    query_service: TrainerAssignmentContentQueryServiceDependency,
    current_user: CurrentTraineeOrTrainer,
):
    return await query_service.list_assignments(
        CourseViewRequestSchema(course_id=course_id, viewer_id=current_user)
    )


@trainer_router.get(
    "/submissions/{assignment_id}", response_model=Paginated[TrainerSubmissionDetail]
)
async def list_submissions(
    assignment_id: AssignmentID,
    query_params: Annotated[AssignmentSubmissionQuerySchema, Depends()],
    query_service: TrainerAssignmentContentQueryServiceDependency,
    current_user: CurrentAdminOrTrainer,
):
    return await query_service.list_submissions(
        query=AssignmentViewRequestSchema(
            assignment_id=assignment_id, viewer_id=current_user
        ),
        filters=AssignmentSubmissionFilters(
            from_date=query_params.from_date,
            to_date=query_params.to_date,
            status=query_params.status,
            sort_by_grade=query_params.sort_by_grade,
        ),
        page_meta=PageMeta(page=query_params.page, limit=query_params.limit),
    )


@trainer_router.get(
    "/contents/{assignment_id}", response_model=Optional[TrainerAssignmentContent]
)
async def get_assignment_content(
    assignment_id: AssignmentID,
    query_service: TrainerAssignmentContentQueryServiceDependency,
    current_user: CurrentAdminOrTrainer,
):
    return await query_service.get_assignment_contents(
        AssignmentViewRequestSchema(assignment_id=assignment_id, viewer_id=current_user)
    )
