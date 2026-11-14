"""Abstract base repository contract with standard CRUD signatures."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract generic repository establishing database access boundaries."""

    @abstractmethod
    def get_by_id(self, id: Any) -> T | None:
        """Fetch a single entity by its primary identifier."""
        raise NotImplementedError

    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """Fetch entities with pagination."""
        raise NotImplementedError

    @abstractmethod
    def list(self, limit: int = 100, offset: int = 0, **filters: Any) -> list[T]:
        """Fetch entities with pagination and optional filtering."""
        raise NotImplementedError

    @abstractmethod
    def create(self, entity: T) -> T:
        """Persist a new entity record."""
        raise NotImplementedError

    @abstractmethod
    def update(self, id: Any, entity: Any) -> T:
        """Update an existing entity record."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, id: Any) -> bool:
        """Remove an entity record by identifier."""
        raise NotImplementedError
