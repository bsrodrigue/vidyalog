import pytest
from datetime import datetime
from unittest.mock import Mock
from modules.play_session_timer.services import (
    PlaySessionTimerService,
    PlaySessionError,
)


class TestPlaySessionTimerService:
    """Test suite for PlaySessionTimerService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        return Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a PlaySessionTimerService instance with mocked repository."""
        return PlaySessionTimerService(mock_repository)

    @pytest.fixture
    def sample_session(self):
        """Create a mock PlaySession for testing."""
        session = Mock()
        session.id = 1
        session.created_at = datetime.now()
        session.updated_at = datetime.now()
        session.session_start = datetime.now()
        session.session_end = None
        return session

    @pytest.fixture
    def completed_session(self):
        """Create a mock completed PlaySession for testing."""
        session = Mock()
        session.id = 1
        session.created_at = datetime.now()
        session.updated_at = datetime.now()
        session.session_start = datetime.now()
        session.session_end = datetime.now()
        return session

    # ===============================
    # START SESSION TESTS
    # ===============================

    def test_start_session_creates_new_session(self, service, mock_repository):
        """Test that start_session calls repository.create with correct parameters."""
        # Arrange
        mock_session = Mock()
        mock_repository.create.return_value = mock_session

        # Act
        result = service.start_session()

        # Assert
        mock_repository.create.assert_called_once()
        created_session_arg = mock_repository.create.call_args[0][0]

        assert result == mock_session
        # Service should pass PlaySession with None ID and session_end
        assert created_session_arg.id is None
        assert created_session_arg.session_end is None
        assert isinstance(created_session_arg.session_start, datetime)
        assert isinstance(created_session_arg.created_at, datetime)
        assert isinstance(created_session_arg.updated_at, datetime)

    def test_start_session_sets_timestamps_correctly(self, service, mock_repository):
        """Test that start_session sets session_start timestamp."""
        # Arrange
        mock_session = Mock()
        mock_repository.create.return_value = mock_session

        # Act
        service.start_session()

        # Assert
        created_session_arg = mock_repository.create.call_args[0][0]

        # Service sets session_start timestamp
        assert isinstance(created_session_arg.session_start, datetime)

        # Session start should be recent (within 1 second)
        time_diff = abs(
            (datetime.now() - created_session_arg.session_start).total_seconds()
        )
        assert time_diff < 1

    # ===============================
    # STOP SESSION TESTS
    # ===============================

    def test_stop_session_updates_existing_session(
        self, service, mock_repository, sample_session
    ):
        """Test that stop_session updates an existing session with end time."""
        # Arrange
        session_id = 1
        mock_repository.get_by_id.return_value = sample_session
        mock_repository.update.return_value = sample_session

        # Act
        result = service.stop_session(session_id)

        # Assert
        mock_repository.get_by_id.assert_called_once_with(session_id)
        mock_repository.update.assert_called_once_with(sample_session)
        assert result == sample_session
        assert sample_session.session_end is not None
        assert isinstance(sample_session.session_end, datetime)

    def test_stop_session_raises_error_when_session_not_found(
        self, service, mock_repository
    ):
        """Test that stop_session raises PlaySessionError when session doesn't exist."""
        # Arrange
        session_id = 999
        mock_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(PlaySessionError) as exc_info:
            service.stop_session(session_id)

        assert (
            f"Error while stopping session: Session {session_id} does not exist"
            in str(exc_info.value)
        )
        mock_repository.get_by_id.assert_called_once_with(session_id)
        mock_repository.update.assert_not_called()

    def test_stop_session_sets_end_time_to_current_time(
        self, service, mock_repository, sample_session
    ):
        """Test that stop_session sets session_end to current time."""
        # Arrange
        session_id = 1
        mock_repository.get_by_id.return_value = sample_session
        mock_repository.update.return_value = sample_session

        # Act
        service.stop_session(session_id)

        # Assert
        assert sample_session.session_end is not None
        # Should be very recent (within 1 second)
        time_diff = abs((datetime.now() - sample_session.session_end).total_seconds())
        assert time_diff < 1

    # ===============================
    # GET ALL SESSIONS TESTS
    # ===============================

    def test_get_all_sessions_returns_all_sessions(self, service, mock_repository):
        """Test that get_all_sessions returns all sessions from repository."""
        # Arrange
        mock_sessions = [Mock(), Mock()]
        mock_repository.list_all.return_value = mock_sessions

        # Act
        result = service.get_all_sessions()

        # Assert
        mock_repository.list_all.assert_called_once()
        assert result == mock_sessions
        assert len(result) == 2

    def test_get_all_sessions_returns_empty_list_when_no_sessions(
        self, service, mock_repository
    ):
        """Test that get_all_sessions returns empty list when no sessions exist."""
        # Arrange
        mock_repository.list_all.return_value = []

        # Act
        result = service.get_all_sessions()

        # Assert
        mock_repository.list_all.assert_called_once()
        assert result == []
        assert isinstance(result, list)

    # ===============================
    # INTEGRATION-STYLE TESTS
    # ===============================

    def test_complete_session_workflow(self, service, mock_repository):
        """Test a complete workflow: start session, then stop it."""
        # Arrange
        mock_session = Mock()
        mock_session.id = 1
        mock_session.session_end = None

        mock_repository.create.return_value = mock_session
        mock_repository.get_by_id.return_value = mock_session
        mock_repository.update.return_value = mock_session

        # Act
        session = service.start_session()
        completed_session = service.stop_session(session.id)

        # Assert
        assert session == mock_session
        assert completed_session == mock_session
        # The service should have set session_end during stop_session
        assert mock_session.session_end is not None

    def test_repository_dependency_injection(self, mock_repository):
        """Test that the service properly accepts and uses the injected repository."""
        # Arrange & Act
        service = PlaySessionTimerService(mock_repository)

        # Assert
        assert service.session_repository is mock_repository

    # ===============================
    # INTEGRATION WITH INMEMORYREPOSITORY
    # ===============================

    def test_service_with_real_repository(self):
        """Test service with actual InMemoryRepository implementation."""
        from modules.repositories.repositories import InMemoryRepository

        # Arrange
        repo = InMemoryRepository()
        service = PlaySessionTimerService(repo)

        # Act - start a session
        session = service.start_session()

        # Assert - check repository behavior
        assert session.id == 1  # First ID assigned by repository
        assert session.session_end is None
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)
        assert isinstance(session.session_start, datetime)

        # Act - stop the session
        stopped_session = service.stop_session(session.id)

        # Assert - check repository behavior
        assert stopped_session.id == session.id
        assert stopped_session.session_end is not None
        assert stopped_session.updated_at >= session.updated_at

        # Act - get all sessions
        all_sessions = service.get_all_sessions()

        # Assert - check repository behavior
        assert len(all_sessions) == 1
        assert all_sessions[0].id == session.id
        assert all_sessions[0].session_end is not None

    def test_service_with_real_repository_multiple_sessions(self):
        """Test service with real repository handling multiple sessions."""
        from modules.repositories.repositories import InMemoryRepository

        # Arrange
        repo = InMemoryRepository()
        service = PlaySessionTimerService(repo)

        # Act - create multiple sessions
        session1 = service.start_session()
        session2 = service.start_session()
        service.stop_session(session1.id)

        # Assert - check repository behavior
        all_sessions = service.get_all_sessions()
        assert len(all_sessions) == 2

        # Check that sessions have different IDs
        session_ids = [s.id for s in all_sessions]
        assert session1.id in session_ids
        assert session2.id in session_ids
        assert session1.id != session2.id

    # ===============================
    # ERROR HANDLING TESTS
    # ===============================

    def test_play_session_error_inheritance(self):
        """Test that PlaySessionError properly inherits from Exception."""
        error = PlaySessionError("Test error message")
        assert isinstance(error, Exception)
        assert str(error) == "Test error message"

    def test_play_session_error_with_multiple_args(self):
        """Test that PlaySessionError handles multiple arguments."""
        error = PlaySessionError("Error", "Additional info", 123)
        assert isinstance(error, Exception)
        # The exact string representation depends on Python version, but should contain the args
        assert "Error" in str(error)
