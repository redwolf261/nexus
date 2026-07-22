# Failure Injection & Analysis Report
**Phase 7.1 Analytical Intelligence**

## Objective
Identify how the Analytical Intelligence Engine degrades when external dependencies fail, when inputs are malformed, or when database connections time out. The goal is "Graceful Degradation"—the system should continue serving basic requests even if intelligence processing is offline.

---

## 1. Neo4j Unavailable (Graph Failure)
**Failure Scenario:** Neo4j database is unreachable.
**Degradation Path:** 
- `GraphAnalyticsEngine` intercepts `neo4j.exceptions.ServiceUnavailable`.
- Endpoints return `{"metrics": {}, "message": "Graph engine unavailable"}`.
- *Crucially*, the Workspace Dashboard (`investigations_service.py`) wraps graph intelligence calls in a `try/except` block. If Neo4j is offline, the workspace still loads normally, just without the "Graph Metrics" panel.

## 2. PostgreSQL Unavailable
**Failure Scenario:** PostgreSQL connection refused (as observed in local test runs).
**Degradation Path:** 
- Critical failure. The backend cannot serve CRUD endpoints, nor can it serve Intelligence. 
- Fast API returns `500 Internal Server Error` with SQLAlchemy timeout/connection refused logs.

## 3. Missing Scikit-Learn Dependency
**Failure Scenario:** Deployment server lacks `scikit-learn` in `requirements.txt`.
**Degradation Path:**
- `crime_series.py` and `spatial_analytics.py` catch the `ImportError` gracefully via a global `SKLEARN_AVAILABLE` flag.
- Requests to these endpoints return `{"error": "scikit-learn not installed", "series": []}`.
- Workspace loading continues unhindered.

## 4. Incomplete Data (Missing Coordinates / Timestamps)
**Failure Scenario:** 80% of FIRs lack `latitude` and `longitude`.
**Degradation Path:**
- `SpatialAnalyticsEngine` pre-filters `FIR.latitude.isnot(None)`. If the remaining valid FIR count drops below `SPATIAL_MIN_FIRS=3`, the engine returns `{"message": "Insufficient geo data"}` safely. It does not attempt to cluster null data.

## 5. Large Investigation (1000+ Attached Entities)
**Failure Scenario:** An analyst attaches 1000 FIRs to a single investigation workspace.
**Degradation Path:**
- The Workspace Service (`investigations_service.py`) slices inputs before passing to the Intelligence Engine.
- Graph Metrics are only computed for `person_ids[:5]`. 
- Crime Series detection parses all FIRs, but DBSCAN handles N=1000 efficiently.
- Event timelines are capped locally or via API pagination.

## Conclusion
The Analytical Engine fails closed (silently omits insights) rather than failing open (crashing the main application). Analysts will never be blocked from viewing a case file simply because an intelligence algorithm threw a math error or timed out.
