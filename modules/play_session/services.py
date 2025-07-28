from math import fsum
from datetime import datetime
from typing import Optional
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
        self.logger = logger

    # ===============================
    # PLAY SESSION TIMER OPERATIONS
    # ===============================

    def start_session(self, backlog_entry: int) -> PlaySession:
        session = self.session_repository.create(
            PlaySession(session_start=datetime.now(), backlog_entry=backlog_entry)
        )
        self.logger.debug(f"Start Play Session for backlog entry: {backlog_entry}")
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
                "session_start": session.session_start,
                "session_end": session.session_end,
            },
        )

        self.logger.debug(f"Stop Play Session {session_id}")
        return session

    def get_all_entry_sessions(self, backlog_entry: int) -> list[PlaySession]:
        result = self.session_repository.filter(
            filters={"backlog_entry": backlog_entry}
        )

        self.logger.debug(f"Get all play sessions for backlog entry {backlog_entry}")
        return result.result

    def get_max_playtime(self, backlog_entry: int) -> float:
        result = self.session_repository.filter(
            filters={"backlog_entry": backlog_entry}
        )

        sessions = result.result

        return fsum(s.time_played for s in sessions)

    def get_session(self, session_id: int) -> Optional[PlaySession]:
        session = self.session_repository.get_by_id(session_id)
        return session

    def get_all_sessions(self) -> list[PlaySession]:
        sessions = self.session_repository.list_all()
        return sessions

    def get_active_sessions(self) -> list[PlaySession]:
        result = self.session_repository.filter(
            filters={"session_end__isnull": ""}
        )  # Definitely not my proudest API, why not just: "session_end_eq":None
        return result.result

    def get_played_entries(self) -> set[int]:
        return set(
            [session.backlog_entry for session in self.session_repository.list_all()]
        )

    def get_entries_with_playtime(self) -> dict[int, float]:
        result = dict()

        for e in self.get_played_entries():
            result[e] = self.get_max_playtime(e)

        return result
