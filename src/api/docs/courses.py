from src.api.docs._responses import _generate_error
from src.api.docs._type import EndpointDoc
from src.api.schemas.courses import CourseOutSchema
from src.exceptions import (
    CourseAlreadyExistsError,
    CourseNotFoundError,
    InvalidRoleError,
    UnAuthenticated,
    UnAuthorizedError,
    UserNotFoundError,
)

GET_COURSE: EndpointDoc = {
    "summary": "Get Course by ID",
    "description": "Retrieve a course's details by its ID.",
    "response_description": "Returns the course's details.",
    "responses": {
        200: {"model": CourseOutSchema, "description": "Course details"},
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
            description="Course Not Found",
            message="No course found with the given ID.",
            type=CourseNotFoundError,
        ),
    },
}


CREATE_COURSE: EndpointDoc = {
    "summary": "Create Course",
    "description": "Create a new course.",
    "response_description": "Returns the created course's details.",
    "responses": {
        201: {"model": CourseOutSchema, "description": "Course created successfully"},
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
            description="Course Already Exists",
            message="Course already exists with the given title.",
            type=CourseAlreadyExistsError,
        ),
        404: _generate_error(
            description="User Not Found",
            message="Trainer not found.",
            type=UserNotFoundError,
        ),
        400: _generate_error(
            description="Invalid Role",
            message="The user is not a trainer.",
            type=InvalidRoleError,
        ),
    },
}


DELETE_COURSE: EndpointDoc = {
    "summary": "Delete Course",
    "description": "Delete a course by its ID.",
    "response_description": "Course deleted successfully.",
    "responses": {
        204: {"description": "Course deleted successfully"},
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
            description="Course Not Found",
            message="No course found with the given ID.",
            type=CourseNotFoundError,
        ),
    },
}


UPDATE_BASIC_INFO: EndpointDoc = {
    "summary": "Update Basic Course Info",
    "description": "Update the basic information of a course.",
    "response_description": "Returns the updated course's details.",
    "responses": {
        200: {"model": CourseOutSchema, "description": "Course updated successfully"},
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
            description="Course Not Found",
            message="No course found with the given ID.",
            type=CourseNotFoundError,
        ),
        400: _generate_error(
            description="Invalid Role",
            message="The user is not a trainer.",
            type=InvalidRoleError,
        ),
    },
}


UPDATE_PRE_RECORDED_COURSE_INFO: EndpointDoc = {
    "summary": "Update Pre-Recorded Course Info",
    "description": "Update the details of a pre-recorded course.",
    "response_description": "Returns the updated course's details.",
    "responses": {
        200: {"model": CourseOutSchema, "description": "Course updated successfully"},
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
            description="Course Not Found",
            message="No course found with the given ID.",
            type=CourseNotFoundError,
        ),
    },
}
