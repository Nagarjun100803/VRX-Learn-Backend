from typing import Optional
from datetime import datetime
from src.command.commands.enrollments import (
    EnrollmentBase, EnrollmentCore, 
    EnrollmentUpdateCore, EnrollmentCreateCore
)

class EnrollmentCreateSchema(EnrollmentCreateCore): ...

class EnrollmentUpdateSchema(EnrollmentUpdateCore): ...

class EnrollmentOut(EnrollmentCore, EnrollmentBase):
    expire_at: Optional[datetime] = None
