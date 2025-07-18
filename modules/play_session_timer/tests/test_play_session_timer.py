import pytest
from datetime import datetime
from modules.repositories.repositories import InMemoryRepository
from modules.play_session_timer.services import (
    PlaySessionTimerService,
    PlaySessionError,
)


@pytest.fixture
def repository():
    return InMemoryRepository()


@pytest.fixture
def service(repository):
    return PlaySessionTimerService(repository)


# ===============================
# START SESSION TESTS
# ===============================


def test_start_session_creates_new_session(service: PlaySessionTimerService):
    session = service.start_session()

    assert session.id == 1
    assert isinstance(session.session_start, datetime)
    assert session.session_end is None
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.updated_at, datetime)


def test_start_session_sets_timestamps_correctly(service):
    session = service.start_session()

    now = datetime.now()
    assert isinstance(session.session_start, datetime)
    assert abs((now - session.session_start).total_seconds()) < 1


# ===============================
# STOP SESSION TESTS
# ===============================


def test_stop_session_updates_existing_session(service):
    session = service.start_session()
    updated = service.stop_session(session.id)

    assert updated.session_end is not None
    assert isinstance(updated.session_end, datetime)


def test_stop_session_sets_end_time_to_current_time(service):
    session = service.start_session()
    stopped = service.stop_session(session.id)

    now = datetime.now()
    assert stopped.session_end is not None
    assert abs((now - stopped.session_end).total_seconds()) < 1


def test_stop_session_raises_error_when_session_not_found(service):
    with pytest.raises(PlaySessionError) as exc_info:
        service.stop_session(999)

    assert "does not exist" in str(exc_info.value)


# ===============================
# GET ALL SESSIONS TESTS
# ===============================


def test_get_all_sessions_returns_all_sessions(service):
    session1 = service.start_session()
    session2 = service.start_session()
    sessions = service.get_all_sessions()

    assert len(sessions) == 2
    assert session1 in sessions
    assert session2 in sessions


def test_get_all_sessions_returns_empty_list_when_no_sessions(service):
    sessions = service.get_all_sessions()
    assert sessions == []


# ===============================
# INTEGRATION-STYLE TESTS
# ===============================


def test_complete_session_workflow(service):
    session = service.start_session()
    completed = service.stop_session(session.id)

    assert completed.id == session.id
    assert completed.session_end is not None


def test_service_with_real_repository_multiple_sessions(service):
    session1 = service.start_session()
    session2 = service.start_session()
    service.stop_session(session1.id)

    all_sessions = service.get_all_sessions()
    assert len(all_sessions) == 2

    ids = [s.id for s in all_sessions]
    assert session1.id in ids
    assert session2.id in ids
    assert session1.id != session2.id


# ===============================
# ERROR HANDLING TESTS
# ===============================


def test_play_session_error_inheritance():
    error = PlaySessionError("Test error message")
    assert isinstance(error, Exception)
    assert str(error) == "Test error message"


def test_play_session_error_with_multiple_args():
    error = PlaySessionError("Error", "Details", 123)
    assert isinstance(error, Exception)
    assert "Error" in str(error)
