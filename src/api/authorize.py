from enum import StrEnum
from typing import Literal, Optional, Set

from fastapi import Depends
from fastapi.requests import Request
from pydantic import TypeAdapter

from src.api.dependencies import get_current_user_context
from src.auth import Action, Entity
from src.command.commands.authentication import UserContext
from src.command.commands.base import UserID
from src.dependencies import auth_service
from src.exceptions import UnAuthorizedError


class AuthorizeOn(StrEnum):
    """
    Actions that can be authorized on entities.
    """

    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_VIEW = "user:view"

    COURSE_CREATE = "course:create"
    COURSE_UPDATE = "course:update"
    COURSE_DELETE = "course:delete"
    COURSE_VIEW = "course:view"

    MODULE_CREATE = "module:create"
    MODULE_UPDATE = "module:update"
    MODULE_DELETE = "module:delete"
    MODULE_VIEW = "module:view"

    LESSON_CREATE = "lesson:create"
    LESSON_UPDATE = "lesson:update"
    LESSON_DELETE = "lesson:delete"
    LESSON_VIEW = "lesson:view"

    ASSIGNMENT_CREATE = "assignment:create"
    ASSIGNMENT_UPDATE = "assignment:update"
    ASSIGNMENT_DELETE = "assignment:delete"
    ASSIGNMENT_VIEW = "assignment:view"

    ASSIGNMENT_SUBMISSION_CREATE = "assignment-submission:create"
    ASSIGNMENT_SUBMISSION_UPDATE = "assignment-submission:update"
    ASSIGNMENT_SUBMISSION_DELETE = "assignment-submission:delete"
    ASSIGNMENT_SUBMISSION_VIEW = "assignment-submission:view"


class Authorize:
    def __init__(
        self,
        on: AuthorizeOn,
        entity_id_field: Optional[str] = None,
        parent_id: Optional[int] = None,
        allowed_user_roles: Optional[
            Set[Literal["admin", "trainer", "trainee"]]
        ] = None,
    ) -> None:
        """
        `Authorize` object is used as a dependency in FastAPI route handlers.
        This will perform the authorization against the `User` and the `Entity`.

        ```python
        @app.get("/{course_id}")
        async def get_item(
            course_id: int,
            current_user: Annotated[UserID, Depends(Authorize(on=AuthorizeOn.COURSE_VIEW, entity_id_field="course_id"))],
        ):
            ...
        ```
        """

        entity, action = on.split(":")

        self.on = on
        self.entity = Entity(entity)
        self.action = Action(action)
        self.entity_id_field = entity_id_field
        self.parent_id = parent_id
        self.allowed_user_roles = allowed_user_roles

    async def _get_entity_id(self, request: Request) -> Optional[int]:
        """
        Extract the entity ID from the request's path parameter.
        """
        if self.entity_id_field is None:
            return None

        entity_id: str = request.path_params[self.entity_id_field]
        entity_id = entity_id.split("-")[-1]

        adapter = TypeAdapter(int)

        return adapter.validate_python(entity_id)

    def _validate_role(self, current_user: UserContext) -> None:
        """
        Validate the user's role against the allowed roles.
        """
        if self.allowed_user_roles is not None:
            if current_user.role not in self.allowed_user_roles:
                raise UnAuthorizedError(
                    f"Only {', '.join(self.allowed_user_roles)} are allowed to perform this action"
                )

    async def __call__(
        self,
        request: Request,
        current_user: UserContext = Depends(get_current_user_context),
    ) -> UserID:

        self._validate_role(current_user)

        entity_id = await self._get_entity_id(request=request)
        await auth_service.authorize(
            entity=self.entity,
            action=self.action,
            entity_id=entity_id,
            parent_id=self.parent_id,
            user_id=current_user.user_id,
            user_role=current_user.role,
        )

        return current_user.user_id
