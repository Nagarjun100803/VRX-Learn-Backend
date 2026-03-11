from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, FutureDatetime
from typing import Optional, Annotated
from src.command.commands.base import UserID, CourseID, EnrollmentBase, AuditFields, NullField
from src.command.commands.validator import UpdateValidatorMixin



class EnrollmentStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    SUSPENDED = "suspended"
    DROPPED = "dropped"
    COMPLETED = "completed"


class EnrollmentCore(BaseModel):
    user_id: UserID
    course_id: CourseID
    status: EnrollmentStatus = EnrollmentStatus.IN_PROGRESS    


class EnrollmentCreateCore(EnrollmentCore):
    expire_at: Optional[FutureDatetime] = None
    

class EnrollmentCreate(EnrollmentCreateCore):
    created_by: UserID
    
class EnrollmentUpdateCore(UpdateValidatorMixin, BaseModel):

    # NOTE: When updating expire_at it is not necessary to provide a future date,
    # because to make the enrollment expire, we can set expire_at to the current date or a past date.
    
    status: Annotated[Optional[EnrollmentStatus], NullField]
    expire_at: Annotated[Optional[datetime], NullField]
    

class EnrollmentUpdate(EnrollmentUpdateCore, EnrollmentBase):
    updated_by: UserID
    

class EnrollmentDelete(EnrollmentBase):
    deleted_by: UserID
    

class EnrollmentGet(EnrollmentBase):
    viewer_id: UserID


class Enrollment(AuditFields, EnrollmentCore, EnrollmentBase):
    expire_at: Optional[datetime] = None