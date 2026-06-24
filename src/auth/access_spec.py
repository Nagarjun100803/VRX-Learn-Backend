from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Type, Union

from asyncpg import Connection
from pypika import Parameter, functions
from pypika.dialects import PostgreSQLQuery
from pypika.terms import Criterion, ExistsCriterion, ValueWrapper

from src.auth.permission_policy import Entity
from src.command.commands.enrollments import EnrollmentStatus
from src.database import AsyncPgDBManager, ExecutableSQL
from src.query_builder import (
    assignment_submission_table,
    assignment_table,
    course_table,
    enrollment_table,
    lesson_table,
    module_table,
    user_table,
)


class AccessSpec(ABC):
    """
    Abstract base class for entity-specific access control.

    Each entity type (Course, Lesson, Assignment, etc.) has its own AccessSpec
    implementation that defines how to check if a user has access to that entity.

    AccessSpec queries the database to verify the access relationship between a user
    and an entity. It answers: **"Does user X have access to entity Y?**"

    The access check is purely relational - it verifies the existence of a relationship
    (trainer, enrollment, ownership, etc.) **`without checking if the entity exists`**.
    Entity existence should be verified at the service layer.

        Attributes:
            user_id (int): The user attempting to access the entity
            entity_id (int): The entity being accessed
            db (AsyncPgDBManager): Database manager for executing queries
    """

    def __init__(self, user_id: int, entity_id: int, db: AsyncPgDBManager) -> None:

        self.user_id = user_id
        self.entity_id = entity_id
        self.db = db

    @abstractmethod
    def get_executable(self) -> ExecutableSQL:
        """
        Return the SQL query that checks access for this entity.

        Should return a query that:
        - Checks if user_id has access to entity_id
        - Returns a row if access granted, NULL if denied
        """
        ...

    async def has_access(self, connection: Optional[Connection] = None) -> bool:
        """
        Execute the access check query and return boolean result.

        Args:
            connection: Optional connection for transactional context

        Returns:
            True if user has access, False otherwise
        """

        executable = self.get_executable()
        res = await self.db.execute(
            executable, fetch_returns="one", connection=connection
        )
        return res is not None


class UserAccessSpec(AccessSpec):
    """
    Access control for User entities.

    A user can access another user if they are:
    - The user themselves, OR
    - The user who created them

    Use cases:
        - User viewing their own profile
        - Admin viewing a user they created
    """

    def get_executable(self):

        sql = (
            PostgreSQLQuery.from_(user_table)
            .where(
                Criterion.all(
                    terms=[
                        user_table.id == Parameter("$1"),
                        Criterion.any(
                            terms=[
                                user_table.created_by == Parameter("$2"),
                                user_table.id == Parameter("$2"),
                            ]
                        ),
                    ]
                )
            )
            .select(ValueWrapper(1))
            .get_sql()
        )

        return ExecutableSQL(sql=sql, values=(self.entity_id, self.user_id))


AllowedEnrollmentStatus: list[str] = [
    EnrollmentStatus.COMPLETED,
    EnrollmentStatus.IN_PROGRESS,
]
"""The enrollment statuses that allow access to course content. """


def get_course_access_check():
    trainer_check = course_table.trainer_id == Parameter("$2")
    enrollment_check = (
        PostgreSQLQuery.from_(enrollment_table)
        .where(
            Criterion.all(
                terms=[
                    enrollment_table.course_id == course_table.id,
                    enrollment_table.user_id == Parameter("$2"),
                    enrollment_table.deleted_at.isnull(),
                    enrollment_table.status.isin(AllowedEnrollmentStatus),
                    Criterion.any(
                        terms=[
                            enrollment_table.expire_at.isnull(),
                            enrollment_table.expire_at >= functions.Now(),
                        ]
                    ),
                ]
            )
        )
        .select(ValueWrapper(1))
    )

    enrollment_exists = ExistsCriterion(enrollment_check)

    access_check = Criterion.any(terms=[trainer_check, enrollment_exists])

    return access_check


