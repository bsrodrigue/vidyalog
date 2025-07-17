from dataclasses import dataclass
from datetime import datetime
from modules.base.models import InputBaseModel, RepositoryBaseModel
from typing import Optional


@dataclass
class InputPlaySession(InputBaseModel):
    """
    Tracks individual gaming sessions
    """

    session_start: datetime
    session_end: Optional[datetime] = None

    @staticmethod
    def from_dict(args: dict):
        return InputPlaySession(**args)


class PlaySession(RepositoryBaseModel):
    """
    Tracks individual gaming sessions
    """

    session_start: datetime
    session_end: Optional[datetime] = None

    @property
    def time_played(self) -> float:
        if self.session_end is None:
            return 0.0

        return (self.session_end - self.session_start).total_seconds()
