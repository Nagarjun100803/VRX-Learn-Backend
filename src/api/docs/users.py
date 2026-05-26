from src.api.docs._responses import _generate_error
from src.api.docs._type import EndpointDoc
from src.api.schemas.users import UserOutSchema
from src.exceptions import (
    PasswordMismatchError,
    UnAuthenticated,
    UnAuthorizedError,
    UserAlreadyExistsError,
)

LOGIN: EndpointDoc = {
    "summary": "Authenticate User",
    "description": """
Authenticate a user with `email` and `password`

On success, sets an **HTTP-only cookie(access_token) with a signed JWT.
the token is never returned in the response body.

**Raises**
- `UnAuthenticated`-> 401 - email not found or password mismatch.
""",
    "response_description": "Login successful, JWT set in `access_token` cookie.",
    "responses": {
        200: {
            "description": "Authenticated successfully",
            "content": {
                "application/json": {"example": {"message": "Logged in successfully."}}
            },
        },
        401: _generate_error(
            description="Email not found or Invalid password.",
            type=UnAuthenticated,
            message="Email not found or invalid password.",
        ),
    },
}


CREATE_USER: EndpointDoc = {
    "responses": {
        201: {"model": UserOutSchema, "description": "Create New User"},
        403: _generate_error(
            description="Forbidden",
            message="Cannot perform this action.",
            type=UnAuthorizedError,
        ),
        400: _generate_error(
            description="Password Mismatch",
            message="Password and confirm password did not match.",
            type=PasswordMismatchError,
        ),
        409: _generate_error(
            description="User Exists",
            message="User already exist with a given email.",
            type=UserAlreadyExistsError,
        ),
    }
}


ME: EndpointDoc = {
    "summary": "Get Current User",
    "description": "Retrieve the details of the currently authenticated user.",
    "response_description": "Returns the current user's details.",
    "responses": {
        200: {"model": UserOutSchema, "description": "Current user details"},
        401: _generate_error(
            description="Unauthenticated",
            message="User is not authenticated.",
            type=UnAuthenticated,
        ),
    },
}


LOGOUT: EndpointDoc = {
    "summary": "Logout User",
    "description": "Logout the currently authenticated user by clearing the JWT cookie.",
    "response_description": "Logout successful, JWT cookie cleared.",
    "responses": {
        200: {
            "description": "Logged out successfully",
            "content": {
                "application/json": {"example": {"message": "Logged out successfully."}}
            },
        }
    },
}


GET_USER: EndpointDoc = {
    "summary": "Get User by ID",
    "description": "Retrieve a user's details by their ID.",
    "response_description": "Returns the user's details.",
    "responses": {
        200: {"model": UserOutSchema, "description": "User details"},
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


DELETE_USER: EndpointDoc = {
    "summary": "Delete User",
    "description": "Delete a user by their ID.",
    "response_description": "User deleted successfully.",
    "responses": {
        204: {"description": "User deleted successfully"},
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
