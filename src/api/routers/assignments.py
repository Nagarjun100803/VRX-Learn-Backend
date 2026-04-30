from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import AssignmentServiceDependency, CurrentUser
from src.api.docs.assignments import (
    CREATE_ASSIGNMENT,
    DELETE_ASSIGNMENT,
    GET_ASSIGNMENT,
    UPDATE_ASSIGNMENT,
)
from src.api.schemas.assignments import AssignmentCreateSchema, AssignmentUpdateSchema
from src.command.commands.assignments import (
    AssignmentCreate,
    AssignmentDelete,
    AssignmentDetail,
    AssignmentGetQuery,
    AssignmentUpdate,
)
from src.command.commands.base import AssignmentID

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.get("/{assignment_id}", response_model=AssignmentDetail, **GET_ASSIGNMENT)
async def get_assignment(
    assignment_id: AssignmentID,
    assignment_service: AssignmentServiceDependency,
    current_user: CurrentUser,
):

    return await assignment_service.get(
        AssignmentGetQuery(id=assignment_id, viewer_id=current_user)
    )


@router.post("/", **CREATE_ASSIGNMENT)
async def create_assignment(
    assignment_payload: AssignmentCreateSchema,
    assignment_service: AssignmentServiceDependency,
    current_user: CurrentUser,
):

    # If no instruction's and attachment is provided.
    instructions = assignment_payload.assignment.instructions
    if (
        instructions is not None
        and instructions.strip() == ""
        and assignment_payload.file_metadata is None
    ):
        raise HTTPException(
            status_code=400, detail="Either instruction or attachment is required."
        )

    # Assignment creation without an attachment.
    if assignment_payload.file_metadata is None:
        return await assignment_service.create(
            AssignmentCreate(
                **assignment_payload.assignment.model_dump(), created_by=current_user
            )
        )

    return await assignment_service.init_assignment_create(
        file_cmd=assignment_payload.file_metadata,
        cmd=AssignmentCreate(
            **assignment_payload.assignment.model_dump(), created_by=current_user
        ),
    )


@router.patch(
    "/{assignment_id}/update-details",
    response_model=AssignmentUpdateSchema,
    **UPDATE_ASSIGNMENT,
)
async def update_assignment(
    assignment_id: AssignmentID,
    assignment: AssignmentUpdateSchema,
    assignment_service: AssignmentServiceDependency,
    current_user: CurrentUser,
):
    return await assignment_service.update(
        AssignmentUpdate(
            **assignment.model_dump(), updated_by=current_user, id=assignment_id
        )
    )


@router.delete(
    "/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT, **DELETE_ASSIGNMENT
)
async def delete_assignment(
    assignment_id: AssignmentID,
    assignment_service: AssignmentServiceDependency,
    current_user: CurrentUser,
):

    return await assignment_service.delete(
        AssignmentDelete(id=assignment_id, deleted_by=current_user)
    )


# NOTE: Rearrange is not implemented. Will implement if requires.
