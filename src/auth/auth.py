import inspect
from typing import Any, Optional, Union, Callable, TypeVar, ParamSpec
from functools import wraps
from asyncpg import Connection
from src.auth.permission_policy import get_policy, Entity, Action
from src.auth.access_spec import get_spec_type
from src.commands.users import UserGetByID
from src.database import AsyncPgDBManager
from src.repository.users import UserRespository
from src.exceptions import UnauthorizedError



class AuthService:
    
    def __init__(self, user_repo: UserRespository, db: AsyncPgDBManager) -> None:
        """
        Initializes the AuthService with required repositories and database managers.

        Args:
            user_repo: The repository used to fetch user details and roles.
            db: The asynchronous database manager used for executing 
                contextual access specification queries.
        """
        
        self.user_repo = user_repo
        self.db = db
        
        

    async def authorize(
        self,
        entity: Union[Entity, str],
        action: Union[Action, str],
        user_id: int,
        entity_id: Optional[int] = None,
        parent_id: Optional[int] = None,
        connection: Optional[Connection] = None
    ) -> None:
        
        """
        Orchestrates the two-tier authorization process for a specific request.

        - Tier 1 (RBAC): Validates if the user's role is permitted to perform the 
        action on the entity type.
        - Tier 2 (ReBAC): If the policy is 'contextual', evaluates the dynamic 
        relationship between the user and the specific resource (or its parent).
        
        Args:
            entity: The target entity type.
            action: The operation being performed (CREATE, READ, etc.).
            user_id: The ID of the user requesting access.
            entity_id: The specific ID of the resource (required for non-CREATE actions).
            parent_id: The ID of the parent resource (required for CREATE actions 
                within a hierarchy).
            connection: Optional database connection for transactional integrity.
            
        Raises:
            UnauthorizedError: If the policy check fails or no valid relationship exists.
            ValueError: If required IDs are missing for the specific action type.
        """
        
        # Normalize enums.
        entity = Entity(entity)
        action = Action(action)
        
        if action != Action.CREATE and entity_id is None:
            raise ValueError("Requires an entity_id to verify relationship.")
        
        user = await self.user_repo.get(UserGetByID(id=user_id))
        if user is None:
            raise UnauthorizedError(
                message=f"No user found with this id '{user_id}' to perform this action."
            )

        policy = get_policy(user.role, entity)
        if not policy.allows(action):
            raise UnauthorizedError(
                message="Policy does not allow performing this action on this entity."
            )
            
        
        if policy.scope == "contextual":
            # Check for the relationship.
            spec_type = get_spec_type(entity)
            # Validate with access spec.
            if action == Action.CREATE:
                if spec_type.parent is None:
                    #NOTE: No contextual checks required.
                    return

                if spec_type.parent is not None and parent_id is None:
                    raise ValueError("`CREATE` action requires `parent_id` to verify relationship") 
            
                access_spec = spec_type.parent(user_id, parent_id, self.db)
            else:
                access_spec = spec_type.type(user_id, entity_id, self.db)
            
            
            if not await access_spec.has_access(connection):
                raise UnauthorizedError(
                    message="No contextual relationship found with this `user_id` and `entity_id`."
                )
            
            
P = ParamSpec("P")
R = TypeVar("R")
    

def require_authorization(
    action: Union[Action, str],
    entity: Union[Entity, str],
    user_id_field: str,
    entity_id_field: Optional[str] = None,
    parent_id_field: Optional[str] = None,
    object_name: str = "cmd"
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    
    """
    A method decorator that enforces authorization before executing the wrapped function.

    This decorator extracts identity and resource IDs from a command/DTO object 
    passed as an argument to the function and forwards them to the AuthService.
    
    Args:
        action: The action to authorize.
        entity: The entity type being accessed.
        user_id_field: The attribute name on the command object containing the user's ID.
        entity_id_field: The attribute name containing the target resource ID.
        parent_id_field: The attribute name containing the parent resource ID.
        object_name: The name of the parameter in the decorated function to 
            inspect (defaults to "cmd").
    Returns:
        A wrapped function that performs authorization before execution.
        
    Examples:
        ### Example 1: Authorizing an update on a specific lesson
        >>> @require_authorization(
        ...    action=Action.UPDATE,
        ...    entity=Entity.LESSON,
        ...    user_id_field="updated_by",
        ...    entity_id_field="id"
        ...)
        ... async def update_lesson(self, cmd: UpdateLessonCommand):
        ...    # This code only runs if the user has access to lesson_id
            

        ### Example 2: Authorizing a creation within a parent module
        >>> @require_authorization(
        ...    action=Action.CREATE,
        ...    entity=Entity.LESSON,
        ...    user_id_field="created_by",
        ...    parent_id_field="module_id"
        ... )
        ... async def create_lesson(self, cmd: CreateLessonCommand):
        ...    # This code only runs if the user can create items inside module_id
    """
    
    
    
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(fn)
        @wraps(fn)
        async def wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> R:
            # Bind the parameter to this wrapper function
            bound_arguments = sig.bind(self, *args, **kwargs)
            bound_arguments.apply_defaults()
            
            # Check the object_name is found in function signature as parameter.
            obj = bound_arguments.arguments.get(object_name)
            if obj is None:
                raise ValueError(f"Argument {object_name} was not found in function call.")
        
            # Get the enities from the object.
            user_id = getattr(obj, user_id_field, None)
            entity_id = getattr(obj, entity_id_field, None) if entity_id_field else None
            parent_id = getattr(obj, parent_id_field, None) if parent_id_field else None
            
            if user_id is None:
                raise ValueError(
                    f"Object missing required field: '{user_id_field}'"
                )

            # Perform authorization.
            await self.auth_service.authorize(entity, action, user_id, entity_id, parent_id)
            
            # Authorization passed, execute the actual function
            return await fn(self, *args, **kwargs)

        return wrapper
    
    return decorator