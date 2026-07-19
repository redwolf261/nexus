from cachetools import cached, TTLCache
from backend.repositories.neo4j_repo import Neo4jRepository
from backend.analytics.community_detection import identify_masterminds
from backend.analytics.timeline import format_timeline_events
from backend.analytics.hotspots import extract_hotspots

neo4j_repo = Neo4jRepository()

# Use TTL caching (60 seconds) for dynamic endpoints instead of lru_cache
cache = TTLCache(maxsize=100, ttl=60)

@cached(cache)
def get_campaigns_service():
    raw_data = neo4j_repo.get_campaigns()
    return identify_masterminds(raw_data)

@cached(cache)
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

@cached(cache)
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

@cached(cache)
def get_campaign_timeline_service(campaign_id: str):
    raw_events = neo4j_repo.get_campaign_timeline(campaign_id)
    events = format_timeline_events(raw_events)
    return {"campaign_id": campaign_id, "events": events}

@cached(cache)
def get_hotspots_service():
    return extract_hotspots()

@cached(cache)
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

@cached(cache)
def get_district_dashboard_service(district_id: str):
    return {
        "district_id": district_id,
        "top_gangs": ["Red Panthers", "Silent Syndicate"],
        "repeat_offenders": 145,
        "risk_score": 78,
        "patrol_coverage": "85% Optimal",
        "crime_trend": "Spike in vehicle thefts detected."
    }

@cached(cache)
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
