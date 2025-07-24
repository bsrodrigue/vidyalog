from datetime import datetime
from libs.log.base_logger import ILogger
from libs.log.file_logger import FileLogger
from modules.exceptions.exceptions import ServiceError
from modules.play_session.models import PlaySession
from modules.repositories.abstract_repository import IRepository


class PlaySessionError(ServiceError):
    def __init__(self, message, message_markup=None, *args, **kwargs) -> None:
        super().__init__(message, message_markup=message_markup, *args, **kwargs)


class PlaySessionService:
    """Service layer for managing Play Session Timer."""

    def __init__(
        self,
        session_repository: IRepository[int, PlaySession],
        logger: ILogger = FileLogger("PlaySessionService"),
    ):
        self.session_repository = session_repository

    # ===============================
    # PLAY SESSION TIMER OPERATIONS
    # ===============================

    def start_session(self, backlog_entry: int) -> PlaySession:
        session = self.session_repository.create(
            PlaySession(session_start=datetime.now(), backlog_entry=backlog_entry)
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
