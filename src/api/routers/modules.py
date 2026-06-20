from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.api.authorize import Authorize, AuthorizeOn
from src.api.dependencies import ModuleServiceDependency
from src.api.docs.modules import (
    CREATE_MODULE,
    DELETE_MODULE,
    GET_MODULE,
    UPDATE_MODULE,
    UPDATE_MODULE_POSITION,
)
from src.api.schemas.modules import (
    CourseID,
    ModuleCreateSchema,
    ModuleOutSchema,
    ModuleUpdateSchema,
)
from src.command.commands.base import ModuleID, UserID
from src.command.commands.modules import (
    ModuleCreate,
    ModuleDelete,
    ModuleGetQuery,
    ModuleReorderParticipants,
    ModuleReorderParticipantsCore,
    ModuleUpdate,
)

router = APIRouter(prefix="/modules", tags=["Modules"])


def get_parent_id(module: ModuleCreateSchema) -> CourseID:
    """Extract the parent ID from the module create schema."""
    return module.course_id


type AuthorizeModuleCreate = Annotated[
    UserID,
    Depends(
        Authorize(
            on=AuthorizeOn.MODULE_CREATE,
            parent_id=Depends(get_parent_id),
            allowed_user_roles={"admin", "trainer"},
        )
    ),
]

type AuthorizeModuleUpdate = Annotated[
    UserID,
    Depends(
        Authorize(
            on=AuthorizeOn.MODULE_UPDATE,
            entity_id_field="module_id",
            allowed_user_roles={"admin", "trainer"},
        )
    ),
]

type AuthorizeModuleDelete = Annotated[
    UserID,
    Depends(
        Authorize(
            on=AuthorizeOn.MODULE_DELETE,
            entity_id_field="module_id",
            allowed_user_roles={"admin", "trainer"},
        )
    ),
]

type AuthorizeModuleView = Annotated[
    UserID, Depends(Authorize(on=AuthorizeOn.MODULE_VIEW, entity_id_field="module_id"))
]


@router.get("/{module_id}", response_model=ModuleOutSchema, **GET_MODULE)
async def get_module(
    module_id: ModuleID,
    module_service: ModuleServiceDependency,
    current_user: AuthorizeModuleView,
):
    return await module_service.get(
        ModuleGetQuery(id=module_id, viewer_id=current_user)
    )


@router.post(
    "/",
    response_model=ModuleOutSchema,
    status_code=status.HTTP_201_CREATED,
    **CREATE_MODULE,
)
async def create_module(
    module: ModuleCreateSchema,
    module_service: ModuleServiceDependency,
    current_user: AuthorizeModuleCreate,
):
    return await module_service.create(
        ModuleCreate(**module.model_dump(), created_by=current_user)
    )


@router.patch("/{module_id}", response_model=ModuleUpdateSchema, **UPDATE_MODULE)
async def update_module(
    module_id: ModuleID,
    module: ModuleUpdateSchema,
    module_service: ModuleServiceDependency,
    current_user: AuthorizeModuleUpdate,
):

    return await module_service.update(
        ModuleUpdate(updated_by=current_user, id=module_id, **module.model_dump())
    )


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT, **DELETE_MODULE)
async def delete_module(
    module_id: ModuleID,
    module_service: ModuleServiceDependency,
    current_user: AuthorizeModuleDelete,
):
    return await module_service.delete(
        ModuleDelete(id=module_id, deleted_by=current_user)
    )


@router.patch("/{module_id}/position", response_model=str, **UPDATE_MODULE_POSITION)
async def update_module_position(
    module_id: ModuleID,
    participants: ModuleReorderParticipantsCore,
    module_service: ModuleServiceDependency,
    current_user: AuthorizeModuleUpdate,
):

    return await module_service.reorder(
        ModuleReorderParticipants(
            preceding_id=participants.preceding_id,
            succeeding_id=participants.succeeding_id,
            target_id=module_id,
            updated_by=current_user,
        )
    )
