from datetime import datetime
from typing import Optional

from modules.base.models import BaseDomainModel
from modules.enums.enums import BacklogPriority, BacklogStatus, Genre, Platform


class GameMetadata(BaseDomainModel):
    title: str = ""
    description: str = ""
    cover_url: str = ""
    release_date: Optional[datetime] = None
    developer: str = ""
    publisher: str = ""
    avg_completion_time: float = 0
    genres: list[Genre] = []
    platforms: list[Platform] = []


class GameBacklogEntry(BaseDomainModel):
    meta_data: int
    priority: BacklogPriority = BacklogPriority.P3
    status: BacklogStatus = BacklogStatus.INBOX

    # Relations
    backlog: int  # GameBacklog


class GameBacklog(BaseDomainModel):
    title: str = ""

    # Relations
    entries: list[int] = []
