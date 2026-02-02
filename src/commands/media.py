from pydantic import BaseModel, Field
from typing import Annotated, Union
from enum import StrEnum
from src.commands.base import UserID, MediaBase, AuditFields
from pathlib import Path


class AllowedContentTypes(StrEnum):
    PDF = "application/pdf"
    PNG = "image/png"
    JPG = "image/jpg"
    JPEG = "image/jpeg"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    MP4 = "video/mp4"



class MediableType(StrEnum):
    LESSON = "LESSON"
    ASSIGNMENT = "ASSIGNMENT"
    ASSIGNMENT_SUBMISSIONS = "ASSIGNMENT_SUBMISSIONS"
    LAB_CREDENTIALS = "LAB_CREDENTIALS"
    
    
class MediaStatus(StrEnum):
    PENDING = "PENDING"
    UPLOADED = "UPLOADED"


class MediaCreateCore(BaseModel):
    filename: Union[str, Path]
    mime_type: AllowedContentTypes
    file_size: Annotated[int, Field(gt=0, examples=[1024])]
    mediable_id: int
    mediable_type: MediableType
    is_private: bool = True
    status: MediaStatus = MediaStatus.PENDING # Initally it's pending.
        
 
class MediaCreate(MediaCreateCore):
    created_by: UserID
    

class MediaStatusUpdateCore(BaseModel):
    status: MediaStatus
    

class MediaStatusUpdate(MediaStatusUpdateCore, MediaBase):
    updated_by: UserID
    

class MediaDeleteCore(MediaBase): ...

    
class MediaDelete(MediaDeleteCore, MediaBase):
    deleted_by: UserID
    
    
class MediaGet(MediaBase): ...
    # viewer_id: UserID
    

class Media(AuditFields, MediaCreateCore, MediaBase): ...