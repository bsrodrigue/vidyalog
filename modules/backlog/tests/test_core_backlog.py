import pytest
from datetime import datetime
from modules.repositories.repositories import InMemoryRepository
from modules.backlog.services import GameBacklogService
from modules.backlog.models import (
    BacklogPriority,
    BacklogStatus,
    Genre,
    InputGameBacklog,
    InputGameMetadata,
    Platform,
)


@pytest.fixture
def service():
    backlog_repo = InMemoryRepository()
    entry_repo = InMemoryRepository()
    metadata_repo = InMemoryRepository()
    return GameBacklogService(backlog_repo, entry_repo, metadata_repo)


# ===============================
# BACKLOG OPERATIONS TESTS
# ===============================


def test_create_backlog_creates_new_backlog(service):
    backlog = service.create_backlog("My Gaming Backlog")

    assert backlog.id == 1
    assert backlog.title == "My Gaming Backlog"
    assert backlog.entries == []
    assert isinstance(backlog.created_at, datetime)
    assert isinstance(backlog.updated_at, datetime)


def test_create_backlog_with_empty_title(service):
    backlog = service.create_backlog("")

    assert backlog.title == ""
    assert backlog.entries == []


def test_create_multiple_backlogs_have_different_ids(service):
    backlog1 = service.create_backlog("First Backlog")
    backlog2 = service.create_backlog("Second Backlog")

    assert backlog1.id != backlog2.id
    assert backlog1.title == "First Backlog"
    assert backlog2.title == "Second Backlog"


