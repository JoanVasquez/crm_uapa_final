from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class ICRUD(ABC, Generic[T]):
    @abstractmethod
    def save(self, entity: T) -> Optional[T]:
        """Save an entity and return it or None."""

    @abstractmethod
    def find_by_id(self, id: int) -> Optional[T]:
        """Find an entity by its ID and return it or None."""

    @abstractmethod
    def update(self, id: int, updated_data: Dict[str, Any]) -> Optional[T]:
        """
        Update an entity by its ID with the given data and return it or None.
        """

    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete an entity by its ID and return True on success."""

    @abstractmethod
    def find_all(self) -> List[T]:
        """Return a list of all entities."""

    @abstractmethod
    def find_with_pagination(self, skip: int, take: int) -> Dict[str, Any]:
        """
        Return a dictionary with paginated results.
        Expected keys: 'data' (list of entities) and 'count' (total number).
        """
