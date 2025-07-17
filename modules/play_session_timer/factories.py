from datetime import datetime
from modules.play_session_timer.models import InputPlaySession


class PlaySessionFactory:
    """Factory for creating PlaySession instances."""

    @staticmethod
    def create(session_start: datetime) -> InputPlaySession:
        """Create a PlaySession from creation data and assigned ID."""
        now = datetime.utcnow()
        return InputPlaySession(
            id=None,
            created_at=now,
            updated_at=now,
            session_start=session_start,
            session_end=None,
        )
