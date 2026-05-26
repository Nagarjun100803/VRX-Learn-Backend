from typing import Type

import src.exceptions as exc

exception_registry: dict[Type[exc.DomainError], int] = {
    exc.EntityNotFoundError: 404,
    exc.AlreadyExistsError: 409,
    exc.UnAuthenticated: 401,
    exc.UnAuthorizedError: 403,
    exc.SecurityError: 401,
    exc.ValidationError: 400,
}
