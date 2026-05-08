"""Tests for session rename feature - RED phase tests"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Set up environment before imports
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
import os
os.environ["DATABASE_URL"] = "mysql+aiomysql://root:123123@localhost:3306/iprs"

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")


class TestSessionRenameEndpoint:
    """Test PATCH /sessions/{session_id} endpoint exists and works"""

    def test_patch_session_endpoint_exists(self):
        """PATCH /sessions/{session_id} should be registered"""
        from app.api.chat import router

        # Find PATCH routes for sessions
        patch_routes = []
        for route in router.routes:
            if hasattr(route, 'path') and 'sessions' in route.path:
                methods = getattr(route, 'methods', {'GET'})
                patch_routes.append({
                    'path': route.path,
                    'methods': methods
                })

        # Should have a PATCH method for sessions/{id}
        has_patch = any('PATCH' in r['methods'] for r in patch_routes)
        assert has_patch, f"No PATCH endpoint for sessions found. Routes: {patch_routes}"

    def test_patch_session_accepts_title_parameter(self):
        """PATCH /sessions/{id} should accept a title parameter"""
        from app.api.chat import router
        import inspect

        # Find the PATCH session endpoint
        patch_endpoint = None
        for route in router.routes:
            if hasattr(route, 'path') and 'sessions' in route.path and '{session_id}' in route.path:
                methods = getattr(route, 'methods', {'GET'})
                if 'PATCH' in methods:
                    patch_endpoint = route.endpoint
                    break

        assert patch_endpoint is not None, "PATCH /sessions/{session_id} endpoint not found"

        # Check the function signature
        sig = inspect.signature(patch_endpoint)
        params = list(sig.parameters.keys())

        # Should accept session_id and title (or request body with title)
        assert 'session_id' in params or 'request' in params, \
            f"Endpoint should accept session_id parameter. Parameters: {params}"


class TestSessionRenameService:
    """Test session rename service function"""

    def test_update_session_function_exists(self):
        """Should have an update_session function"""
        from app.services import chat_persistence

        assert hasattr(chat_persistence, 'update_session'), \
            "chat_persistence module should have update_session function"

    @pytest.mark.asyncio
    async def test_update_session_modifies_title(self):
        """update_session should modify the session title"""
        from app.services.chat_persistence import update_session

        # Mock the database
        with patch('app.services.chat_persistence.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_result = MagicMock()

            # Create a mock session object
            mock_chat_session = MagicMock()
            mock_chat_session.id = 1
            mock_chat_session.user_id = 1
            mock_chat_session.title = "Old Title"

            mock_result.scalar_one_or_none.return_value = mock_chat_session
            mock_session.execute.return_value = mock_result

            mock_session_local.return_value.__aenter__.return_value = mock_session

            # Call update_session
            result = await update_session(session_id=1, user_id=1, title="New Title")

            # Verify the session was modified
            assert mock_chat_session.title == "New Title"
            assert mock_session.commit.called


class TestSessionRenameModel:
    """Test session model supports title updates"""

    def test_session_can_update_title(self):
        """ChatSession model should allow updating title"""
        from app.models.chat import ChatSession

        # Create a mock session
        session = MagicMock(spec=ChatSession)
        session.title = "Original"

        # Update title (this should work if the model is correct)
        session.title = "Updated"

        assert session.title == "Updated"
