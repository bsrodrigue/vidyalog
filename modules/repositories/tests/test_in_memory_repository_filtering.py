from typing import Optional
from pydantic import BaseModel
import pytest
from datetime import datetime, timedelta

from modules.repositories.abstract_repository import FilterOp, FilterQuery
from modules.repositories.in_memory_repository import InMemoryRepository


class DummyModel(BaseModel):
    name: str
    score: Optional[int] = None
    created_at: Optional[datetime] = None


@pytest.fixture
def repository():
    return InMemoryRepository[int, DummyModel]()


@pytest.fixture
def setup_data(repository):
    now = datetime.now()
    entities = [
        DummyModel(name="Alpha", score=10, created_at=now - timedelta(days=5)),
        DummyModel(name="Bravo", score=20, created_at=now - timedelta(days=4)),
        DummyModel(name="Charlie", score=30, created_at=now - timedelta(days=3)),
        DummyModel(name="delta", score=40, created_at=now - timedelta(days=2)),
        DummyModel(name="Echo", score=50, created_at=now - timedelta(days=1)),
    ]
    for e in entities:
        repository.create(e)
    return entities


# ---------------------
# Filtering Tests
# ---------------------


def test_filter_exact_match(repository, setup_data):
    result = repository.filter(
        filters=[FilterQuery("name", FilterOp.EQ, "Alpha")]
    ).result
    assert len(result) == 1
    assert result[0].name == "Alpha"


def test_filter_lt(repository, setup_data):
    result = repository.filter(filters=[FilterQuery("score", FilterOp.LT, 30)]).result
    names = {e.name for e in result}
    assert names == {"Alpha", "Bravo"}


def test_filter_lte(repository, setup_data):
    result = repository.filter(filters=[FilterQuery("score", FilterOp.LTE, 30)]).result
    names = {e.name for e in result}
    assert names == {"Alpha", "Bravo", "Charlie"}


def test_filter_gt(repository, setup_data):
    result = repository.filter(filters=[FilterQuery("score", FilterOp.GT, 30)]).result
    names = {e.name for e in result}
    assert names == {"delta", "Echo"}


def test_filter_gte(repository, setup_data):
    result = repository.filter(filters=[FilterQuery("score", FilterOp.GTE, 30)]).result
    names = {e.name for e in result}
    assert names == {"Charlie", "delta", "Echo"}


def test_filter_contains(repository, setup_data):
    result = repository.filter(
        filters=[FilterQuery("name", FilterOp.CONTAINS, "lph")]
    ).result
    assert len(result) == 1
    assert result[0].name == "Alpha"


def test_filter_icontains(repository, setup_data):
    result = repository.filter(
        filters=[FilterQuery("name", FilterOp.ICONTAINS, "DEL")]
    ).result
    assert len(result) == 1
    assert result[0].name == "delta"


def test_filter_eq_explicit(repository, setup_data):
    result = repository.filter(
        filters=[FilterQuery("name", FilterOp.EQ, "Bravo")]
    ).result
    assert len(result) == 1
    assert result[0].name == "Bravo"


def test_filter_neq(repository, setup_data):
    result = repository.filter(
        filters=[FilterQuery("name", FilterOp.NEQ, "Echo")]
    ).result
    names = {e.name for e in result}
    assert "Echo" not in names
    assert len(result) == 4


def test_filter_combined_conditions(repository, setup_data):
    result = repository.filter(
        filters=[
            FilterQuery("score", FilterOp.GT, 20),
            FilterQuery("name", FilterOp.ICONTAINS, "a"),
        ]
    ).result
    names = {e.name for e in result}
    assert names == {"Charlie", "delta"}


def test_filter_on_missing_field(repository, setup_data):
    result = repository.filter(
        filters=[FilterQuery("nonexistent", FilterOp.EQ, "value")]
    ).result
    assert result == []


def test_filter_in_operator(repository, setup_data):
    result = repository.filter(
        filters=[FilterQuery("name", FilterOp.IN, ["Alpha", "Echo"])]
    ).result
    names = {e.name for e in result}
    assert names == {"Alpha", "Echo"}


def test_filter_isnull(repository):
    model = DummyModel(name="Foxtrot")
    repository.create(model)
    result = repository.filter(filters=[FilterQuery("score", FilterOp.EQ, None)]).result
    assert len(result) == 1
