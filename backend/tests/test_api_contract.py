import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_executive_dashboard():
    response = client.get("/api/dashboard/executive")
    assert response.status_code == 200
    data = response.json()
    assert "todays_firs" in data
    assert "active_campaigns" in data

def test_district_dashboard():
    response = client.get("/api/district/D-001")
    assert response.status_code == 200
    data = response.json()
    assert data["district_id"] == "D-001"
    assert "risk_score" in data

def test_cross_jurisdiction():
    response = client.get("/api/analytics/cross-jurisdiction?fir_id=FIR-123")
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "reasons" in data
    assert "linked_crimes" in data

def test_person_graph():
    response = client.get("/api/graph/person/P-001")
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "reasons" in data
    assert "neighbors" in data

def test_omni_search():
    response = client.get("/api/search?q=robbery")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "robbery"
    assert "results" in data

def test_campaign_summary():
    response = client.get("/api/campaign/C-14/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["campaign_id"] == "C-14"
    assert "mastermind" in data
