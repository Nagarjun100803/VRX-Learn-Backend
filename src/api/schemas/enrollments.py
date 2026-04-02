from datetime import datetime
from typing import Optional

from src.command.commands.enrollments import (
    EnrollmentBase,
    EnrollmentCore,
    EnrollmentCreateCore,
    EnrollmentUpdateCore,
)


class EnrollmentCreateSchema(EnrollmentCreateCore): ...


class EnrollmentUpdateSchema(EnrollmentUpdateCore): ...


class EnrollmentOut(EnrollmentCore, EnrollmentBase):
    expire_at: Optional[datetime] = None