class CourseAccessSpec(AccessSpec):
    """
    Access control for Course entities.

    #### A user can access a course if they are:
    - The course trainer (creator), OR
    - A student enrolled in the course with active, non-expired enrollment

    Enrollment status must be ACTIVE or COMPLETED.
    Enrollment must not be soft-deleted.
    Enrollment must not be expired (or have no expiration).

    Use cases:
        - Student viewing their enrolled course
        - Trainer viewing their own course
        - Trainer grading student work in their course

    """

    def get_executable(self):

        sql = (
            PostgreSQLQuery.from_(course_table)
            .where(
                Criterion.all(
                    terms=[
                        course_table.id == Parameter("$1"),
                        get_course_access_check(),
                    ]
                )
            )
            .select(ValueWrapper(1))
            .get_sql()
        )

        executable = ExecutableSQL(sql=sql, values=(self.entity_id, self.user_id))
        return executable


class ModuleAccessSpec(AccessSpec):
    """
    Access control for Module entities.

    A user can access a module if they can access the parent course.
    Inherits course access rules: trainer or enrolled student.

    Module access is hierarchical: module -> course -> enrollment/trainer check.

    Use cases:
        - Student viewing modules in their enrolled course
        - Trainer viewing modules they created in their course
    """

    def get_executable(self):
        sql = (
            PostgreSQLQuery.from_(course_table)
            .left_join(module_table)
            .on(course_table.id == module_table.course_id)
            .where(
                Criterion.all(
                    terms=[
                        module_table.id == Parameter("$1"),
                        get_course_access_check(),
                    ]
                )
            )
            .select(ValueWrapper(1))
        ).get_sql()

        return ExecutableSQL(sql=sql, values=(self.entity_id, self.user_id))


class LessonAccessSpec(AccessSpec):
    """
    Access control for Lesson entities.

    A user can access a lesson if they can access the parent course.
    Inherits course access rules: trainer or enrolled student.

    Lesson access is hierarchical: lesson -> module -> course -> enrollment/trainer check.

    Use cases:
        - Student viewing lessons in their enrolled course
        - Trainer viewing lessons they created
        - Student watching lesson videos
    """

    def get_executable(self):

        sql = (
            PostgreSQLQuery.from_(course_table)
            .join(module_table)
            .on(course_table.id == module_table.course_id)
            .left_join(lesson_table)
            .on(module_table.id == lesson_table.module_id)
            .where(
                Criterion.all(
                    terms=[
                        lesson_table.id == Parameter("$1"),
                        get_course_access_check(),
                    ]
                )
            )
            .select(ValueWrapper(1))
        ).get_sql()

        return ExecutableSQL(sql=sql, values=(self.entity_id, self.user_id))


class AssignmentAccessSpec(AccessSpec):
    """
    Access control for Assignment entities.

    A user can access an assignment if they are:
    - The course trainer, OR
    - A student enrolled in the parent course with active, non-expired enrollment

    Assignment access is hierarchical: assignment -> course -> enrollment/trainer check.

    Use cases:
        - Student viewing assignments in their course
        - Trainer creating and grading assignments
        - Student submitting assignment work
    """

    def get_executable(self):
        sql = (
            PostgreSQLQuery.from_(assignment_table)
            .left_join(course_table)
            .on(assignment_table.course_id == course_table.id)
            .where(
                Criterion.all(
                    terms=[
                        assignment_table.id == Parameter("$1"),
                        get_course_access_check(),
                    ]
                )
            )
            .select(ValueWrapper(1))
        ).get_sql()

        return ExecutableSQL(sql=sql, values=(self.entity_id, self.user_id))


