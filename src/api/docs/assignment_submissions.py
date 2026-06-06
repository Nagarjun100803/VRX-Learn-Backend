from src.api.docs._responses import _generate_error
from src.api.docs._type import EndpointDoc
from src.command.commands.assignment_submissions import (
    AssignmentSubmissionAttachmentUploadContext,
    AssignmentSubmissionFeedbackUpdate,
    AssignmentSubmissionVerify,
    AssignmentSubmissionWithMedia,
)
from src.exceptions import (
    AssignmentNotFoundError,
    AssignmentSubmissionNotFoundError,
    AssignmentSubmissionNotGraded,
    UnAuthenticated,
    UnAuthorizedError,
)

GET_ASSIGNMENT_SUBMISSION: EndpointDoc = {
    "summary": "Get Assignment Submission by ID",
    "description": "Retrieve an assignment submission's details by its ID, including associated media.",
    "response_description": "Returns the assignment submission's details with media.",
    "responses": {
        200: {
            "model": AssignmentSubmissionWithMedia,
            "description": "Assignment submission details with media",
        },
        401: _generate_error(
            description="Unauthenticated",
            message="User is not authenticated.",
            type=UnAuthenticated,
        ),
        403: _generate_error(
            description="Forbidden",
            message="Cannot perform this action.",
            type=UnAuthorizedError,
        ),
        404: _generate_error(
            description="Assignment Submission Not Found",
            message="No assignment submission found with the given ID.",
            type=AssignmentSubmissionNotFoundError,
        ),
    },
}


CREATE_ASSIGNMENT_SUBMISSION: EndpointDoc = {
    "summary": "Create Assignment Submission",
    "description": """
Create a new assignment submission with an attachment. This endpoint:

1. Validates file size (max 5MB) and content type (PDF only).
2. Creates the submission record.
3. Generates a presigned upload URL for the submission file.

**Note**: The submission and media record creation are executed within a single database transaction to ensure consistency.
""",
    "response_description": "Returns the created assignment submission and upload URL for the attachment.",
    "responses": {
        201: {
            "model": AssignmentSubmissionAttachmentUploadContext,
            "description": "Assignment submission created and upload URL generated",
        },
        401: _generate_error(
            description="Unauthenticated",
            message="User is not authenticated.",
            type=UnAuthenticated,
        ),
        403: _generate_error(
            description="Forbidden",
            message="Cannot perform this action.",
            type=UnAuthorizedError,
        ),
        404: _generate_error(
            description="Assignment Not Found",
            message="No assignment found with the given ID.",
            type=AssignmentNotFoundError,
        ),
        400: {
            "description": "Bad Request - Validation Errors",
            "content": {
                "application/json": {
                    "examples": {
                        "file_size_exceeded": {
                            "summary": "File Size Exceeded",
                            "value": {
                                "message": "The uploaded file exceeds the maximum allowed size of 5MB.",
                                "type": "FileSizeExceededError",
                                "status": "error",
                            },
                        },
                        "invalid_content_type": {
                            "summary": "Invalid Content Type",
                            "value": {
                                "message": "Invalid content type. Only PDF files are allowed.",
                                "type": "InvalidContentTypeError",
                                "status": "error",
                            },
                        },
                        "max_attempts_reached": {
                            "summary": "Max Attempts Reached",
                            "value": {
                                "message": "Maximum number of attempts reached for this assignment.",
                                "type": "MaxAttemptsReachedError",
                                "status": "error",
                            },
                        },
                    }
                }
            },
        },
    },
}


VERIFY_ASSIGNMENT_SUBMISSION: EndpointDoc = {
    "summary": "Verify Assignment Submission",
    "description": "Verify and grade an assignment submission.",
    "response_description": "Returns the verified assignment submission details.",
    "responses": {
        200: {
            "model": AssignmentSubmissionVerify,
            "description": "Assignment submission verified successfully",
        },
        401: _generate_error(
            description="Unauthenticated",
            message="User is not authenticated.",
            type=UnAuthenticated,
        ),
        403: _generate_error(
            description="Forbidden",
            message="Cannot perform this action.",
            type=UnAuthorizedError,
        ),
        404: _generate_error(
            description="Assignment Submission Not Found",
            message="No assignment submission found with the given ID.",
            type=AssignmentSubmissionNotFoundError,
        ),
        400: {
            "description": "Bad Request - Validation Errors",
            "content": {
                "application/json": {
                    "examples": {
                        "already_verified": {
                            "summary": "Already Verified",
                            "value": {
                                "message": "Assignment submission is already verified and graded.",
                                "type": "AssignmentSubmissionAlreadyVerified",
                                "status": "error",
                            },
                        },
                        "media_not_found": {
                            "summary": "Media Not Found",
                            "value": {
                                "message": "Submission has no attached file.",
                                "type": "AssignmentSubmissionMediaNotFoundError",
                                "status": "error",
                            },
                        },
                        "media_not_uploaded": {
                            "summary": "Media Not Uploaded",
                            "value": {
                                "message": "File upload not completed.",
                                "type": "AssignmentSubmissionMediaNotUploadedError",
                                "status": "error",
                            },
                        },
                        "invalid_score": {
                            "summary": "Invalid Score",
                            "value": {
                                "message": "Invalid score. Score must be less than or equal to the maximum allowed score.",
                                "type": "InvalidScoreError",
                                "status": "error",
                            },
                        },
                    }
                }
            },
        },
    },
}


UPDATE_FEEDBACK: EndpointDoc = {
    "summary": "Update Feedback",
    "description": "Update feedback for an assignment submission.",
    "response_description": "Returns the updated feedback details.",
    "responses": {
        200: {
            "model": AssignmentSubmissionFeedbackUpdate,
            "description": "Feedback updated successfully",
        },
        401: _generate_error(
            description="Unauthenticated",
            message="User is not authenticated.",
            type=UnAuthenticated,
        ),
        403: _generate_error(
            description="Forbidden",
            message="Cannot perform this action.",
            type=UnAuthorizedError,
        ),
        404: _generate_error(
            description="Assignment Submission Not Found",
            message="No assignment submission found with the given ID.",
            type=AssignmentSubmissionNotFoundError,
        ),
        400: _generate_error(
            description="Not Graded",
            message="Assignment submission is not verified/graded.",
            type=AssignmentSubmissionNotGraded,
        ),
    },
}
