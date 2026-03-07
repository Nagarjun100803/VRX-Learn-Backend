from typing import Optional, Type, Union
from asyncpg import Connection
from abc import ABC, abstractmethod
from src.auth.permission_policy import Entity
from src.query_builder.base import BaseExecutableSQL
from src.database import AsyncPgDBManager
from src.commands.enrollments import EnrollmentStatus



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
    
    def __init__(
        self, 
        user_id: int, 
        entity_id: int,
        db: AsyncPgDBManager
    ) -> None:

        self.user_id = user_id
        self.entity_id = entity_id
        self.db = db
    
        
    
    @abstractmethod
    def get_executable(self) -> BaseExecutableSQL:
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
        res = await self.db.execute(executable, fetch_returns="one", connection=connection)
        return bool(res) 
        
    
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
        
        sql = """
            SELECT
                1
            WHERE EXISTS(
                SELECT
                    1
                FROM
                    users AS u
                WHERE
                    u.id = $1 AND 
                    (
                        u.created_by = $2 OR
                        u.id = $3
                    )   
                );
        """
        
        return self.db.query_builder.build_executable(
            sql, values=(self.entity_id, self.user_id, self.user_id)
        )


AllowedEnrollmentStatus: list[str] = [
    EnrollmentStatus.COMPLETED.value,
    EnrollmentStatus.IN_PROGRESS.value
]
"""The enrollment statuses that allow access to course content. """


    
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
        sql = """
            SELECT
                1
            WHERE EXISTS(
                SELECT
                    1
                FROM
                    courses AS c
                WHERE
                    c.id = $1 AND
                    (
                        -- Case 1: User is Trainer.
                        c.trainer_id = $2 OR 
                        
                        -- Case 2: User is Trainee.
                        EXISTS(
                            SELECT
                                1
                            FROM
                                enrollments AS e
                            WHERE
                                e.course_id = c.id AND
                                e.user_id = $3 AND 
                                e.deleted_at IS NULL AND
                                e.status = ANY($4::text[]) AND
                                (
                                    e.expire_at IS NULL OR
                                    e.expire_at > NOW()
                                )
                        )
                    )
            )
        """
        return self.db.query_builder.build_executable(
            sql=sql, 
            values=(self.entity_id, self.user_id, self.user_id, AllowedEnrollmentStatus
            )
        )
    
        
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
        sql = """
            SELECT
                1
            WHERE EXISTS(
                SELECT
                    1
                FROM
                    courses AS c
                LEFT JOIN
                    modules AS m
                ON
                    c.id = m.course_id
                WHERE
                    m.id = $1 AND
                    (
                        -- Case 1: User is Trainer.
                        c.trainer_id = $2 OR
                        
                        -- Case 2: User is Trainee.
                        EXISTS(
                            SELECT
                                1
                            FROM
                                enrollments AS e
                            WHERE
                                e.user_id = $3 AND 
                                e.course_id = m.course_id AND
                                e.deleted_at IS NULL AND
                                e.status = ANY($4::text[]) AND
                                (
                                    e.expire_at IS NULL OR
                                    e.expire_at > NOW()
                                )
                        )
                        
                )
            )
        """
    
        return self.db.query_builder.build_executable(
            sql=sql,
            values=(self.entity_id, self.user_id, self.user_id, AllowedEnrollmentStatus)
        )
        

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
        sql = """
            SELECT
                1
            WHERE EXISTS(
                SELECT
                    1
                FROM
                    courses AS c
                JOIN
                    modules AS m
                ON
                    c.id = m.course_id
                LEFT JOIN
                    lessons AS l
                ON
                    m.id = l.module_id
                WHERE
                    l.id = $1 AND
                    (
                        -- Case 1: User is Trainer.
                        c.trainer_id = $2 OR
                        
                        -- Case 2: User is Trainee.
                        EXISTS(
                            SELECT
                                1
                            FROM
                                enrollments AS e
                            WHERE
                                e.course_id = c.id AND
                                e.user_id = $3 AND
                                e.deleted_at IS NULL AND
                                e.status = ANY($4::text[]) AND
                                (
                                    e.expire_at IS NULL OR
                                    e.expire_at > NOW()
                                )
                        )
                    )
                    
            )
        """
        return self.db.query_builder.build_executable(
            sql=sql,
            values=(self.entity_id, self.user_id, self.user_id, AllowedEnrollmentStatus)
        )
        

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
        sql = """
            SELECT
                1
            WHERE EXISTS(
                SELECT
                    1
                FROM
                    courses AS c
                LEFT JOIN
                    assignments AS a
                ON
                    c.id = a.course_id
                WHERE
                    a.id = $1 AND
                    (
                        -- Case 1: User is a Trainer.
                        c.trainer_id = $2 OR
                        
                        -- Case 2: User is a Trainee.
                        EXISTS(
                            SELECT
                                1
                            FROM
                                enrollments AS e
                            WHERE
                                e.course_id = a.course_id AND
                                e.user_id = $3 AND
                                e.deleted_at IS NULL AND
                                e.status = ANY($4::text[]) AND
                                (
                                    e.expire_at IS NULL OR
                                    e.expire_at > NOW()
                                )
                        )
                    )
            )
        """
        
        return self.db.query_builder.build_executable(
            sql=sql,
            values=(self.entity_id, self.user_id, self.user_id, AllowedEnrollmentStatus)
        )
        
        
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
        sql = """
            SELECT
                1
            WHERE EXISTS(
                SELECT
                    1
                FROM
                    courses AS c
                JOIN
                    assignments AS a
                ON
                    c.id = a.course_id
                LEFT JOIN
                    assignment_submissions AS asub
                ON
                    a.id = asub.assignment_id
                WHERE
                    asub.id = $1 AND
                    (
                        -- Case 1: User is Trainer.
                        c.trainer_id = $2 OR
                        
                        -- Case 2: User is Trainee.
                        asub.created_by = $3
                    )
                
            )
        """
        return self.db.query_builder.build_executable(
            sql=sql,
            values=(self.entity_id, self.user_id,self.user_id)
        )
        

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
        sql = """
            SELECT
                1
            WHERE EXISTS(
                SELECT
                    1
                FROM
                    enrollments AS e
                LEFT JOIN
                    courses AS c
                ON
                    c.id = e.course_id
                WHERE
                    e.id = $1 AND
                    (
                        -- Case 1: User is Trainer.
                        c.trainer_id = $2 OR
                        
                        -- Case 2: User is Trainee.
                        e.user_id = $3
                    )
            )
        """
        
        return self.db.query_builder.build_executable(
            sql=sql,
            values=(self.entity_id, self.user_id, self.user_id)
        )
        
        

from dataclasses import dataclass

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
    Entity.ASSIGNMENT_SUBMISSION: SpecType(type=AssignmentSubmissionAccessSpec, parent=AssignmentAccessSpec)
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
    
    return AccessSpecMapper.get(Entity(entity))