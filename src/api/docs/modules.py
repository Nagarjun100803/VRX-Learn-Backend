from src.api.docs._responses import _generate_error
from src.api.docs._type import EndpointDoc
from src.api.schemas.modules import ModuleOutSchema, ModuleUpdateSchema
from src.exceptions import (
    CourseModuleAlreadyExistsError,
    CourseModuleNotFoundError,
    CourseNotFoundError,
    UnAuthenticated,
    UnAuthorizedError,
)

GET_MODULE: EndpointDoc = {
    "summary": "Get Module by ID",
    "description": "Retrieve a module's details by its ID.",
    "response_description": "Returns the module's details.",
    "responses": {
        200: {"model": ModuleOutSchema, "description": "Module details"},
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
            description="Module Not Found",
            message="No module found with the given ID.",
            type=CourseModuleNotFoundError,
        ),
    },
}


CREATE_MODULE: EndpointDoc = {
    "summary": "Create Module",
    "description": "Create a new module.",
    "response_description": "Returns the created module's details.",
    "responses": {
        201: {"model": ModuleOutSchema, "description": "Module created successfully"},
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
            description="Module Already Exists",
            message="Module already exists with the given title in the course.",
            type=CourseModuleAlreadyExistsError,
        ),
        404: _generate_error(
            description="Course Not Found",
            message="No course found with the given ID.",
            type=CourseNotFoundError,
        ),
    },
}


UPDATE_MODULE: EndpointDoc = {
    "summary": "Update Module",
    "description": "Update a module's details by its ID.",
    "response_description": "Returns the updated module's details.",
    "responses": {
        200: {
            "model": ModuleUpdateSchema,
            "description": "Module updated successfully",
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
            description="Module Not Found",
            message="No module found with the given ID.",
            type=CourseModuleNotFoundError,
        ),
        409: _generate_error(
            description="Module Already Exists",
            message="Module already exists with the given title in the course.",
            type=CourseModuleAlreadyExistsError,
        ),
    },
}


DELETE_MODULE: EndpointDoc = {
    "summary": "Delete Module",
    "description": "Delete a module by its ID.",
    "response_description": "Module deleted successfully.",
    "responses": {
        204: {"description": "Module deleted successfully"},
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
            description="Module Not Found",
            message="No module found with the given ID.",
            type=CourseModuleNotFoundError,
        ),
    },
}


UPDATE_MODULE_POSITION: EndpointDoc = {
    "summary": "Update Module Position",
    "description": "Reorder the position of a module within a course.",
    "response_description": "Returns the updated position string.",
    "responses": {
        200: {"description": "Module position updated successfully"},
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
