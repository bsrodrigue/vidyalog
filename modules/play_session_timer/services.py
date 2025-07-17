from datetime import datetime
from modules.play_session_timer.factories import (
    PlaySessionFactory,
)
from modules.play_session_timer.models import InputPlaySession, PlaySession
from modules.repositories.repositories import BaseRepository


class PlaySessionError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class PlaySessionTimerService:
    """Service layer for managing Play Session Timer."""

    def __init__(
        self, session_repository: BaseRepository[InputPlaySession, PlaySession]
    ):
        self.session_repository = session_repository

    # ===============================
    # PLAY SESSION TIMER OPERATIONS
    # ===============================

    def start_session(self) -> PlaySession:
        session = self.session_repository.create(
            PlaySessionFactory.create(session_start=datetime.now())
        )
        return session

    def stop_session(self, session_id: int) -> PlaySession:
        session = self.session_repository.get_by_id(session_id)

        if session is None:
            raise PlaySessionError(
                f"Error while stopping session: Session {session_id} does not exist"
            )

        now = datetime.now()

        session.session_end = now

        session = self.session_repository.update(
            session_id,
            InputPlaySession(
                id=session.id,
                created_at=session.created_at,
                updated_at=now,
                session_start=session.session_start,
                session_end=session.session_end,
            ),
        )

        return session

    def get_all_sessions(self) -> list[PlaySession]:
        sessions = self.session_repository.list_all()
        return sessions
