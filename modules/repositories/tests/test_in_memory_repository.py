import pytest
from datetime import datetime
from typing import Optional

from modules.repositories.repositories import InMemoryRepository
from modules.base.models import InputBaseModel, RepositoryBaseModel


# ---------------------------------------------
# Dummy Models for testing
# ---------------------------------------------


class DummyInputModel(InputBaseModel):
    def __init__(self, name: str):
        self.id: Optional[int] = None
        self.name = name
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None


class DummyRepoModel(RepositoryBaseModel):
    name: str


# ---------------------------------------------
# Fixtures
# ---------------------------------------------


@pytest.fixture
def repository():
    return InMemoryRepository[DummyInputModel, DummyRepoModel]()


@pytest.fixture
def sample_entity():
    return DummyInputModel(name="Test Entity")


# ---------------------------------------------
# Test Suite
# ---------------------------------------------


def test_create_entity(repository, sample_entity):
    result = repository.create(sample_entity)

    assert result.id == 1
    assert result.name == "Test Entity"
    assert isinstance(result.created_at, datetime)
    assert isinstance(result.updated_at, datetime)


def test_get_by_id_returns_correct_entity(repository, sample_entity):
    created = repository.create(sample_entity)
    retrieved = repository.get_by_id(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == "Test Entity"


def test_get_by_id_returns_none_for_invalid_id(repository):
    assert repository.get_by_id(999) is None


def test_list_all_returns_all_entities(repository):
    entity1 = DummyInputModel(name="A")
    entity2 = DummyInputModel(name="B")

    repository.create(entity1)
    repository.create(entity2)

    all_entities = repository.list_all()

    assert len(all_entities) == 2
    assert {e.name for e in all_entities} == {"A", "B"}


def test_update_entity_updates_fields(repository):
    original = repository.create(DummyInputModel(name="Old Name"))

    updated_entity = DummyInputModel(name="New Name")
    updated = repository.update(original.id, updated_entity)

    assert updated.id == original.id
    assert updated.name == "New Name"
    assert updated.updated_at > original.updated_at


def test_update_raises_on_missing_entity(repository):
    updated_entity = DummyInputModel(name="Not there")
    with pytest.raises(ValueError, match="Entity with id 123 not found"):
        repository.update(123, updated_entity)


def test_delete_existing_entity(repository):
    entity = repository.create(DummyInputModel(name="Delete me"))

    success = repository.delete(entity.id)
    assert success is True
    assert repository.get_by_id(entity.id) is None


def test_delete_nonexistent_entity(repository):
    success = repository.delete(999)
    assert success is False


def test_find_by_attribute_returns_correct_entities(repository):
    repository.create(DummyInputModel(name="foo"))
    repository.create(DummyInputModel(name="bar"))
    repository.create(DummyInputModel(name="foo"))

    result = repository.find_by_attribute("name", "foo")

    assert len(result) == 2
    assert all(e.name == "foo" for e in result)


def test_find_by_attribute_with_invalid_attr_returns_empty(repository):
    repository.create(DummyInputModel(name="value"))
    result = repository.find_by_attribute("nonexistent", "value")
    assert result == []
