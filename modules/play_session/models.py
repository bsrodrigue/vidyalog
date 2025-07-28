from datetime import datetime
from libs.fmt.datetime_formatter import DateTimeFormatter
from modules.base.models import BaseDomainModel
from typing import Optional


class PlaySession(BaseDomainModel):
    """
    Tracks individual gaming sessions
    """

    session_start: datetime
    session_end: Optional[datetime] = None
    backlog_entry: int

    @property
    def time_played(self) -> float:
        if self.session_end is None:
            return (datetime.now() - self.session_start).total_seconds()

        return (self.session_end - self.session_start).total_seconds()

    @property
    def is_active(self) -> bool:
        return self.session_end is None

    def __str__(self) -> str:
        start = DateTimeFormatter.fmt(self.session_start)
        end = DateTimeFormatter.fmt(self.session_end) if self.session_end else ""

        status = "In Progress" if self.session_end is None else f"Ended: {end}"

        time_played = DateTimeFormatter.fmt_playtime(self.time_played)

        _str = f"{self.id}: Started {start} | {status} | Time Played: {time_played}"
        return _str
