from typing import ClassVar, Optional, Any

from src.service.permission_policy import UserRole


class DomainError(Exception):
    """Base class for all domain exceptions. Don't use it directly"""
    _default: ClassVar[str] = "A domain error occured"
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or self._default
        super().__init__(message)
        
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.message!r})"
    
    def __str__(self):
        return f"{self.message}"


"""
===================================
Not Found Errors
=========================================
"""
class EntityNotFoundError(DomainError):
    """
        Base class for NotFound domain errors. Do not use directly.
    """
    _entity: ClassVar[str]
    _default: ClassVar[str] = "No '{display_name}' found with the '{identifier}' = '{value}';"
    
    def __init__(
        self, 
        value: Optional[Any] = None,
        identifier: str = "id",
        *,
        message: Optional[str] = None,
        alias: Optional[str] = None
    ) -> None:
        
        if value is None and message is None:
            raise ValueError("Requires either a value or a custom message.") 
        
        self.value = value
        self.identifier = identifier
        
        self.message = message or self._default.format(
            display_name=alias or self._entity,
            identifier=self.identifier,
            value=self.value
        )

        super().__init__(self.message)
        
        
class UserNotFoundError(EntityNotFoundError):
    _entity = "User"

class CourseNotFoundError(EntityNotFoundError):
    _entity = "Course"
    
class CourseModuleNotFoundError(EntityNotFoundError):
    _entity = "Module"
    
class ResourceNotFoundError(EntityNotFoundError):
    _entity = "Resource"



"""
======================================
Security Errors
==============================================
"""

class SecurityError(DomainError):
    """Base class for authentication and authorization errors."""
    
    _default = "A Security error occurred."
    

class InvalidPassword(SecurityError):
    _default = "The provided password does not match our records."
    
class UnAuthenticated(SecurityError):
    _default = "Authentication is required."

class UnauthorizedError(SecurityError):
    _default = "Do not have a permission to perform this action."



"""
======================================
Already Exists Errors
==============================================
"""

class AlreadyExistsError(DomainError):
    
    """Base class for AlreadyExists domain errors. Do not use directly."""

    _entity: ClassVar[str]
    _default: ClassVar[str] = "{display_name} already exists with {identifier} = '{value}'."
    
    
    def __init__(
        self,
        value: Any,
        identifier: str = "id",
        *,
        alias: Optional[str] = None,
        message: Optional[str] = None
    ) -> None:
        
        self.value = value
        self.identifier = identifier
        
        self.message = message or self._default.format(
            identifier=self.identifier,
            value=self.value,
            display_name=alias or self._entity
        )
        
        super().__init__(self.message)

class CourseAlreadyExistsError(AlreadyExistsError):
    _entity: ClassVar[str] = "Course"
    

class CourseModuleAlreadyExistsError(AlreadyExistsError):
    _entity: ClassVar[str] = "Module"
    
class ResourceAlreadyExistsError(AlreadyExistsError):
    _entity: ClassVar[str] = "Resource"
    
class UserAlreadyExistsError(AlreadyExistsError):
    _entity: ClassVar[str] = "User"
    
class EnrollmentAlreadyExistsError(AlreadyExistsError):
    _entity: ClassVar[str] = "Enrollment"
    
    

"""
==================================
Validation Errors
======================================
"""

class ValidationError(DomainError):
    """Base class for validation errors."""
    _default = "A validation error occurred."
    

class PasswordMismatchError(ValidationError):
    _default = "Password and confirm password did not match."
    

class InvalidRoleError(ValidationError):
    _default = "The user is not a {role}"
    
    def __init__(
        self, 
        role: UserRole, 
        message: Optional[str] = None, 
    ):
        message = message or self._default.format(role=role)
        super().__init__(message)


    
    