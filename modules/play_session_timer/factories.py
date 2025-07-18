from datetime import datetime
from typing import Optional
from modules.play_session_timer.models import InputPlaySession


class PlaySessionFactory:
    """Factory for creating PlaySession instances."""

    @staticmethod
    def create(
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        session_start: Optional[datetime] = None,
        session_end: Optional[datetime] = None,
    ) -> InputPlaySession:
        """Create a PlaySession from creation data and assigned ID."""

        return InputPlaySession(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            session_start=session_start or datetime.now(),
            session_end=session_end,
        )
