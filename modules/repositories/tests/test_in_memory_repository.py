import pytest
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from modules.repositories.in_memory_repository import (
    InMemoryRepository,
    InMemoryRepositoryValueException,
)
from modules.repositories.abstract_repository import PaginatedResult


# Dummy Pydantic model for testing
class DummyModel(BaseModel):
    id: Optional[int] = None
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


@pytest.fixture
def repository():
    return InMemoryRepository[int, DummyModel]()


@pytest.fixture
def sample_entity():
    return DummyModel(name="Test Entity")


def test_create_entity(repository, sample_entity):
    created = repository.create(sample_entity)
    assert created.id == 1
    assert created.name == sample_entity.name
    assert isinstance(created.created_at, datetime)
    assert isinstance(created.updated_at, datetime)
    assert created.deleted_at is None


def test_get_by_id_returns_entity(repository, sample_entity):
    created = repository.create(sample_entity)
    fetched = repository.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == created.name


def test_get_by_id_returns_none_for_missing(repository):
    assert repository.get_by_id(9999) is None


def test_list_all_returns_all_entities(repository):
    repository.create(DummyModel(name="A"))
    repository.create(DummyModel(name="B"))
    all_entities = repository.list_all()
    assert len(all_entities) >= 2
    names = {e.name for e in all_entities}
    assert "A" in names and "B" in names


def test_update_entity_patch(repository):
    created = repository.create(DummyModel(name="Old"))
    updated = repository.update(created.id, {"name": "New"})
    assert updated.id == created.id
    assert updated.name == "New"
    assert updated.updated_at > created.updated_at


def test_update_nonexistent_entity_raises(repository):
    with pytest.raises(InMemoryRepositoryValueException):
        repository.update(1234, {"name": "Should fail"})


def test_delete_soft_marks_deleted(repository):
    created = repository.create(DummyModel(name="To delete"))
    success = repository.delete(created.id, soft=True)
    assert success
    entity = repository.get_by_id(created.id)
    assert entity is not None
    assert entity.deleted_at is not None


def test_delete_hard_removes_entity(repository):
    created = repository.create(DummyModel(name="To delete hard"))
    success = repository.delete(created.id, soft=False)
    assert success
    assert repository.get_by_id(created.id) is None


def test_delete_nonexistent_returns_false(repository):
    assert not repository.delete(9999)


def test_exists_and_count(repository):
    repository.create(DummyModel(name="foo"))
    repository.create(DummyModel(name="foo"))
    repository.create(DummyModel(name="bar"))
    assert repository.exists({"name": "foo"})
    assert not repository.exists({"name": "baz"})
    assert repository.count({"name": "foo"}) == 2
    assert repository.count({"name": "baz"}) == 0


def test_filter_basic(repository):
    repository.create(DummyModel(name="a"))
    repository.create(DummyModel(name="b"))
    repository.create(DummyModel(name="c"))
    result: PaginatedResult[DummyModel] = repository.filter(
        filters={}, order_by="name", descending=False, limit=2
    )
    assert isinstance(result, PaginatedResult)
    assert len(result.result) == 2
    assert result.result[0].name < result.result[1].name
    assert result.has_next is True


def test_filter_with_cursor_and_offset(repository):
    for n in range(5):
        repository.create(DummyModel(name=chr(65 + n)))  # names: A, B, C, D, E

    first_page = repository.filter(filters={}, order_by="id", descending=False, limit=2)
    assert len(first_page.result) == 2
    second_page = repository.filter(
        filters={}, order_by="id", descending=False, limit=2, offset=2
    )
    assert len(second_page.result) == 2
    assert first_page.next_cursor != second_page.next_cursor
