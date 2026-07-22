"""
Phase 7.1 Analytical Intelligence Integration Tests

Tests all endpoints in backend/api/routers/intelligence.py
Validates API contracts, explainability inclusion, and status codes.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import get_db

client = TestClient(app)

# ===========================================================================
# Mock Dependency
# ===========================================================================

def override_get_db():
    from unittest.mock import MagicMock
    db = MagicMock()
    return db

def override_get_current_user():
    return {"sub": "test_user", "role": "admin"}

app.dependency_overrides[get_db] = override_get_db
from backend.auth.deps import get_current_user
app.dependency_overrides[get_current_user] = override_get_current_user

# ===========================================================================
# Phase 7 Endpoints
# ===========================================================================

def test_entity_resolution_endpoint():
    with pytest.MonkeyPatch.context() as m:
        # Mock the engine
        def mock_resolve(*args, **kwargs):
            return {
                "entity_id": "P-1",
                "primary_matches": [
                    {
                        "candidate_id": "P-2",
                        "match_score": 0.85,
                        "explanation": {
                            "inference_type": "ENTITY_MATCH",
                            "observation": "test",
                            "evidence": [],
                            "analytical_rule": "test",
                            "inference": "test",
                            "confidence": {"overall_confidence": 0.9}
                        }
                    }
                ]
            }
        import backend.intelligence.entity_resolution as er
        m.setattr(er.EntityResolutionEngine, "resolve_person", mock_resolve)

        response = client.get("/api/intelligence/entity-resolution/P-1?entity_type=PERSON")
        assert response.status_code == 200
        data = response.json()
        assert "primary_matches" in data
        assert len(data["primary_matches"]) > 0
        assert "explanation" in data["primary_matches"][0]


def test_crime_series_endpoint():
    with pytest.MonkeyPatch.context() as m:
        def mock_detect(*args, **kwargs):
            return {
                "total_firs_analyzed": 100,
                "series": [
                    {
                        "series_id": "S-1",
                        "explanation": {
                            "inference_type": "CRIME_SERIES",
                            "observation": "test",
                            "evidence": [],
                            "analytical_rule": "test",
                            "inference": "test",
                            "confidence": {"overall_confidence": 0.9}
                        }
                    }
                ]
            }
        import backend.intelligence.crime_series as cs
        m.setattr(cs.CrimeSeriesEngine, "detect_series", mock_detect)

        response = client.get("/api/intelligence/crime-series")
        assert response.status_code == 200
        data = response.json()
        assert "series" in data
        assert "total_firs_analyzed" in data
        assert "explanation" in data["series"][0]


def test_graph_analysis_endpoint():
    with pytest.MonkeyPatch.context() as m:
        def mock_get_metrics(*args, **kwargs):
            return {
                "entity_id": "P-1",
                "metrics": {
                    "pagerank": {"score": 0.9, "algorithm": "cypher"}
                }
            }
        import backend.intelligence.graph_analytics as ga
        m.setattr(ga.GraphAnalyticsEngine, "get_entity_metrics", mock_get_metrics)

        response = client.get("/api/intelligence/graph-analysis/P-1")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "pagerank" in data["metrics"]


def test_temporal_analysis_endpoint():
    with pytest.MonkeyPatch.context() as m:
        def mock_detect_anomalies(*args, **kwargs):
            return {
                "total_alerts": 1,
                "alerts": [
                    {
                        "alert_type": "CRIME_SPIKE",
                        "explanation": {
                            "inference_type": "TEMPORAL_ANOMALY",
                            "observation": "test",
                            "evidence": [],
                            "analytical_rule": "test",
                            "inference": "test",
                            "confidence": {"overall_confidence": 0.9}
                        }
                    }
                ]
            }
        import backend.intelligence.temporal_analytics as ta
        m.setattr(ta.TemporalAnalyticsEngine, "detect_anomalies", mock_detect_anomalies)

        response = client.get("/api/intelligence/temporal")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "explanation" in data["alerts"][0]


def test_spatial_analysis_endpoint():
    with pytest.MonkeyPatch.context() as m:
        def mock_detect_hotspots(*args, **kwargs):
            return {
                "total_clusters": 1,
                "clusters": [
                    {
                        "cluster_id": "C-1",
                        "explanation": {
                            "inference_type": "SPATIAL_CLUSTER",
                            "observation": "test",
                            "evidence": [],
                            "analytical_rule": "test",
                            "inference": "test",
                            "confidence": {"overall_confidence": 0.9}
                        }
                    }
                ]
            }
        import backend.intelligence.spatial_analytics as sa
        m.setattr(sa.SpatialAnalyticsEngine, "detect_hotspot_clusters", mock_detect_hotspots)

        response = client.get("/api/intelligence/spatial")
        assert response.status_code == 200
        data = response.json()
        assert "clusters" in data
        assert "explanation" in data["clusters"][0]
