import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from backend.compliance.schema import ComplianceViolationRecord
from backend.compliance.compliance_contracts import (
    ComplianceRiskDTO, RiskBand, RuleCategory, SeverityLevel
)

SUBSYSTEM_WEIGHTS = {
    "AUTHENTICATION": 0.15,
    "ASSIGNMENT": 0.15,
    "GOVERNANCE": 0.15,
    "APPROVAL": 0.15,
    "EVIDENCE": 0.15,
    "NOTIFICATIONS": 0.10,
    "AUDIT": 0.10,
    "OPERATIONAL": 0.05
}

SEVERITY_SCORES = {
    SeverityLevel.CRITICAL.value: 25.0,
    SeverityLevel.HIGH.value: 15.0,
    SeverityLevel.MEDIUM.value: 8.0,
    SeverityLevel.LOW.value: 3.0
}


class RiskEngine:
    """
    Computes deterministic operational compliance risk scores (0-100).
    """

    @classmethod
    def calculate_risk(cls, db: Session) -> ComplianceRiskDTO:
        # Fetch active unresolved violations
        active_violations = db.query(ComplianceViolationRecord).filter_by(resolved=False).all()
        
        category_raw_scores: Dict[str, float] = {k: 0.0 for k in SUBSYSTEM_WEIGHTS.keys()}
        factors: List[Dict[str, Any]] = []

        for v in active_violations:
            cat = v.category.upper()
            if cat not in category_raw_scores:
                cat = "OPERATIONAL"

            sev = v.severity.upper()
            add_points = SEVERITY_SCORES.get(sev, 8.0)
            category_raw_scores[cat] += add_points

            factors.append({
                "violation_id": v.id,
                "rule_id": v.rule_id,
                "rule_name": v.rule_name,
                "category": cat,
                "severity": sev,
                "impact_points": add_points,
                "explanation": v.explanation,
                "entity": f"{v.violated_entity_type or 'Entity'}:{v.violated_entity_id or 'N/A'}"
            })

        # Cap each category raw score at 100
        subsystem_breakdown = {}
        weighted_overall = 0.0
        for cat, weight in SUBSYSTEM_WEIGHTS.items():
            capped_score = min(100.0, category_raw_scores[cat])
            subsystem_breakdown[cat] = round(capped_score, 2)
            weighted_overall += capped_score * weight

        overall_score = round(min(100.0, weighted_overall), 2)

        # Risk band assignment
        if overall_score <= 25.0:
            risk_band = RiskBand.LOW
        elif overall_score <= 50.0:
            risk_band = RiskBand.MODERATE
        elif overall_score <= 75.0:
            risk_band = RiskBand.HIGH
        else:
            risk_band = RiskBand.CRITICAL

        return ComplianceRiskDTO(
            overall_score=overall_score,
            risk_band=risk_band,
            subsystem_breakdown=subsystem_breakdown,
            contributing_factors=factors[:50],  # Top contributing factors
            total_active_violations=len(active_violations),
            calculated_at=datetime.datetime.utcnow()
        )
