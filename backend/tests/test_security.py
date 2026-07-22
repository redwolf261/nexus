from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_cors_preflight():
    response = client.options(
        "/api/firs",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_security_headers():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("content-security-policy") == "default-src 'self'"

def test_unauthorized_access():
    response = client.get("/api/firs")
    assert response.status_code == 401
