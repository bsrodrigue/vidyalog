from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar, List, cast
from datetime import datetime

from modules.base.models import InputBaseModel, RepositoryBaseModel

# Define a generic type for entities that inherit from BaseModel
T = TypeVar("T", bound=InputBaseModel)
R = TypeVar("R", bound=RepositoryBaseModel)


class BaseRepository(ABC, Generic[T, R]):
    """Abstract base class for repositories handling CRUD operations."""

    @abstractmethod
    def create(self, entity: T) -> R:
        """Create a new entity and return it."""
        pass

    @abstractmethod
    def update(self, entity_id: int, entity: T) -> R:
        """Update an existing entity and return it."""
        pass

    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[R]:
        """Get an entity by id"""
        pass

    @abstractmethod
    def list_all(self) -> List[R]:
        """Return a list of all entities."""
        pass


class InMemoryRepository(BaseRepository[T, R]):
    """In-memory repository implementation for storing entities."""

    def __init__(self):
        self._store: dict[int, T] = {}
        self._next_id: int = 1

    def create(self, entity: T) -> R:
        """Create a new entity with an assigned ID and timestamps."""
        if not hasattr(entity, "created_at") or not hasattr(entity, "updated_at"):
            raise ValueError("Entity must have created_at, and updated_at attributes")

        # Assign ID and timestamps
        entity.id = self._next_id
        entity.created_at = datetime.utcnow()
        entity.updated_at = datetime.utcnow()

        # Store entity
        self._store[self._next_id] = entity
        self._next_id += 1

        return cast(R, entity)

    def get_by_id(self, entity_id: int) -> Optional[R]:
        """Get an entity by ID."""
        return cast(R, self._store.get(entity_id))

    def list_all(self) -> List[R]:
        """Return all entities in the store."""
        return [cast(R, entity) for entity in self._store.values()]

    def update(self, entity_id, entity: T) -> R:
        """Update an existing entity."""
        if entity_id not in self._store:
            raise ValueError(f"Entity with id {entity_id} not found")

        entity.updated_at = datetime.utcnow()
        self._store[entity_id] = entity
        return cast(R, entity)

    def delete(self, entity_id: int) -> bool:
        """Delete an entity by ID."""
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def find_by_attribute(self, attr_name: str, value) -> List[R]:
        """Find entities by a specific attribute value."""
        return [
            cast(R, entity)
            for entity in self._store.values()
            if hasattr(entity, attr_name) and getattr(entity, attr_name) == value
        ]
