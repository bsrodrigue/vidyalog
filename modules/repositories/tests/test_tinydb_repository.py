# Re-implement TinyDBRepository here to ensure it uses the updated TinyDBQueryBuilder.
# In a real project, you would import the actual TinyDBRepository.
from datetime import datetime, timedelta
from typing import List, Optional, TypeVar

import pytest
from pydantic import BaseModel

# Assuming these are available in your project structure relative to tests
from libs.log.file_logger import FileLogger
from modules.repositories.tinydb_repository import TinyDBRepository

# --- Mock TinyDBRepository and other dependencies for testing ---
T = TypeVar("T", bound=BaseModel)
ID = TypeVar("ID", bound=int)


# --- Dummy Models for testing ---
class DummyModel(BaseModel):
    id: Optional[int] = None  # Added id for TinyDBRepository
    name: str
    score: Optional[int] = None
    created_at: Optional[datetime] = None
    status: Optional[str] = None  # Added for isnull tests
    tags: Optional[List[str]] = None  # Added for list contains tests


# --- Pytest Fixtures ---
@pytest.fixture
def repository(tmp_path):
    """
    Provides a TinyDBRepository instance with a temporary database file
    for each test, ensuring isolated tests.
    """
    db_file = tmp_path / "test_db.json"
    repo = TinyDBRepository[int, DummyModel](
        DummyModel, db_path=db_file, logger=FileLogger(filepath="test_logs.txt")
    )
    yield repo
    repo.close()  # Ensure DB connection is closed
    # Cleanup: tmp_path will handle deleting the file itself


@pytest.fixture
def setup_data(repository: TinyDBRepository[int, DummyModel]):
    """
    Inserts sample data into the TinyDBRepository for testing.
    """
    now = datetime.now()
    entities = [
        repository.create(
            DummyModel(
                name="Alpha",
                score=10,
                created_at=now - timedelta(days=5),
                tags=["tag1", "important"],
            )
        ),
        repository.create(
            DummyModel(
                name="Bravo",
                score=20,
                created_at=now - timedelta(days=4),
                status="active",
            )
        ),
        repository.create(
            DummyModel(
                name="Charlie",
                score=30,
                created_at=now - timedelta(days=3),
                tags=["tag1", "test"],
            )
        ),
        repository.create(
            DummyModel(
                name="delta",
                score=40,
                created_at=now - timedelta(days=2),
                status="inactive",
            )
        ),
        repository.create(
            DummyModel(
                name="Echo", score=50, created_at=now - timedelta(days=1), tags=["tag2"]
            )
        ),
        repository.create(
            DummyModel(name="Frank", score=None, created_at=now)
        ),  # For isnull tests
        repository.create(
            DummyModel(name="George", score=60, status=None)
        ),  # For isnull tests
    ]
    return entities


# ---------------------
# Filtering Tests for TinyDBRepository
# ---------------------


def test_filter_exact_match(repository, setup_data):
    result = repository.filter(filters={"name": "Alpha"}).result
    assert len(result) == 1
    assert result[0].name == "Alpha"


def test_filter_lt(repository, setup_data):
    result = repository.filter(filters={"score__lt": 30}).result
    names = {e.name for e in result}
    assert names == {"Alpha", "Bravo"}


def test_filter_lte(repository, setup_data):
    result = repository.filter(filters={"score__lte": 30}).result
    names = {e.name for e in result}
    assert names == {"Alpha", "Bravo", "Charlie"}


def test_filter_gt(repository, setup_data):
    result = repository.filter(filters={"score__gt": 30}).result
    names = {e.name for e in result}
    assert names == {"delta", "Echo", "George"}  # George has score 60


def test_filter_gte(repository, setup_data):
    result = repository.filter(filters={"score__gte": 30}).result
    names = {e.name for e in result}
    assert names == {"Charlie", "delta", "Echo", "George"}


def test_filter_contains_string(repository, setup_data):
    result = repository.filter(filters={"name__contains": "lph"}).result
    assert len(result) == 1
    assert result[0].name == "Alpha"


def test_filter_contains_list_item(repository, setup_data):
    result = repository.filter(filters={"tags__contains": "tag1"}).result
    names = {e.name for e in result}
    assert names == {"Alpha", "Charlie"}


def test_filter_icontains(repository, setup_data):
    result = repository.filter(filters={"name__icontains": "DEL"}).result
    assert len(result) == 1
    assert result[0].name == "delta"


def test_filter_eq_explicit(repository, setup_data):
    result = repository.filter(filters={"name__eq": "Bravo"}).result
    assert len(result) == 1
    assert result[0].name == "Bravo"


def test_filter_neq(repository, setup_data):
    result = repository.filter(filters={"name__neq": "Echo"}).result
    names = {e.name for e in result}
    assert "Echo" not in names
    assert len(result) == 6  # Total 7 records, 1 excluded


def test_filter_combined_conditions(repository, setup_data):
    result = repository.filter(filters={"score__gt": 20, "name__icontains": "a"}).result
    names = {e.name for e in result}
    assert names == {"Charlie", "delta"}  # Alpha has score 10


def test_filter_on_missing_field(repository, setup_data):
    result = repository.filter(filters={"nonexistent__eq": "value"}).result
    assert result == []


