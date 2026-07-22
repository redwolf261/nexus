from sqlalchemy.orm import Session
from typing import List, Dict, Any

class RecommendationEngine:
    def __init__(self, db: Session):
        self.db = db

    def generate_case_recommendations(self, case_id: str) -> List[Dict[str, Any]]:
        """Generates contextual recommendations for a case."""
        from backend.db.schema import InvestigationEntity, FIR, Person, Criminal
        
        entities = self.db.query(InvestigationEntity).filter_by(investigation_id=case_id).all()
        recs = []

        firs = [e.entity_id for e in entities if e.entity_type == "FIR"]
        people = [e.entity_id for e in entities if e.entity_type in ["PERSON", "CRIMINAL"]]

        # 1. CCTV Recommendation based on FIR
        if firs:
            for fir_id in firs:
                f = self.db.query(FIR).filter_by(fir_id=fir_id).first()
                if f and f.occurred_date and f.latitude and f.longitude:
                    # In a real app, we'd do a geospatial query for nearest CCTV.
                    # Here we mock the context based on presence of coordinates.
                    time_str = f.occurred_time.strftime("%H:%M") if f.occurred_time else "unknown time"
                    recs.append({
                        "type": "CCTV",
                        "priority": "High",
                        "suggestion": f"Request CCTV footage near lat {f.latitude}, lng {f.longitude} around {time_str}.",
                        "evidence": f"FIR {fir_id} location"
                    })

        # 2. Interview Recommendation based on Criminal record
        if people:
            for pid in people:
                c = self.db.query(Criminal).filter((Criminal.citizen_id == pid) | (Criminal.criminal_id == pid)).first()
                if c and c.is_gang_member:
                    recs.append({
                        "type": "INTERVIEW",
                        "priority": "Medium",
                        "suggestion": f"Interview {pid} due to repeated proximity to Gang {c.gang_id}.",
                        "evidence": f"Gang membership record for {pid}"
                    })
                    
        # 3. Priority Recommendation
        if len(firs) > 1:
            recs.append({
                "type": "PRIORITIZE",
                "priority": "Critical",
                "suggestion": f"Prioritize investigating overlap between {len(firs)} attached FIRs.",
                "evidence": f"Multiple active FIRs in same workspace"
            })

        return recs
