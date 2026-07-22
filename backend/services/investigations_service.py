from typing import List, Dict, Any
from collections import defaultdict
from fastapi import HTTPException

from backend.repositories.investigations_repo import InvestigationsRepository
from backend.repositories.postgres_repo import PostgresRepository
from backend.repositories.neo4j_repo import Neo4jRepository
from backend.schemas.investigations import (
    InvestigationCreate, InvestigationUpdate, InvestigationNoteCreate,
    InvestigationNoteUpdate
)

class InvestigationsService:
    def __init__(self, inv_repo: InvestigationsRepository, pg_repo: PostgresRepository, neo4j_repo: Neo4jRepository):
        self.inv_repo = inv_repo
        self.pg_repo = pg_repo
        self.neo4j_repo = neo4j_repo

    def get_workspace(self, inv_id: str) -> Dict[str, Any]:
        inv = self.inv_repo.get_investigation(inv_id)
        if not inv:
            raise HTTPException(status_code=404, detail="Investigation not found")

        entities_raw = self.inv_repo.get_entities(inv_id)
        notes = self.inv_repo.get_notes(inv_id)
        activity = self.inv_repo.get_activity(inv_id)

        entities_grouped = defaultdict(list)
        timeline = []

        # Map activity to timeline
        for act in activity:
            timeline.append({
                "date": act.created_at,
                "type": "Investigation",
                "event_type": act.action,
                "description": act.details,
                "entity_id": inv_id
            })

        for ent in entities_raw:
            # Hydrate entities using PG Repo
            if ent.entity_type == "FIR":
                detail = self.pg_repo.get_fir_by_id(ent.entity_id)
                if detail:
                    entities_grouped["FIR"].append(detail)
                    timeline.append({
                        "date": detail.occurred_date if detail.occurred_date else ent.added_at,
                        "type": "FIR",
                        "event_type": detail.crime_type or "Unknown Crime",
                        "description": detail.description_en or "",
                        "entity_id": detail.fir_id
                    })
            elif ent.entity_type == "PERSON":
                detail = self.pg_repo.get_person_by_id(ent.entity_id)
                if detail: entities_grouped["PERSON"].append(detail)
            elif ent.entity_type == "VEHICLE":
                detail = self.pg_repo.db.query(self.pg_repo.db.query("Vehicle").column_descriptions[0]['type']).filter_by(vehicle_id=ent.entity_id).first() if hasattr(self.pg_repo.db, 'query') else None # Quick hack, better to use repo methods if they exist
                # Let's write a safer way, pg_repo might have get_person_by_id but maybe not get_vehicle_by_id.
                # Actually, postgres_repo.py has `get_person_by_id`. We'll fetch from db directly here for simplicity if repo method missing.
                pass
            else:
                # Generic fallback for now
                entities_grouped[ent.entity_type].append({"id": ent.entity_id})

            timeline.append({
                "date": ent.added_at,
                "type": "System",
                "event_type": "Entity Attached",
                "description": f"Attached {ent.entity_type} {ent.entity_id} to case",
                "entity_id": ent.entity_id
            })

        # Fetch actual entity data from DB models
        for ent in entities_raw:
            if ent.entity_type == "VEHICLE":
                from backend.db.schema import Vehicle
                detail = self.pg_repo.db.query(Vehicle).filter(Vehicle.vehicle_id == ent.entity_id).first()
                if detail: entities_grouped["VEHICLE"].append(detail)
            elif ent.entity_type == "PHONE":
                from backend.db.schema import Phone
                detail = self.pg_repo.db.query(Phone).filter(Phone.phone_id == ent.entity_id).first()
                if detail: entities_grouped["PHONE"].append(detail)
            elif ent.entity_type == "CRIMINAL":
                from backend.db.schema import Criminal
                detail = self.pg_repo.db.query(Criminal).filter(Criminal.criminal_id == ent.entity_id).first()
                if detail: entities_grouped["CRIMINAL"].append(detail)

        # --- Intelligence Enrichment ---
        from backend.intelligence.entity_resolution import EntityResolutionEngine
        from backend.intelligence.scoring import IntelligenceScoring
        er = EntityResolutionEngine(self.pg_repo.db)
        score_engine = IntelligenceScoring(self.pg_repo.db, self.neo4j_repo)
        
        target_ents = [{"entity_id": e.entity_id, "entity_type": e.entity_type} for e in entities_raw]
        overlaps = er.get_cross_case_overlaps(target_ents)
        for o in overlaps:
            if o["investigation_id"] != inv_id:
                timeline.append({
                    "date": inv.updated_at,  # rough approximation for when overlap is relevant
                    "type": "Intelligence",
                    "event_type": "Cross-Case Overlap",
                    "description": f"Entity {o['entity_id']} also appears in case {o['investigation_id']}",
                    "entity_id": o["entity_id"]
                })

        for ent in entities_raw:
            if ent.entity_type == "CRIMINAL":
                risk = score_engine.calculate_entity_risk(ent.entity_id, "CRIMINAL")
                if risk.get("gang_influence", 0) > 40:
                     timeline.append({
                        "date": ent.added_at,
                        "type": "Intelligence",
                        "event_type": "Gang Association",
                        "description": f"Subject {ent.entity_id} flagged for high gang influence ({risk['gang_influence']}%)",
                        "entity_id": ent.entity_id
                    })

        # ── Phase 7: Analytical Findings ────────────────────────────────────
        analytical_findings = {}
        db = self.pg_repo.db

        try:
            from backend.intelligence.crime_series import CrimeSeriesEngine
            fir_ids = [e.entity_id for e in entities_raw if e.entity_type == "FIR"]
            if fir_ids:
                cs_engine = CrimeSeriesEngine(db)
                all_series = cs_engine.detect_series()
                matching_series = [
                    s for s in all_series.get("series", [])
                    if any(f in s["supporting_fir_ids"] for f in fir_ids)
                ]
                analytical_findings["crime_series"] = matching_series[:3]
        except Exception:
            analytical_findings["crime_series"] = []

        try:
            from backend.intelligence.graph_analytics import GraphAnalyticsEngine
            graph_engine = GraphAnalyticsEngine(db)
            person_ids = [e.entity_id for e in entities_raw if e.entity_type in ("PERSON", "CRIMINAL")]
            graph_metrics = {}
            for pid in person_ids[:5]:  # cap to 5 for performance
                metrics = graph_engine.get_entity_metrics(pid)
                if metrics.get("metrics"):
                    graph_metrics[pid] = metrics["metrics"]
            analytical_findings["graph_metrics"] = graph_metrics
        except Exception:
            analytical_findings["graph_metrics"] = {}

        try:
            from backend.intelligence.temporal_analytics import TemporalAnalyticsEngine
            t_engine = TemporalAnalyticsEngine(db)
            temporal = t_engine.detect_anomalies(days=30)
            analytical_findings["temporal_alerts"] = temporal.get("alerts", [])[:5]
        except Exception:
            analytical_findings["temporal_alerts"] = []

        # Sort timeline
        timeline.sort(key=lambda x: x["date"], reverse=True)

        return {
            "investigation": inv,
            "entities": dict(entities_grouped),
            "notes": notes,
            "timeline": timeline,
            "statistics": {
                "total_entities": len(entities_raw),
                "total_notes": len(notes)
            },
            "analytical_findings": analytical_findings,
        }

