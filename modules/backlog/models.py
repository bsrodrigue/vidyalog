from datetime import datetime
from typing import Optional

from modules.base.models import BaseDomainModel, BasePersistenceModel
from modules.enums.enums import BacklogPriority, BacklogStatus, Genre, Platform


class GameMetadata(BaseDomainModel):
    title: str = ""
    description: str = ""
    cover_url: str = ""
    release_date: Optional[datetime] = None
    developer: str = ""
    publisher: str = ""
    avg_completion_time: Optional[float] = None
    genres: list[Genre] = []
    platforms: list[Platform] = []


class GameMetadataPersistenceModel(BasePersistenceModel):
    """
    The Game Information can be provided manually or by scraping the web.
    """

    title: str = ""
    description: str = ""
    cover_url: str = ""
    release_date: Optional[datetime] = None
    developer: str = ""
    publisher: str = ""
    avg_completion_time: Optional[float] = None
    genres: list[Genre] = []
    platforms: list[Platform] = []


class GameBacklogEntry(BaseDomainModel):
    meta_data: Optional[int] = None
    priority: Optional[BacklogPriority] = None
    status: Optional[BacklogStatus] = None

    # Relations
    backlog: Optional[int] = None  # GameBacklog


class GameBacklogEntryPersistenceModel(BasePersistenceModel):
    """
    Main class for the game entry.
    """

    meta_data: int = 0
    priority: BacklogPriority = BacklogPriority.P3
    status: BacklogStatus = BacklogStatus.INBOX

    # Relations
    backlog: int = 0  # GameBacklog


class GameBacklog(BaseDomainModel):
    title: Optional[str] = ""

    # Relations
    entries: list[int] = []


class GameBacklogPersistenceModel(BasePersistenceModel):
    """
    Main class for the backlog.
    """

    title: str = ""

    # Relations
    entries: list[int] = []