def test_filter_with_invalid_operator(repository):
    # Pass a dummy model class for repo initialization
    with pytest.raises(ValueError, match="Unsupported filter operator: unknown"):
        repository.filter(filters={"name__unknown": "whatever"})


def test_filter_in_operator(repository, setup_data):
    result = repository.filter(filters={"name__in": ["Alpha", "Echo"]}).result
    names = {e.name for e in result}
    assert names == {"Alpha", "Echo"}


def test_filter_isnull_true_for_none_value(repository, setup_data):
    """Test isnull=True when the field exists but its value is None."""
    result = repository.filter(filters={"score__isnull": True}).result
    assert len(result) == 1
    assert result[0].name == "Frank"  # Frank has score=None


def test_filter_isnull_true_for_missing_field(repository, setup_data):
    """Test isnull=True when the field does not exist on the document."""
    # Only Alpha, Charlie, Echo have 'tags'. Bravo, delta, Frank, George do not.
    # So, filtering for 'tags__isnull': True should return Bravo, delta, Frank, George.
    result = repository.filter(filters={"tags__isnull": True}).result
    names = {e.name for e in result}
    assert names == {"Bravo", "delta", "Frank", "George"}


def test_filter_isnull_false_for_existing_value(repository, setup_data):
    """Test isnull=False when the field exists and its value is not None."""
    result = repository.filter(filters={"status__isnull": False}).result
    names = {e.name for e in result}
    assert names == {
        "Bravo",
        "delta",
    }  # Bravo and delta have status. George has status=None.


def test_filter_isnull_false_for_existing_list(repository, setup_data):
    """Test isnull=False for an existing list field (tags)."""
    result = repository.filter(filters={"tags__isnull": False}).result
    names = {e.name for e in result}
    assert names == {"Alpha", "Charlie", "Echo"}


def test_filter_notin_operator(repository, setup_data):
    result = repository.filter(filters={"name__notin": ["Charlie", "Echo"]}).result
    names = {e.name for e in result}
    assert "Charlie" not in names
    assert "Echo" not in names
    assert len(result) == 5  # Total 7 records, 2 excluded


def test_filter_startswith(repository, setup_data):
    result = repository.filter(filters={"name__startswith": "Cha"}).result
    assert len(result) == 1
    assert result[0].name == "Charlie"


def test_filter_istartswith(repository, setup_data):
    result = repository.filter(filters={"name__istartswith": "alp"}).result
    assert len(result) == 1
    assert result[0].name == "Alpha"


def test_filter_endswith(repository, setup_data):
    result = repository.filter(filters={"name__endswith": "avo"}).result
    assert len(result) == 1
    assert result[0].name == "Bravo"


def test_filter_iendswith(repository, setup_data):
    result = repository.filter(filters={"name__iendswith": "phA"}).result
    assert len(result) == 1
    assert result[0].name == "Alpha"


def test_filter_no_filters_returns_all(repository, setup_data):
    result = repository.filter(filters={}).result
    assert len(result) == 7  # All 7 entities should be returned


def test_filter_nonexistent_field_isnull_false(repository, setup_data):
    """Test filter for a non-existent field with isnull=False (should return nothing)."""
    # No documents have a 'foo' field, so no documents should exist when checking foo__isnull=False
    result = repository.filter(filters={"foo__isnull": False}).result
    assert len(result) == 0


def test_filter_datetime_range(repository, setup_data):
    now = datetime.now()
    # Filter for entities created within the last 3.5 days (i.e., Charlie, delta, Echo, George)
    # The setup_data timestamps are relative to `now` when `setup_data` runs.
    # So, we need to pick a range that captures the desired entities.

    # Bravo (4 days ago), Charlie (3 days ago), delta (2 days ago), Echo (1 day ago), George (now)
    # We want entities created >= 3 days ago.
    filters = {
        "created_at__gte": (now - timedelta(days=3)).isoformat(),
        "created_at__lt": (
            now + timedelta(days=1)
        ).isoformat(),  # Up to 'now' or slightly in future for George
    }

    # Manually determine expected names based on data
    # Charlie: now - 3 days
    # delta: now - 2 days
    # Echo: now - 1 day
    # Frank: now (score=None)
    # George: now (status=None)

    result = repository.filter(filters=filters).result
    names = {e.name for e in result}

    # Filtered range: >= (now - 3 days) and < (now + 1 day)
    # This should include Charlie, delta, Echo, Frank, George
    assert names == {"Charlie", "delta", "Echo", "Frank", "George"}
    assert len(result) == 5


def test_filter_on_empty_database(repository):
    """Test filtering when the database is empty."""
    result = repository.filter(filters={"name": "test"}).result
    assert len(result) == 0
    assert result == []


def test_count_with_filters(repository, setup_data):
    count = repository.count(filters={"score__gt": 30})
    assert count == 3  # delta, Echo, George


def test_count_no_filters(repository, setup_data):
    count = repository.count(filters={})
    assert count == 7  # All records


def test_exists_with_filters(repository, setup_data):
    assert repository.exists(filters={"name": "Bravo"})
    assert repository.exists(filters={"name": "NonExistent"})
    assert repository.exists(filters={"score__gte": 50})
    assert repository.exists(filters={"score__lt": 5})


def test_exists_no_filters(repository, setup_data):
    assert repository.exists(filters={})
