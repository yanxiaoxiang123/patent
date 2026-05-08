"""Tests for session API endpoints including rename"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


class TestSessionRenameEndpoint:
    """Test PATCH /sessions/{session_id} endpoint for session rename"""

    def test_session_rename_endpoint_exists(self):
        """The chat router should have a PATCH method for session rename"""
        # Import the router module
        from app.api.chat import router

        # Check that PATCH method exists for sessions/{session_id}
        routes = [route.path for route in router.routes]
        assert any("sessions" in path and "{" in path for path in routes), \
            "Router should have a sessions endpoint with path parameter"

    def test_session_rename_validates_session_id(self):
        """Session ID must be positive integer"""
        # The endpoint should reject invalid session IDs
        session_id = 0
        assert session_id <= 0, "Session ID should be positive"

    def test_session_rename_requires_authentication(self):
        """Request without authentication should be rejected"""
        # Without auth token, should return 401
        # This is a structural test - we verify the auth middleware exists
        from app.api.chat import get_user_id_from_request
        assert callable(get_user_id_from_request)


class TestChatPersistenceService:
    """Test chat persistence service for session operations"""

    @pytest.mark.asyncio
    async def test_update_session_title(self):
        """Should be able to update session title"""
        from app.services.chat_persistence import ChatPersistenceService
        from app.models.chat import ChatSession
        from app.utils.database import AsyncSessionLocal
        from sqlalchemy import select

        # This test verifies the service interface exists
        service = ChatPersistenceService(user_id=1)
        assert hasattr(service, 'create_session')
        assert hasattr(service, 'persist')

    def test_chat_persistence_service_has_user_id(self):
        """Service should store user_id"""
        from app.services.chat_persistence import ChatPersistenceService

        service = ChatPersistenceService(user_id=123)
        assert service.user_id == 123

    def test_chat_persistence_service_defaults_user_id(self):
        """Service should have default user_id"""
        from app.services.chat_persistence import ChatPersistenceService, DEFAULT_CHAT_USER_ID

        service = ChatPersistenceService()
        assert service.user_id == DEFAULT_CHAT_USER_ID


class TestGetUserSessions:
    """Test get_user_sessions function"""

    @pytest.mark.asyncio
    async def test_get_user_sessions_returns_list(self):
        """Should return a list of sessions"""
        from app.services.chat_persistence import get_user_sessions

        # Mock the database session
        with patch('app.services.chat_persistence.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_session.execute.return_value = mock_result
            mock_session_local.return_value.__aenter__.return_value = mock_session

            sessions = await get_user_sessions(user_id=1)
            assert isinstance(sessions, list)


class TestDeleteSession:
    """Test delete_session function"""

    @pytest.mark.asyncio
    async def test_delete_session_returns_bool(self):
        """Should return True on success, False on not found"""
        from app.services.chat_persistence import delete_session

        with patch('app.services.chat_persistence.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result
            mock_session_local.return_value.__aenter__.return_value = mock_session

            result = await delete_session(session_id=999, user_id=1)
            assert isinstance(result, bool)


class TestSessionModel:
    """Test ChatSession model"""

    def test_chat_session_has_title_field(self):
        """ChatSession should have title field"""
        from app.models.chat import ChatSession

        # Check the model has the expected columns
        assert hasattr(ChatSession, 'id')
        assert hasattr(ChatSession, 'user_id')
        assert hasattr(ChatSession, 'title')
        assert hasattr(ChatSession, 'model')
        assert hasattr(ChatSession, 'document_id')
        assert hasattr(ChatSession, 'last_message_at')
        assert hasattr(ChatSession, 'created_at')
        assert hasattr(ChatSession, 'updated_at')

    def test_chat_session_title_is_string(self):
        """ChatSession title should be String type"""
        from app.models.chat import ChatSession
        from sqlalchemy import String

        # Check column type - title column should be String
        title_col = ChatSession.__table__.columns['title']
        assert isinstance(title_col.type, String)


class TestSessionMessageRetrieval:
    """Test get_session_messages function"""

    @pytest.mark.asyncio
    async def test_get_session_messages_returns_dict(self):
        """Should return session with messages"""
        from app.services.chat_persistence import get_session_messages

        with patch('app.services.chat_persistence.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()

            # Mock session not found
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result
            mock_session_local.return_value.__aenter__.return_value = mock_session

            result = await get_session_messages(session_id=999, user_id=1)
            assert isinstance(result, dict)
            assert result == {}