class AssignmentSubmissionAccessSpec(AccessSpec):
    """
    Access control for AssignmentSubmission entities.

    A user can access a submission if they are:
    - The submission author (student who submitted it), OR
    - The trainer of the course containing the assignment

    Submission access does not require enrollment status check - it's based on
    authorship or teaching relationship.

    Use cases:
        - Student viewing their own submission and feedback
        - Trainer viewing and grading a student's submission
    """

    def get_executable(self):

        sql = (
            PostgreSQLQuery.from_(course_table)
            .join(assignment_table)
            .on(assignment_table.course_id == course_table.id)
            .left_join(assignment_submission_table)
            .on(assignment_submission_table.assignment_id == assignment_table.id)
            .where(
                Criterion.all(
                    terms=[
                        assignment_submission_table.id == Parameter("$1"),
                        Criterion.any(
                            terms=[
                                course_table.trainer_id == Parameter("$2"),
                                assignment_submission_table.created_by
                                == Parameter("$2"),
                            ]
                        ),
                    ]
                )
            )
            .select(ValueWrapper(1))
        ).get_sql()

        return ExecutableSQL(sql=sql, values=(self.entity_id, self.user_id))


class EnrollmentAccessSpec(AccessSpec):
    """
    Access control for Enrollment entities.

    A user can access an enrollment if they are:
    - The enrolled student (themselves), OR
    - The trainer of the course

    Enrollment access allows viewing enrollment status, progress, and management.
    Does not check enrollment status or expiration - the enrollment record itself
    is the source of truth for those attributes.

    Use cases:
        - Student viewing their own enrollment status
        - Trainer viewing student enrollments in their course
        - Admin managing course enrollments
    """

    def get_executable(self):

        sql = (
            PostgreSQLQuery.from_(enrollment_table)
            .left_join(course_table)
            .on(enrollment_table.course_id == course_table.id)
            .where(
                Criterion.all(
                    terms=[
                        enrollment_table.id == Parameter("$1"),
                        Criterion.any(
                            terms=[
                                course_table.trainer_id == Parameter("$2"),
                                enrollment_table.user_id == Parameter("$2"),
                            ]
                        ),
                    ]
                )
            )
            .select(ValueWrapper(1))
        ).get_sql()

        return ExecutableSQL(sql=sql, values=(self.entity_id, self.user_id))


@dataclass
class SpecType:
    """
    Encapsulates access control metadata for a specific system entity.

    This class maps a high-level entity (e.g., a Lesson) to the specific
    logic class responsible for evaluating permissions and defines its
    position within the system's authorization hierarchy.

    Attributes:
        type: The specific subclass of AccessSpec that contains the
            permission logic for this entity.
        parent: The AccessSpec type of the logical parent container
            (e.g., a Course is the parent of a Module), used for
            permission inheritance.
    """

    type: Type[AccessSpec]
    parent: Optional[Type[AccessSpec]]


AccessSpecMapper: dict[Entity, SpecType] = {
    Entity.USER: SpecType(type=UserAccessSpec, parent=None),
    Entity.COURSE: SpecType(type=CourseAccessSpec, parent=None),
    Entity.ENROLLMENT: SpecType(type=EnrollmentAccessSpec, parent=None),
    Entity.MODULE: SpecType(type=ModuleAccessSpec, parent=CourseAccessSpec),
    Entity.LESSON: SpecType(type=LessonAccessSpec, parent=ModuleAccessSpec),
    Entity.ASSIGNMENT: SpecType(type=AssignmentAccessSpec, parent=CourseAccessSpec),
    Entity.ASSIGNMENT_SUBMISSION: SpecType(
        type=AssignmentSubmissionAccessSpec, parent=AssignmentAccessSpec
    ),
}


def get_spec_type(entity: Union[Entity, str]) -> SpecType:
    """
    Retrieves the access specification configuration for a given entity.

    This function looks up the mapping between a logical entity (e.g., Entity.LESSON)
    and its corresponding SpecType, which defines the class responsible for
    handling access logic and its parent relationship in the hierarchy.

    Args:
        entity: The entity to look up. Can be an instance of the Entity
            enum or a string matching an enum member name.

    Returns:
        SpecType: An object containing the AccessSpec class type and its
            optional parent AccessSpec type.

    Raises:
        ValueError: If a string is provided that does not correspond to a
            valid Entity member.

    Example:
        >>> spec = get_spec_type("Entity.MODULE")
        >>> print(spec.parent)
        <class 'CourseAccessSpec'>
    """

    spec_type = AccessSpecMapper.get(Entity(entity))
    if spec_type is None:
        raise ValueError(f"Unknown entity: {entity}")
    return spec_type
