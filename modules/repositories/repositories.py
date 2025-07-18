from enum import Enum
import json
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar, List, cast, Type
from datetime import datetime
from dataclasses import asdict, replace
from modules.base.models import InputBaseModel, RepositoryBaseModel
from modules.enums.enums import BacklogPriority, BacklogStatus

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
    def delete(self, entity_id: int) -> bool:
        """Delete an existing entity and return nothing."""
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
        self._store: dict[int, R] = {}
        self._next_id: int = 1

    def create(self, entity: T) -> R:
        """Create a new entity with an assigned ID and timestamps."""
        if not hasattr(entity, "created_at") or not hasattr(entity, "updated_at"):
            raise ValueError("Entity must have created_at, and updated_at attributes")

        # Assign ID and timestamps
        entity.id = self._next_id
        entity.created_at = datetime.now()
        entity.updated_at = datetime.now()

        _entity = cast(R, entity)
        # Store entity
        self._store[self._next_id] = _entity
        self._next_id += 1

        return _entity

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

        original = self._store[entity_id]

        entity.id = entity_id
        entity.created_at = original.created_at
        entity.updated_at = datetime.now()

        _entity = cast(R, entity)

        self._store[entity_id] = _entity

        return _entity

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


class LocalStorageRepository(BaseRepository[T, R]):
    def __init__(self, input_cls: Type[T], repo_cls: Type[R], entity_name: str):
        self.input_cls = input_cls
        self.repo_cls = repo_cls
        self.entity_name = entity_name.lower() + "s"
        self.base_path = Path.home() / ".local/share/vidyalog" / self.entity_name
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._next_id = self._compute_next_id()

    def _compute_next_id(self) -> int:
        ids = [int(p.stem) for p in self.base_path.glob("*.json") if p.stem.isdigit()]
        return max(ids, default=0) + 1

    def _get_path(self, entity_id: int) -> Path:
        return self.base_path / f"{entity_id}.json"

    def _serialize(self, obj: R) -> dict:
        data = asdict(obj)
        for key in ("created_at", "updated_at"):
            if isinstance(data[key], datetime):
                data[key] = data[key].isoformat()

        # Convert enums to their names
        for key, value in data.items():
            if isinstance(value, Enum):
                data[key] = value.name

        return data

    def _deserialize(self, data: dict) -> R:
        for key in ("created_at", "updated_at"):
            if key in data and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])

        # Convert enum fields back from strings to enum instances
        # You need to know which keys correspond to which enum type.
        # Example assuming 'priority' and 'status' fields:

        if "priority" in data:
            data["priority"] = BacklogPriority[data["priority"]]

        if "status" in data:
            data["status"] = BacklogStatus[data["status"]]

        print(data)
        return self.repo_cls(**data)

    def create(self, entity: T) -> R:
        now = datetime.now()
        entity = replace(
            entity,
            id=self._next_id,
            created_at=now,
            updated_at=now,
        )
        repo_entity = self.repo_cls(**asdict(entity))
        self._get_path(repo_entity.id).write_text(
            json.dumps(self._serialize(repo_entity), indent=2)
        )
        self._next_id += 1
        return repo_entity

    def get_by_id(self, entity_id: int) -> Optional[R]:
        path = self._get_path(entity_id)
        if not path.exists():
            return None
        return self._deserialize(json.loads(path.read_text()))

    def list_all(self) -> List[R]:
        return [
            self._deserialize(json.loads(p.read_text()))
            for p in self.base_path.glob("*.json")
        ]

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
        path.write_text(json.dumps(self._serialize(repo_entity), indent=2))
        return repo_entity

    def delete(self, entity_id: int) -> bool:
        path = self._get_path(entity_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def find_by_attribute(self, attr_name: str, value) -> List[R]:
        return [e for e in self.list_all() if getattr(e, attr_name, None) == value]
