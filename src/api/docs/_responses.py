from typing import Any

from src.api.schemas.error import ErrorResponse
from src.exceptions import DomainError


def _generate_error(
    description: str, type: type[DomainError], message: str
) -> dict[str, Any]:
    return {
        "model": ErrorResponse,
        "description": description,
        "content": {
            "application/json": {
                "example": {
                    "message": message,
                    "type": type.__name__,
                    "status": "error",
                }
            }
        },
    }
