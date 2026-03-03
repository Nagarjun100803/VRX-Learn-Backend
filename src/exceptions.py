from enum import StrEnum
from typing import ClassVar, Optional, Any, Sequence, Union

from src.service.permission_policy import UserRole


class DomainError(Exception):
    """Base class for all domain exceptions. Don't use it directly"""
    _default: ClassVar[str] = "A domain error occurred"
    
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
    
class EnrollmentNotFoundError(EntityNotFoundError):
    _entity = "Enrollment"

class MediaNotFoundError(EntityNotFoundError):
    _entity = "Media"
    
class LessonNotFoundError(EntityNotFoundError):
    _entity = "Lesson"
    
class AssignmentNotFoundError(EntityNotFoundError):
    _entity = "Assignment"

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
    _default: ClassVar[str] = "{display_name} already exists with '{identifier}' = '{value}'."
    
    
    def __init__(
        self,
        value: Any,
        identifier: Any = "id",
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
        
class UserAlreadyExistsError(AlreadyExistsError):
    _entity: ClassVar[str] = "User"
    
class EnrollmentAlreadyExistsError(AlreadyExistsError):
    _entity: ClassVar[str] = "Enrollment"
    
class MediaAlreadyExistsError(AlreadyExistsError):
    _entity: ClassVar[str] = "Media"
    
class LessonAlreadyExistsError(AlreadyExistsError):
    _entity: ClassVar[str] = "Lesson"

class AssignmentAlreadyExistsError(AlreadyExistsError):
    _entity: ClassVar[str] = "Assignment"

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
    

class InvalidContentTypeError(ValidationError):
    
    _template = "Invalid content type '{content_type}'. Allowed types are: {allowed_types}."
    
    def __init__(
        self,
        content_type: str,
        allowed_types: Union[Sequence[str], StrEnum, None] = None,
        message: Optional[str] = None,
    ) -> None:
        
        if message is None and allowed_types is None:
            raise ValueError("Requires either a custom message or allowed_types.")
        
        self.content_type = content_type
        self.allowed_types = allowed_types._member_names_ if issubclass(allowed_types, StrEnum) else allowed_types
        message = message or self._template.format(content_type=content_type, allowed_types=self.allowed_types)
            
        super().__init__(message)
        



class FileSizeExceededError(ValidationError):
    _default = "The uploaded file exceeds the maximum allowed size."
    _template = "The uploaded file exceeds the maximum allowed size of {max_size} bytes."
    
    def __init__(
        self, 
        max_size: Optional[int], 
        message: Optional[str] = None
    ) -> None:
        if not any([max_size, message]):
            raise ValueError("Requires either max_size or a custom message.")
        
        if not message:
            message = self._template.format(max_size=max_size)
        else:
            message = self._default
            
        super().__init__(message)
        
    

class InvalidRoleError(ValidationError):
    _default = "The user is not a '{role}'"
    
    def __init__(
        self, 
        role: Optional[UserRole] = None, 
        message: Optional[str] = None, 
    ) -> None:
        
        if role is None and message is None:
            raise ValueError("Either role or message must be provided.")
        
        message = message or self._default.format(role=str(role))
        self.message = message
        super().__init__(message)


    
    