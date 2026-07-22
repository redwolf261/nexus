"""
Tests for Intelligence module
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

@pytest.mark.skipif(not pg_up, reason="PostgreSQL not reachable")
def test_case_risk():
    # Attempt to fetch risk for a known case or a non-existent one
    res = client.get("/api/intelligence/risk/INV-999999")
    # Even if missing, should return default baseline zeroes
    assert res.status_code == 200
    data = res.json()
    assert "case_threat_score" in data
    assert "network_complexity" in data

@pytest.mark.skipif(not pg_up, reason="PostgreSQL not reachable")
def test_case_recommendations():
    res = client.get("/api/intelligence/recommendations/INV-999999")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

@pytest.mark.skipif(not pg_up, reason="PostgreSQL not reachable")
def test_entity_links():
    res = client.get("/api/intelligence/links/PERSON-123?entity_type=PERSON")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

@pytest.mark.skipif(not pg_up, reason="PostgreSQL not reachable")
def test_entity_risk():
    res = client.get("/api/intelligence/entity/PERSON-123?entity_type=PERSON")
    assert res.status_code == 200
    data = res.json()
    assert "threat_score" in data
    assert "repeat_offender_index" in data

@pytest.mark.skipif(not pg_up, reason="PostgreSQL not reachable")
def test_case_overlaps():
    res = client.get("/api/intelligence/overlaps/INV-999999")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
