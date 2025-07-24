from datetime import datetime
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
            return 0.0

        return (self.session_end - self.session_start).total_seconds()
