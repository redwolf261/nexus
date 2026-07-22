"""
Integration tests for Investigation Case management.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def _pg_available() -> bool:
    import socket
    try:
        s = socket.create_connection(("127.0.0.1", 5432), timeout=1)
        s.close()
        return True
    except OSError:
        return False

pg_up = _pg_available()
pg_reason = "PostgreSQL not reachable — required for Investigations"

@pytest.fixture
def new_inv():
    if not pg_up: pytest.skip(pg_reason)
    res = client.post("/api/investigations", json={"title": "Test Operation", "priority": "High"})
    assert res.status_code == 200
    return res.json()

@pytest.mark.skipif(not pg_up, reason=pg_reason)
def test_create_and_list_investigations(new_inv):
    res = client.get("/api/investigations")
    assert res.status_code == 200
    data = res.json()
    assert any(inv["id"] == new_inv["id"] for inv in data)

@pytest.mark.skipif(not pg_up, reason=pg_reason)
def test_investigation_entity_attachment(new_inv):
    inv_id = new_inv["id"]
    
    # Attach Entity
    res = client.post(f"/api/investigations/{inv_id}/entities?entity_type=FIR&entity_id=FIR-TEST-123")
    assert res.status_code == 200

    # Fetch Workspace
    ws_res = client.get(f"/api/investigations/{inv_id}/workspace")
    assert ws_res.status_code == 200
    ws = ws_res.json()
    
    assert "FIR" in ws["entities"]
    assert any(e.get("id") == "FIR-TEST-123" or e.get("fir_id") == "FIR-TEST-123" for e in ws["entities"]["FIR"])
    
    # Verify Timeline has entity added event
    assert any(evt["type"] == "System" and evt["entity_id"] == "FIR-TEST-123" for evt in ws["timeline"])

@pytest.mark.skipif(not pg_up, reason=pg_reason)
def test_investigation_notes(new_inv):
    inv_id = new_inv["id"]
    
    # Add Note
    res = client.post(f"/api/investigations/{inv_id}/notes", json={"markdown": "Target spotted at coordinates"})
    assert res.status_code == 200
    note = res.json()
    assert note["markdown"] == "Target spotted at coordinates"
    
    # Update Note
    res = client.patch(f"/api/investigations/notes/{note['id']}", json={"markdown": "Target apprehended"})
    assert res.status_code == 200
    
    # Check Workspace
    ws_res = client.get(f"/api/investigations/{inv_id}/workspace")
    ws = ws_res.json()
    assert len(ws["notes"]) == 1
    assert ws["notes"][0]["markdown"] == "Target apprehended"

@pytest.mark.skipif(not pg_up, reason=pg_reason)
def test_remove_entity(new_inv):
    inv_id = new_inv["id"]
    client.post(f"/api/investigations/{inv_id}/entities?entity_type=VEHICLE&entity_id=V-TEST")
    
    res = client.delete(f"/api/investigations/{inv_id}/entities/V-TEST?entity_type=VEHICLE")
    assert res.status_code == 200
    
    ws = client.get(f"/api/investigations/{inv_id}/workspace").json()
    assert "VEHICLE" not in ws["entities"] or len(ws["entities"]["VEHICLE"]) == 0
