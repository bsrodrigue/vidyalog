from datetime import datetime
from typing import Any, List, Optional
from libs.log.base_logger import ILogger
from libs.log.file_logger import FileLogger
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
        logger: ILogger = FileLogger("GameBacklogService"),
    ):
        self.backlog_repo = backlog_repo
        self.entry_repo = entry_repo
        self.metadata_repo = metadata_repo
        self.logger = logger

    # BACKLOG OPERATIONS

    def create_backlog(
        self, title: str, entries: Optional[list[int]] = None
    ) -> GameBacklog:
        backlog = self.backlog_repo.create(
            GameBacklog(title=title, entries=entries or [])
        )
        self.logger.info(f"Backlog {backlog} created successfully")
        return backlog

    def get_backlog(self, backlog_id: int) -> Optional[GameBacklog]:
        backlog = self.backlog_repo.get_by_id(backlog_id)
        if not backlog:
            self.logger.info(f"Backlog {backlog_id} not found")
        else:
            self.logger.info(f"Backlog {backlog} found")
        return backlog

    def search_backlogs(self, query: str) -> PaginatedResult[GameBacklog]:
        result = self.backlog_repo.filter(filters={"title__icontains": query})

        self.logger.info(f"Backlogs found: {result}")
        return result

    def list_all_backlogs(self) -> List[GameBacklog]:
        backlogs = self.backlog_repo.list_all()
        self.logger.info(f"All backlogs found: {backlogs}")
        return backlogs

    def update_backlog(self, backlog_id: int, fields: dict[str, Any]) -> GameBacklog:
        backlog = self.backlog_repo.update(backlog_id, fields)
        self.logger.info(f"Backlog {backlog} updated successfully")
        return backlog

    def delete_backlog(self, backlog_id: int) -> bool:
        backlog = self.backlog_repo.get_by_id(backlog_id)
        if not backlog:
            self.logger.info(f"Backlog {backlog_id} not found for deletion")
            return False
        for entry_id in backlog.entries:
            self.entry_repo.delete(entry_id)
        return self.backlog_repo.delete(backlog_id)

    def get_backlog_by_fuzzy_match(self, query: str) -> Optional[GameBacklog]:
        """Find backlog by ID or fuzzy title match"""
        if query.isdigit():
            backlog = self.get_backlog(int(query))
            if backlog:
                return backlog
        backlogs = self.list_all_backlogs()
        query_lower = query.lower()
        for b in backlogs:
            if b.title.lower() == query_lower:
                return b
        matches = [b for b in backlogs if query_lower in b.title.lower()]
        if len(matches) == 1:
            return matches[0]
        return None

    # GAME METADATA OPERATIONS

    def create_game_metadata(
        self,
        title: str,
        description: str = "",
        cover_url: str = "",
        release_date: Optional[datetime] = None,
        developer: str = "",
        publisher: str = "",
        avg_completion_time: float = 0,
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

    def get_game_by_fuzzy_match(self, query: str) -> Optional[GameMetadata]:
        if query.isdigit():
            game = self.get_game_metadata(int(query))
            if game:
                return game
        games = self.list_all_game_metadata()
        query_lower = query.lower()
        for g in games:
            if g.title.lower() == query_lower:
                return g
        matches = [g for g in games if query_lower in g.title.lower()]
        if len(matches) == 1:
            return matches[0]
        return None

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

    def get_entry_by_fuzzy_match(self, query: str) -> Optional[GameBacklogEntry]:
        """Find backlog by ID or fuzzy title match"""
        if query.isdigit():
            entry = self.get_entry(int(query))
            if entry:
                return entry
        entries = self.entry_repo.list_all()
        query_lower = query.lower()
        for e in entries:
            meta_data = self.get_game_metadata(e.meta_data)
            if not meta_data:
                return None
            if meta_data.title.lower() == query_lower:
                return e
        matches = []
        for e in entries:
            meta_data = self.get_game_metadata(e.meta_data)
            if not meta_data:
                continue
            if query_lower in meta_data.title.lower():
                matches.append(e)
        if len(matches) == 1:
            return matches[0]
        return None

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
