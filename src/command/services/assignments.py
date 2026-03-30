import asyncio
from uuid import uuid4
from asyncpg import Connection
from typing import Type, ClassVar, Optional

from slugify import slugify

from src.command.services.base import BaseService
from src.command.repositories.assignments import AssignmentRepository
from src.command.repositories.courses import CourseRepository
from src.command.services.files import FileMetadata
from src.command.services.media import MediaService
from src.command.commands.assignments import (
    Assignment, AssignmentCreate, AssignmentCreateWithPosition, 
    AssignmentDelete, AssignmentGetQuery, AssignmentGet, 
    AssignmentUpdate, AssignmentReArrange, AllowedAssignmentFileType,
    AssignmentUploadUrl
)
from src.command.commands.media import MediaStatus, MediableType, MediaCreate
from src.exceptions import (
    EntityNotFoundError, AssignmentNotFoundError, 
    AssignmentAlreadyExistsError, CourseNotFoundError, FileSizeExceededError, 
    InvalidContentTypeError,
)

from src.auth import AuthService, Entity, Action, require_authorization

MAX_FILE_SIZE_FOR_ASSIGNMENT = 5 * 1024 * 1024 # 5 Mega Bytes.


class AssignmentService(BaseService[Assignment]):
    
    def __init__(
        self,
        repo: AssignmentRepository,
        course_repo: CourseRepository,
        media_service: MediaService,
        auth_service: AuthService
    ) -> None:
        
        self.repo = repo
        self.course_repo = course_repo
        self.media_service = media_service
        self.auth_service = auth_service
    
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = AssignmentNotFoundError
    _entity: ClassVar[Entity] = Entity.ASSIGNMENT
    

    async def _raise_if_duplicate_title(self, title: str, course_id: int) -> None:
        duplicate_flag = await self.repo.exists_by(title=title, course_id=course_id)
        if duplicate_flag:
            raise AssignmentAlreadyExistsError(value=title, identifier="title")


    @require_authorization(
        action=Action.CREATE,
        entity=Entity.ASSIGNMENT,
        user_id_field="created_by",
        parent_id_field="course_id",
        object_name="cmd"
    )
    async def create(self, cmd: AssignmentCreate, connection: Optional[Connection] = None) -> Assignment:
        # Check if the Assignment title is exist within a course.
        course_id_exist_flag, _ = await asyncio.gather(
            self.course_repo.exists_by(id=cmd.course_id),
            self._raise_if_duplicate_title(title=cmd.title, course_id=cmd.course_id)
        )
        
        if not course_id_exist_flag:
            raise CourseNotFoundError(value=cmd.course_id)
            
        return await self.repo.add(cmd,connection=connection)
    
    
    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.ASSIGNMENT,
        user_id_field="updated_by",
        entity_id_field="id",
        object_name="cmd"
    )
    async def update(self, cmd: AssignmentUpdate) -> Assignment:
        
        assignment = await self.repo.get(AssignmentGet(id=cmd.id))
        
        if assignment is None:
            raise AssignmentNotFoundError(value=cmd.id)
        
        if cmd.title and cmd.title != assignment.title :
            await self._raise_if_duplicate_title(title=assignment.title, course_id=assignment.course_id)
        
        return self._require_entity(
            await self.repo.update(cmd),
            value=cmd.id
        )
    
    
    @require_authorization(
        action=Action.DELETE,
        entity=Entity.ASSIGNMENT,
        user_id_field="deleted_by",
        entity_id_field="id",
        object_name="cmd"        
    )
    async def delete(self, cmd: AssignmentDelete) -> Assignment:
        return self._require_entity(
            await self.repo.delete(cmd),
            value=cmd.id
        )
    
    
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query"
    )
    async def get(self, query: AssignmentGetQuery) -> Assignment:
        return self._require_entity(
            await self.repo.get(
                AssignmentGet(id=query.id)
            ),
            value=query.id
        )
        


    async def init_assignment_create(
        self,
        cmd: AssignmentCreate,
        file_cmd: FileMetadata
    ) -> AssignmentUploadUrl:
        
        # Check for file size.
        if file_cmd.size > MAX_FILE_SIZE_FOR_ASSIGNMENT:
            raise FileSizeExceededError(max_size=MAX_FILE_SIZE_FOR_ASSIGNMENT)
        
        # Check for content type.
        if file_cmd.content_type not in AllowedAssignmentFileType:
            raise InvalidContentTypeError(content_type=file_cmd.content_type, allowed_types=AllowedAssignmentFileType)
        
        # Create an assignment and media in a transaction. 
        # So if any of the operation fails, the transaction will be rolled back and 
        # we won't have an orphan media or assignment.
        async with self.repo.db.transaction() as connection:
            
            assignment = await self.create(cmd, connection=connection)
            
            # Generate a s3 key for this assignment.
            slugged_filename = slugify(file_cmd.filename)
            
            key = f"courses/C-{cmd.course_id}/assignments/{str(uuid4())}/{slugged_filename}"
            
            # Create a media with Assignment Mediable Type and 
            # Pass mediable_id = new assignment id.
            media = MediaCreate(
                filename=file_cmd.filename,
                mime_type=file_cmd.content_type,
                file_size=file_cmd.size,
                mediable_id=assignment.id,
                mediable_type=MediableType.ASSIGNMENT,
                is_private=True,
                status=MediaStatus.PENDING,
                created_by=cmd.created_by,
                key=key
            )
            
            # presigned url.
            media_id, url = await self.media_service.prepare_upload_url(media, connection=connection)
            
        return AssignmentUploadUrl(
            id=assignment.id,
            media_id=media_id,
            upload_url=url
        )

