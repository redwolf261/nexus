"""
NEXUS API contract tests.

PostgreSQL and Neo4j-dependent tests are automatically skipped when the 
databases are not reachable (e.g. CI without Docker, or local dev without Docker Desktop running).
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def _db_available(port: int) -> bool:
    """Return True if the local DB port is reachable."""
    import socket
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=1)
        s.close()
        return True
    except OSError:
        return False

neo4j_up = _db_available(7687)
pg_up = _db_available(5432)
neo4j_reason = "Neo4j not reachable — start Docker Desktop and run `docker compose up -d`"
pg_reason = "PostgreSQL not reachable — start Docker Desktop and run `docker compose up -d`"


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.skipif(not pg_up, reason=pg_reason)
def test_executive_dashboard():
    response = client.get("/api/dashboard/executive")
    assert response.status_code == 200
    data = response.json()
    assert "todays_firs" in data
    assert "active_campaigns" in data

@pytest.mark.skipif(not pg_up, reason=pg_reason)
def test_district_dashboard():
    response = client.get("/api/district/D-001")
    assert response.status_code == 200
    data = response.json()
    assert data["district_id"] == "D-001"
    assert "risk_score" in data

@pytest.mark.skipif(not pg_up, reason=pg_reason)
def test_omni_search():
    response = client.get("/api/search?q=robbery")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "robbery"
    assert "results" in data

@pytest.mark.skipif(not pg_up, reason=pg_reason)
def test_campaign_summary():
    response = client.get("/api/campaign/C-14/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["campaign_id"] == "C-14"
    assert "mastermind" in data

@pytest.mark.skipif(not pg_up, reason=pg_reason)
def test_fir_detail():
    response = client.get("/api/fir/FIR-123")
    assert response.status_code in [200, 404]

@pytest.mark.skipif(not pg_up, reason=pg_reason)
def test_person_detail():
    response = client.get("/api/person/P-123")
    assert response.status_code in [200, 404]

@pytest.mark.skipif(not pg_up, reason=pg_reason)
def test_vehicle_detail():
    response = client.get("/api/vehicle/V-123")
    assert response.status_code in [200, 404]

@pytest.mark.skipif(not pg_up, reason=pg_reason)
def test_criminal_detail():
    response = client.get("/api/criminal/C-123")
    assert response.status_code in [200, 404]

@pytest.mark.skipif(not neo4j_up, reason=neo4j_reason)
def test_cross_jurisdiction():
    response = client.get("/api/analytics/cross-jurisdiction?fir_id=FIR-123")
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "reasons" in data
    assert "linked_crimes" in data

@pytest.mark.skipif(not neo4j_up, reason=neo4j_reason)
def test_person_graph():
    response = client.get("/api/graph/person/P-001")
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "reasons" in data
    assert "neighbors" in data
