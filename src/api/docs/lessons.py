from src.api.docs._responses import _generate_error
from src.api.docs._type import EndpointDoc
from src.api.schemas.lessons import LessonUpdateSchema
from src.command.commands.base import AttachmentUploadContext
from src.command.commands.lessons import LessonContext, LessonWithMedia
from src.exceptions import (
    CourseModuleNotFoundError,
    LessonAlreadyExistsError,
    LessonNotFoundError,
    UnAuthenticated,
    UnAuthorizedError,
)

GET_LESSON: EndpointDoc = {
    "summary": "Get Lesson by ID",
    "description": "Retrieve a lesson's details by its ID, including associated media.",
    "response_description": "Returns the lesson's details with media.",
    "responses": {
        200: {"model": LessonWithMedia, "description": "Lesson details with media"},
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
            description="Lesson Not Found",
            message="No lesson found with the given ID.",
            type=LessonNotFoundError,
        ),
    },
}


CREATE_LESSON: EndpointDoc = {
    "summary": "Create Lesson",
    "description": "Create a new lesson and prepare for media upload.",
    "response_description": "Returns the created lesson and upload URL for media.",
    "responses": {
        201: {
            "model": AttachmentUploadContext[LessonContext],
            "description": "Lesson created and upload URL generated",
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
        409: _generate_error(
            description="Lesson Already Exists",
            message="Lesson already exists with the given title in the module.",
            type=LessonAlreadyExistsError,
        ),
        404: _generate_error(
            description="Module Not Found",
            message="No module found with the given ID.",
            type=CourseModuleNotFoundError,
        ),
    },
}


DELETE_LESSON: EndpointDoc = {
    "summary": "Delete Lesson",
    "description": "Delete a lesson by its ID.",
    "response_description": "Lesson deleted successfully.",
    "responses": {
        204: {"description": "Lesson deleted successfully"},
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
            description="Lesson Not Found",
            message="No lesson found with the given ID.",
            type=LessonNotFoundError,
        ),
    },
}


LESSON_UPDATE: EndpointDoc = {
    "summary": "Update Lesson",
    "description": "Update a lesson's details by its ID.",
    "response_description": "Returns the updated lesson's details.",
    "responses": {
        200: {
            "model": LessonUpdateSchema,
            "description": "Lesson updated successfully",
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
            description="Lesson Not Found",
            message="No lesson found with the given ID.",
            type=LessonNotFoundError,
        ),
        409: _generate_error(
            description="Lesson Already Exists",
            message="Lesson already exists with the given title in the module.",
            type=LessonAlreadyExistsError,
        ),
    },
}


UPDATE_LESSON_POSITION: EndpointDoc = {
    "summary": "Update Lesson Position",
    "description": "Reorder the position of a lesson within a module.",
    "response_description": "Returns the updated position string.",
    "responses": {
        200: {"description": "Lesson position updated successfully"},
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
    },
}
