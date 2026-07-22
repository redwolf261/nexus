from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from backend.db.schema import Criminal, FIR, Person
from backend.repositories.neo4j_repo import Neo4jRepository

class IntelligenceScoring:
    def __init__(self, db: Session, neo4j_repo: Neo4jRepository = None):
        self.db = db
        self.neo4j = neo4j_repo or Neo4jRepository()

    def calculate_entity_risk(self, entity_id: str, entity_type: str = "PERSON") -> Dict[str, Any]:
        """Calculates dynamic risk metrics combining SQL constraints and Neo4j topological stats."""
        scores = {
            "threat_score": 0.0,
            "gang_influence": 0.0,
            "financial_risk": 0.0,
            "repeat_offender_index": 0.0,
            "network_centrality": 0.0
        }
        
        # SQL Baseline Scoring
        if entity_type == "PERSON" or entity_type == "CRIMINAL":
            # Check criminal record
            c = self.db.query(Criminal).filter((Criminal.citizen_id == entity_id) | (Criminal.criminal_id == entity_id)).first()
            if c:
                scores["repeat_offender_index"] = min(1.0, (c.total_crimes_committed or 0) / 10.0)
                scores["gang_influence"] = 0.8 if c.is_gang_leader else (0.5 if c.is_gang_member else 0.0)
                scores["threat_score"] = min(1.0, scores["repeat_offender_index"] * 0.6 + scores["gang_influence"] * 0.4)
            else:
                p = self.db.query(Person).filter_by(citizen_id=entity_id).first()
                if p and p.socioeconomic_class == "High":
                    scores["financial_risk"] = 0.3 # arbitrary baseline heuristic

        # Graph Topology Scoring (if neo4j is alive)
        try:
            # We fetch 1-hop degree to estimate centrality
            graph_data = self.neo4j.get_person_subgraph(entity_id)
            degree = len(graph_data)
            scores["network_centrality"] = min(1.0, degree / 20.0)  # max out at 20 edges
            
            # Boost threat based on network centrality
            scores["threat_score"] = min(1.0, scores["threat_score"] + (scores["network_centrality"] * 0.2))
        except Exception:
            pass # degrade gracefully if Neo4j is offline
            
        # Normalize to 100 scale for UI
        return {k: round(v * 100, 1) for k, v in scores.items()}

    def calculate_case_risk(self, case_id: str) -> Dict[str, Any]:
        """Calculates risk metrics for an entire investigation."""
        from backend.db.schema import InvestigationEntity
        
        entities = self.db.query(InvestigationEntity).filter_by(investigation_id=case_id).all()
        
        total_threat = 0.0
        max_gang = 0.0
        
        people_ids = [e.entity_id for e in entities if e.entity_type in ["PERSON", "CRIMINAL"]]
        
        for pid in people_ids:
            s = self.calculate_entity_risk(pid, "PERSON")
            total_threat += s["threat_score"]
            if s["gang_influence"] > max_gang:
                max_gang = s["gang_influence"]
                
        avg_threat = (total_threat / len(people_ids)) if people_ids else 0.0
        
        return {
            "case_threat_score": round(avg_threat, 1),
            "gang_involvement": round(max_gang, 1),
            "evidence_completeness": min(100.0, len(entities) * 10.0),
            "network_complexity": min(100.0, len(entities) * 5.0)
        }
