from fastapi import APIRouter
from src.command.commands.base import MediaID
from src.api.dependencies import MediaServiceDependency, CurrentUser
from src.command.commands.media import MediaStatus, MediaStatusUpdate, MediableType


from pydantic import BaseModel

class MediaOut(BaseModel):
    id: MediaID
    status: MediaStatus
    filename: str
    mediable_id: int
    mediable_type: MediableType

router = APIRouter(prefix="/media", tags=["Media"])


@router.patch("/{media_id}/update-status", response_model=MediaOut)
async def update_status(
    media_id: MediaID,
    media_service : MediaServiceDependency,
    current_user: CurrentUser
):
    return await media_service.update(
        MediaStatusUpdate(
            id=media_id,
            status=MediaStatus.UPLOADED,
            updated_by=current_user
        )
    )