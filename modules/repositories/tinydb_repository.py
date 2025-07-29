from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Generic, Optional, TypeVar, cast, Dict, List, Type

from pydantic import BaseModel
from tinydb import TinyDB, Query

from libs.filter.filter_expression_evaluator import FilterExpressionEvaluator
from libs.log.base_logger import ILogger
from libs.log.file_logger import FileLogger
from modules.repositories.abstract_repository import IRepository, PaginatedResult
from modules.repositories.utils.tinydb_query_builder import TinyDBQueryBuilder

T = TypeVar("T", bound=BaseModel)  # Domain type must be a Pydantic model
ID = TypeVar("ID", bound=int)


class TinyDBRepositoryValueException(Exception):
    def __init__(self, message: str, logger: ILogger = FileLogger("TinyDBRepository")):
        self.message = message
        logger.error(message)


class TinyDBRepository(Generic[ID, T], IRepository[ID, T]):
    def __init__(
        self,
        entity_class: Type[T],
        db_path: str | Path = "data/app.json",
        table_name: str = "entities",
        logger: ILogger = FileLogger("TinyDBRepository"),
    ):
        self._entity_class = entity_class
        self._db_path = Path(db_path)
        self._table_name = table_name
        self._logger = logger

        # Ensure directory exists
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._logger.debug(
            f"Initializing TinyDBRepository for Entity {entity_class}..."
        )
        # Initialize TinyDB with caching for better performance
        self._db = TinyDB(
            self._db_path,
            indent=2,
            separators=(",", ": "),
        )
        self._table = self._db.table(table_name)

        # Initialize next_id based on existing data
        self._next_id: ID = self._get_next_id()

        self._logger.debug(
            f"Initialized TinyDBRepository with db_path={db_path}, table={table_name}"
        )

    def _get_next_id(self) -> ID:
        """Get the next available ID based on existing data"""
        if not self._table.all():
            return cast(ID, 1)

        max_id = max((doc.get("id", 0) for doc in self._table.all()), default=0)
        return cast(ID, max_id + 1)

    def _assign_id_and_timestamps(self, entity: T, is_new: bool = True) -> T:
        """Assign ID and timestamps to entity"""
        now = datetime.now()
        update_fields = {
            "id": self._next_id if is_new else getattr(entity, "id", None),
            "created_at": now if is_new else getattr(entity, "created_at", None),
            "updated_at": now,
        }
        self._logger.debug(f"Assigning id and timestamps: {update_fields}")
        return entity.model_copy(update=update_fields)

    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """Convert Pydantic model to dictionary for TinyDB storage"""
        data = entity.model_dump()
        # Convert datetime objects to ISO strings for JSON serialization
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            if isinstance(value, Enum):
                data[key] = value.value
        return data

    def _dict_to_entity(self, data: Dict[str, Any]) -> T:
        """Convert dictionary from TinyDB back to Pydantic model"""
        if not data:
            raise TinyDBRepositoryValueException("Missing Data")

        # Convert ISO strings back to datetime objects
        converted_data = {}
        for key, value in data.items():
            if isinstance(value, str) and key.endswith("_at"):
                try:
                    converted_data[key] = datetime.fromisoformat(value)
                except (ValueError, TypeError):
                    converted_data[key] = (
                        value  # Keep as string if not a valid datetime
                    )
            else:
                converted_data[key] = value

        return self._entity_class.model_validate(converted_data)

    def _dicts_to_entities(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """Convert list of dictionaries to list of entities"""
        return [self._dict_to_entity(data) for data in data_list if data]

    def create(self, entity: T) -> T:
        """Create a new entity"""
        entity = self._assign_id_and_timestamps(entity)

        # Store in TinyDB
        doc_data = self._entity_to_dict(entity)
        self._table.insert(doc_data)

        # Update next_id
        self._next_id = cast(ID, self._next_id + 1)

        self._logger.debug(f"Created entity: {entity}")
        return entity

    def update(self, entity_id: ID, patch: Dict[str, Any]) -> T:
        """Update an existing entity"""
        Entity = Query()
        existing_docs = self._table.search(Entity.id == entity_id)

        if not existing_docs:
            raise TinyDBRepositoryValueException(
                f"Entity with id {entity_id} not found."
            )

        existing_data = existing_docs[0]

        # Apply patch with updated timestamp
        patch_copy = patch.copy()
        patch_copy["updated_at"] = datetime.now().isoformat()

        # Convert datetime objects in patch to ISO strings
        for key, value in patch_copy.items():
            if isinstance(value, datetime):
                patch_copy[key] = value.isoformat()

        updated_data = {**existing_data, **patch_copy}

        # Update in database
        self._table.update(updated_data, Entity.id == entity_id)

        # Get updated entity and convert back to model
        updated_doc = self._table.search(Entity.id == entity_id)[0]
        updated_entity = self._dict_to_entity(updated_doc)

        self._logger.debug(f"Updated entity: {updated_entity}")
        return updated_entity

    def delete(self, entity_id: ID, soft: bool = False) -> bool:
        """Delete an entity (hard or soft delete)"""
        Entity = Query()
        existing_docs = self._table.search(Entity.id == entity_id)

        if not existing_docs:
            self._logger.debug(f"Cannot delete: entity with id {entity_id} not found.")
            return False

        if soft:
            self._logger.debug("Enable soft deletion")
            patch = {"deleted_at": datetime.now().isoformat()}
            self._table.update(patch, Entity.id == entity_id)
        else:
            self._table.remove(Entity.id == entity_id)

        self._logger.debug(f"Successfully deleted entity with id {entity_id}")
        return True

    def get_by_id(self, entity_id: ID, include_relations: bool = False) -> Optional[T]:
        """Get entity by ID"""
        self._logger.debug(f"Get entity with id: {entity_id}")
        Entity = Query()
        results = self._table.search(Entity.id == entity_id)

        if not results:
            return None

        return self._dict_to_entity(results[0])

    def get_many_by_ids(
        self, entity_ids: List[ID], include_relations: bool = False
    ) -> List[T]:
        """Get multiple entities by their IDs"""
        self._logger.debug(f"Get all entities with ids: {entity_ids}")
        Entity = Query()
        results = self._table.search(Entity.id.one_of(entity_ids))
        return self._dicts_to_entities(cast(list[dict[str, Any]], results))

    def list_all(self) -> List[T]:
        """Get all entities"""
        self._logger.debug("Get all entities")
        results = self._table.all()
        return self._dicts_to_entities(cast(list[dict[str, Any]], results))

    def exists(self, filters: Dict[str, Any]) -> bool:
        """Check if any entities match the filters"""
        self._logger.debug(f"Check existence of entities with filters: {filters}")
        return len(self._table.search(self._build_tinydb_query(filters))) > 0

    def count(self, filters: Dict[str, Any]) -> int:
        """Count entities matching filters"""
        self._logger.debug(f"Count entities with filters: {filters}")
        return len(self._table.search(self._build_tinydb_query(filters)))

    # def _build_tinydb_query(self, filters: Dict[str, Any]) -> Query:
    #     """Build TinyDB query from filters dictionary"""
    #     if not filters:
    #         return Query().noop()  # Match all
    #
    #     Entity = Query()
    #     query = None
    #
    #     for key, value in filters.items():
    #         # Convert datetime values to ISO strings for querying
    #         if isinstance(value, datetime):
    #             value = value.isoformat()
    #
    #         condition = Entity[key] == value
    #         query = condition if query is None else query & condition
    #
    #     return query if query is not None else Query().noop()

    def _build_tinydb_query(self, filters: Dict[str, Any]) -> Query:
        return TinyDBQueryBuilder.build_tinydb_query(filters)

    def _match_filters_fallback(self, entity: T, filters: Dict[str, Any]) -> bool:
        """Fallback filter matching using the original evaluator"""
        return FilterExpressionEvaluator.evaluate(entity, filters)

    def filter(
        self,
        filters: Dict[str, Any],
        order_by: Optional[str] = None,
        descending: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        cursor: Optional[Any] = None,
        distinct: bool = False,
    ) -> PaginatedResult[T]:
        """Filter entities with pagination support"""

        self._logger.debug(
            f"Filter entities in {self._table_name} with filters: {filters}"
        )
        # Get filtered results
        try:
            # Try using TinyDB query first for simple filters
            if filters:
                raw_items = self._table.search(self._build_tinydb_query(filters))
            else:
                raw_items = self._table.all()

            # Convert to entities
            items = self._dicts_to_entities(cast(list[dict[str, Any]], raw_items))

        except Exception as e:
            self._logger.error(f"TinyDB query failed, using fallback: {e}")
            # Fallback to manual filtering for complex filters
            all_entities = self.list_all()
            items = [
                entity
                for entity in all_entities
                if self._match_filters_fallback(entity, filters)
            ]

        # Apply sorting
        if order_by and items:
            items = [
                item for item in items if getattr(item, order_by, None) is not None
            ]
            items.sort(key=lambda x: getattr(x, order_by), reverse=descending)

        # Handle cursor-based pagination
        if cursor is not None:
            try:
                cursor_index = next(
                    i
                    for i, item in enumerate(items)
                    if getattr(item, "id", None) == cursor
                )
                items = items[cursor_index + 1 :]
            except StopIteration:
                items = []

        total = len(items)

        # Apply offset
        if offset:
            items = items[offset:]

        # Apply limit and determine pagination info
        has_next = False
        next_cursor = None

        if limit is not None:
            has_next = len(items) > limit
            items = items[:limit]
            if has_next and items:
                next_cursor = str(getattr(items[-1], "id"))

        self._logger.debug(f"Filtered {len(items)} entities")
        return PaginatedResult(
            result=items, total=total, has_next=has_next, next_cursor=next_cursor
        )

    @contextmanager
    def atomic(self):
        """Context manager for atomic operations (basic implementation)"""
        # TinyDB doesn't have built-in transactions, but we can implement basic rollback
        backup = self._table.all()
        try:
            yield
        except Exception:
            # Rollback by clearing and restoring from backup
            self._table.truncate()
            for item in backup:
                self._table.insert(item)
            raise

    def close(self):
        """Close the database connection"""
        self._db.close()
        self._logger.debug("Database connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
