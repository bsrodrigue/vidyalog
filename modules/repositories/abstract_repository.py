from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, ContextManager, Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")
ID = TypeVar("ID", bound=int)


class FilterOp(Enum):
    EQ = "EQ"  # Equal ==
    NEQ = "NEQ"  # Not Equal !=
    LT = "LT"  # Less Than <
    LTE = "LTE"  # Less Than or Equal <=
    GT = "GT"  # Greater Than >
    GTE = "GTE"  # Greater Than or Equal >=
    IN = "IN"
    NOT_IN = "NOT_IN"
    CONTAINS = "CONTAINS"
    ICONTAINS = "ICONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ISTARTS_WITH = "ISTARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    IENDS_WITH = "IENDS_WITH"


@dataclass
class FilterQuery:
    column: str
    op: FilterOp
    value: Any


class PaginatedResult(BaseModel, Generic[T]):
    result: list[T]
    total: int
    has_next: bool
    next_cursor: Optional[str]


class IRepository(ABC, Generic[ID, T]):
    @abstractmethod
    def create(self, entity: T) -> T:
        raise NotImplementedError()

    @abstractmethod
    def update(self, entity_id: ID, patch: dict[str, Any]) -> T:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, entity_id: ID, soft: bool = True) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_by_id(self, entity_id: ID, include_relations: bool = False) -> Optional[T]:
        raise NotImplementedError()

    @abstractmethod
    def get_many_by_ids(
        self, entity_ids: list[ID], include_relations: bool = False
    ) -> list[T]:
        raise NotImplementedError()

    @abstractmethod
    def list_all(self) -> List[T]:
        raise NotImplementedError()

    @abstractmethod
    def exists(self, filters: list[FilterQuery]) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def count(self, filters: list[FilterQuery]) -> int:
        raise NotImplementedError()

    @abstractmethod
    def atomic(self) -> ContextManager[None]:
        pass

    @abstractmethod
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
        raise NotImplementedError()
