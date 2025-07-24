from abc import ABC, abstractmethod
from typing import Any, ContextManager, Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")  # Domain
ID = TypeVar("ID", bound=int)


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
    def exists(self, filters: dict[str, Any]) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def count(self, filters: dict[str, Any]) -> int:
        raise NotImplementedError()

    @abstractmethod
    def atomic(self) -> ContextManager[None]:
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()
