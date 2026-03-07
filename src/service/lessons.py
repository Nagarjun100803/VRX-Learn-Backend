import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Type, Optional
from asyncpg import Connection
from src.commands.lessons import Lesson, LessonCreate, LessonCreateWithPosition, LessonTitleUpdate, LessonDelete, LessonGetQuery, LessonReArrange, LessonUpload
from src.commands.media import MediaCreate, MediaStatus, MediableType
from src.exceptions import EntityNotFoundError, LessonNotFoundError, LessonAlreadyExistsError, CourseModuleNotFoundError
from src.repository.modules import ModuleRepository
from src.service.base import BaseService
from src.repository.lessons import LessonRepository
from src.service.media import MediaService
from src.service.files import FileMetadata
from src.auth import AuthService, require_authorization, Entity, Action


@dataclass(kw_only=True)
class LessonService(BaseService[Lesson]):
    
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = LessonNotFoundError
    _entity: ClassVar[Type[Entity]] = Entity.LESSON
    
    repo: LessonRepository
    module_repo: ModuleRepository
    media_service: MediaService
    auth_service: AuthService
    

    @require_authorization(
        action=Action.CREATE,
        entity=Entity.LESSON,
        user_id_field="created_by",
        parent_id_field="module_id",
        object_name="cmd"
    )
    async def create(self, cmd: LessonCreate, connection: Optional[Connection] = None) -> Lesson:
        
        module_exist_flag, duplicate_title_flag = await asyncio.gather(
            self.module_repo.exists_by(id=cmd.module_id),
            self.repo.exists_by(title=cmd.title, module_id=cmd.module_id)
        )
        
        if not module_exist_flag: 
            raise CourseModuleNotFoundError(value=cmd.module_id)
        
        if duplicate_title_flag: 
            raise LessonAlreadyExistsError(value=cmd.title, identifier="title")
                
        position_string = await self.generate_position_string(module_id=cmd.module_id)
        
        return await self.repo.add(
            LessonCreateWithPosition(
                **cmd.model_dump(),
                position_string=position_string
            ),
            connection=connection
        )
    
             
    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.LESSON,
        user_id_field="updated_by",
        entity_id_field="id",
        object_name="cmd"   
    )
    async def update(self, cmd: LessonTitleUpdate) -> Lesson:
        
        lesson = await self.repo.pick(columns=("id", "module_id"), id=cmd.id)
        if not lesson: 
            raise LessonNotFoundError(value=cmd.id)
        
        # Check for duplicate title name in the same module.
        duplicate_lesson_title_flag = await self.repo.exists_by(title=cmd.title, module_id=lesson["module_id"])
        if duplicate_lesson_title_flag:
            raise LessonAlreadyExistsError(value=cmd.title, identifier="title")
        
        return self._require_entity(
            await self.repo.update(cmd),
            value=cmd.id
        )
    
    
            
    @require_authorization(
        action=Action.DELETE,
        entity=Entity.LESSON,
        user_id_field="deleted_by",
        entity_id_field="id",
        object_name="cmd"
    )
    async def delete(self, cmd: LessonDelete) -> Lesson:
        # TODO: Need to delete the actual file from the object storage also.
        return self._require_entity(
            await self.repo.delete(cmd),
            value=cmd.id
        )

    
    
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.LESSON,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query"
    )
    async def get(self, query: LessonGetQuery):
        return self._require_entity(
            await self.repo.get(query),
            value=query.id
        )
    
    
    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.LESSON,
        user_id_field="updated_by",
        entity_id_field="target_id",
        object_name="cmd"
    )
    async def rearrange_sequence(
        self, 
        cmd: LessonReArrange, 
        scope: str = "module_id"
    ) -> Lesson:
        return await super().rearrange_sequence(cmd, scope)
    
    
    async def init_lesson_create(
        self, 
        cmd: LessonCreate,
        file_cmd: FileMetadata
    ) -> LessonUpload:
        
        async with self.repo.db.transaction() as connection:
            lesson = await self.create(cmd, connection=connection)
            
            # Get the Id and create a record in media
            # TODO: Need to add the course details in the Key.
            key = f"modules/{lesson.module_id}/lessons/{lesson.id}/{Path(file_cmd.filename).name.strip().replace(" ", "_")}"
            file_cmd.filename = key
            
            media = MediaCreate(
                filename=key,
                mime_type=file_cmd.content_type,
                file_size=file_cmd.size,
                mediable_id=lesson.id,
                mediable_type=MediableType.LESSON,
                created_by=lesson.created_by,
                is_private=True,
                status=MediaStatus.PENDING
            )
            
            upload_url = await self.media_service.prepare_upload_url(media, expire_mins=120, connection=connection)
        
        return LessonUpload(lesson_id=lesson.id, upload_url=upload_url)
  
