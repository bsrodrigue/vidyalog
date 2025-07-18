import shutil
import tempfile
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from modules.base.models import InputBaseModel, RepositoryBaseModel
from modules.enums.enums import BacklogPriority
from modules.repositories.repositories import LocalStorageRepository


# Example enums similar to your BacklogPriority / BacklogStatus
@dataclass
class EnumInputModel(InputBaseModel):
    priority: BacklogPriority = BacklogPriority.P0
    name: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True)
class EnumRepoModel(RepositoryBaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    name: str
    priority: BacklogPriority


# ----------------------
# Repo Helpers
# ----------------------
def make_repo():
    temp_dir = tempfile.mkdtemp()
    original_home = Path.home
    Path.home = lambda: Path(temp_dir)

    repo = LocalStorageRepository(
        input_cls=EnumInputModel, repo_cls=EnumRepoModel, entity_name="dummy"
    )

    def cleanup():
        shutil.rmtree(temp_dir)
        Path.home = original_home

    return repo, cleanup


def make_input(name: str = "Test Item") -> EnumInputModel:
    return EnumInputModel(name=name)


def test_enum_serialization():
    repo, cleanup = make_repo()
    try:
        item = EnumInputModel(
            id=None,
            created_at=None,
            updated_at=None,
            name="EnumTest",
            priority=BacklogPriority.P1,
        )
        created = repo.create(item)
        assert created.priority == BacklogPriority.P1

        # Directly read JSON file to check if priority was saved as string
        path = repo._get_path(created.id)
        raw = path.read_text()
        assert '"priority": "P1"' in raw

        # Fetch back from repo to check deserialization
        loaded = repo.get_by_id(created.id)
        assert loaded is not None
        assert loaded.priority == BacklogPriority.P1

    finally:
        cleanup()
