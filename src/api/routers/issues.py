from typing import Union

from fastapi import APIRouter

from src.api.dependencies import (
    CurrentAdmin,
    CurrentUser,
    IssueQueryServiceDependency,
    IssueServiceDependency,
)
from src.api.schemas.issues import IssueCreateSchema, IssueOutSchema
from src.command.commands.base import IssueID
from src.command.commands.issues import (
    AllowedIssueFileType,
    IssueCreate,
    IssueStatus,
    IssueStatusUpdate,
    IssueUpload,
)
from src.exceptions import InvalidContentTypeError
from src.query.dto.issues import IssueDetail

router = APIRouter(prefix="/issues", tags=["Issues"])


@router.get("/{issue_id}", response_model=IssueDetail)
async def get_issue(
    issue_id: IssueID,
    issue_service: IssueQueryServiceDependency,
    current_user: CurrentAdmin,
):
    return await issue_service.get_issue(issue_id)


@router.post("/", response_model=Union[IssueOutSchema, IssueUpload])
async def create_issue(
    issue: IssueCreateSchema,
    issue_service: IssueServiceDependency,
    current_user: CurrentUser,
):

    if issue.file_metadata is not None:
        if issue.file_metadata.content_type not in list(AllowedIssueFileType):
            raise InvalidContentTypeError(
                content_type=issue.file_metadata.content_type,
                allowed_types=AllowedIssueFileType,
            )

    return await issue_service.create(
        file_cmd=issue.file_metadata,
        cmd=IssueCreate(**issue.issue.model_dump(), created_by=current_user),
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
