"""
Tests for /api/sync-schedule endpoint
TDD: These tests are written BEFORE implementation
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_sync_token(monkeypatch):
    """Set a test sync token"""
    from src.core import config
    monkeypatch.setattr(config, "SYNC_SECRET_TOKEN", "test-secret-token")


@pytest.fixture
def client(mock_sync_token):
    """Create test client with mocked token"""
    from src.app.server import app
    return TestClient(app)


class TestSyncScheduleEndpoint:
    """Tests for /api/sync-schedule endpoint"""
    
    def test_no_token_returns_401(self, client):
        """Request without token should return 401 Unauthorized"""
        response = client.get("/api/sync-schedule")
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"
    
    def test_wrong_token_returns_401(self, client):
        """Request with incorrect token should return 401 Unauthorized"""
        response = client.get("/api/sync-schedule?token=wrong-token")
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"
    
    def test_correct_token_returns_200(self, client):
        """Request with correct token should return 200 and start sync"""
        with patch("src.app.server._run_sync_with_safeguards"):
            response = client.get("/api/sync-schedule?token=test-secret-token")
            assert response.status_code == 200
            assert response.json()["status"] == "started"
    
    def test_concurrent_request_returns_skipped(self, client):
        """Second request while sync in progress should be skipped"""
        import src.app.server as server_module
        
        # Simulate sync in progress
        with server_module._sync_lock:
            original_value = server_module._sync_in_progress
            server_module._sync_in_progress = True
        
        try:
            response = client.get("/api/sync-schedule?token=test-secret-token")
            assert response.status_code == 200
            assert response.json()["status"] == "skipped"
            assert "already in progress" in response.json()["message"]
        finally:
            # Restore original state
            with server_module._sync_lock:
                server_module._sync_in_progress = original_value
    
    def test_sync_calls_fetch_and_sync(self, client):
        """Verify fetch_and_sync is called in background"""
        import src.app.server as server_module
        
        # Ensure clean state
        with server_module._sync_lock:
            server_module._sync_in_progress = False

        # Patch the ThreadPoolExecutor submit method directly on the object instance
        with patch.object(server_module._sync_executor, "submit") as mock_submit:
            response = client.get("/api/sync-schedule?token=test-secret-token")
            assert response.status_code == 200
            assert response.json()["status"] == "started"  # Ensure it wasn't skipped
            mock_submit.assert_called_once()
