from datetime import date, datetime
from typing import Annotated, Literal, Optional
from unittest.mock import Base

from pydantic import Field, model_validator

from src.command.commands.assignment_submissions import AssignmentSubmissionStatus, Attempt, Score
from src.command.commands.assignments import AssignmentTitle, MaxScore, NumberOfAttempts
from src.command.commands.base import AssignmentID, AssignmentSubmissionID,  CourseID, EnrollmentID, LessonID, MediaID, ModuleID, UserID
from src.command.commands.courses import CourseTitle
from src.command.commands.enrollments import EnrollmentStatus
from src.command.commands.lessons import LessonTitle
from src.command.commands.media import AllowedContentTypes
from src.command.commands.modules import ModuleTitile
from src.command.commands.users import Email, UserRole
from src.query.dto.base import BaseDTO, PageMeta



class ModuleDetail(BaseDTO):
    id: ModuleID
    title: ModuleTitile
    


class LessonDetail(BaseDTO):
    id: LessonID
    title: LessonTitle
    media_id: MediaID
    mime_type: AllowedContentTypes
    
    

class AssignmentDetail(BaseDTO):
    id: AssignmentID
    title: AssignmentTitle
    
    

class AssignmentDetailWithDue(AssignmentDetail):
    due_date: Optional[datetime] = None


    
class TraineeDetail(BaseDTO):
    trainee_id: UserID
    name: str
    email: Email
    enrollment_date: date
    role: UserRole
    

OptionalOrder = Optional[Literal["asc", "desc"]]
    

class TraineeFilters(BaseDTO):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    sort_by_enrollment_date: OptionalOrder = None
    sort_by_username: OptionalOrder = None


class UserDetail(BaseDTO):
    id: UserID
    name: str
    email: Email
    role: UserRole
    last_login: Optional[date] = None
    # TODO: Need to implement the status in users.
    status: str = "active"
    

class UserFilters(BaseDTO):
    name_or_email: Optional[str] = None
    role: Optional[UserRole] = None
    sort_by_created_at: OptionalOrder = None
    sort_by_username: OptionalOrder = None
    
    
class EnrollmentDetail(BaseDTO):
    id: EnrollmentID
    name: str
    email: Email
    role: UserRole
    course_name: CourseTitle
    enrollment_date: date
    status: EnrollmentStatus
    
    
class EnrollmentFilters(BaseDTO):
    name_or_email: Optional[str] = None
    status: Optional[EnrollmentStatus] = None
    role: Optional[UserRole] = None
    sort_by_enrollment_date: OptionalOrder = None
    sort_by_course_name: OptionalOrder = None


class CourseDetail(BaseDTO):
    id: CourseID
    title: CourseTitle
    short_description: str
    trainer_name: str
    no_of_trainees: Annotated[int, Field(ge=0)]
    created_at: date
    

class CourseFilters(BaseDTO):
    course_name_or_trainer_name: Optional[str] = None
    sort_by_course_name: OptionalOrder = None
    sort_by_created_at: OptionalOrder = None
    sort_by_no_of_trainees: OptionalOrder = None


class AssignmentSubmissionDetail(BaseDTO):
    id: AssignmentSubmissionID
    username: str
    email: Email
    attempt: Attempt
    max_attempt: NumberOfAttempts
    status: AssignmentSubmissionStatus
    score: Optional[Score] = None
    max_score: MaxScore
    submitted_at: datetime
    

class AssignmentSubmissionFilters(BaseDTO):
    from_date: Optional[date] = None
    to_date: date
    status: Optional[AssignmentSubmissionStatus] = None
    sort_by_grade: Optional[Literal["asc", "desc"]] = None
    

class CourseQueryParams(CourseFilters, PageMeta): ...
class EnrollmentQueryParams(EnrollmentFilters, PageMeta): ...
class AssignmentSubmissionQueryParams(AssignmentSubmissionFilters, PageMeta): ...
class UserQueryParams(UserFilters, PageMeta): ...
class TraineeQueryParams(TraineeFilters, PageMeta): ...