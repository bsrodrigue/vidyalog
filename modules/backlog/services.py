from datetime import datetime
from typing import List, Optional
from modules.backlog.factories import (
    GameBacklogEntryFactory,
    GameBacklogFactory,
    GameMetadataFactory,
)
from modules.backlog.models import (
    BacklogPriority,
    BacklogStatus,
    GameBacklog,
    GameBacklogEntry,
    GameMetadata,
    Genre,
    InputGameBacklog,
    InputGameBacklogEntry,
    InputGameMetadata,
    Platform,
)
from modules.repositories.repositories import IRepository


class GameBacklogService:
    """Service layer for managing game backlog operations."""

    def __init__(
        self,
        backlog_repo: IRepository[InputGameBacklog, GameBacklog],
        entry_repo: IRepository[InputGameBacklogEntry, GameBacklogEntry],
        metadata_repo: IRepository[InputGameMetadata, GameMetadata],
    ):
        self.backlog_repo = backlog_repo
        self.entry_repo = entry_repo
        self.metadata_repo = metadata_repo

    # ===============================
    # BACKLOG OPERATIONS
    # ===============================

    def create_backlog(self, title: str) -> GameBacklog:
        """Create a new game backlog."""
        backlog = GameBacklogFactory.create(
            title=title,
        )
        return self.backlog_repo.create(backlog)

    def get_backlog(self, backlog_id: int) -> Optional[GameBacklog]:
        """Get a backlog by ID."""
        return self.backlog_repo.get_by_id(backlog_id)

    def search_backlogs(self, query: str) -> List[GameBacklog]:
        """Search for backlogs by title."""
        return self.backlog_repo.find_by_attribute("title", query)

    def list_all_backlogs(self) -> List[GameBacklog]:
        """Get all backlogs."""
        return self.backlog_repo.list_all()

    def update_backlog(self, backlog_id: int, backlog: InputGameBacklog) -> GameBacklog:
        """Update an existing backlog."""
        return self.backlog_repo.update(backlog_id, backlog)

    def delete_backlog(self, backlog_id: int) -> bool:
        """Delete a backlog and all its entries."""
        backlog = self.backlog_repo.get_by_id(backlog_id)
        if not backlog:
            return False

        # Delete all entries in the backlog
        for entry_id in backlog.entries:
            self.entry_repo.delete(entry_id)

        return self.backlog_repo.delete(backlog_id)

    # ===============================
    # GAME METADATA OPERATIONS
    # ===============================

    def create_game_metadata(
        self,
        title: str,
        description: str = "",
        cover_url: str = "",
        release_date: Optional[datetime] = None,
        developer: str = "",
        publisher: str = "",
        avg_completion_time: Optional[float] = None,
        genres: List[Genre] = [],
        platforms: List[Platform] = [],
    ) -> GameMetadata:
        """Create new game metadata."""
        metadata = GameMetadataFactory.create(
            title=title,
            description=description,
            cover_url=cover_url,
            release_date=release_date,
            developer=developer,
            publisher=publisher,
            avg_completion_time=avg_completion_time,
            genres=genres or [],
            platforms=platforms or [],
        )
        return self.metadata_repo.create(metadata)

    def get_game_metadata(self, metadata_id: int) -> Optional[GameMetadata]:
        """Get game metadata by ID."""
        return self.metadata_repo.get_by_id(metadata_id)

    def get_many_game_metadata(self, metadata_ids: List[int]) -> List[GameMetadata]:
        """Get game metadatas by ID."""
        return self.metadata_repo.get_by_ids(metadata_ids)

    def list_all_game_metadata(self) -> List[GameMetadata]:
        """Get all game metadata."""
        return self.metadata_repo.list_all()

    def update_game_metadata(
        self, metadata_id: int, metadata: InputGameMetadata
    ) -> GameMetadata:
        """Update existing game metadata."""
        return self.metadata_repo.update(metadata_id, metadata)

    def delete_game_metadata(self, metadata_id: int) -> bool:
        """Delete game metadata."""
        return self.metadata_repo.delete(metadata_id)

    # ===============================
    # ENTRY OPERATIONS
    # ===============================

    def add_game_to_backlog(
        self,
        backlog_id: int,
        metadata_id: int,
        priority: BacklogPriority = BacklogPriority.P3,
        status: BacklogStatus = BacklogStatus.INBOX,
    ) -> GameBacklogEntry:
        """Add a game to a backlog."""
        # Check if backlog exists
        backlog = self.backlog_repo.get_by_id(backlog_id)
        if not backlog:
            raise ValueError(f"Backlog with id {backlog_id} not found")

        # Check if metadata exists
        metadata = self.metadata_repo.get_by_id(metadata_id)
        if not metadata:
            raise ValueError(f"Game metadata with id {metadata_id} not found")

        # Create entry
        entry = GameBacklogEntryFactory.create(
            meta_data=metadata_id,
            priority=priority,
            status=status,
            backlog=backlog_id,
        )

        entry = self.entry_repo.create(entry)

        # Update backlog with new entry
        backlog.entries.append(entry.id)
        self.backlog_repo.update(
            backlog_id,
            GameBacklogFactory.create(title=backlog.title, entries=backlog.entries),
        )

        return entry

    def get_entry(self, entry_id: int) -> Optional[GameBacklogEntry]:
        """Get a backlog entry by ID."""
        return self.entry_repo.get_by_id(entry_id)

    def list_entries_in_backlog(self, backlog_id: int) -> List[GameBacklogEntry]:
        """Get all entries in a specific backlog."""
        backlog = self.backlog_repo.get_by_id(backlog_id)
        if not backlog:
            return []

        entries = []
        for entry_id in backlog.entries:
            entry = self.entry_repo.get_by_id(entry_id)
            if entry:
                entries.append(entry)

        return entries

    def update_entry_status(
        self, entry_id: int, status: BacklogStatus
    ) -> Optional[GameBacklogEntry]:
        """Update the status of a backlog entry."""
        entry = self.entry_repo.get_by_id(entry_id)
        if not entry:
            return None

        return self.entry_repo.update(
            entry_id,
            GameBacklogEntryFactory.create(
                backlog=entry.backlog,
                priority=entry.priority,
                status=status,
                meta_data=entry.meta_data,
            ),
        )

    def update_entry_priority(
        self, entry_id: int, priority: BacklogPriority
    ) -> Optional[GameBacklogEntry]:
        """Update the priority of a backlog entry."""
        entry = self.entry_repo.get_by_id(entry_id)
        if not entry:
            return None

        return self.entry_repo.update(
            entry_id,
            GameBacklogEntryFactory.create(
                backlog=entry.backlog,
                priority=priority,
                status=entry.status,
                meta_data=entry.meta_data,
            ),
        )

    def delete_entry(self, entry_id: int) -> bool:
        """Delete an entry and all its sessions."""
        entry = self.entry_repo.get_by_id(entry_id)
        if not entry:
            return False

        # Remove entry from backlog
        backlog = self.backlog_repo.get_by_id(entry.backlog)
        if backlog and entry_id in backlog.entries:
            backlog.entries.remove(entry_id)

            self.backlog_repo.update(
                backlog.id,
                GameBacklogFactory.create(title=backlog.title, entries=backlog.entries),
            )

        return self.entry_repo.delete(entry_id)
