from datetime import datetime
from typing import Optional

from src.command.commands.base import BaseCmd, ModuleID
from src.command.commands.enrollments import (
    EnrollmentBase,
    EnrollmentCore,
    EnrollmentCreateCore,
    EnrollmentUpdateCore,
)


class EnrollmentCreateSchema(EnrollmentCreateCore):
    restricted_module_ids: set[ModuleID]


class RestrictedModuleIds(BaseCmd):
    module_ids: set[int]


class EnrollmentUpdateSchema(EnrollmentUpdateCore): ...


class EnrollmentOut(EnrollmentCore, EnrollmentBase):
    expire_at: Optional[datetime] = None