def test_get_backlog_returns_existing_backlog(service):
    created = service.create_backlog("Test Backlog")
    retrieved = service.get_backlog(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.title == created.title


def test_get_backlog_returns_none_when_not_found(service):
    retrieved = service.get_backlog(999)

    assert retrieved is None


def test_list_all_backlogs_returns_all_backlogs(service):
    backlog1 = service.create_backlog("Backlog 1")
    backlog2 = service.create_backlog("Backlog 2")
    backlog3 = service.create_backlog("Backlog 3")

    all_backlogs = service.list_all_backlogs()

    assert len(all_backlogs) == 3
    ids = [b.id for b in all_backlogs]
    assert backlog1.id in ids
    assert backlog2.id in ids
    assert backlog3.id in ids


def test_list_all_backlogs_returns_empty_list_when_no_backlogs(service):
    all_backlogs = service.list_all_backlogs()

    assert all_backlogs == []


def test_update_backlog_updates_existing_backlog(service):
    backlog = service.create_backlog("Original Title")

    updated_input = InputGameBacklog(title="Updated Title", entries=[1, 2, 3])

    updated = service.update_backlog(backlog.id, updated_input)

    assert updated.title == "Updated Title"
    assert updated.entries == [1, 2, 3]


def test_delete_backlog_removes_backlog(service):
    backlog = service.create_backlog("To Delete")

    result = service.delete_backlog(backlog.id)

    assert result is True
    assert service.get_backlog(backlog.id) is None


def test_delete_backlog_returns_false_when_not_found(service):
    result = service.delete_backlog(999)

    assert result is False


def test_delete_backlog_removes_all_entries(service):
    # Create backlog and metadata
    backlog = service.create_backlog("Test Backlog")
    metadata = service.create_game_metadata("Test Game")

    # Add game to backlog
    entry = service.add_game_to_backlog(backlog.id, metadata.id)

    # Verify entry exists
    assert service.get_entry(entry.id) is not None

    # Delete backlog
    result = service.delete_backlog(backlog.id)

    assert result is True
    assert service.get_backlog(backlog.id) is None
    assert service.get_entry(entry.id) is None


# ===============================
# GAME METADATA OPERATIONS TESTS
# ===============================


def test_create_game_metadata_with_minimal_data(service):
    metadata = service.create_game_metadata("Test Game")

    assert metadata.id == 1
    assert metadata.title == "Test Game"
    assert metadata.description == ""
    assert metadata.cover_url == ""
    assert metadata.release_date is None
    assert metadata.developer == ""
    assert metadata.publisher == ""
    assert metadata.avg_completion_time is None
    assert metadata.genres == []
    assert metadata.platforms == []


def test_create_game_metadata_with_full_data(service):
    release_date = datetime(2023, 1, 15)
    genres = [Genre.ACTION, Genre.RPG]
    platforms = [Platform.PC, Platform.PLAYSTATION_5]

    metadata = service.create_game_metadata(
        title="Epic Adventure",
        description="An epic adventure game",
        cover_url="https://example.com/cover.jpg",
        release_date=release_date,
        developer="Epic Studios",
        publisher="Big Publisher",
        avg_completion_time=45.5,
        genres=genres,
        platforms=platforms,
    )

    assert metadata.title == "Epic Adventure"
    assert metadata.description == "An epic adventure game"
    assert metadata.cover_url == "https://example.com/cover.jpg"
    assert metadata.release_date == release_date
    assert metadata.developer == "Epic Studios"
    assert metadata.publisher == "Big Publisher"
    assert metadata.avg_completion_time == 45.5
    assert metadata.genres == genres
    assert metadata.platforms == platforms


def test_create_game_metadata_with_empty_lists(service):
    metadata = service.create_game_metadata(title="Test Game", genres=[], platforms=[])

    assert metadata.genres == []
    assert metadata.platforms == []


def test_get_game_metadata_returns_existing_metadata(service):
    created = service.create_game_metadata("Test Game")
    retrieved = service.get_game_metadata(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.title == created.title


def test_get_game_metadata_returns_none_when_not_found(service):
    retrieved = service.get_game_metadata(999)

    assert retrieved is None


def test_list_all_game_metadata_returns_all_metadata(service):
    metadata1 = service.create_game_metadata("Game 1")
    metadata2 = service.create_game_metadata("Game 2")
    metadata3 = service.create_game_metadata("Game 3")

    all_metadata = service.list_all_game_metadata()

    assert len(all_metadata) == 3
    ids = [m.id for m in all_metadata]
    assert metadata1.id in ids
    assert metadata2.id in ids
    assert metadata3.id in ids


def test_list_all_game_metadata_returns_empty_list_when_no_metadata(service):
    all_metadata = service.list_all_game_metadata()

    assert all_metadata == []


def test_update_game_metadata_updates_existing_metadata(service):
    metadata = service.create_game_metadata("Original Game")

    updated_input = InputGameMetadata(
        title="Updated Game",
        description="Updated description",
        developer="New Developer",
    )

    updated = service.update_game_metadata(metadata.id, updated_input)

    assert updated.title == "Updated Game"
    assert updated.description == "Updated description"
    assert updated.developer == "New Developer"


def test_delete_game_metadata_removes_metadata(service):
    metadata = service.create_game_metadata("To Delete")

    result = service.delete_game_metadata(metadata.id)

    assert result is True
    assert service.get_game_metadata(metadata.id) is None


def test_delete_game_metadata_returns_false_when_not_found(service):
    result = service.delete_game_metadata(999)

    assert result is False


# ===============================
# ENTRY OPERATIONS TESTS
# ===============================


def test_add_game_to_backlog_creates_entry(service):
    backlog = service.create_backlog("Test Backlog")
    metadata = service.create_game_metadata("Test Game")

    entry = service.add_game_to_backlog(backlog.id, metadata.id)

    assert entry.id == 1
    assert entry.backlog == backlog.id
    assert entry.meta_data == metadata.id
    assert entry.priority == BacklogPriority.P3  # Default priority
    assert entry.status == BacklogStatus.INBOX  # Default status


def test_add_game_to_backlog_with_custom_priority_and_status(service):
    backlog = service.create_backlog("Test Backlog")
    metadata = service.create_game_metadata("Test Game")

    entry = service.add_game_to_backlog(
        backlog.id,
        metadata.id,
        priority=BacklogPriority.P1,
        status=BacklogStatus.PLAYING,
    )

    assert entry.priority == BacklogPriority.P1
    assert entry.status == BacklogStatus.PLAYING


def test_add_game_to_backlog_updates_backlog_entries(service):
    backlog = service.create_backlog("Test Backlog")
    metadata = service.create_game_metadata("Test Game")

    entry = service.add_game_to_backlog(backlog.id, metadata.id)

    updated_backlog = service.get_backlog(backlog.id)
    assert entry.id in updated_backlog.entries


def test_add_game_to_backlog_raises_error_when_backlog_not_found(service):
    metadata = service.create_game_metadata("Test Game")

    with pytest.raises(ValueError) as exc_info:
        service.add_game_to_backlog(999, metadata.id)

    assert "Backlog with id 999 not found" in str(exc_info.value)


def test_add_game_to_backlog_raises_error_when_metadata_not_found(service):
    backlog = service.create_backlog("Test Backlog")

    with pytest.raises(ValueError) as exc_info:
        service.add_game_to_backlog(backlog.id, 999)

    assert "Game metadata with id 999 not found" in str(exc_info.value)


def test_get_entry_returns_existing_entry(service):
    backlog = service.create_backlog("Test Backlog")
    metadata = service.create_game_metadata("Test Game")
    created = service.add_game_to_backlog(backlog.id, metadata.id)

    retrieved = service.get_entry(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.backlog == backlog.id
    assert retrieved.meta_data == metadata.id


def test_get_entry_returns_none_when_not_found(service):
    retrieved = service.get_entry(999)

    assert retrieved is None


def test_list_entries_in_backlog_returns_all_entries(service):
    backlog = service.create_backlog("Test Backlog")
    metadata1 = service.create_game_metadata("Game 1")
    metadata2 = service.create_game_metadata("Game 2")
    metadata3 = service.create_game_metadata("Game 3")

    entry1 = service.add_game_to_backlog(backlog.id, metadata1.id)
    entry2 = service.add_game_to_backlog(backlog.id, metadata2.id)
    entry3 = service.add_game_to_backlog(backlog.id, metadata3.id)

    entries = service.list_entries_in_backlog(backlog.id)

    assert len(entries) == 3
    ids = [e.id for e in entries]
    assert entry1.id in ids
    assert entry2.id in ids
    assert entry3.id in ids


def test_list_entries_in_backlog_returns_empty_list_when_no_entries(service):
    backlog = service.create_backlog("Empty Backlog")

    entries = service.list_entries_in_backlog(backlog.id)

    assert entries == []


def test_list_entries_in_backlog_returns_empty_list_when_backlog_not_found(service):
    entries = service.list_entries_in_backlog(999)

    assert entries == []


def test_list_entries_in_backlog_filters_deleted_entries(service):
    backlog = service.create_backlog("Test Backlog")
    metadata = service.create_game_metadata("Test Game")

    entry = service.add_game_to_backlog(backlog.id, metadata.id)

    # Manually delete the entry from entry repo (simulating corruption)
    service.entry_repo.delete(entry.id)

    entries = service.list_entries_in_backlog(backlog.id)

    assert entries == []


def test_update_entry_status_updates_status(service):
    backlog = service.create_backlog("Test Backlog")
    metadata = service.create_game_metadata("Test Game")
    entry = service.add_game_to_backlog(backlog.id, metadata.id)

    updated = service.update_entry_status(entry.id, BacklogStatus.FINISHED)

    assert updated is not None
    assert updated.status == BacklogStatus.FINISHED
    assert updated.id == entry.id
    assert updated.backlog == entry.backlog
    assert updated.meta_data == entry.meta_data
    assert updated.priority == entry.priority


def test_update_entry_status_returns_none_when_not_found(service):
    updated = service.update_entry_status(999, BacklogStatus.FINISHED)

    assert updated is None


def test_update_entry_priority_updates_priority(service):
    backlog = service.create_backlog("Test Backlog")
    metadata = service.create_game_metadata("Test Game")
    entry = service.add_game_to_backlog(backlog.id, metadata.id)

    updated = service.update_entry_priority(entry.id, BacklogPriority.P1)

    assert updated is not None
    assert updated.priority == BacklogPriority.P1
    assert updated.id == entry.id
    assert updated.backlog == entry.backlog
    assert updated.meta_data == entry.meta_data
    assert updated.status == entry.status


def test_update_entry_priority_returns_none_when_not_found(service):
    updated = service.update_entry_priority(999, BacklogPriority.P1)

    assert updated is None


def test_delete_entry_removes_entry(service):
    backlog = service.create_backlog("Test Backlog")
    metadata = service.create_game_metadata("Test Game")
    entry = service.add_game_to_backlog(backlog.id, metadata.id)

    result = service.delete_entry(entry.id)

    assert result is True
    assert service.get_entry(entry.id) is None


def test_delete_entry_removes_entry_from_backlog(service):
    backlog = service.create_backlog("Test Backlog")
    metadata = service.create_game_metadata("Test Game")
    entry = service.add_game_to_backlog(backlog.id, metadata.id)

    # Verify entry is in backlog
    updated_backlog = service.get_backlog(backlog.id)
    assert entry.id in updated_backlog.entries

    result = service.delete_entry(entry.id)

    assert result is True

    # Verify entry is removed from backlog
    updated_backlog = service.get_backlog(backlog.id)
    assert entry.id not in updated_backlog.entries


def test_delete_entry_returns_false_when_not_found(service):
    result = service.delete_entry(999)

    assert result is False


def test_delete_entry_handles_missing_backlog_gracefully(service):
    backlog = service.create_backlog("Test Backlog")
    metadata = service.create_game_metadata("Test Game")
    entry = service.add_game_to_backlog(backlog.id, metadata.id)

    # Manually delete the backlog
    service.backlog_repo.delete(backlog.id)

    result = service.delete_entry(entry.id)

    assert result is True
    assert service.get_entry(entry.id) is None


# ===============================
# INTEGRATION-STYLE TESTS
# ===============================


def test_complete_backlog_workflow(service):
    # Create backlog and metadata
    backlog = service.create_backlog("My Games")
    metadata = service.create_game_metadata("Epic Game")

    # Add game to backlog
    entry = service.add_game_to_backlog(backlog.id, metadata.id)

    # Update entry status through workflow
    _playing = service.update_entry_status(entry.id, BacklogStatus.PLAYING)
    completed = service.update_entry_status(entry.id, BacklogStatus.FINISHED)

    # Verify final state
    assert completed.status == BacklogStatus.FINISHED

    # Verify entry is still in backlog
    entries = service.list_entries_in_backlog(backlog.id)
    assert len(entries) == 1
    assert entries[0].id == entry.id
    assert entries[0].status == BacklogStatus.FINISHED


def test_multiple_games_in_multiple_backlogs(service):
    # Create backlogs
    backlog1 = service.create_backlog("RPGs")
    backlog2 = service.create_backlog("Action Games")

    # Create metadata
    rpg1 = service.create_game_metadata("Final Fantasy")
    rpg2 = service.create_game_metadata("The Witcher")
    action1 = service.create_game_metadata("God of War")
    action2 = service.create_game_metadata("Devil May Cry")

    # Add games to backlogs
    service.add_game_to_backlog(backlog1.id, rpg1.id, priority=BacklogPriority.P1)
    service.add_game_to_backlog(backlog1.id, rpg2.id, priority=BacklogPriority.P2)
    service.add_game_to_backlog(backlog2.id, action1.id, priority=BacklogPriority.P1)
    service.add_game_to_backlog(backlog2.id, action2.id, priority=BacklogPriority.P3)

    # Verify backlog contents
    rpg_entries = service.list_entries_in_backlog(backlog1.id)
    action_entries = service.list_entries_in_backlog(backlog2.id)

    assert len(rpg_entries) == 2
    assert len(action_entries) == 2

    # Verify priorities
    rpg_priorities = {e.meta_data: e.priority for e in rpg_entries}
    action_priorities = {e.meta_data: e.priority for e in action_entries}

    assert rpg_priorities[rpg1.id] == BacklogPriority.P1
    assert rpg_priorities[rpg2.id] == BacklogPriority.P2
    assert action_priorities[action1.id] == BacklogPriority.P1
    assert action_priorities[action2.id] == BacklogPriority.P3


def test_game_metadata_with_multiple_entries(service):
    # Create one game metadata
    metadata = service.create_game_metadata("Multi-platform Game")

    # Create multiple backlogs
    pc_backlog = service.create_backlog("PC Games")
    console_backlog = service.create_backlog("Console Games")

    # Add same game to different backlogs
    pc_entry = service.add_game_to_backlog(pc_backlog.id, metadata.id)
    console_entry = service.add_game_to_backlog(console_backlog.id, metadata.id)

    # Verify both entries exist and reference same metadata
    assert pc_entry.meta_data == metadata.id
    assert console_entry.meta_data == metadata.id
    assert pc_entry.id != console_entry.id

    # Verify entries are in correct backlogs
    pc_entries = service.list_entries_in_backlog(pc_backlog.id)
    console_entries = service.list_entries_in_backlog(console_backlog.id)

    assert len(pc_entries) == 1
    assert len(console_entries) == 1
    assert pc_entries[0].id == pc_entry.id
    assert console_entries[0].id == console_entry.id


def test_backlog_deletion_cascade_with_multiple_entries(service):
    backlog = service.create_backlog("To Delete")
    metadata1 = service.create_game_metadata("Game 1")
    metadata2 = service.create_game_metadata("Game 2")
    metadata3 = service.create_game_metadata("Game 3")

    entry1 = service.add_game_to_backlog(backlog.id, metadata1.id)
    entry2 = service.add_game_to_backlog(backlog.id, metadata2.id)
    entry3 = service.add_game_to_backlog(backlog.id, metadata3.id)

    # Verify entries exist
    assert service.get_entry(entry1.id) is not None
    assert service.get_entry(entry2.id) is not None
    assert service.get_entry(entry3.id) is not None

    # Delete backlog
    result = service.delete_backlog(backlog.id)

    assert result is True
    assert service.get_backlog(backlog.id) is None

    # Verify all entries are deleted
    assert service.get_entry(entry1.id) is None
    assert service.get_entry(entry2.id) is None
    assert service.get_entry(entry3.id) is None

    # Verify metadata still exists
    assert service.get_game_metadata(metadata1.id) is not None
    assert service.get_game_metadata(metadata2.id) is not None
    assert service.get_game_metadata(metadata3.id) is not None


# ===============================
# EDGE CASE TESTS
# ===============================


def test_service_with_empty_repositories(service):
    assert service.list_all_backlogs() == []
    assert service.list_all_game_metadata() == []
    assert service.get_backlog(1) is None
    assert service.get_game_metadata(1) is None
    assert service.get_entry(1) is None


def test_operations_with_non_existent_ids(service):
    # Test all operations that take IDs
    assert service.get_backlog(999) is None
    assert service.get_game_metadata(999) is None
    assert service.get_entry(999) is None
    assert service.delete_backlog(999) is False
    assert service.delete_game_metadata(999) is False
    assert service.delete_entry(999) is False
    assert service.update_entry_status(999, BacklogStatus.FINISHED) is None
    assert service.update_entry_priority(999, BacklogPriority.P1) is None
    assert service.list_entries_in_backlog(999) == []


def test_add_game_to_backlog_with_boundary_enum_values(service):
    backlog = service.create_backlog("Test Backlog")
    metadata = service.create_game_metadata("Test Game")

    # Test all priority values
    for priority in BacklogPriority:
        for status in BacklogStatus:
            entry = service.add_game_to_backlog(
                backlog.id, metadata.id, priority=priority, status=status
            )
            assert entry.priority == priority
            assert entry.status == status


def test_game_metadata_with_extreme_values(service):
    # Test with very long strings
    long_title = "A" * 1000
    long_description = "B" * 5000
    long_url = "https://example.com/" + "C" * 1000

    metadata = service.create_game_metadata(
        title=long_title,
        description=long_description,
        cover_url=long_url,
        avg_completion_time=999999.99,
    )

    assert metadata.title == long_title
    assert metadata.description == long_description
    assert metadata.cover_url == long_url
    assert metadata.avg_completion_time == 999999.99


def test_concurrent_operations_simulation(service):
    """Simulate concurrent operations to test state consistency"""
    # Create initial data
    backlog = service.create_backlog("Concurrent Test")
    metadata = service.create_game_metadata("Concurrent Game")

    # Simulate rapid operations
    entries = []
    for i in range(10):
        entry = service.add_game_to_backlog(backlog.id, metadata.id)
        entries.append(entry)

    # Verify all entries were created
    backlog_entries = service.list_entries_in_backlog(backlog.id)
    assert len(backlog_entries) == 10

    # Update all entries rapidly
    for entry in entries:
        service.update_entry_status(entry.id, BacklogStatus.PLAYING)
        service.update_entry_priority(entry.id, BacklogPriority.P1)

    # Verify all updates
    updated_entries = service.list_entries_in_backlog(backlog.id)
    for entry in updated_entries:
        assert entry.status == BacklogStatus.PLAYING
        assert entry.priority == BacklogPriority.P1

    # Delete half the entries
    for i in range(0, len(entries), 2):
        service.delete_entry(entries[i].id)

    # Verify correct number remain
    remaining_entries = service.list_entries_in_backlog(backlog.id)
    assert len(remaining_entries) == 5
