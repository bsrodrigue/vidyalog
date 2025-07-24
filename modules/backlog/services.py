from datetime import datetime
from typing import Any, List, Optional
from modules.backlog.models import (
    BacklogPriority,
    BacklogStatus,
    GameBacklog,
    GameBacklogEntry,
    GameMetadata,
    Genre,
    Platform,
)
from modules.repositories.abstract_repository import IRepository, PaginatedResult


class GameBacklogService:
    def __init__(
        self,
        backlog_repo: IRepository[int, GameBacklog],
        entry_repo: IRepository[int, GameBacklogEntry],
        metadata_repo: IRepository[int, GameMetadata],
    ):
        self.backlog_repo = backlog_repo
        self.entry_repo = entry_repo
        self.metadata_repo = metadata_repo

    # BACKLOG OPERATIONS

    def create_backlog(
        self, title: str, entries: Optional[list[int]] = None
    ) -> GameBacklog:
        return self.backlog_repo.create(GameBacklog(title=title, entries=entries or []))

    def get_backlog(self, backlog_id: int) -> Optional[GameBacklog]:
        return self.backlog_repo.get_by_id(backlog_id)

    def search_backlogs(self, query: str) -> PaginatedResult[GameBacklog]:
        return self.backlog_repo.filter(filters={"title__icontains": query})

    def list_all_backlogs(self) -> List[GameBacklog]:
        return self.backlog_repo.list_all()

    def update_backlog(self, backlog_id: int, fields: dict[str, Any]) -> GameBacklog:
        return self.backlog_repo.update(backlog_id, fields)

    def delete_backlog(self, backlog_id: int) -> bool:
        backlog = self.backlog_repo.get_by_id(backlog_id)
        if not backlog:
            return False
        for entry_id in backlog.entries:
            self.entry_repo.delete(entry_id)
        return self.backlog_repo.delete(backlog_id)

    # GAME METADATA OPERATIONS

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
        return self.metadata_repo.create(
            GameMetadata(
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
        )

    def get_game_metadata(self, metadata_id: int) -> Optional[GameMetadata]:
        return self.metadata_repo.get_by_id(metadata_id)

    def get_many_game_metadata(self, metadata_ids: List[int]) -> List[GameMetadata]:
        return self.metadata_repo.get_many_by_ids(metadata_ids)

    def list_all_game_metadata(self) -> List[GameMetadata]:
        return self.metadata_repo.list_all()

    def update_game_metadata(
        self, metadata_id: int, fields: dict[str, Any]
    ) -> GameMetadata:
        return self.metadata_repo.update(metadata_id, fields)

    def delete_game_metadata(self, metadata_id: int) -> bool:
        return self.metadata_repo.delete(metadata_id)

    # ENTRY OPERATIONS

    def add_game_to_backlog(
        self,
        backlog_id: int,
        metadata_id: int,
        priority: BacklogPriority = BacklogPriority.P3,
        status: BacklogStatus = BacklogStatus.INBOX,
    ) -> GameBacklogEntry:
        backlog = self.backlog_repo.get_by_id(backlog_id)
        if not backlog:
            raise ValueError(f"Backlog {backlog_id} not found")

        metadata = self.metadata_repo.get_by_id(metadata_id)
        if not metadata:
            raise ValueError(f"Metadata {metadata_id} not found")

        entry = self.entry_repo.create(
            GameBacklogEntry(
                meta_data=metadata_id,
                backlog=backlog_id,
                priority=priority,
                status=status,
            )
        )

        if entry.id is None:
            raise ValueError("Entry creation failed")

        # Append entry ID to backlog and update
        if backlog.id is None:
            raise ValueError("Backlog has no ID, cannot update")

        backlog.entries.append(entry.id)
        self.backlog_repo.update(backlog.id, {"entries": backlog.entries})
        return entry

    def get_entry(self, entry_id: int) -> Optional[GameBacklogEntry]:
        return self.entry_repo.get_by_id(entry_id)

    def list_entries_in_backlog(self, backlog_id: int) -> List[GameBacklogEntry]:
        backlog = self.backlog_repo.get_by_id(backlog_id)
        if not backlog:
            return []
        return self.entry_repo.get_many_by_ids(backlog.entries)

    def update_entry_status(
        self, entry_id: int, status: BacklogStatus
    ) -> Optional[GameBacklogEntry]:
        entry = self.entry_repo.get_by_id(entry_id)
        if not entry:
            return None
        return self.entry_repo.update(entry_id, {"status": status})

    def update_entry_priority(
        self, entry_id: int, priority: BacklogPriority
    ) -> Optional[GameBacklogEntry]:
        entry = self.entry_repo.get_by_id(entry_id)
        if not entry:
            return None
        return self.entry_repo.update(entry_id, {"priority": priority})

    def delete_entry(self, entry_id: int) -> bool:
        entry = self.entry_repo.get_by_id(entry_id)
        if not entry or entry.backlog is None:
            return False

        backlog = self.backlog_repo.get_by_id(entry.backlog)
        if backlog and entry_id in backlog.entries:
            backlog.entries.remove(entry_id)
            if backlog.id is None:
                raise ValueError("Backlog has no ID")
            self.backlog_repo.update(backlog.id, {"entries": backlog.entries})

        return self.entry_repo.delete(entry_id)
