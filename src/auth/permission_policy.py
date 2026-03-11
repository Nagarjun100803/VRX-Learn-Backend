from enum import StrEnum
from typing import Literal, NamedTuple, FrozenSet, Union
from src.command.commands.users import UserRole

class Entity(StrEnum):
    USER = "user"
    COURSE = "course"
    MODULE = "module"
    LESSON = "lesson"
    ENROLLMENT = "enrollment"
    ASSIGNMENT = "assignment"
    ASSIGNMENT_SUBMISSION = "assignment-submission"

    

class Action(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    

class Policy(NamedTuple):
    name: str
    capabilities: Union[FrozenSet[Action], Literal["*"]]
    scope: Literal["global", "contextual"]
    
    
    def allows(self, action: Union[Action, str]) -> bool:
        if isinstance(self.capabilities, str) and self.capabilities.strip() == "*":
            return True
        return Action(action) in self.capabilities
    


""" Predefined Policies."""
CRUD_ALL = Policy("crud-all", capabilities="*", scope="global")
"""**`CRUD_ALL`** allows all actions such as `create`, `update`, `delete` and `view` globally."""
OWNED_CRUD_ALL = Policy("owned-crud-all", capabilities="*", scope="contextual")
"""**`OWNED_CRUD_ALL`** allows all actions such as `create`, `update`, `delete` and `view` but only on owned resources."""

STAFF_EDIT = Policy("staff-edit", capabilities=frozenset({Action.CREATE, Action.UPDATE, Action.VIEW}), scope="global")
"""**`STAFF_EDIT`** allows `create`, `update` and `view` actions globally but does not allow delete action."""
OWNED_STAFF_EDIT = Policy("owned-staff-edit", capabilities=frozenset({Action.CREATE, Action.UPDATE, Action.VIEW}), scope="contextual")
"""**`OWNED_STAFF_EDIT`** allows `create`, `update` and `view` actions but only on owned resources and does not allow delete action."""

READ_AND_UPDATE = Policy("read-and-update", capabilities=frozenset({Action.VIEW, Action.UPDATE}), scope="global")
"""**`READ_AND_UPDATE`** allows `view` and `update` actions globally."""

OWNED_READ_AND_UPDATE = Policy("owned-read-and-update", capabilities=frozenset({Action.VIEW, Action.UPDATE}), scope="contextual")
"""**`OWNED_READ_AND_UPDATE`** allows `view` and `update` actions but only on owned resources."""

READ_ONLY = Policy("read-only", capabilities=frozenset({Action.VIEW}), scope="global")
"""**`READ_ONLY`** allows only `view` action globally."""

OWNED_READ_ONLY = Policy("owned-read-only", capabilities=frozenset({Action.VIEW}), scope="contextual")
"""**`OWNED_READ_ONLY`** allows only `view` action but only on owned resources."""

CREATE_AND_VIEW = Policy("create-and-view", capabilities=frozenset({Action.CREATE, Action.VIEW}), scope="global")
"""**`CREATE_AND_VIEW`** allows `create` and `view` actions globally but does not allow update and delete actions."""

OWNED_CREATE_AND_VIEW = Policy("owned-create-and-view", capabilities=frozenset({Action.CREATE, Action.VIEW}), scope="contextual")
"""**`OWNED_CREATE_AND_VIEW`** allows `create` and `view` actions but only on owned resources and does not allow update and delete actions."""


POLICY_V1: dict[UserRole, dict[Entity, Policy]] = {
    
    UserRole.SUBADMIN: {
        Entity.USER: STAFF_EDIT,
        Entity.COURSE: READ_AND_UPDATE,
        Entity.ENROLLMENT: STAFF_EDIT,
        Entity.MODULE: STAFF_EDIT,
        Entity.LESSON: STAFF_EDIT,
        Entity.ASSIGNMENT: READ_ONLY,
        Entity.ASSIGNMENT_SUBMISSION: READ_ONLY
    },
    
    UserRole.TRAINER: {
        Entity.USER: OWNED_READ_ONLY,
        Entity.COURSE: OWNED_READ_AND_UPDATE,
        Entity.ENROLLMENT: OWNED_READ_ONLY,
        Entity.MODULE: OWNED_CRUD_ALL,
        Entity.LESSON: OWNED_CRUD_ALL,
        Entity.ASSIGNMENT: OWNED_CRUD_ALL,
        Entity.ASSIGNMENT_SUBMISSION: OWNED_READ_AND_UPDATE
    },
    
    UserRole.TRAINEE: {
        Entity.USER: OWNED_READ_ONLY,
        Entity.ENROLLMENT: OWNED_READ_ONLY,
        Entity.COURSE: OWNED_READ_ONLY,
        Entity.MODULE: OWNED_READ_ONLY,
        Entity.LESSON: OWNED_READ_ONLY,
        Entity.ASSIGNMENT: OWNED_READ_ONLY,
        Entity.ASSIGNMENT_SUBMISSION: OWNED_CREATE_AND_VIEW
    }
    
}
"""
### POLICY_V1: Role-Based Access Control Matrix (Version 1.0)

This is the authoritative permission policy matrix that defines what actions each user role 
can perform on different entities across the platform.

**Scope Semantics:**
    - "global": User can perform the action on ANY resource of this entity type
    - "contextual": User can only perform the action on resources they own or they are linked contextually.
        Case 1: `Owned resources` 
            - A trainer can only edit modules they created.
            - A trainee can update their own profile but not others.
        
        Case 2: `Contextual access`
            - A trainer can view enrollments for courses they teach(even if they didn't create the course).
            - A trainee can view the lessons of the courses they are enrolled in (even if they didn't create the course).
    
**Role Definitions:**

    SUBADMIN (Administration & Support):
        - Can manage users across the platform
        - Can view and update courses (global access)
        - Can manage enrollments (enroll/unenroll students)
        - Can create/update course content (modules, lessons, assignments)
        - Can only VIEW submissions and student work (read-only, no grading authority)
        - Typical use case: Platform administrator, support staff, course coordinator

    TRAINER (Course Instructor/Teacher):
        - Can view and update only their own courses
        - Can manage (create/update/delete) their own course structure
        - Can manage (create/update/delete) their own modules and lessons
        - Can manage (create/update/delete) their own assignments
        - Can view and grade student submissions in their courses
        - Can only view enrollments in their courses
        - Typical use case: Course instructor, course creator

    TRAINEE (Student/Learner):
        - Can view (read-only) their own enrolled courses
        - Can view (read-only) their own course modules, lessons, and assignments
        - Can CREATE new submissions for assignments they are enrolled in
        - Can VIEW only their own submissions (cannot view other students' work)
        - Cannot modify, delete, or view submissions after grading
        - Cannot create, update, or delete any course content
        - Typical use case: Student, course participant, learner

**Authorization Flow:**

    1. Check this policy matrix: Does the user's role allow this action on this entity?
    2. If policy.scope == "contextual": Verify access via AccessSpec (entity must belong to user)
    3. If both checks pass: Authorization granted
    4. Otherwise: ForbiddenError raised

**Important Notes:**

    - This policy is role-based only. access checks happen separately via AccessSpec.
    - TRAINEE submissions follow strict isolation: students can only see/manage their own submissions.
    - TRAINER and SUBADMIN have no DELETE permissions on submissions (soft-delete enforced at service level).
    - All timestamp fields (created_at, updated_at, deleted_at) are managed by the system, not users.
    - This policy supports FERPA compliance (US educational privacy law).

"""

def get_policy(
    user_role: Union[UserRole, str],
    entity: Union[Entity, str]
) -> Policy:
    
    """
        Helper function to retrieve the appropriate Policy based on 
        user role and entity type.
        Args:
            user_role: The role of the user (e.g., "admin", "trainer", "trainee")
            entity: The type of entity being accessed (e.g., "course", "enrollment")
        Returns:
            A Policy object that defines the permissions for the given role and entity.
    """
    
    if UserRole(user_role) == UserRole.ADMIN:
        return CRUD_ALL
    return POLICY_V1.get(UserRole(user_role)).get(Entity(entity))
