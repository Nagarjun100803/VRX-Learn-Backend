from fastapi import APIRouter, status
from src.api.dependencies import LessonServiceDependency, CurrentUser
from src.command.commands.base import LessonID
from src.command.commands.lessons import LessonDelete, LessonGetQuery, LessonReorderParticipants, LessonReorderParticipantsCore, LessonUpdate, LessonUploadUrl, LessonCreate
from src.api.schemas.lessons import LessonCreateSchema, LessonOutSchema, LessonUpdateSchema
from src.command.services.files import FileMetadata


router = APIRouter(prefix="/lessons", tags=["Lessons"])


@router.get("/{lesson_id}", response_model=LessonOutSchema)
async def get_lesson(
    lesson_id: LessonID,
    lesson_service: LessonServiceDependency,
    current_user: CurrentUser
):
    return await lesson_service.get(
        LessonGetQuery(
            id=lesson_id,
            viewer_id=current_user
        )
    )
    

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=LessonUploadUrl)
async def create_lesson(
    lesson: LessonCreateSchema,
    lesson_service: LessonServiceDependency,
    current_user: CurrentUser
):
    
    return await lesson_service.init_lesson_create(
        LessonCreate(
            title=lesson.title,
            description=lesson.description,
            module_id=lesson.module_id,
            created_by=current_user,
        ),
        FileMetadata(
            filename=lesson.filename,
            content_type=lesson.content_type,
            size=lesson.file_size
        )
    )
    

@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: LessonID,
    lesson_service: LessonServiceDependency,
    current_user: CurrentUser
):
    
    return await lesson_service.delete(
        LessonDelete(
            id=lesson_id,
            deleted_by=current_user
        )
    )
    

@router.patch("/{lesson_id}/update", response_model=LessonUpdateSchema)
async def lesson_update(
    lesson_id: LessonID,
    lesson: LessonUpdateSchema,
    lesson_service: LessonServiceDependency,
    current_user: CurrentUser
):
    return await lesson_service.update(
        LessonUpdate(
            title=lesson.title,
            description=lesson.description,
            id=lesson_id,
            updated_by=current_user,
        )
    )
    

@router.patch("/{lesson_id}/update-position", response_model=str)
async def update_lesson_position(
    lesson_id: LessonID,
    participants: LessonReorderParticipantsCore,
    lesson_service: LessonServiceDependency,
    current_user: CurrentUser
):
    
    return await lesson_service.reorder(
        LessonReorderParticipants(
            preceding_id=participants.preceding_id,
            target_id=lesson_id,
            succeeding_id=participants.succeeding_id,
            updated_by=current_user
        )
    )
    
