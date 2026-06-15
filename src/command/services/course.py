import asyncio
from typing import ClassVar, Type, Union, cast

from src.auth import Entity
from src.command.commands.courses import (
    Course,
    CourseCreate,
    CourseDelete,
    CourseGet,
    CourseGetByIDQuery,
    CourseInfoUpdate,
    RecordedCourseDetailsUpdate,
)
from src.command.commands.users import UserGetByID, UserRole
from src.command.repositories.courses import CourseRepository
from src.command.repositories.users import UserRepository
from src.command.services.base import BaseService
from src.exceptions import (
    CourseAlreadyExistsError,
    CourseNotFoundError,
    EntityNotFoundError,
    InvalidRoleError,
    UserNotFoundError,
)


class CourseService(BaseService[Course]):
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = CourseNotFoundError
    _entity: ClassVar[Entity] = Entity.COURSE

    def __init__(self, repo: CourseRepository, user_repo: UserRepository) -> None:

        self.repo = repo
        self.user_repo = user_repo

    async def _validate_trainer(self, trainer_id: int) -> None:

        user = await self.user_repo.get(UserGetByID(id=trainer_id))

        if user is None:
            raise UserNotFoundError(value=trainer_id, alias="Trainer")

        if user.role != UserRole.TRAINER:
            raise InvalidRoleError(role=UserRole.TRAINER)

    async def _validate_title(self, title: str) -> None:
        if await self.repo.exists_by(title=title):
            raise CourseAlreadyExistsError(value=title, identifier="title")

    async def create(self, cmd: CourseCreate) -> Course:
        # Check if course already exists and validate trainer
        await asyncio.gather(
            self._validate_title(cmd.title),
            self._validate_trainer(trainer_id=cmd.trainer_id),
        )

        return cast(Course, await self.repo.add(cmd))

    async def update(
        self, cmd: Union[RecordedCourseDetailsUpdate, CourseInfoUpdate]
    ) -> Course:

        if isinstance(cmd, CourseInfoUpdate):
            if cmd.trainer_id is not None:
                await self._validate_trainer(trainer_id=cmd.trainer_id)

            # Check if title already exists
            if cmd.title is not None:
                await self._validate_title(cmd.title)

            course = await self.repo.update(cmd)
            return self._require_entity(course, value=cmd.id)

        else:
            course = await self.repo.update(cmd)
            return self._require_entity(course, value=cmd.id)

    async def delete(self, cmd: CourseDelete):
        course = await self.repo.delete(cmd)
        return self._require_entity(course, value=cmd.id)

    async def get(self, query: CourseGetByIDQuery):
        course = await self.repo.get(CourseGet(id=query.id))
        return self._require_entity(course, value=query.id)
