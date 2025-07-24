from datetime import datetime
from modules.play_session.models import PlaySession
from modules.repositories.abstract_repository import IRepository


class PlaySessionError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class PlaySessionTimerService:
    """Service layer for managing Play Session Timer."""

    def __init__(self, session_repository: IRepository[int, PlaySession]):
        self.session_repository = session_repository

    # ===============================
    # PLAY SESSION TIMER OPERATIONS
    # ===============================

    def start_session(self) -> PlaySession:
        session = self.session_repository.create(
            PlaySession(session_start=datetime.now(), backlog_entry=0)
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
            {
                "id": session.id,
                "created_at": session.created_at,
                "updated_at": now,
                "session_start": session.session_start,
                "session_end": session.session_end,
            },
        )

        return session

    def get_all_sessions(self) -> list[PlaySession]:
        sessions = self.session_repository.list_all()
        return sessions
