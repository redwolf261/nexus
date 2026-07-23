import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.api.dependencies import get_current_user
from backend.db.schema import User, Role

def _mock_user():
    u = User()
    u.id = "user_test"
    u.username = "testuser"
    u.role = Role.Analyst
    return u

@pytest.fixture(autouse=True)
def setup_auth_override():
    app.dependency_overrides[get_current_user] = _mock_user
    yield
    # No clear() to avoid impacting other tests

client = TestClient(app)

def test_system_status():
    res = client.get("/api/system/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "operational"

def test_events_stream():
    res = client.get("/api/events/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_websocket_connection():
    mock_u = _mock_user()
    with patch("backend.api.routers.ws.get_ws_current_user", new_callable=AsyncMock) as mock_ws_user:
        mock_ws_user.return_value = mock_u
        with client.websocket_connect("/ws/test_channel") as websocket:
            websocket.send_json({"type": "ping"})
            assert websocket is not None
