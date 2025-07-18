import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

import pytest

from modules.base.models import InputBaseModel, RepositoryBaseModel
from modules.repositories.repositories import LocalStorageRepository


# ----------------------
# Dummy Models
# ----------------------
@dataclass
class DummyInputModel(InputBaseModel):
    name: str = ""


@dataclass(frozen=True)
class DummyRepoModel(RepositoryBaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    name: str


# ----------------------
# Repo Helpers
# ----------------------
def make_repo():
    temp_dir = tempfile.mkdtemp()
    original_home = Path.home
    Path.home = lambda: Path(temp_dir)

    repo = LocalStorageRepository(
        input_cls=DummyInputModel, repo_cls=DummyRepoModel, entity_name="dummy"
    )

    def cleanup():
        shutil.rmtree(temp_dir)
        Path.home = original_home

    return repo, cleanup


def make_input(name: str = "Test Item") -> DummyInputModel:
    return DummyInputModel(id=None, created_at=None, updated_at=None, name=name)


# ----------------------
# Tests
# ----------------------
def test_create_entity():
    repo, cleanup = make_repo()
    try:
        dummy = make_input()
        created = repo.create(dummy)
        assert created.id == 1
        assert created.name == dummy.name
        assert isinstance(created.created_at, datetime)
        assert isinstance(created.updated_at, datetime)
    finally:
        cleanup()


def test_get_by_id_returns_correct_entity():
    repo, cleanup = make_repo()
    try:
        dummy = make_input()
        created = repo.create(dummy)
        found = repo.get_by_id(created.id)
        assert found == created
    finally:
        cleanup()


def test_list_all_returns_all_entities():
    repo, cleanup = make_repo()
    try:
        repo.create(make_input("A"))
        repo.create(make_input("B"))
        all_items = repo.list_all()
        assert len(all_items) == 2
        assert all(isinstance(i, DummyRepoModel) for i in all_items)
    finally:
        cleanup()


def test_update_entity_updates_fields():
    repo, cleanup = make_repo()
    try:
        created = repo.create(make_input("Old Name"))
        updated = repo.update(created.id, make_input("New Name"))
        assert updated.id == created.id
        assert updated.name == "New Name"
        assert updated.updated_at > created.updated_at
    finally:
        cleanup()


def test_delete_existing_entity():
    repo, cleanup = make_repo()
    try:
        created = repo.create(make_input())
        deleted = repo.delete(created.id)
        assert deleted is True
        assert repo.get_by_id(created.id) is None
    finally:
        cleanup()


def test_find_by_attribute_returns_correct_entities():
    repo, cleanup = make_repo()
    try:
        repo.create(make_input("Match"))
        repo.create(make_input("No Match"))
        matches = repo.find_by_attribute("name", "Match")
        assert len(matches) == 1
        assert matches[0].name == "Match"
    finally:
        cleanup()


def test_find_by_attribute_with_invalid_attr_returns_empty():
    repo, cleanup = make_repo()
    try:
        repo.create(make_input())
        matches = repo.find_by_attribute("nonexistent_field", "irrelevant")
        assert matches == []
    finally:
        cleanup()


def test_get_by_id_returns_none_for_nonexistent():
    repo, cleanup = make_repo()
    try:
        assert repo.get_by_id(999) is None
    finally:
        cleanup()


def test_update_nonexistent_entity_raises():
    repo, cleanup = make_repo()
    try:
        with pytest.raises(ValueError):
            repo.update(999, make_input("X"))
    finally:
        cleanup()


def test_delete_nonexistent_entity_returns_false():
    repo, cleanup = make_repo()
    try:
        assert repo.delete(999) is False
    finally:
        cleanup()
