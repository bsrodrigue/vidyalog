from datetime import datetime
from typing import Optional

from smolorm.sqlmodel import SqlModel


class PlaySessionModel(SqlModel):
    table_name: str = "play_sessions"
    session_start: datetime = datetime(1, 1, 1)
    session_end: Optional[datetime] = None
    backlog_entry: int = 0
