from typing import Any, ClassVar, Optional, Type

from src.auth import Entity
from src.exceptions import EntityNotFoundError


class BaseService[T]:
    """
    Base class for all the service. Do not use it directly.
    """

    _not_found_exc: ClassVar[Type[EntityNotFoundError]]
    _entity: ClassVar[Entity]

    def _require_entity(self, entity: Optional[T], **error_kwargs: Any) -> T:
        """
        Helper function that return the entity if not None.
        Otherwise it raise NotFoundError.
        """
        if entity is None:
            raise self._not_found_exc(**error_kwargs)
        return entity
