import pytest
from modules.backlog.models import (
    BacklogPriority,
    BacklogStatus,
    GameBacklog,
    GameBacklogEntry,
    GameMetadata,
)
from modules.repositories.in_memory_repository import InMemoryRepository
from modules.backlog.services import GameBacklogService


@pytest.fixture
def service():
    backlog_repo = InMemoryRepository[int, GameBacklog]()
    entry_repo = InMemoryRepository[int, GameBacklogEntry]()
    metadata_repo = InMemoryRepository[int, GameMetadata]()
    svc = GameBacklogService(backlog_repo, entry_repo, metadata_repo)
    return svc, backlog_repo, entry_repo, metadata_repo


def test_create_and_get_backlog(service):
    svc, backlog_repo, _, _ = service
    backlog = svc.create_backlog("My Backlog")
    assert backlog.id is not None
    assert backlog.title == "My Backlog"
    assert backlog.entries == []

    fetched = svc.get_backlog(backlog.id)
    assert fetched is not None
    assert fetched.title == backlog.title


def test_search_backlogs_and_list_all(service):
    svc, backlog_repo, _, _ = service
    svc.create_backlog("First backlog")
    svc.create_backlog("Second backlog")
    svc.create_backlog("Third")

    result = svc.search_backlogs("backlog")
    assert all("backlog" in b.title.lower() for b in result.result)

    all_backlogs = svc.list_all_backlogs()
    assert len(all_backlogs) >= 3


def test_update_backlog(service):
    svc, backlog_repo, _, _ = service
    backlog = svc.create_backlog("Old Title")
    updated = svc.update_backlog(backlog.id, {"title": "New Title"})
    assert updated.title == "New Title"


def test_delete_backlog_deletes_entries_and_backlog(service):
    svc, backlog_repo, entry_repo, _ = service

    # Setup metadata first
    metadata = GameMetadata(title="Game")
    md = svc.metadata_repo.create(metadata)

    # Create backlog
    backlog = svc.create_backlog("Backlog To Delete")

    # Add entries to backlog
    entry1 = svc.add_game_to_backlog(backlog.id, md.id)
    entry2 = svc.add_game_to_backlog(backlog.id, md.id)

    # Confirm entries are in the backlog
    backlog = svc.get_backlog(backlog.id)
    assert len(backlog.entries) == 2

    # Delete backlog
    deleted = svc.delete_backlog(backlog.id)
    assert deleted is True

    # Confirm everything is deleted
    assert svc.get_backlog(backlog.id) is None
    assert svc.get_entry(entry1.id) is None
    assert svc.get_entry(entry2.id) is None


def test_create_game_metadata_and_get(service):
    svc, _, _, metadata_repo = service
    md = svc.create_game_metadata(title="Game X", developer="Dev", publisher="Pub")
    assert md.id is not None
    assert md.title == "Game X"

    fetched = svc.get_game_metadata(md.id)
    assert fetched is not None
    assert fetched.developer == "Dev"


def test_get_many_game_metadata(service):
    svc, _, _, metadata_repo = service
    md1 = svc.create_game_metadata(title="G1")
    md2 = svc.create_game_metadata(title="G2")

    many = svc.get_many_game_metadata([md1.id, md2.id])
    assert len(many) == 2
    assert {md.title for md in many} == {"G1", "G2"}


def test_list_all_game_metadata(service):
    svc, _, _, metadata_repo = service
    svc.create_game_metadata(title="A")
    svc.create_game_metadata(title="B")
    all_md = svc.list_all_game_metadata()
    assert len(all_md) >= 2


def test_update_game_metadata(service):
    svc, _, _, _ = service
    md = svc.create_game_metadata(title="Old")
    updated = svc.update_game_metadata(md.id, {"title": "New"})
    assert updated.title == "New"


def test_delete_game_metadata(service):
    svc, _, _, _ = service
    md = svc.create_game_metadata(title="To Delete")
    deleted = svc.delete_game_metadata(md.id)
    assert deleted is True
    assert svc.get_game_metadata(md.id) is None


def test_add_game_to_backlog_happy_path(service):
    svc, backlog_repo, entry_repo, metadata_repo = service
    backlog = svc.create_backlog("Backlog")
    metadata = svc.create_game_metadata(title="Game 1")

    entry = svc.add_game_to_backlog(backlog.id, metadata.id)
    assert entry.id is not None
    assert entry.backlog == backlog.id
    assert entry.meta_data == metadata.id

    updated_backlog = svc.get_backlog(backlog.id)
    assert entry.id in updated_backlog.entries


def test_add_game_to_backlog_raises_if_missing_backlog(service):
    svc, _, _, metadata_repo = service
    metadata = svc.create_game_metadata(title="Game 1")
    with pytest.raises(ValueError):
        svc.add_game_to_backlog(999, metadata.id)


