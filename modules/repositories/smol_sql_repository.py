from contextlib import contextmanager
from datetime import datetime
import json
from typing import Any, Generic, Optional, TypeVar, cast

from pydantic import BaseModel

from libs.filter.filter_expression_evaluator import FilterExpressionEvaluator
from libs.log.base_logger import ILogger
from libs.log.file_logger import FileLogger
from modules.repositories.abstract_repository import IRepository, PaginatedResult
from smolorm.expressions import col
from smolorm.sqlmodel import SqlModel

T = TypeVar("T", bound=BaseModel)  # Domain type must be a Pydantic model
SQL = TypeVar("SQL", bound=SqlModel)  # Domain type must be a Pydantic model
ID = TypeVar("ID", bound=int)


def serialize(entity: dict[str, Any]) -> dict[str, Any]:
    for key, val in entity.items():
        if isinstance(val, list):
            entity[key] = json.dumps(entity[key])
        if isinstance(val, datetime):
            entity[key] = val.isoformat()

    return entity


def deserialize(entity: dict[str, Any]) -> dict[str, Any]:
    for key, val in entity.items():
        if isinstance(val, str) and val.startswith("[") and val.endswith("]"):
            entity[key] = json.loads(entity[key])
        if isinstance(val, str) and val.endswith("Z"):
            entity[key] = datetime.fromisoformat(val)

    return entity


class SmolORMRepositoryValueException(Exception):
    def __init__(
        self,
        message: str,
        logger: ILogger = FileLogger("SmolORMRepository", "test_logs.txt"),
    ):
        self.message = message
        logger.error(message)


class SmolORMRepository(Generic[ID, T], IRepository[ID, T]):
    def __init__(
        self,
        model: type[SqlModel],
        pydantic_model: type[T],
        logger: ILogger = FileLogger("SmolORMRepository", "test_logs.txt"),
    ):
        self._store: dict[ID, T] = {}
        self._next_id: ID = cast(ID, 1)
        self._logger = logger
        self._model = model
        self._pydantic_model = pydantic_model

    def _assign_timestamps(self, entity: T, is_new: bool = True) -> T:
        now = datetime.now()
        update_fields = {
            "created_at": now if is_new else getattr(entity, "created_at", None),
            "updated_at": now,
        }
        self._logger.debug(f"Assigning id and timestamps: {update_fields}")
        return entity.model_copy(update=update_fields)

    def create(self, entity: T) -> T:
        entity = self._assign_timestamps(entity)
        _entity = entity.model_dump()

        del _entity["id"]

        _entity = serialize(_entity)
        self._logger.debug(f"Created entity: {_entity}")
        result = self._model.create(_entity)

        if not isinstance(result, dict):
            print(result)
            raise ValueError("Result is not a dictionary")

        result = deserialize(result)
        return entity.model_validate(result)

    def update(self, entity_id: ID, patch: dict[str, Any]) -> T:
        patch["updated_at"] = datetime.now()
        patch = serialize(patch)
        result_id = self._model.update(patch).where(col("id") == entity_id).run()

        if isinstance(result_id, list):
            raise ValueError("Result is not an id")

        result = self._model.select().where(col("id") == result_id).run()

        if not isinstance(result, list):
            raise ValueError("Result is not a list")

        if len(result) <= 0:
            raise SmolORMRepositoryValueException(
                "Could not update entity with id {entity_id}."
            )

        entity = result[0]
        if not isinstance(entity, dict):
            print(result)
            raise ValueError("Result is not a dictionary")

        entity = deserialize(entity)
        updated = self._pydantic_model.model_validate(entity)

        self._logger.debug(f"Updated entity: {updated}")
        return updated

    def delete(self, entity_id: ID, soft: bool = False) -> bool:
        try:
            self._model.delete().where(col("id") == entity_id).run()
            self._logger.debug(f"Successful deleted entity: {entity_id}")
            return True
        except Exception as e:
            print(e)
            return False

    def get_by_id(self, entity_id: ID, include_relations: bool = False) -> Optional[T]:
        self._logger.debug(f"Get entity with id: {entity_id}")
        result = self._model.select().where(col("id") == (entity_id)).run()

        if not isinstance(result, list):
            raise ValueError("Result is not a list")

        if len(result) <= 0:
            raise ValueError("No entity with id {entity_id} found.")

        result = result[0]
        result = deserialize(result)
        return self._pydantic_model.model_validate(result)

    def get_many_by_ids(
        self, entity_ids: list[ID], include_relations: bool = False
    ) -> list[T]:
        self._logger.debug(f"Get all entities with ids: {entity_ids}")
        result = self._model.select().where(col("id").in_(entity_ids)).run()

        if not isinstance(result, list):
            raise ValueError("Result is not a list")

        result = map(
            lambda x: self._pydantic_model.model_validate(deserialize(x)), result
        )
        return list(result)

    def list_all(self) -> list[T]:
        self._logger.debug("Get all entities")
        result = self._model.select().run()

        if not isinstance(result, list):
            raise ValueError("Result is not a list")

        result = map(
            lambda x: self._pydantic_model.model_validate(deserialize(x)), result
        )
        return list(result)

    def exists(self, filters: dict[str, Any]) -> bool:
        self._logger.debug(f"Check existence of entities with filters: {filters}")
        return any(self._match_filters(e, filters) for e in self._store.values())

    def count(self, filters: dict[str, Any]) -> int:
        self._logger.debug(f"Count entities with filters: {filters}")
        return sum(1 for e in self._store.values() if self._match_filters(e, filters))

    def _match_filters(self, entity: T, filters: dict[str, Any]) -> bool:
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
