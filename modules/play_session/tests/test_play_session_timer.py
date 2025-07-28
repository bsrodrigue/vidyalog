from math import fsum
import pytest
from modules.play_session.models import PlaySession
from modules.repositories.in_memory_repository import InMemoryRepository
from modules.play_session.services import PlaySessionService


@pytest.fixture
def service():
    session_repo = InMemoryRepository[int, PlaySession]()
    svc = PlaySessionService(session_repo)

    return svc, session_repo


def test_get_all_entry_sessions(service):
    svc, _ = service

    backlog_entry_1 = 1
    backlog_entry_2 = 2
    backlog_entry_3 = 3

    s1 = svc.start_session(backlog_entry_1)
    s2 = svc.start_session(backlog_entry_1)
    s3 = svc.start_session(backlog_entry_1)
    s4 = svc.start_session(backlog_entry_2)

    svc.stop_session(s1.id)
    svc.stop_session(s2.id)
    svc.stop_session(s3.id)
    svc.stop_session(s4.id)

    s1 = svc.get_session(s1.id)
    s2 = svc.get_session(s2.id)
    s3 = svc.get_session(s3.id)
    s4 = svc.get_session(s4.id)

    sessions_1 = svc.get_all_entry_sessions(backlog_entry_1)
    sessions_2 = svc.get_all_entry_sessions(backlog_entry_2)
    sessions_3 = svc.get_all_entry_sessions(backlog_entry_3)

    assert len(sessions_1) == 3
    assert len(sessions_2) == 1
    assert len(sessions_3) == 0

    assert s1 is sessions_1[0]
    assert s2 is sessions_1[1]
    assert s3 is sessions_1[2]
    assert s4 is sessions_2[0]


def test_get_max_playtime(service):
    svc, _ = service

    backlog_entry_1 = 1

    svc.stop_session(svc.start_session(backlog_entry_1).id)
    svc.stop_session(svc.start_session(backlog_entry_1).id)
    svc.stop_session(svc.start_session(backlog_entry_1).id)

    sessions = svc.get_all_entry_sessions(backlog_entry_1)
    time_played_1 = fsum(session.time_played for session in sessions)
    time_played_2 = svc.get_max_playtime(backlog_entry_1)

    assert (time_played_1) == (time_played_2)


def test_get_active_sessions(service):
    svc, _ = service

    backlog_entry_1 = 1

    svc.stop_session(svc.start_session(backlog_entry_1).id)
    svc.stop_session(svc.start_session(backlog_entry_1).id)
    svc.stop_session(svc.start_session(backlog_entry_1).id)

    active = svc.get_active_sessions()
    assert len(active) == 0

    svc.start_session(backlog_entry_1)
    active = svc.get_active_sessions()
    assert len(active) == 1
