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
    AssignmentSubmissionVerifySchema,
)
from src.command.commands.assignment_submissions import (
    AssignmentSubmissionCreate,
    AssignmentSubmissionFeedbackUpdate,
    AssignmentSubmissionGet,
    AssignmentSubmissionUpload,
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
    response_model=AssignmentSubmissionUpload,
    **CREATE_ASSIGNMENT_SUBMISSION,
)
async def create_assignment_submission(
    assignment_submission: AssignmentSubmissionCreateSchema,
    assignment_submission_service: AssignmentSubmissionServiceDependency,
    current_user: CurrentUser,
):

    return await assignment_submission_service.create_with_attachment(
        cmd=AssignmentSubmissionCreate(
            **assignment_submission.assignment_submission.model_dump(),
            created_by=current_user,
        ),
        file_cmd=assignment_submission.file_metadata,
    )


@router.patch(
    "/{assignment_submission_id}/verify",
    response_model=AssignmentSubmissionVerify,
    **VERIFY_ASSIGNMENT_SUBMISSION,
)
async def verify_assignment_submission(
    assignment_submission_id: AssignmentSubmissionID,
    assignment_verify_payload: AssignmentSubmissionVerifySchema,
    assignment_submission_service: AssignmentSubmissionServiceDependency,
    current_user: CurrentUser,
):
    return await assignment_submission_service.update(
        AssignmentSubmissionVerify(
            **assignment_verify_payload.model_dump(),
            id=assignment_submission_id,
            updated_by=current_user,
        )
    )


@router.patch(
    "/{assignment_submission_id}/update-feedback",
    response_model=AssignmentSubmissionFeedbackUpdate,
    **UPDATE_FEEDBACK,
)
async def update_feedback(
    assignment_submission_id: AssignmentSubmissionID,
    feedback_payload: AssignmentSubmissionFeedbackUpdateSchema,
    assignment_submission_service: AssignmentSubmissionServiceDependency,
    current_user: CurrentUser,
):

    return await assignment_submission_service.update(
        AssignmentSubmissionFeedbackUpdate(
            **feedback_payload.model_dump(),
            id=assignment_submission_id,
            updated_by=current_user,
        )
    )
