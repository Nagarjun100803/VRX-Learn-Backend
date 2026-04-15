from datetime import UTC, datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import Field

from src.command.commands.base import (
    AssignmentID,
    AssignmentSubmissionID,
    BaseCmd,
    CourseID,
    EnrollmentID,
    LessonID,
    ModuleID,
    UserID,
)
from src.command.commands.users import Email, UserRole


class BaseEvent(BaseCmd):
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    event_type: str


class UserCreatedEvent(BaseEvent):
    event_type: str = "user.created"
    id: UserID
    username: str
    email: Email
    role: UserRole
    created_by: Optional[UserID] = None


class UserDeletedEvent(BaseEvent):
    event_type: str = "user.deleted"
    id: UserID
    deleted_by: UserID


class CourseCreatedEvent(BaseEvent):
    event_type: str = "course.created"
    id: CourseID
    trainer_id: UserID
    created_by: UserID


class CourseUpdatedEvent(BaseEvent):
    event_type: str = "course.updated"
    id: CourseID
    trainer_id: UserID
    updated_by: UserID


class CourseDeletedEvent(BaseEvent):
    event_type: str = "course.deleted"
    id: CourseID
    trainer_id: UserID
    deleted_by: UserID


class EnrollmentCreatedEvent(BaseEvent):
    event_type: str = "enrollment.created"
    id: EnrollmentID
    user_id: UserID
    course_id: CourseID
    created_by: UserID


class EnrollmentUpdatedEvent(BaseEvent):
    event_type: str = "enrollment.updated"
    id: EnrollmentID
    user_id: UserID
    course_id: CourseID
    updated_by: UserID


class EnrollmentDeletedEvent(BaseEvent):
    event_type: str = "enrollment.deleted"
    id: EnrollmentID
    user_id: UserID
    course_id: CourseID
    deleted_by: UserID


class ModuleCreatedEvent(BaseEvent):
    event_type: str = "module.created"
    id: ModuleID
    course_id: CourseID
    created_by: UserID


class ModuleUpdatedEvent(BaseEvent):
    event_type: str = "module.updated"
    id: ModuleID
    course_id: CourseID | None
    updated_by: UserID


class ModuleReorderedEvent(BaseEvent):
    event_type: str = "module.reordered"
    id: ModuleID
    updated_by: UserID


class ModuleDeletedEvent(BaseEvent):
    event_type: str = "module.deleted"
    id: ModuleID
    course_id: CourseID
    deleted_by: UserID


class LessonCreatedEvent(BaseEvent):
    event_type: str = "lesson.created"
    id: LessonID
    module_id: ModuleID
    created_by: UserID


class LessonUpdatedEvent(BaseEvent):
    event_type: str = "lesson.updated"
    id: LessonID
    module_id: ModuleID
    updated_by: UserID


class LessonReorderedEvent(BaseEvent):
    event_type: str = "lesson.reordered"
    id: LessonID
    updated_by: UserID


class LessonDeletedEvent(BaseEvent):
    event_type: str = "lesson.deleted"
    id: LessonID
    module_id: ModuleID
    deleted_by: UserID


class AssignmentCreatedEvent(BaseEvent):
    event_type: str = "assignment.created"
    id: AssignmentID
    course_id: CourseID
    created_by: UserID


class AssignmentUpdatedEvent(BaseEvent):
    event_type: str = "assignment.updated"
    id: AssignmentID
    course_id: CourseID
    updated_by: UserID


class AssignmentDeletedEvent(BaseEvent):
    event_type: str = "assignment.deleted"
    id: AssignmentID
    course_id: CourseID
    deleted_by: UserID


class AssignmentSubmissionCreatedEvent(BaseEvent):
    event_type: str = "assignment.submission.created"
    id: AssignmentSubmissionID
    assignment_id: AssignmentID
    created_by: UserID
