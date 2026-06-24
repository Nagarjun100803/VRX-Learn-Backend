from src.command.commands.base import BaseCmd, EnrollmentID, ModuleID, UserID


class ModuleRestrictionBase(BaseCmd):
    enrollment_id: EnrollmentID
    module_ids: set[ModuleID]


class ModuleRestrictionCreate(ModuleRestrictionBase):
    created_by: UserID


class ModuleRestrictionDelete(ModuleRestrictionBase):
    deleted_by: UserID


class ModuleRestrictionSync(ModuleRestrictionBase):
    by: UserID
