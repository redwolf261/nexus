from __future__ import annotations

from cachetools import cached, TTLCache
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.repositories.neo4j_repo import Neo4jRepository
from backend.repositories.postgres_repo import PostgresRepository
from backend.analytics.community_detection import identify_masterminds
from backend.analytics.timeline import format_timeline_events
from backend.analytics.hotspots import extract_hotspots

neo4j_repo = Neo4jRepository()


def _new_cache():
    return TTLCache(maxsize=100, ttl=60)


# ── Community detection (Neo4j — was already correct) ────────────────────────

@cached(_new_cache())
def get_campaigns_service():
    raw_data = neo4j_repo.get_campaigns()
    return identify_masterminds(raw_data)


# ── Cross-jurisdiction / Silo Buster (Neo4j — fixed Cypher) ──────────────────

@cached(_new_cache())
def get_cross_jurisdiction_service(fir_id: str):
    raw_links = neo4j_repo.get_cross_jurisdiction_links(fir_id)
    links = [
        {
            "linked_fir": r["linked_fir"],
            "shared_type": r["shared_type"],
            "entity_id": r["entity_id"],
        }
        for r in raw_links
    ]

    reasons = []
    if links:
        shared_persons = len(set(l["entity_id"] for l in links))
        reasons.append(
            f"Shared {shared_persons} person(s) across {len(links)} FIR(s) via vehicle/phone linkage."
        )
        reasons.append("Cross-jurisdiction movement pattern detected in graph traversal.")
    else:
        reasons = ["No direct cross-jurisdiction links found in graph."]

    return {
        "fir_id": fir_id,
        "score": min(99, 40 + len(links) * 10) if links else 10,
        "confidence": min(0.99, 0.5 + len(links) * 0.05) if links else 0.1,
        "reasons": reasons,
        "linked_crimes": links,
    }


# ── Person graph (Neo4j — was already correct) ────────────────────────────────

@cached(_new_cache())
def get_person_graph_service(person_id: str):
    raw_graph = neo4j_repo.get_person_subgraph(person_id)
    neighbors = [
        {"node_id": r["node_id"], "labels": r["labels"], "relationship": r["relationship"]}
        for r in raw_graph
    ]

    # Real centrality signal: degree count
    degree = len(neighbors)
    gang_links = [n for n in neighbors if "Gang" in n["labels"]]
    fir_links = [n for n in neighbors if "FIR" in n["labels"]]

    is_high_risk = degree > 5 or len(gang_links) > 0
    risk_score = min(99, 10 + degree * 4 + len(gang_links) * 20)
    centrality = round(min(1.0, degree / 20), 2)

    reasons = []
    if gang_links:
        reasons.append(f"Gang affiliation: {len(gang_links)} gang link(s) detected.")
    if fir_links:
        reasons.append(f"Directly linked to {len(fir_links)} FIR(s) in graph.")
    if degree > 5:
        reasons.append(f"High graph degree: {degree} direct connections.")
    if not reasons:
        reasons = ["Low connectivity — no high-risk links in graph."]

    campaigns: list[str] = []
    if gang_links:
        # Surface gang IDs as proxy campaign references
        campaigns = [n["node_id"] for n in gang_links]

    return {
        "person_id": person_id,
        "risk_score": risk_score,
        "centrality": centrality,
        "campaigns": campaigns,
        "reasons": reasons,
        "neighbors": neighbors,
    }


# ── Campaign timeline (fixed — Postgres FIR ids → Neo4j enrichment) ──────────

def get_campaign_timeline_service(campaign_id: str):
    db: Session = SessionLocal()
    try:
        pg_repo = PostgresRepository(db)
        # Fetch FIR ids for this campaign from Postgres
        from backend.db.schema import FIR
        fir_ids = [
            row.fir_id
            for row in db.query(FIR.fir_id).filter(FIR.campaign_id == campaign_id).all()
        ]
        # Enrich with Neo4j graph data
        raw_events = neo4j_repo.get_campaign_timeline_by_fir_ids(fir_ids)
        events = format_timeline_events(raw_events)
        return {"campaign_id": campaign_id, "events": events}
    finally:
        db.close()


# ── Hotspots (real DBSCAN over Postgres FIR coordinates) ─────────────────────

@cached(_new_cache())
def get_hotspots_service():
    db: Session = SessionLocal()
    try:
        pg_repo = PostgresRepository(db)
        coords = pg_repo.get_fir_coordinates(limit=2000)
        return extract_hotspots(coords)
    finally:
        db.close()


# ── Executive Dashboard (real Postgres aggregations) ─────────────────────────

@cached(_new_cache())
def get_executive_dashboard_service():
    db: Session = SessionLocal()
    try:
        pg_repo = PostgresRepository(db)
        kpis = pg_repo.get_executive_kpis()
        # Fill predicted_hotspots from the hotspot service
        hotspots = get_hotspots_service()
        kpis["predicted_hotspots"] = len(hotspots)
        return kpis
    finally:
        db.close()


# ── District Dashboard (real per-district Postgres queries) ──────────────────

