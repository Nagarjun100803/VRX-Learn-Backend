from fastapi import APIRouter, status

from src.api.dependencies import AssignmentSubmissionServiceDependency, CurrentUser
from src.api.docs.assignment_submissions import (
    CREATE_ASSIGNMENT_SUBMISSION,
    GET_ASSIGNMENT_SUBMISSION,
    UPDATE_FEEDBACK,
    VERIFY_ASSIGNMENT_SUBMISSION,
)
from src.api.schemas.assignment_submissions import (
    AssignmentSubmissionCreateSchema,
    AssignmentSubmissionFeedbackUpdateSchema,
    AssignmentSubmissionOut,
    AssignmentSubmissionVerifySchema,
)
from src.command.commands.assignment_submissions import (
    AssignmentSubmissionAttachmentStatusUpdate,
    AssignmentSubmissionAttachmentUploadContext,
    AssignmentSubmissionCreate,
    AssignmentSubmissionFeedbackUpdate,
    AssignmentSubmissionGet,
    AssignmentSubmissionVerify,
    AssignmentSubmissionWithMedia,
)
from src.command.commands.base import AssignmentSubmissionID

router = APIRouter(prefix="/assignment-submission", tags=["Assignment Submissions"])


@router.get(
    "/{assignment_submission_id}",
    response_model=AssignmentSubmissionWithMedia,
    **GET_ASSIGNMENT_SUBMISSION,
)
async def get_assignment_submission(
    assignment_submission_id: AssignmentSubmissionID,
    assignment_submission_service: AssignmentSubmissionServiceDependency,
    current_user: CurrentUser,
):

    return await assignment_submission_service.get_with_media(
        AssignmentSubmissionGet(id=assignment_submission_id, viewer_id=current_user)
    )


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=AssignmentSubmissionAttachmentUploadContext,
    **CREATE_ASSIGNMENT_SUBMISSION,
)
async def create_assignment_submission(
    assignment_submission: AssignmentSubmissionCreateSchema,
    assignment_submission_service: AssignmentSubmissionServiceDependency,
    current_user: CurrentUser,
):

    return await assignment_submission_service.create(
        cmd=AssignmentSubmissionCreate(
            **assignment_submission.assignment_submission.model_dump(),
            created_by=current_user,
        ),
        attachment=assignment_submission.attachment,
    )


@router.patch(
    "/{assignment_submission_id}/verify",
    response_model=AssignmentSubmissionOut,
    **VERIFY_ASSIGNMENT_SUBMISSION,
)
async def verify_assignment_submission(
    assignment_submission_id: AssignmentSubmissionID,
    assignment_verify_payload: AssignmentSubmissionVerifySchema,
    assignment_submission_service: AssignmentSubmissionServiceDependency,
    current_user: CurrentUser,
):
    return await assignment_submission_service.grade(
        cmd=AssignmentSubmissionVerify(
            **assignment_verify_payload.model_dump(),
            id=assignment_submission_id,
            updated_by=current_user,
        )
    )


@router.patch(
    "/{assignment_submission_id}/update-feedback",
    response_model=AssignmentSubmissionOut,
    **UPDATE_FEEDBACK,
)
async def update_feedback(
    assignment_submission_id: AssignmentSubmissionID,
    feedback_payload: AssignmentSubmissionFeedbackUpdateSchema,
    assignment_submission_service: AssignmentSubmissionServiceDependency,
    current_user: CurrentUser,
):

    return await assignment_submission_service.update_feedback(
        cmd=AssignmentSubmissionFeedbackUpdate(
            **feedback_payload.model_dump(),
            id=assignment_submission_id,
            updated_by=current_user,
        )
    )


@router.patch(
    "/{assignment_submission_id}/attachment/uploaded",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_attachment_status(
    assignment_submission_id: AssignmentSubmissionID,
    assignment_submission_service: AssignmentSubmissionServiceDependency,
    current_user: CurrentUser,
):
    await assignment_submission_service.mark_attachment_as_uploaded(
        cmd=AssignmentSubmissionAttachmentStatusUpdate(
            id=assignment_submission_id, updated_by=current_user
        )
    )


@router.get("/{assignment_submission_id}/attachment/view-url", response_model=str)
async def get_attachment_view_url(
    assignment_submission_id: AssignmentSubmissionID,
    assignment_submission_service: AssignmentSubmissionServiceDependency,
    current_user: CurrentUser,
):
    return await assignment_submission_service.get_attachment_view_url(
        query=AssignmentSubmissionGet(
            id=assignment_submission_id, viewer_id=current_user
        )
    )
