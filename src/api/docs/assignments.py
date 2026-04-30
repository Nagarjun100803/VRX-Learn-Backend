from src.api.docs._responses import _generate_error
from src.api.docs._type import EndpointDoc
from src.api.schemas.assignments import AssignmentUpdateSchema
from src.command.commands.assignments import AssignmentDetail
from src.exceptions import (
    AssignmentAlreadyExistsError,
    AssignmentNotFoundError,
    CourseNotFoundError,
    UnAuthenticated,
    UnauthorizedError,
)

GET_ASSIGNMENT: EndpointDoc = {
    "summary": "Get Assignment by ID",
    "description": "Retrieve an assignment's details by its ID.",
    "response_description": "Returns the assignment's details.",
    "responses": {
        200: {"model": AssignmentDetail, "description": "Assignment details"},
        401: _generate_error(
            description="Unauthenticated",
            message="User is not authenticated.",
            type=UnAuthenticated,
        ),
        403: _generate_error(
            description="Forbidden",
            message="Cannot perform this action.",
            type=UnauthorizedError,
        ),
        404: _generate_error(
            description="Assignment Not Found",
            message="No assignment found with the given ID.",
            type=AssignmentNotFoundError,
        ),
    },
}


CREATE_ASSIGNMENT: EndpointDoc = {
    "summary": "Create Assignment",
    "description": """
Create a new assignment. This endpoint supports two scenarios:

1. **Without Attachment**:
   - Only requires `title`, `instructions`, and other assignment details.
   - Returns the created assignment details (`AssignmentDetail`).

2. **With Attachment**:
   - Requires `title`, `file_metadata` (filename, content_type, size), and other assignment details.
   - Validates file size (max 5MB) and content type (PDF only).
   - Returns the created assignment details along with a presigned upload URL for the attachment (`AssignmentUpload`).

**Note**: Either `instructions` or `file_metadata` must be provided.
""",
    "response_description": "Returns the created assignment details or assignment with upload URL.",
    "responses": {
        200: {
            "description": "Assignment created successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "without_attachment": {
                            "summary": "Assignment created without attachment",
                            "value": {
                                "id": 1,
                                "title": "Sample Assignment",
                                "instructions": "Complete the task.",
                                "course_id": 1,
                                "max_score": 100,
                                "number_of_attempts": 3,
                                "created_at": "2023-01-01T00:00:00",
                                "created_by": 1,
                            },
                        },
                        "with_attachment": {
                            "summary": "Assignment created with attachment",
                            "value": {
                                "assignment": {
                                    "id": 1,
                                    "title": "Sample Assignment",
                                    "instructions": "Complete the task.",
                                    "course_id": 1,
                                    "max_score": 100,
                                    "number_of_attempts": 3,
                                    "created_at": "2023-01-01T00:00:00",
                                    "created_by": 1,
                                },
                                "media": {
                                    "media_id": 1,
                                    "filename": "assignment.pdf",
                                    "mime_type": "application/pdf",
                                    "upload_url": "https://example.com/upload-url",
                                },
                            },
                        },
                    }
                }
            },
        },
        401: _generate_error(
            description="Unauthenticated",
            message="User is not authenticated.",
            type=UnAuthenticated,
        ),
        403: _generate_error(
            description="Forbidden",
            message="Cannot perform this action.",
            type=UnauthorizedError,
        ),
        409: _generate_error(
            description="Assignment Already Exists",
            message="Assignment already exists with the given title in the course.",
            type=AssignmentAlreadyExistsError,
        ),
        404: _generate_error(
            description="Course Not Found",
            message="No course found with the given ID.",
            type=CourseNotFoundError,
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
                    }
                }
            },
        },
    },
}


UPDATE_ASSIGNMENT: EndpointDoc = {
    "summary": "Update Assignment",
    "description": "Update an assignment's details by its ID.",
    "response_description": "Returns the updated assignment's details.",
    "responses": {
        200: {
            "model": AssignmentUpdateSchema,
            "description": "Assignment updated successfully",
        },
        401: _generate_error(
            description="Unauthenticated",
            message="User is not authenticated.",
            type=UnAuthenticated,
        ),
        403: _generate_error(
            description="Forbidden",
            message="Cannot perform this action.",
            type=UnauthorizedError,
        ),
        404: _generate_error(
            description="Assignment Not Found",
            message="No assignment found with the given ID.",
            type=AssignmentNotFoundError,
        ),
        409: _generate_error(
            description="Assignment Already Exists",
            message="Assignment already exists with the given title in the course.",
            type=AssignmentAlreadyExistsError,
        ),
    },
}


DELETE_ASSIGNMENT: EndpointDoc = {
    "summary": "Delete Assignment",
    "description": "Delete an assignment by its ID.",
    "response_description": "Assignment deleted successfully.",
    "responses": {
        204: {"description": "Assignment deleted successfully"},
        401: _generate_error(
            description="Unauthenticated",
            message="User is not authenticated.",
            type=UnAuthenticated,
        ),
        403: _generate_error(
            description="Forbidden",
            message="Cannot perform this action.",
            type=UnauthorizedError,
        ),
        404: _generate_error(
            description="Assignment Not Found",
            message="No assignment found with the given ID.",
            type=AssignmentNotFoundError,
        ),
    },
}
