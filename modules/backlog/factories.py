from datetime import datetime
from modules.backlog.models import (
    InputGameMetadata,
    InputGameBacklog,
    InputGameBacklogEntry,
    Genre,
    Platform,
    BacklogPriority,
    BacklogStatus,
)


class GameMetadataFactory:
    """Factory for creating InputGameMetadata instances."""

    @staticmethod
    def create(
        title: str = "Untitled Game",
        description: str = "",
        cover_url: str = "",
        release_date: datetime | None = None,
        developer: str = "",
        publisher: str = "",
        avg_completion_time: float | None = None,
        genres: list[Genre] = [],
        platforms: list[Platform] = [],
    ) -> InputGameMetadata:
        return InputGameMetadata(
            id=None,
            created_at=None,
            updated_at=None,
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


class GameBacklogFactory:
    """Factory for creating InputGameBacklog instances."""

    @staticmethod
    def create(
        title: str = "My Backlog",
        entries: list[int] = [],
    ) -> InputGameBacklog:
        return InputGameBacklog(
            id=None,
            created_at=None,
            updated_at=None,
            title=title,
            entries=entries or [],
        )


class GameBacklogEntryFactory:
    """Factory for creating InputGameBacklogEntry instances."""

    @staticmethod
    def create(
        meta_data: int | None = None,
        priority: BacklogPriority | None = None,
        status: BacklogStatus | None = None,
        backlog: int | None = None,
        sessions: list[int] = [],
    ) -> InputGameBacklogEntry:
        return InputGameBacklogEntry(
            id=None,
            created_at=None,
            updated_at=None,
            meta_data=meta_data,
            priority=priority,
            status=status,
            backlog=backlog,
            sessions=sessions or [],
        )
