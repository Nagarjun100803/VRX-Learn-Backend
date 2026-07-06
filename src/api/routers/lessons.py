from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.api.authorize import Authorize, AuthorizeOn
from src.api.dependencies import CurrentUser, LessonServiceDependency
from src.api.docs.lessons import (
    CREATE_LESSON,
    DELETE_LESSON,
    GET_LESSON,
    LESSON_UPDATE,
    UPDATE_LESSON_POSITION,
)
from src.api.schemas.lessons import LessonCreateSchema, LessonUpdateSchema
from src.command.commands.base import AttachmentUploadContext, LessonID, UserID
from src.command.commands.lessons import (
    LessonAttachmentStatusUpdate,
    LessonContext,
    LessonCreate,
    LessonDelete,
    LessonGetQuery,
    LessonReorderParticipants,
    LessonReorderParticipantsCore,
    LessonUpdate,
    LessonWithMedia,
)

router = APIRouter(prefix="/lessons", tags=["Lessons"])


type AuthorizeLessonCreate = Annotated[
    UserID,
    Depends(
        Authorize(
            on=AuthorizeOn.LESSON_CREATE,
            parent_id_field="module_id",
            allowed_user_roles={"admin", "trainer"},
        )
    ),
]

type AuthorizeLessonUpdate = Annotated[
    UserID,
    Depends(
        Authorize(
            on=AuthorizeOn.LESSON_UPDATE,
            entity_id_field="lesson_id",
            allowed_user_roles={"admin", "trainer"},
        )
    ),
]

type AuthorizeLessonDelete = Annotated[
    UserID,
    Depends(
        Authorize(
            on=AuthorizeOn.LESSON_DELETE,
            entity_id_field="lesson_id",
            allowed_user_roles={"admin", "trainer"},
        )
    ),
]

type AuthorizeLessonView = Annotated[
    UserID, Depends(Authorize(on=AuthorizeOn.LESSON_VIEW, entity_id_field="lesson_id"))
]


@router.get("/{lesson_id}", response_model=LessonWithMedia, **GET_LESSON)
async def get_lesson(
    lesson_id: LessonID,
    lesson_service: LessonServiceDependency,
    current_user: AuthorizeLessonView,
):
    return await lesson_service.get_with_media(
        LessonGetQuery(id=lesson_id, viewer_id=current_user)
    )


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentUploadContext[LessonContext],
    **CREATE_LESSON,
)
async def create_lesson(
    lesson: LessonCreateSchema,
    lesson_service: LessonServiceDependency,
    current_user: AuthorizeLessonCreate,
):

    return await lesson_service.create(
        cmd=LessonCreate(
            module_id=lesson.module_id,
            **lesson.lesson.model_dump(),
            created_by=current_user,
        ),
        attachment=lesson.attachment,
    )


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT, **DELETE_LESSON)
async def delete_lesson(
    lesson_id: LessonID,
    lesson_service: LessonServiceDependency,
    current_user: AuthorizeLessonDelete,
):

    return await lesson_service.delete(
        LessonDelete(id=lesson_id, deleted_by=current_user)
    )


@router.patch("/{lesson_id}", response_model=LessonUpdateSchema, **LESSON_UPDATE)
async def lesson_update(
    lesson_id: LessonID,
    lesson: LessonUpdateSchema,
    lesson_service: LessonServiceDependency,
    current_user: AuthorizeLessonUpdate,
):
    return await lesson_service.update(
        LessonUpdate(
            title=lesson.title,
            description=lesson.description,
            is_preview=lesson.is_preview,
            id=lesson_id,
            updated_by=current_user,
        )
    )


@router.patch("/{lesson_id}/position", response_model=str, **UPDATE_LESSON_POSITION)
async def update_lesson_position(
    lesson_id: LessonID,
    participants: LessonReorderParticipantsCore,
    lesson_service: LessonServiceDependency,
    current_user: AuthorizeLessonUpdate,
):

    return await lesson_service.reorder(
        LessonReorderParticipants(
            preceding_id=participants.preceding_id,
            target_id=lesson_id,
            succeeding_id=participants.succeeding_id,
            updated_by=current_user,
        )
    )


@router.patch(
    "/{lesson_id}/attachment/uploaded", status_code=status.HTTP_204_NO_CONTENT
)
async def update_attachment_status(
    lesson_id: LessonID,
    lesson_service: LessonServiceDependency,
    current_user: AuthorizeLessonUpdate,
):
    await lesson_service.mark_attachment_as_uploaded(
        LessonAttachmentStatusUpdate(id=lesson_id, updated_by=current_user)
    )


@router.get("/{lesson_id}/attachment/view-url", response_model=str)
async def get_view_url(
    lesson_id: LessonID,
    lesson_service: LessonServiceDependency,
    current_user: AuthorizeLessonView,
):
    return await lesson_service.get_attachment_view_url(
        LessonGetQuery(id=lesson_id, viewer_id=current_user)
    )


@router.get("/{lesson_id}/attachment/preview-url", response_model=str)
async def get_preview_url(
    lesson_id: LessonID,
    lesson_service: LessonServiceDependency,
    current_user: CurrentUser,
):
    return await lesson_service.get_lesson_attachment_preview_url(
        LessonGetQuery(id=lesson_id, viewer_id=current_user)
    )
