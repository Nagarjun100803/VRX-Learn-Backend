import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Type, ClassVar
from src.service.base import BaseService
from src.repository.assignments import AssignmentRepository
from src.repository.courses import CourseRepository
from src.service.files import FileMetadata
from src.service.media import MediaService
from src.service.permission_policy import Entity
from src.commands.assignments import (
    Assignment, AssignmentCreate, AssignmentCreateWithPosition, 
    AssignmentDelete, AssignmentGetQuery, AssignmentGet, 
    AssignmentUpdate, AssignmentReArrange, AllowedAssignmentFileType,
    AssignmentUploadUrl
)
from src.commands.media import MediaStatus, MediableType, MediaCreate
from src.exceptions import (
    EntityNotFoundError, AssignmentNotFoundError, 
    AssignmentAlreadyExistsError, CourseNotFoundError, FileSizeExceededError, 
    InvalidContentTypeError,
)
from src.service.base import require_access
from src.dependencies import course_repository


MAX_FILE_SIZE_FOR_ASSIGNMENT = 5 * 1024 * 1024 # 5 Mega Bytes.


@dataclass(kw_only=True)
class AssignmentService(BaseService[Assignment]):
    
    repo: AssignmentRepository
    course_repo: CourseRepository
    media_service: MediaService
    
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = AssignmentNotFoundError
    _entity: ClassVar[Entity] = Entity.ASSIGNMENT
    

    async def _raise_if_duplicate_title(self, title: str, course_id: int) -> None:
        duplicate_flag = await self.repo.exists_by(title=title, course_id=course_id)
        if duplicate_flag:
            raise AssignmentAlreadyExistsError(value=title, identifier="title")


    @require_access(action="create", user_id_alias="created_by", entity_id_alias="course_id", parent_repo=course_repository)
    async def create(self, cmd: AssignmentCreate) -> Assignment:
        # Check if the Assignment title is exist within a course.
        course_id_exist_flag, _ = await asyncio.gather(
            self.course_repo.exists_by(id=cmd.course_id),
            self._raise_if_duplicate_title(title=cmd.title, course_id=cmd.course_id)
        )
        
        if not course_id_exist_flag:
            raise CourseNotFoundError(value=cmd.course_id)
    
        position_string = await self.generate_position_string(course_id=cmd.course_id)
        
        return await self.repo.add(
            AssignmentCreateWithPosition(
                **cmd.model_dump(),
                position_string=position_string
            )
        )
    
    
    @require_access(action="update", user_id_alias="updated_by", entity_id_alias="id")
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
    
    
    @require_access(action="delete", user_id_alias="deleted_by", entity_id_alias="id")
    async def delete(self, cmd: AssignmentDelete) -> Assignment:
        return self._require_entity(
            await self.repo.delete(cmd),
            value=cmd.id
        )
    
    
    @require_access(action="view", user_id_alias="viewer_id", entity_id_alias="id", obj_name="query")
    async def get(self, query: AssignmentGetQuery) -> Assignment:
        return self._require_entity(
            await self.repo.get(
                AssignmentGet(id=query.id)
            ),
            value=query.id
        )
        
    
    @require_access(action="update", user_id_alias="updated_by", entity_id_alias="target_id")
    async def rearrange_sequence(
        self, 
        cmd: AssignmentReArrange, 
        scope: str = "course_id"
    ) -> Assignment:
        
        # NOTE: But in-practice, We don't need to rearrange based on position string.
        # We sort with due date and created_at. But for the sake of demonstration, I am implementing this method.
        
        return await super().rearrange_sequence(cmd, scope)
        

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
        
        assignment, course_details, = await asyncio.gather(
            self.create(cmd),
            # Get a course title and id of this course
            self.course_repo.pick(columns=("id", "title"), id=cmd.course_id)
        )
        
        # Generate a s3 key for this assignment.
        key = f"C-{course_details["id"]}:{course_details["title"]}/Assignments/A-{assignment.id}:{Path(assignment.title).name.strip().replace(" ", "")}"
        file_cmd.filename = key
        
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
            created_by=cmd.created_by
        )
        
        # presigned url.
        url = await self.media_service.prepare_upload_url(media)
        
        return AssignmentUploadUrl(
            id=assignment.id,
            upload_url=url
        )

