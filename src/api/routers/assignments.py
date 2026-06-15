from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import AssignmentServiceDependency, CurrentUser
from src.api.docs.assignments import (
    DELETE_ASSIGNMENT,
    GET_ASSIGNMENT,
    UPDATE_ASSIGNMENT,
)
from src.api.schemas.assignments import (
    AssignmentCreateSchema,
    AssignmentCreateWithAttachmentSchema,
    AssignmentOut,
    AssignmentUpdateSchema,
)
from src.command.commands.assignments import (
    AssignmentAttachmentStatusUpdate,
    AssignmentContext,
    AssignmentCreate,
    AssignmentDelete,
    AssignmentGetQuery,
    AssignmentUpdate,
)
from src.command.commands.base import AssignmentID, AttachmentUploadContext

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.get("/{assignment_id}", response_model=AssignmentOut, **GET_ASSIGNMENT)
async def get_assignment(
    assignment_id: AssignmentID,
    assignment_service: AssignmentServiceDependency,
    current_user: CurrentUser,
):

    return await assignment_service.get(
        AssignmentGetQuery(id=assignment_id, viewer_id=current_user)
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AssignmentOut)
async def create_assignment(
    assignment_payload: AssignmentCreateSchema,
    assignment_service: AssignmentServiceDependency,
    current_user: CurrentUser,
):
    if (
        assignment_payload.instructions is None
        or assignment_payload.instructions.strip() == ""
    ):
        raise HTTPException(status_code=400, detail="Instruction is required.")
    return await assignment_service.create(
        AssignmentCreate(**assignment_payload.model_dump(), created_by=current_user)
    )


@router.post(
    "/with-attachment",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentUploadContext[AssignmentContext],
)
async def create_assignment_with_attachment(
    assignment_payload: AssignmentCreateWithAttachmentSchema,
    assignment_service: AssignmentServiceDependency,
    current_user: CurrentUser,
):
    return await assignment_service.create_with_attachment(
        AssignmentCreate(
            **assignment_payload.assignment.model_dump(), created_by=current_user
        ),
        assignment_payload.attachment,
    )


@router.patch(
    "/{assignment_id}", response_model=AssignmentUpdateSchema, **UPDATE_ASSIGNMENT
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


@router.patch(
    "/{assignment_id}/attachment/uploaded", status_code=status.HTTP_204_NO_CONTENT
)
async def update_attachment_status(
    assignment_id: AssignmentID,
    assignment_service: AssignmentServiceDependency,
    current_user: CurrentUser,
):
    await assignment_service.mark_attachment_as_uploaded(
        AssignmentAttachmentStatusUpdate(id=assignment_id, updated_by=current_user)
    )


@router.get("/{assignment_id}/attachment/view-url", response_model=str)
async def get_view_url(
    assignment_id: AssignmentID,
    assignment_service: AssignmentServiceDependency,
    current_user: CurrentUser,
):
    return await assignment_service.get_attachment_view_url(
        AssignmentGetQuery(id=assignment_id, viewer_id=current_user)
    )


# NOTE: Rearrange is not implemented. Will implement if requires.