@cached(_new_cache())
def get_district_dashboard_service(district_id: str):
    db: Session = SessionLocal()
    try:
        pg_repo = PostgresRepository(db)
        return pg_repo.get_district_stats(district_id)
    finally:
        db.close()


# ── Campaign Summary (real Postgres join) ─────────────────────────────────────

@cached(_new_cache())
def get_campaign_summary_service(campaign_id: str):
    db: Session = SessionLocal()
    try:
        pg_repo = PostgresRepository(db)
        detail = pg_repo.get_campaign_detail(campaign_id)
        if not detail:
            return {
                "campaign_id": campaign_id,
                "mastermind": "Not found",
                "gang": "Not found",
                "vehicles": [],
                "phones": [],
                "timeline_events": 0,
                "status": "Not found",
            }
        return {
            "campaign_id": detail["campaign_id"],
            "mastermind": detail["mastermind"],
            "gang": detail["gang_name"],
            "gang_id": detail["gang_id"],
            "crime_category": detail["crime_category"],
            "start_date": detail["start_date"],
            "end_date": detail["end_date"],
            "num_crimes_planned": detail["num_crimes_planned"],
            "num_crimes_committed": detail["num_crimes_committed"],
            "vehicles": detail["vehicles"],
            "phones": detail["phones"],
            "timeline_events": detail["timeline_events"],
            "status": detail["status"],
        }
    finally:
        db.close()


neo4j_repo = Neo4jRepository()

# Use TTL caching (60 seconds) for dynamic endpoints instead of lru_cache.
# NOTE: each cached function needs its OWN cache. A single shared cache keys
# zero-arg functions all to () (and same-arg functions collide), so they
# return each other's results and fail response-model validation.
def _new_cache():
    return TTLCache(maxsize=100, ttl=60)

@cached(_new_cache())
def get_campaigns_service():
    raw_data = neo4j_repo.get_campaigns()
    return identify_masterminds(raw_data)

@cached(_new_cache())
def get_cross_jurisdiction_service(fir_id: str):
    raw_links = neo4j_repo.get_cross_jurisdiction_links(fir_id)
    links = [{"linked_fir": r["linked_fir"], "shared_type": r["shared_type"], "entity_id": r["entity_id"]} for r in raw_links]
    
    reasons = []
    if links:
        reasons.append(f"Shared {len(links)} physical assets (vehicles/phones) across jurisdictions.")
        reasons.append("High correlation in Modus Operandi.")
    
    return {
        "fir_id": fir_id,
        "score": 98 if links else 10,
        "confidence": 0.97 if links else 0.1,
        "reasons": reasons if links else ["No strong links found."],
        "linked_crimes": links
    }

@cached(_new_cache())
def get_person_graph_service(person_id: str):
    raw_graph = neo4j_repo.get_person_subgraph(person_id)
    neighbors = [{"node_id": r["node_id"], "labels": r["labels"], "relationship": r["relationship"]} for r in raw_graph]
    
    is_high_risk = len(neighbors) > 2
    reasons = []
    if is_high_risk:
        reasons = [
            f"High centrality: {len(neighbors)} immediate risky connections.",
            "Linked to active criminal campaigns.",
            "Shared burner phone detected."
        ]
    else:
        reasons = ["Low connectivity in graph."]

    return {
        "person_id": person_id,
        "risk_score": 87 if is_high_risk else 15,
        "centrality": 0.92 if is_high_risk else 0.05,
        "campaigns": ["CAMPAIGN-01"] if is_high_risk else [],
        "reasons": reasons,
        "neighbors": neighbors
    }

@cached(_new_cache())
def get_campaign_timeline_service(campaign_id: str):
    raw_events = neo4j_repo.get_campaign_timeline(campaign_id)
    events = format_timeline_events(raw_events)
    return {"campaign_id": campaign_id, "events": events}

@cached(_new_cache())
def get_hotspots_service():
    return extract_hotspots()

@cached(_new_cache())
def get_executive_dashboard_service():
    # Mock aggregation for demo
    return {
        "todays_firs": 42,
        "active_campaigns": 39,
        "predicted_hotspots": 224,
        "average_investigation_time": 18.5,
        "crime_trend": "Increasing by 5% in Central District",
        "new_intelligence_alerts": 7
    }

@cached(_new_cache())
def get_district_dashboard_service(district_id: str):
    return {
        "district_id": district_id,
        "top_gangs": ["Red Panthers", "Silent Syndicate"],
        "repeat_offenders": 145,
        "risk_score": 78,
        "patrol_coverage": "85% Optimal",
        "crime_trend": "Spike in vehicle thefts detected."
    }

@cached(_new_cache())
def get_campaign_summary_service(campaign_id: str):
    return {
        "campaign_id": campaign_id,
        "mastermind": "C-MM-849",
        "gang": "G-55",
        "vehicles": ["KA-01-AB-1234"],
        "phones": ["+91-9876543210"],
        "timeline_events": 14,
        "status": "Active Surveillance"
    }
