from enum import StrEnum
from typing import Literal, Optional, Set, Union

from fastapi import Depends
from fastapi.requests import Request
from pydantic.alias_generators import to_camel

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


def get_int_part(s: Union[str, int]) -> int:
    """
    Extract the integer part of a string or return the integer as-is.
    """
    if isinstance(s, str):
        return int(s.split("-")[-1])
    return int(s)


class Authorize:
    def __init__(
        self,
        on: AuthorizeOn,
        entity_id_field: Optional[str] = None,
        parent_id_field: Optional[str] = None,
        allowed_user_roles: Optional[
            Set[Literal["admin", "trainer", "trainee"]]
        ] = None,
    ) -> None:
        """
        `Authorize` object is used as a dependency in FastAPI route handlers.
        This will perform the authorization against the `User` and the `Entity`.

        1.Entity Specific used for `GET`, `PATCH`, `PUT`, `DELETE`
        ```python
        @app.get("/{course_id}")
        async def get_item(
            course_id: int,
            current_user: Annotated[
                UserID,
                Depends(
                    Authorize(
                        on=AuthorizeOn.COURSE_VIEW,
                        entity_id_field="course_id",
                    )
                )
            ],
        ):
            ...
        ```

        2. Parent Specific used for `POST`
        ```python
        @app.post("/")
        async def create_module(
            course_id: int,
            current_user: Annotated[
                UserID,
                Depends(
                    Authorize(
                        on=AuthorizeOn.COURSE_CREATE,
                        parent_id_field="course_id",
                    )
                )
            ],
        ):
            ...
        ```
        """

        entity, action = on.split(":")

        self.on = on
        self.entity = Entity(entity)
        self.action = Action(action)
        self.entity_id_field = entity_id_field
        self.parent_id_field = parent_id_field
        self.allowed_user_roles = allowed_user_roles

        # Validate that either entity_id_field or parent_id_field is set
        if self.entity_id_field is None and self.parent_id_field is None:
            raise ValueError("entity_id_field and parent_id_field cannot both be None")
        if self.parent_id_field:
            self.parent_id_field = to_camel(self.parent_id_field)

    async def _get_entity_id_and_parent_id(
        self, request: Request
    ) -> tuple[Optional[int], Optional[int]]:
        """
        Extract the entity ID and parent ID from the request.
        """

        if self.entity_id_field:
            entity_id_str: str = request.path_params[self.entity_id_field]
            entity_id = get_int_part(entity_id_str)
            print(f"entity_id={entity_id}, parent_id=None")
            return (entity_id, None)
        else:
            entity_id = None
            body = await request.json()
            print(f"body={body}")
            parent_id_str = body[self.parent_id_field]
            parent_id = get_int_part(parent_id_str)
            print(f"entity_id={entity_id}, parent_id={parent_id}")
            return (entity_id, parent_id)

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

        entity_id, parent_id = await self._get_entity_id_and_parent_id(request=request)
        print(f"Calling __call__ with entity_id={entity_id}, parent_id={parent_id}")
        await auth_service.authorize(
            entity=self.entity,
            action=self.action,
            entity_id=entity_id,
            parent_id=parent_id,
            user_id=current_user.user_id,
            user_role=current_user.role,
        )

        return current_user.user_id
