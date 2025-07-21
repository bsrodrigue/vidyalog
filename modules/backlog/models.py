from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from modules.base.models import InputBaseModel, RepositoryBaseModel
from modules.enums.enums import BacklogPriority, BacklogStatus, Genre, Platform


@dataclass
class InputGameMetadata(InputBaseModel):
    title: Optional[str] = ""
    description: str = ""
    cover_url: str = ""
    release_date: Optional[datetime] = None
    developer: str = ""
    publisher: str = ""
    avg_completion_time: Optional[float] = None
    genres: list[Genre] = field(default_factory=list)
    platforms: list[Platform] = field(default_factory=list)


@dataclass(frozen=True)
class GameMetadata(RepositoryBaseModel):
    """
    The Game Information can be provided manually or by scraping the web.
    """

    title: str
    description: str = ""
    cover_url: str = ""
    release_date: Optional[datetime] = None
    developer: str = ""
    publisher: str = ""
    avg_completion_time: Optional[float] = None
    genres: list[Genre] = field(default_factory=list)
    platforms: list[Platform] = field(default_factory=list)


@dataclass
class InputGameBacklogEntry(InputBaseModel):
    meta_data: Optional[int] = None
    priority: Optional[BacklogPriority] = None
    status: Optional[BacklogStatus] = None

    # Relations
    backlog: Optional[int] = None  # GameBacklog


@dataclass(frozen=True)
class GameBacklogEntry(RepositoryBaseModel):
    """
    Main class for the game entry.
    """

    meta_data: int
    priority: BacklogPriority
    status: BacklogStatus

    # Relations
    backlog: int  # GameBacklog


@dataclass
class InputGameBacklog(InputBaseModel):
    title: Optional[str] = ""

    # Relations
    entries: list[int] = field(default_factory=list)  # GameBacklogEntry


@dataclass(frozen=True)
class GameBacklog(RepositoryBaseModel):
    """
    Main class for the backlog.
    """

    title: str

    # Relations
    entries: list[int] = field(default_factory=list)  # GameBacklogEntry
