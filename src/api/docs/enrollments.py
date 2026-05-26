from src.api.docs._responses import _generate_error
from src.api.docs._type import EndpointDoc
from src.api.schemas.enrollments import EnrollmentOut, EnrollmentUpdateSchema
from src.exceptions import (
    EnrollmentAlreadyExistsError,
    EnrollmentNotFoundError,
    InvalidRoleError,
    UnAuthenticated,
    UnAuthorizedError,
)

GET_ENROLLMENT: EndpointDoc = {
    "summary": "Get Enrollment by ID",
    "description": "Retrieve an enrollment's details by its ID.",
    "response_description": "Returns the enrollment's details.",
    "responses": {
        200: {"model": EnrollmentOut, "description": "Enrollment details"},
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
            description="Enrollment Not Found",
            message="No enrollment found with the given ID.",
            type=EnrollmentNotFoundError,
        ),
    },
}


CREATE_ENROLLMENT: EndpointDoc = {
    "summary": "Create Enrollment",
    "description": "Create a new enrollment for a user in a course.",
    "response_description": "Returns the created enrollment's details.",
    "responses": {
        201: {"model": EnrollmentOut, "description": "Enrollment created successfully"},
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
        409: _generate_error(
            description="Enrollment Already Exists",
            message="Enrollment already exists for the given user and course.",
            type=EnrollmentAlreadyExistsError,
        ),
        404: {
            "description": "Not Found - Entity Not Found",
            "content": {
                "application/json": {
                    "examples": {
                        "course_not_found": {
                            "summary": "Course Not Found",
                            "value": {
                                "message": "No course found with the given ID.",
                                "type": "CourseNotFoundError",
                                "status": "error",
                            },
                        },
                        "user_not_found": {
                            "summary": "User Not Found",
                            "value": {
                                "message": "No user found with the given ID.",
                                "type": "UserNotFoundError",
                                "status": "error",
                            },
                        },
                    }
                }
            },
        },
        400: _generate_error(
            description="Invalid Role",
            message="The user's role is not allowed to enroll in a course.",
            type=InvalidRoleError,
        ),
    },
}


UPDATE_ENROLLMENT: EndpointDoc = {
    "summary": "Update Enrollment",
    "description": "Update an enrollment's status or expiration date by its ID.",
    "response_description": "Returns the updated enrollment's details.",
    "responses": {
        200: {
            "model": EnrollmentUpdateSchema,
            "description": "Enrollment updated successfully",
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
            description="Enrollment Not Found",
            message="No enrollment found with the given ID.",
            type=EnrollmentNotFoundError,
        ),
    },
}


DELETE_ENROLLMENT: EndpointDoc = {
    "summary": "Delete Enrollment",
    "description": "Delete an enrollment by its ID.",
    "response_description": "Enrollment deleted successfully.",
    "responses": {
        204: {"description": "Enrollment deleted successfully"},
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
            description="Enrollment Not Found",
            message="No enrollment found with the given ID.",
            type=EnrollmentNotFoundError,
        ),
    },
}
