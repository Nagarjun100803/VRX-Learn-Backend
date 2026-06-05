from fastapi import APIRouter, status

from src.api.dependencies import (
    CurrentAdmin,
    CurrentUser,
    IssueQueryServiceDependency,
    IssueServiceDependency,
)
from src.api.schemas.issues import (
    IssueCreateSchema,
    IssueCreateWithAttachmentSchema,
    IssueOutSchema,
)
from src.command.commands.base import IssueID
from src.command.commands.issues import (
    IssueAttachmentStatusUpdate,
    IssueAttachmentUploadContext,
    IssueCreate,
    IssueGet,
    IssueStatus,
    IssueStatusUpdate,
)
from src.query.dto.issues import IssueDetail

router = APIRouter(prefix="/issues", tags=["Issues"])


@router.get("/{issue_id}", response_model=IssueDetail)
async def get_issue(
    issue_id: IssueID,
    issue_service: IssueQueryServiceDependency,
    current_user: CurrentAdmin,
):
    return await issue_service.get_issue(issue_id)


@router.post("/", response_model=IssueOutSchema)
async def create_issue(
    issue: IssueCreateSchema,
    issue_service: IssueServiceDependency,
    current_user: CurrentUser,
):
    return await issue_service.create(
        cmd=IssueCreate(**issue.model_dump(), created_by=current_user)
    )


@router.post("/with-attachment", response_model=IssueAttachmentUploadContext)
async def create_issue_with_attachment(
    issue: IssueCreateWithAttachmentSchema,
    issue_service: IssueServiceDependency,
    current_user: CurrentUser,
):
    return await issue_service.create_with_attachment(
        cmd=IssueCreate(**issue.issue.model_dump(), created_by=current_user),
        attachment=issue.attachment,
    )


@router.patch("/{issue_id}", response_model=IssueOutSchema)
async def update_status(
    issue_id: IssueID,
    status: IssueStatus,
    issue_service: IssueServiceDependency,
    current_user: CurrentAdmin,
):
    return await issue_service.update(
        IssueStatusUpdate(id=issue_id, status=status, updated_by=current_user)
    )


@router.patch("/{issue_id}/uploaded", status_code=status.HTTP_204_NO_CONTENT)
async def update_attachment_status(
    issue_id: IssueID, issue_service: IssueServiceDependency, current_user: CurrentUser
):
    await issue_service.mark_attachment_as_uploaded(
        cmd=IssueAttachmentStatusUpdate(id=issue_id, updated_by=current_user)
    )


@router.get("/{issue_id}/attachment/view-url", response_model=str)
async def get_view_url(
    issue_id: IssueID, issue_service: IssueServiceDependency, current_user: CurrentAdmin
):
    return await issue_service.get_attachment_view_url(
        IssueGet(id=issue_id, viewer_id=current_user)
    )
