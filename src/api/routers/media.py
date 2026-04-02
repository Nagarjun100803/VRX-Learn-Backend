from fastapi import APIRouter, Response
from pydantic import BaseModel

from src.api.dependencies import CurrentUser, MediaServiceDependency
from src.command.commands.base import MediaID
from src.command.commands.media import MediableType, MediaStatus, MediaStatusUpdate


class MediaOut(BaseModel):
    id: MediaID
    status: MediaStatus
    filename: str
    mediable_id: int
    mediable_type: MediableType


router = APIRouter(prefix="/media", tags=["Media"])


@router.patch("/{media_id}/update-status", response_model=MediaOut)
async def update_status(
    media_id: MediaID, media_service: MediaServiceDependency, current_user: CurrentUser
):
    return await media_service.update(
        MediaStatusUpdate(
            id=media_id, status=MediaStatus.UPLOADED, updated_by=current_user
        )
    )


@router.get("/{media_id}", response_model=str)
async def get_media_view_url(
    media_id: MediaID, media_service: MediaServiceDependency, current_user: CurrentUser
):
    url = await media_service.get_view_url(
        media_id=media_id, expire_mins=60, connection=None
    )

    return Response(
        content=url,
        headers={
            "Cache-Control": "private, max-age=600"  # Cache for 10 minutes, and allow caching in public caches (like CDNs)
        },
    )
