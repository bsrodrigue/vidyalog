from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar, cast

from pydantic import BaseModel

from libs.filter.filter_expression_evaluator import FilterExpressionEvaluator
from libs.log.base_logger import ILogger
from libs.log.file_logger import FileLogger
from modules.repositories.abstract_repository import IRepository, PaginatedResult

T = TypeVar("T", bound=BaseModel)  # Domain type must be a Pydantic model
ID = TypeVar("ID", bound=int)


class InMemoryRepositoryValueException(Exception):
    def __init__(
        self, message: str, logger: ILogger = FileLogger("InMemoryRepository")
    ):
        self.message = message
        logger.error(message)


class InMemoryRepository(Generic[ID, T], IRepository[ID, T]):
    def __init__(self, logger: ILogger = FileLogger("InMemoryRepository")):
        self._store: dict[ID, T] = {}
        self._next_id: ID = cast(ID, 1)
        self._logger = logger

    def _assign_id_and_timestamps(self, entity: T, is_new: bool = True) -> T:
        now = datetime.now()
        update_fields = {
            "id": self._next_id if is_new else getattr(entity, "id", None),
            "created_at": now if is_new else getattr(entity, "created_at", None),
            "updated_at": now,
        }
        self._logger.debug(f"Assigning id and timestamps: {update_fields}")
        return entity.model_copy(update=update_fields)

    def create(self, entity: T) -> T:
        entity = self._assign_id_and_timestamps(entity)
        self._store[self._next_id] = entity
        self._next_id = cast(ID, self._next_id + 1)
        self._logger.debug(f"Created entity: {entity}")
        return entity

    def update(self, entity_id: ID, patch: dict[str, Any]) -> T:
        existing = self._store.get(entity_id)
        if not existing:
            raise InMemoryRepositoryValueException(
                f"Entity with id {entity_id} not found."
            )
        patch["updated_at"] = datetime.now()
        updated = existing.model_copy(update=patch)
        self._store[entity_id] = updated
        self._logger.debug(f"Updated entity: {updated}")
        return updated

    def delete(self, entity_id: ID, soft: bool = False) -> bool:
        entity = self._store.get(entity_id)
        if not entity:
            self._logger.debug(f"Cannot delete: entity with id {entity_id} not found.")
            return False
        if soft:
            self._logger.debug("Enable soft deletion")
            entity = entity.model_copy(update={"deleted_at": datetime.now()})
            self._store[entity_id] = entity
        else:
            del self._store[entity_id]
        self._logger.debug(f"Successful deleted entity: {entity}")
        return True

    def get_by_id(self, entity_id: ID, include_relations: bool = False) -> Optional[T]:
        self._logger.debug(f"Get entity with id: {entity_id}")
        return self._store.get(entity_id)

    def get_many_by_ids(
        self, entity_ids: list[ID], include_relations: bool = False
    ) -> list[T]:
        self._logger.debug(f"Get all entities with ids: {entity_ids}")
        return [entity for id_, entity in self._store.items() if id_ in entity_ids]

    def list_all(self) -> list[T]:
        self._logger.debug("Get all entities")
        return list(self._store.values())

    def exists(self, filters: dict[str, Any]) -> bool:
        self._logger.debug(f"Check existence of entities with filters: {filters}")
        return any(self._match_filters(e, filters) for e in self._store.values())

    def count(self, filters: dict[str, Any]) -> int:
        self._logger.debug(f"Count entities with filters: {filters}")
        return sum(1 for e in self._store.values() if self._match_filters(e, filters))

    def _match_filters(self, entity: T, filters: dict[str, Any]) -> bool:
        # return all(getattr(entity, k, None) == v for k, v in filters.items())
        return FilterExpressionEvaluator.evaluate(entity, filters)

    def filter(
        self,
        filters: dict[str, Any],
        order_by: Optional[str] = None,
        descending: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        cursor: Optional[Any] = None,
        distinct: bool = False,
    ) -> PaginatedResult[T]:
        items = [e for e in self._store.values() if self._match_filters(e, filters)]

        if order_by:
            items = [
                e for e in items if getattr(e, order_by, None) is not None
            ]  # remove unsortables
            items.sort(
                key=lambda x: getattr(x, order_by),
                reverse=descending,  # type: ignore
            )

        if cursor is not None:
            try:
                cursor_index = next(
                    i for i, e in enumerate(items) if getattr(e, "id", None) == cursor
                )
                items = items[cursor_index + 1 :]
            except StopIteration:
                items = []

        total = len(items)

        if offset:
            items = items[offset:]

        has_next = False
        next_cursor = None

        if limit is not None:
            has_next = len(items) > limit
            items = items[:limit]
            if has_next:
                next_cursor = str(getattr(items[-1], "id"))

        self._logger.debug(f"Filtered entities: {items}")
        return PaginatedResult(
            result=items, total=total, has_next=has_next, next_cursor=next_cursor
        )

    @contextmanager
    def atomic(self):
        yield
