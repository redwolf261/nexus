import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_system_status():
    res = client.get("/api/system/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "operational"
    assert "websockets" in data

def test_events_stream():
    res = client.get("/api/events")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_websocket_connection():
    with client.websocket_connect("/ws/test_channel") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert data == "pong"
