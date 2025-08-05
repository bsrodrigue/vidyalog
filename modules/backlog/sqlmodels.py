from smolorm.sqlmodel import SqlModel
from datetime import datetime

from modules.enums.enums import BacklogPriority, BacklogStatus, Genre, Platform


class GameMetadataModel(SqlModel):
    table_name: str = "game_metadatas"
    title: str = ""
    description: str = ""
    cover_url: str = ""
    release_date: datetime = datetime(1, 1, 1)
    developer: str = ""
    publisher: str = ""
    avg_completion_time: float = 0
    genres: list[Genre] = []
    platforms: list[Platform] = []


class GameBacklogEntryModel(SqlModel):
    table_name: str = "game_backlog_entries"
    meta_data: int
    priority: BacklogPriority = BacklogPriority.P3
    status: BacklogStatus = BacklogStatus.INBOX

    # Relations
    backlog: int  # GameBacklog


class GameBacklogModel(SqlModel):
    table_name: str = "game_backlogs"
    title: str = ""

    # Relations
    entries: list[int] = []
