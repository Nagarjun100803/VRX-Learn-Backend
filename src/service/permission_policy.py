from enum import StrEnum
from typing import Literal, Union, NamedTuple, TypeAlias



class Entity(StrEnum):
    USER = "user"
    COURSE = "course"
    MODULE = "module"
    LESSON = "lesson"
    ASSIGNMENT = "assignment"
    SUBMISSIONS = "submissions"
    LAB_CREDENTIALS = "lab_credentials"
    FAQ = "faq"
    
    
    
class UserRole(StrEnum):
    ADMIN = "admin"
    SUBADMIN = "subadmin"
    TRAINER = "trainer"
    TRAINEE = "trainee"
    

class Action(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    

# Virtual Roles.
UserRoleOrVirtual: TypeAlias = Union[UserRole, Literal["manager"]]
    

class Policy(NamedTuple):
    name: str
    capabilities: frozenset[Action]
    scope: Literal["global", "specific"]
    
    def allows(self, action: Action) -> bool:
        return action in self.capabilities
    


CRUD_ALL = Policy("crud-all", frozenset({Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE}), "global")
STAFF_EDIT = Policy("staff-edit", frozenset({Action.CREATE, Action.UPDATE, Action.VIEW}), scope="global")
OWNED_STAFF_EDIT = Policy("owned-staff-edit", frozenset({Action.CREATE, Action.UPDATE, Action.VIEW}), scope="specific")
READ_ONLY = Policy("read-only", frozenset({Action.VIEW}), scope="global")
OWNED_READ_ONLY = Policy("owned-read-only", frozenset({Action.VIEW}), scope="specific")
OWNED_VIEW_UPDATE = Policy("owned-view-update", frozenset({Action.VIEW, Action.UPDATE}), scope="specific")


class PermissionPolicy:
    
    _permission_mapper: dict[UserRole, dict[Entity, Policy]] = {
        UserRole.SUBADMIN: {
            Entity.USER: STAFF_EDIT,
            Entity.COURSE: OWNED_VIEW_UPDATE,
            Entity.MODULE: OWNED_STAFF_EDIT,
            Entity.LESSON: OWNED_STAFF_EDIT,
            Entity.ASSIGNMENT: OWNED_VIEW_UPDATE,
            Entity.SUBMISSIONS: OWNED_VIEW_UPDATE,
            Entity.LAB_CREDENTIALS: OWNED_READ_ONLY
        },
        UserRole.TRAINER: {
            Entity.USER: OWNED_STAFF_EDIT,
            Entity.COURSE: OWNED_READ_ONLY,
            Entity.MODULE: OWNED_STAFF_EDIT,
            Entity.LESSON: OWNED_STAFF_EDIT,
            Entity.ASSIGNMENT: OWNED_STAFF_EDIT,
            Entity.SUBMISSIONS: OWNED_VIEW_UPDATE,
            Entity.LAB_CREDENTIALS: OWNED_STAFF_EDIT
        },
        UserRole.TRAINEE: {
            Entity.USER: OWNED_READ_ONLY,
            Entity.COURSE: OWNED_READ_ONLY,
            Entity.MODULE: OWNED_READ_ONLY,
            Entity.LESSON: OWNED_READ_ONLY,
            Entity.ASSIGNMENT: OWNED_READ_ONLY,
            Entity.SUBMISSIONS: OWNED_STAFF_EDIT,
            Entity.LAB_CREDENTIALS: OWNED_READ_ONLY
        }
    }
    
    def get_policy(
        self,
        role: Union[UserRole, str], 
        entity: Union[Entity, str]
    ) -> Policy:
        
        role = UserRole(role)    
        entity = Entity(entity)
        
        if role == UserRole.ADMIN:
            return CRUD_ALL
            
        return self._permission_mapper[role][entity]
        
