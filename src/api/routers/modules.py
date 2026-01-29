from fastapi import APIRouter, status
from src.commands.base import ModuleID
from src.commands.modules import ModuleCreate, ModuleUpdate, ModuleDelete, ModuleGetQuery, ReArrangeModule
from src.api.schemas.modules import ModuleOutSchema, ModuleCreateSchema, ModuleUpdateSchema, ReArrangeModuleSchema
from src.api.dependencies import CurrentUser, ModuleServiceDependency


router = APIRouter(prefix="/modules", tags=["Modules"])


@router.get("/{module_id}", response_model=ModuleOutSchema)
async def get_module(
    module_id: ModuleID,
    module_service: ModuleServiceDependency,
    current_user: CurrentUser
):
    
    return await module_service.get(
        ModuleGetQuery(
            id=module_id,
            viewer_id=current_user
        )
    )


@router.post("/", response_model=ModuleOutSchema, status_code=status.HTTP_201_CREATED)
async def create_module(
    module: ModuleCreateSchema,
    module_service: ModuleServiceDependency,
    current_user: CurrentUser
):
    return await module_service.create(
        ModuleCreate(
            **module.model_dump(),
            created_by=current_user
        )
    )    
    
    
@router.patch("/{module_id}", response_model=ModuleUpdateSchema)
async def update_module(
    module_id: ModuleID,
    module: ModuleUpdateSchema,
    module_service: ModuleServiceDependency,
    current_user: CurrentUser
):

    return await module_service.update(
        ModuleUpdate(
            updated_by=current_user,
            id=module_id,
            **module.model_dump()
        )
    )
    
@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: ModuleID,
    module_service: ModuleServiceDependency,
    current_user: CurrentUser
):
    return await module_service.delete(
        ModuleDelete(
            id=module_id,
            deleted_by=current_user
        )
    )


@router.patch("/{module_id}/update-position", status_code=status.HTTP_204_NO_CONTENT)
async def update_module_position(
    module_id: ModuleID,
    rearrange_schema: ReArrangeModuleSchema,
    module_service: ModuleServiceDependency,
    current_user: CurrentUser
):
    
    await module_service.rearrange_sequence(
        ReArrangeModule(
            **rearrange_schema.model_dump(),
            target_id=module_id,
            updated_by=current_user
        )
    )
    