def test_add_game_to_backlog_raises_if_missing_metadata(service):
    svc, backlog_repo, _, _ = service
    backlog = svc.create_backlog("Backlog")
    with pytest.raises(ValueError):
        svc.add_game_to_backlog(backlog.id, 999)


def test_add_game_to_backlog_raises_if_entry_id_none(service):
    svc, backlog_repo, entry_repo, metadata_repo = service
    backlog = svc.create_backlog("Backlog")
    metadata = svc.create_game_metadata(title="Game")

    # Patch entry_repo.create to return entry with None id
    def fake_create(entity):
        entity.id = None
        return entity

    entry_repo.create = fake_create

    with pytest.raises(ValueError):
        svc.add_game_to_backlog(backlog.id, metadata.id)


def test_get_entry(service):
    svc, _, entry_repo, _ = service
    entry = GameBacklogEntry(backlog=1, meta_data=1)
    created = entry_repo.create(entry)
    fetched = svc.get_entry(created.id)
    assert fetched == created


def test_list_entries_in_backlog(service):
    svc, backlog_repo, entry_repo, metadata_repo = service
    backlog = svc.create_backlog("BL")
    metadata = svc.create_game_metadata(title="G")
    entry1 = svc.add_game_to_backlog(backlog.id, metadata.id)
    entry2 = svc.add_game_to_backlog(backlog.id, metadata.id)

    entries = svc.list_entries_in_backlog(backlog.id)
    assert len(entries) == 2
    assert {e.id for e in entries} == {entry1.id, entry2.id}

    # If backlog not found, returns empty list
    assert svc.list_entries_in_backlog(999) == []


def test_update_entry_status_and_priority(service):
    svc, _, entry_repo, metadata_repo = service
    metadata = svc.create_game_metadata(title="G")
    backlog = svc.create_backlog("BL")
    entry = svc.add_game_to_backlog(backlog.id, metadata.id)

    updated_status = svc.update_entry_status(entry.id, BacklogStatus.PLAYING)
    assert updated_status.status == BacklogStatus.PLAYING

    updated_priority = svc.update_entry_priority(entry.id, BacklogPriority.P1)
    assert updated_priority.priority == BacklogPriority.P1

    # Updating status/priority on missing entry returns None
    assert svc.update_entry_status(999, BacklogStatus.PLAYING) is None
    assert svc.update_entry_priority(999, BacklogPriority.P1) is None


def test_delete_entry_removes_from_backlog_and_deletes_entry(service):
    svc, backlog_repo, entry_repo, metadata_repo = service
    backlog = svc.create_backlog("BL")
    metadata = svc.create_game_metadata(title="G")
    entry = svc.add_game_to_backlog(backlog.id, metadata.id)

    # Confirm entry is in backlog
    assert entry.id in svc.get_backlog(backlog.id).entries

    deleted = svc.delete_entry(entry.id)
    assert deleted is True

    # Confirm entry removed from backlog
    updated_backlog = svc.get_backlog(backlog.id)
    assert entry.id not in updated_backlog.entries

    # Deleting again returns False
    assert svc.delete_entry(entry.id) is False


def test_get_backlog_by_fuzzy_match(service):
    svc, _, _, _ = service
    # Create test backlogs
    backlog1 = svc.create_backlog("RPG Games")
    backlog2 = svc.create_backlog("Adventure Games")
    backlog3 = svc.create_backlog("Classic RPG")

    # Test exact title match
    result = svc.get_backlog_by_fuzzy_match("RPG Games")
    assert result == backlog1
    assert result.title == "RPG Games"

    # Test partial title match (single match)
    result = svc.get_backlog_by_fuzzy_match("Adventure")
    assert result == backlog2
    assert result.title == "Adventure Games"

    # Test ID match
    result = svc.get_backlog_by_fuzzy_match(str(backlog1.id))
    assert result == backlog1

    # Test multiple matches (should return None)
    result = svc.get_backlog_by_fuzzy_match("RPG")
    assert result is None

    # Test no matches
    result = svc.get_backlog_by_fuzzy_match("Puzzle")
    assert result is None


def test_get_game_by_fuzzy_match(service):
    svc, _, _, _ = service
    # Create test games
    game1 = svc.create_game_metadata(title="The Witcher 3")
    game2 = svc.create_game_metadata(title="Cyberpunk 2077")
    game3 = svc.create_game_metadata(title="Witcher Classic")

    # Test exact title match
    result = svc.get_game_by_fuzzy_match("The Witcher 3")
    assert result == game1
    assert result.title == "The Witcher 3"

    # Test partial title match (single match)
    result = svc.get_game_by_fuzzy_match("Cyberpunk")
    assert result == game2
    assert result.title == "Cyberpunk 2077"

    # Test ID match
    result = svc.get_game_by_fuzzy_match(str(game1.id))
    assert result == game1

    # Test multiple matches (should return None)
    result = svc.get_game_by_fuzzy_match("Witcher")
    assert result is None

    # Test no matches
    result = svc.get_game_by_fuzzy_match("Zelda")
    assert result is None
