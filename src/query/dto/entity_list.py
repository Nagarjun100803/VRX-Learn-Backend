from datetime import date, datetime
from typing import Annotated, Literal, Optional

from pydantic import Field

from src.command.commands.assignment_submissions import (
    AssignmentSubmissionStatus,
    Attempt,
    Score,
)
from src.command.commands.assignments import AssignmentTitle, MaxScore, NumberOfAttempts
from src.command.commands.base import (
    AssignmentID,
    AssignmentSubmissionID,
    CourseID,
    EnrollmentID,
    IssueID,
    LessonID,
    MediaID,
    ModuleID,
    UserID,
)
from src.command.commands.courses import CourseTitle
from src.command.commands.enrollments import EnrollmentStatus
from src.command.commands.issues import (
    IssueCategory,
    IssueDescription,
    IssueStatus,
    IssueSubject,
)
from src.command.commands.lessons import LessonDescription, LessonTitle
from src.command.commands.media import AllowedContentTypes
from src.command.commands.modules import ModuleTitle
from src.command.commands.users import Email, UserRole
from src.query.dto.base import BaseDTO, PageMeta


class ModuleDetail(BaseDTO):
    id: ModuleID
    title: ModuleTitle


class LessonDetail(BaseDTO):
    id: LessonID
    title: LessonTitle
    description: Optional[LessonDescription] = None
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
    last_login: Optional[datetime] = None
    created_at: datetime
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
    expire_at: Optional[date] = None
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
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    trainer_id: UserID
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


class IssueDetail(BaseDTO):
    id: IssueID
    subject: IssueSubject
    category: IssueCategory
    description: Optional[IssueDescription] = None
    status: IssueStatus
    submitted_at: datetime
    user_id: UserID
    username: str
    email: Email
    role: UserRole


class IssueFilters(BaseDTO):
    category: Optional[IssueCategory] = None
    status: Optional[IssueStatus] = None
    role: Optional[UserRole] = None


class CourseQueryParams(CourseFilters, PageMeta): ...


class EnrollmentQueryParams(EnrollmentFilters, PageMeta): ...


class AssignmentSubmissionQueryParams(AssignmentSubmissionFilters, PageMeta): ...


class UserQueryParams(UserFilters, PageMeta): ...


class TraineeQueryParams(TraineeFilters, PageMeta): ...


class IssueQueryParams(IssueFilters, PageMeta): ...


class UserSearchDetail(BaseDTO):
    id: UserID
    email: Email
    username: str
    role: UserRole


class CourseSearchDetail(BaseDTO):
    id: CourseID
    title: CourseTitle
