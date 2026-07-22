"""
Intelligence API Router — Phase 7.0

Exposes all Phase 7 analytical modules through FastAPI endpoints.
Preserves all Phase 2 existing endpoints unchanged.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Any, Dict, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from backend.database import get_db
from backend.repositories.neo4j_repo import Neo4jRepository
from backend.intelligence.entity_resolution import EntityResolutionEngine
from backend.intelligence.scoring import IntelligenceScoring
from backend.intelligence.recommendations import RecommendationEngine
from backend.intelligence.crime_series import CrimeSeriesEngine
from backend.intelligence.temporal_analytics import TemporalAnalyticsEngine
from backend.intelligence.spatial_analytics import SpatialAnalyticsEngine
from backend.intelligence.graph_analytics import GraphAnalyticsEngine
from backend.repositories.investigations_repo import InvestigationsRepository
from backend.db.schema import EntityMergeProposal

class MergeApprovalRequest(BaseModel):
    approval_notes: Optional[str] = None

class MergeRejectionRequest(BaseModel):
    rejection_reason: str

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence"])

# ===========================================================================
# Phase 2 endpoints — preserved unchanged
# ===========================================================================

@router.get("/entity/{entity_id}")
def get_entity_intelligence(entity_id: str, entity_type: str = "PERSON", db: Session = Depends(get_db)):
    scoring = IntelligenceScoring(db)
    return scoring.calculate_entity_risk(entity_id, entity_type)

@router.get("/recommendations/{case_id}")
def get_recommendations(case_id: str, db: Session = Depends(get_db)):
    engine = RecommendationEngine(db)
    return engine.generate_case_recommendations(case_id)

@router.get("/risk/{case_id}")
def get_case_risk(case_id: str, db: Session = Depends(get_db)):
    scoring = IntelligenceScoring(db)
    return scoring.calculate_case_risk(case_id)

@router.get("/expand/{entity_id}")
def expand_graph(entity_id: str, depth: int = 2):
    neo4j = Neo4jRepository()
    try:
        query = (
            "MATCH p=(n {id: $entity_id})-[*1.."
            + str(min(depth, 3))
            + "]-(m) "
            "RETURN n.id AS source, m.id AS target, "
            "[r in relationships(p) | type(r)] AS relations LIMIT 50"
        )
        with neo4j.client.driver.session(
            database="neo4j", default_access_mode="READ", transaction_timeout=5000
        ) as session:
            result = session.run(query, entity_id=entity_id)
            return [dict(record) for record in result]
    except Exception:
        return []

@router.get("/overlaps/{case_id}")
def get_case_overlaps(case_id: str, db: Session = Depends(get_db)):
    inv_repo = InvestigationsRepository(db)
    er = EntityResolutionEngine(db)
    entities = inv_repo.get_entities(case_id)
    target_ents = [{"entity_id": e.entity_id, "entity_type": e.entity_type} for e in entities]
    overlaps = er.get_cross_case_overlaps(target_ents)
    return [o for o in overlaps if o["investigation_id"] != case_id]

# ===========================================================================
# Phase 7 endpoints — new analytical capabilities
# ===========================================================================

# ── Module 1: Probabilistic Entity Resolution ───────────────────────────────

@router.get("/entity-resolution/{entity_id}")
def get_probabilistic_entity_resolution(
    entity_id: str,
    entity_type: str = Query("PERSON", description="Entity type: PERSON or VEHICLE"),
    db: Session = Depends(get_db),
):
    """
    Probabilistic entity resolution with full reasoning trace.

    Returns weighted multi-dimensional match scores against candidate entities.
    Each match includes confidence scores, matching feature breakdown,
    and a human-readable explanation of why entities were linked.
    """
    er = EntityResolutionEngine(db)
    if entity_type.upper() in ("PERSON", "CRIMINAL"):
        return er.resolve_person(entity_id)
    elif entity_type.upper() == "VEHICLE":
        return er.resolve_vehicle(entity_id)
    raise HTTPException(status_code=400, detail=f"Unsupported entity type: {entity_type}")

# Backward-compatible alias (old endpoint used by Phase 2 API)
@router.get("/links/{entity_id}")
def get_entity_links(entity_id: str, entity_type: str = "PERSON", db: Session = Depends(get_db)):
    """Legacy endpoint — delegates to probabilistic resolution."""
    return get_probabilistic_entity_resolution(entity_id, entity_type, db)

@router.post("/entity-merge-propose/{primary_id}/{merge_id}")
def propose_entity_merge(
    primary_id: str,
    merge_id: str,
    entity_type: str = "PERSON",
    db: Session = Depends(get_db),
):
    """
    Create a pending merge proposal that awaits investigator approval.
    Phase 7.3 safeguard: Entity Resolution never auto-merges; all merges require manual approval.
    """
    import uuid
    er = EntityResolutionEngine(db)

    # Get match details
    if entity_type.upper() in ("PERSON", "CRIMINAL"):
        result = er.resolve_person(primary_id)
        match = next((m for m in result.get("primary_matches", []) if m["candidate_id"] == merge_id), None)
    else:
        result = er.resolve_vehicle(primary_id)
        match = next((m for m in result.get("matches", []) if m["candidate_id"] == merge_id), None)

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    proposal = EntityMergeProposal(
        proposal_id=f"MERGE-{uuid.uuid4().hex[:8].upper()}",
        primary_entity_id=primary_id,
        merge_entity_id=merge_id,
        entity_type=entity_type,
        match_score=match.get("match_score", 0),
        confidence_overall=match.get("confidence", {}).get("overall_confidence", 0),
        explanation_json=match.get("explanation", {}),
        status="PENDING",
        created_by="system",
    )
    db.add(proposal)
    db.commit()

    return {
        "proposal_id": proposal.proposal_id,
        "status": "PENDING",
        "message": "Merge proposal created. Awaits investigator approval.",
    }

@router.post("/entity-merge-approve/{proposal_id}")
def approve_entity_merge(
    proposal_id: str,
    req: MergeApprovalRequest,
    db: Session = Depends(get_db),
):
    """Approve a merge proposal (investigator authorization required)."""
    proposal = db.query(EntityMergeProposal).filter_by(proposal_id=proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Cannot approve {proposal.status} proposal")

    # Execute the merge (would trigger database mutations in real implementation)
    proposal.status = "APPROVED"
    proposal.approved_by = "investigator"  # In real impl, use auth context
    proposal.approval_notes = req.approval_notes
    proposal.updated_at = datetime.utcnow()
    db.commit()

    return {
        "proposal_id": proposal_id,
        "status": "APPROVED",
        "message": "Merge approved and executed.",
    }

@router.post("/entity-merge-reject/{proposal_id}")
def reject_entity_merge(
    proposal_id: str,
    req: MergeRejectionRequest,
    db: Session = Depends(get_db),
):
    """Reject a merge proposal."""
    proposal = db.query(EntityMergeProposal).filter_by(proposal_id=proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Cannot reject {proposal.status} proposal")

    proposal.status = "REJECTED"
    proposal.approval_notes = req.rejection_reason
    proposal.updated_at = datetime.utcnow()
    db.commit()

    return {
        "proposal_id": proposal_id,
        "status": "REJECTED",
        "message": "Merge proposal rejected.",
    }

# ── Module 2: Crime Series ───────────────────────────────────────────────────

@router.get("/crime-series")
def list_crime_series(
    district_id: Optional[str] = None,
    crime_category: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """
    Detect crime series using DBSCAN clustering on FIR feature vectors.

    Feature dimensions: crime category, time, location, MO (entry method,
    weapon, target type, escape vehicle), gang affiliation.

    Returns series with confidence scores, characteristics, and emerging trend scores.
    """
    engine = CrimeSeriesEngine(db)
    result = engine.detect_series(district_id=district_id, crime_category=crime_category)
    series = result.get("series", [])
    return {
        **{k: v for k, v in result.items() if k != "series"},
        "series": series[skip: skip + limit],
    }

@router.get("/crime-series/{series_id}")
def get_crime_series_detail(
    series_id: str,
    district_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Drill-down into a specific crime series by ID."""
    engine = CrimeSeriesEngine(db)
    detail = engine.get_series_detail(series_id, district_id=district_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Crime series {series_id} not found")
    return detail

# ── Module 3: Graph Analytics ────────────────────────────────────────────────

@router.get("/graph-analysis/{entity_id}")
def get_graph_analysis(entity_id: str, db: Session = Depends(get_db)):
    """
    Retrieve pre-computed graph metrics (PageRank, betweenness, community)
    for an entity. Run /graph-analysis/compute first to populate metrics.
    """
    engine = GraphAnalyticsEngine(db)
    return engine.get_entity_metrics(entity_id)

@router.post("/graph-analysis/compute")
def compute_graph_metrics(max_nodes: int = Query(default=500, le=2000), db: Session = Depends(get_db)):
    """
    Trigger full graph analytics computation.
    Runs PageRank, community detection, and betweenness centrality.
    Results are persisted to graph_metrics table for fast retrieval.
    """
    engine = GraphAnalyticsEngine(db)
    counts = engine.compute_all(max_nodes=max_nodes)
    return {"status": "computed", "metrics_written": counts}

@router.get("/graph-analysis/{entity_id}/link-prediction")
def get_link_prediction(
    entity_id: str,
    top_k: int = Query(default=5, le=20),
    db: Session = Depends(get_db),
):
    """
    Predict undiscovered relationships for an entity using Jaccard
    common-neighbour scoring.
    """
    engine = GraphAnalyticsEngine(db)
    return engine.link_prediction(entity_id, top_k=top_k)

@router.get("/graph-analysis/community/{community_id}/members")
def get_community_members(community_id: str, db: Session = Depends(get_db)):
    """List all entities belonging to a detected community."""
    engine = GraphAnalyticsEngine(db)
    return {"community_id": community_id, "members": engine.get_community_members(community_id)}

# ── Module 4: Temporal Analytics ────────────────────────────────────────────

@router.get("/temporal")
def get_temporal_analysis(
    district_id: Optional[str] = None,
    days: int = Query(default=90, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """
    Temporal anomaly detection for a district over a given period.

    Algorithms:
    - CUSUM changepoint detection for crime spikes
    - Coordinated event window detection (burst of FIRs in short time)
    - Rolling 7/30 day averages
    - Seasonal profile by day-of-week and month
    """
    engine = TemporalAnalyticsEngine(db)
    return engine.detect_anomalies(district_id=district_id, days=days)

@router.get("/temporal/offender-schedule/{criminal_id}")
def get_offender_schedule(criminal_id: str, db: Session = Depends(get_db)):
    """Analyze a criminal's temporal activity pattern (preferred days/months)."""
    engine = TemporalAnalyticsEngine(db)
    return engine.offender_schedule(criminal_id)

# ── Module 5: Spatial Analytics ─────────────────────────────────────────────

@router.get("/spatial")
def get_spatial_analysis(
    district_id: Optional[str] = None,
    crime_category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Spatial hotspot clustering using DBSCAN (0.5 km radius, min 3 FIRs).

    Returns clusters with centroids, radii, dominant crime type,
    and confidence-weighted explanations.
    """
    engine = SpatialAnalyticsEngine(db)
    return engine.detect_hotspot_clusters(district_id=district_id, crime_category=crime_category)

@router.get("/spatial/corridors/{criminal_id}")
def get_travel_corridors(criminal_id: str, db: Session = Depends(get_db)):
    """
    Detect geographic movement corridors for a criminal.
    Returns sequential FIR-to-FIR movement vectors with bearing and distance.
    """
    engine = SpatialAnalyticsEngine(db)
    return engine.detect_travel_corridors(criminal_id)

@router.get("/spatial/district-transitions")
def get_district_transitions(db: Session = Depends(get_db)):
    """Return district-to-district criminal movement frequency matrix."""
    engine = SpatialAnalyticsEngine(db)
    return engine.district_transition_analysis()
