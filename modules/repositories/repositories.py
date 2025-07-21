import json
import os
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar, List, cast, Type
from datetime import datetime
from dataclasses import asdict, replace
from libs.json.serializer_deserializer import DataclassSerializer
from libs.log.base_logger import AbstractLogger
from libs.log.console_logger import ConsoleLogger
from modules.base.models import InputBaseModel, RepositoryBaseModel

# Define a generic type for entities that inherit from BaseModel
T = TypeVar("T", bound=InputBaseModel)
R = TypeVar("R", bound=RepositoryBaseModel)


class IRepository(ABC, Generic[T, R]):
    """Abstract base class for repositories handling CRUD operations."""

    @abstractmethod
    def create(self, entity: T) -> R:
        """Create a new entity and return it."""
        raise NotImplementedError()

    @abstractmethod
    def update(self, entity_id: int, entity: T) -> R:
        """Update an existing entity and return it."""
        raise NotImplementedError()

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Delete an existing entity and return a boolean."""
        raise NotImplementedError()

    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[R]:
        """Get an entity by id"""
        raise NotImplementedError()

    @abstractmethod
    def get_by_ids(self, entity_ids: List[int]) -> List[R]:
        """Get multiple entities by id"""
        raise NotImplementedError()

    @abstractmethod
    def find_by_attribute(self, attr_name: str, value) -> List[R]:
        """Get an entity by attribute"""
        raise NotImplementedError()

    @abstractmethod
    def list_all(self) -> List[R]:
        """Return a list of all entities."""
        raise NotImplementedError()

    @abstractmethod
    def clear_all(self) -> None:
        """Clears all data"""
        raise NotImplementedError()


class InMemoryRepository(IRepository[T, R]):
    """In-memory repository implementation for storing entities. Good for testing."""

    def __init__(self, logger: AbstractLogger = ConsoleLogger("InMemoryRepository")):
        self._store: dict[int, R] = {}
        self._next_id: int = 1
        self.logger = logger

    def create(self, entity: T) -> R:
        """Create a new entity with an assigned ID and timestamps."""

        # Assign ID and timestamps
        entity.id = self._next_id
        entity.created_at = datetime.now()
        entity.updated_at = datetime.now()

        _entity = cast(R, entity)
        # Store entity
        self._store[self._next_id] = _entity
        self._next_id += 1

        self.logger.debug(f"Create Entity {entity.id} of type {T}")
        return _entity

    def get_by_id(self, entity_id: int) -> Optional[R]:
        """Get an entity by ID."""
        self.logger.debug(f"Get Entity {entity_id} of type {T}")
        return cast(R, self._store.get(entity_id))

    def get_by_ids(self, entity_ids: List[int]) -> List[R]:
        self.logger.debug(f"Get all Entities by IDs {entity_ids}")
        return [
            cast(R, entity)
            for entity in self._store.values()
            if entity.id in entity_ids
        ]

    def list_all(self) -> List[R]:
        """Return all entities in the store."""
        self.logger.debug(f"Get all Entities of type {T}")
        return [cast(R, entity) for entity in self._store.values()]

    def update(self, entity_id, entity: T) -> R:
        """Update an existing entity."""
        if entity_id not in self._store:
            raise ValueError(f"Entity with id {entity_id} not found")

        original = self._store[entity_id]

        entity.id = entity_id
        entity.created_at = original.created_at
        entity.updated_at = datetime.now()

        _entity = cast(R, entity)

        self._store[entity_id] = _entity

        self.logger.debug(f"Update Entity {entity.id} of type {T}")
        return _entity

    def delete(self, entity_id: int) -> bool:
        """Delete an entity by ID."""
        if entity_id in self._store:
            del self._store[entity_id]
            self.logger.debug(f"Delete Entity {entity_id} of type {T}")
            return True
        return False

    def find_by_attribute(self, attr_name: str, value) -> List[R]:
        """Find entities by a specific attribute value."""
        self.logger.debug(f"Find all Entities by attribute {attr_name} of type {T}")
        return [
            cast(R, entity)
            for entity in self._store.values()
            if hasattr(entity, attr_name) and getattr(entity, attr_name) == value
        ]

    def clear_all(self) -> None:
        self._store = {}
        self._next_id = 1


class LocalStorageRepository(IRepository[T, R]):
    def __init__(
        self,
        input_cls: Type[T],
        repo_cls: Type[R],
        entity_name: str,
        logger: AbstractLogger = ConsoleLogger("LocalStorageRepository"),
    ):
        self.input_cls = input_cls
        self.repo_cls = repo_cls
        self.entity_name = entity_name.lower()
        self.base_path = Path.home() / ".local/share/vidyalog" / self.entity_name
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._next_id = self._compute_next_id()
        self.logger = logger

    def _compute_next_id(self) -> int:
        ids = [int(p.stem) for p in self.base_path.glob("*.json") if p.stem.isdigit()]
        return max(ids, default=0) + 1

    def _get_path(self, entity_id: int) -> Path:
        return self.base_path / f"{entity_id}.json"

    def _serialize(self, obj: R) -> str:
        return DataclassSerializer.serialize(obj)

    def _deserialize(self, data_str: str) -> R:
        return DataclassSerializer.deserialize(data_str, self.repo_cls)

    def create(self, entity: T) -> R:
        now = datetime.now()
        entity = replace(
            entity,
            id=self._next_id,
            created_at=now,
            updated_at=now,
        )
        repo_entity = self.repo_cls(**asdict(entity))
        self._get_path(repo_entity.id).write_text(self._serialize(repo_entity))
        self._next_id += 1
        self.logger.debug(f"Create Entity {entity.id} of type {T}")
        return repo_entity

    def get_by_id(self, entity_id: int) -> Optional[R]:
        path = self._get_path(entity_id)
        if not path.exists():
            return None
        return self._deserialize(path.read_text())

    def get_by_ids(self, entity_ids: List[int]) -> List[R]:
        return [
            entity
            for entity in (self.get_by_id(eid) for eid in entity_ids)
            if entity is not None
        ]

    def list_all(self) -> List[R]:
        return [self._deserialize(p.read_text()) for p in self.base_path.glob("*.json")]

    def update(self, entity_id: int, entity: T) -> R:
        path = self._get_path(entity_id)
        if not path.exists():
            raise ValueError(f"Entity with id {entity_id} not found")

        existing_data = json.loads(path.read_text())
        created_at = datetime.fromisoformat(existing_data["created_at"])

        updated_entity = replace(
            entity,
            id=entity_id,
            created_at=created_at,
            updated_at=datetime.now(),
        )
        repo_entity = self.repo_cls(**asdict(updated_entity))
        path.write_text(self._serialize(repo_entity))
        return repo_entity

    def delete(self, entity_id: int) -> bool:
        path = self._get_path(entity_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def find_by_attribute(self, attr_name: str, value) -> List[R]:
        return [e for e in self.list_all() if getattr(e, attr_name, None) == value]

    def clear_all(self) -> None:
        os.rmdir(self.base_path)
