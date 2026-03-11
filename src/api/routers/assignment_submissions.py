from fastapi import APIRouter, status
from src.command.commands.base import AssignmentSubmissionID
from src.api.schemas.assignment_submissions import (
    AssignmentSubmissionCreateSchema,
    AssignmentSubmissionFeedbackUpdateSchema,
    AssignmentSubmissionVerifySchema,
    AssignmentSubmissionOut
)
from src.command.commands.assignment_submissions import (
    AssignmentSubmissionGet, AssignmentSubmissionCreate,
    AssignmentSubmissionVerify
)
from src.command.commands.assignment_submissions import (
    AssignmentSubmissionFeedbackUpdate, 
    AssignmentSubmissionUploadURL
)

from src.api.dependencies import (
    AssignmentSubmissionServiceDependency, 
    CurrentUser
)

router = APIRouter(prefix="/assignment-submission", tags=["Assignment Submissions"])



@router.get("/{assignment_submission_id}", response_model=AssignmentSubmissionOut)
async def get_assignment_submission(
    assignment_submission_id: AssignmentSubmissionID,
    assignment_submission_service: AssignmentSubmissionServiceDependency,
    current_user: CurrentUser
):
    
    return await assignment_submission_service.get(
        AssignmentSubmissionGet(
            id=assignment_submission_id,
            viewer_id=current_user
        ) 
    )
    

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AssignmentSubmissionUploadURL)
async def create_assignment_submission(
    assignment_submission: AssignmentSubmissionCreateSchema,
    assignment_submission_service: AssignmentSubmissionServiceDependency,
    current_user: CurrentUser
):
    
    return await assignment_submission_service.create_with_attachment(
        cmd=AssignmentSubmissionCreate(
            **assignment_submission.assignment_submission.model_dump(),
            created_by=current_user
        ),
        file_cmd=assignment_submission.file_metadata
    )

    
@router.patch("/{assignment_submission_id}/-verify", response_model=AssignmentSubmissionVerify)
async def verify_assignment_submission(
    assignment_submission_id: AssignmentSubmissionID,
    assignment_verify_payload: AssignmentSubmissionVerifySchema,
    assignment_submission_service: AssignmentSubmissionServiceDependency,
    current_user: CurrentUser
):
    return await assignment_submission_service.update(
        AssignmentSubmissionVerify(
            **assignment_verify_payload.model_dump(),
            id=assignment_submission_id,
            updated_by=current_user
        )
    )
    


@router.patch("/{assignment_submission_id}/update-feedback", response_model=AssignmentSubmissionFeedbackUpdate)
async def update_feedback(
    assignment_submission_id: AssignmentSubmissionID,
    feedback_payload: AssignmentSubmissionFeedbackUpdateSchema,
    assignment_submission_service: AssignmentSubmissionServiceDependency,
    current_user: CurrentUser
):
    
    return await assignment_submission_service.update(
        AssignmentSubmissionFeedbackUpdate(
            **feedback_payload.model_dump(),
            id=assignment_submission_id,
            updated_by=current_user   
        )
    )