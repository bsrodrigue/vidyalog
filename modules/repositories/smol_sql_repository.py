from contextlib import contextmanager
from datetime import datetime
from enum import Enum
import json
from typing import Any, Generic, Optional, TypeVar, cast

from pydantic import BaseModel

from libs.filter.filter_expression_evaluator import FilterExpressionEvaluator
from libs.log.base_logger import ILogger
from libs.log.file_logger import FileLogger
from modules.repositories.abstract_repository import (
    FilterQuery,
    IRepository,
    PaginatedResult,
)
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
        if isinstance(val, Enum):
            entity[key] = val.value

    return entity


def deserialize(entity: dict[str, Any]) -> dict[str, Any]:
    for key, val in entity.items():
        if isinstance(val, str) and val.startswith("[") and val.endswith("]"):
            entity[key] = json.loads(entity[key])
        if isinstance(val, str) and val.endswith("Z"):
            entity[key] = datetime.fromisoformat(val)
        if isinstance(val, str) and val.isnumeric():
            entity[key] = int(val)

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
        result = self._model.update(patch).where(col("id") == entity_id).run()

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

    def exists(self, filters: list[FilterQuery]) -> bool:
        self._logger.debug(f"Check existence of entities with filters: {filters}")
        final_expression = FilterExpressionEvaluator.chain_filter_queries_to_sql_query(
            filters
        )

        result = self._model.select().where(final_expression).limit(1).run()

        return len(result) > 0

    def count(self, filters: list[FilterQuery]) -> int:
        self._logger.debug(f"Count entities with filters: {filters}")
        final_expression = FilterExpressionEvaluator.chain_filter_queries_to_sql_query(
            filters
        )

        result = self._model.select().where(final_expression).limit(1).run()

        return len(result)

    def filter(
        self,
        filters: list[FilterQuery],
        order_by: Optional[str] = None,
        descending: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        cursor: Optional[Any] = None,
        distinct: bool = False,
    ) -> PaginatedResult[T]:
        final_expression = FilterExpressionEvaluator.chain_filter_queries_to_sql_query(
            filters
        )

        result = self._model.select().where(final_expression).run()

        total = len(result)

        has_next = False
        next_cursor = None

        self._logger.debug(f"Filtered entities: {result}")

        result = list(
            map(lambda x: self._pydantic_model.model_validate(deserialize(x)), result)
        )

        return PaginatedResult(
            result=result, total=total, has_next=has_next, next_cursor=next_cursor
        )

    @contextmanager
    def atomic(self):
        yield
