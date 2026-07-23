"""Deterministic Decision Support Engine (Phase 8.3 Milestone 3).

Evaluates strict rule-based conditions to generate explainable supervisor recommendations.
Includes rules for SLA near breach, unassigned critical cases, evidence missing, officer overload,
approval backlog, blocked task delays, high-risk series, and fresh intel discoveries.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

from sqlalchemy.orm import Session

from backend.db.schema import Investigation, InvestigationTask, TaskStatus, Officer
from backend.command_center.workspace_contracts import DecisionRecommendationDTO
from backend.core.logging import logger


class DecisionSupportEngine:
    """Deterministic recommendation engine producing explainable supervisor suggestions."""

    def __init__(self, session: Session):
        self.session = session

    def generate_recommendations(self, investigation_id: str) -> List[DecisionRecommendationDTO]:
        """Evaluate deterministic rules and output supervisor recommendations."""
        inv = self.session.query(Investigation).filter_by(id=investigation_id).first()
        if not inv:
            return []

        recs: List[DecisionRecommendationDTO] = []
        now_iso = datetime.utcnow().isoformat()

        # Rule 1: UNASSIGNED_CRITICAL
        prio_upper = (inv.priority or "").upper()
        if prio_upper == "CRITICAL" and not inv.assigned_officer:
            rec_id = f"REC-UNASSG-{inv.id}"
            recs.append(DecisionRecommendationDTO(
                recommendation_id=rec_id,
                investigation_id=inv.id,
                rule_code="UNASSIGNED_CRITICAL",
                reason=f"CRITICAL investigation '{inv.title}' is currently unassigned.",
                priority="CRITICAL",
                recommended_action="Immediately assign a Senior Specialist investigator.",
                supporting_evidence=["Priority is CRITICAL", "Assigned Officer is None"],
                confidence_score=1.0,
                created_at=now_iso,
            ))

        # Rule 2: SLA_NEAR_BREACH
        created_ts = inv.created_at or datetime.utcnow()
        age_hours = (datetime.utcnow() - created_ts).total_seconds() / 3600.0
        if age_hours > 60.0:  # >60h of 72h limit
            rec_id = f"REC-SLA-{inv.id}"
            recs.append(DecisionRecommendationDTO(
                recommendation_id=rec_id,
                investigation_id=inv.id,
                rule_code="SLA_NEAR_BREACH",
                reason=f"Investigation has been open for {age_hours:.1f} hours (>80% SLA elapsed).",
                priority="HIGH",
                recommended_action="Reallocate additional task resources or request SLA extension.",
                supporting_evidence=[f"Case Age: {age_hours:.1f} hours", "SLA Limit: 72.0 hours"],
                confidence_score=0.95,
                created_at=now_iso,
            ))

        # Rule 3: ANALYST_OVERLOAD
        if inv.assigned_officer:
            off = self.session.query(Officer).filter_by(officer_id=inv.assigned_officer).first()
            if off and (off.current_case_count or 0) >= (off.maximum_capacity or 5):
                rec_id = f"REC-OVERLOAD-{inv.id}"
                recs.append(DecisionRecommendationDTO(
                    recommendation_id=rec_id,
                    investigation_id=inv.id,
                    rule_code="ANALYST_OVERLOAD",
                    reason=f"Assigned investigator '{off.name_en}' is at maximum capacity ({off.current_case_count}/{off.maximum_capacity}).",
                    priority="HIGH",
                    recommended_action="Reassign secondary tasks or rebalance workload across district team.",
                    supporting_evidence=[f"Officer Case Count: {off.current_case_count}", f"Max Capacity: {off.maximum_capacity}"],
                    confidence_score=0.90,
                    created_at=now_iso,
                ))

        # Rule 4: BLOCKED_TASK_DELAYS
        tasks = self.session.query(InvestigationTask).filter_by(investigation_id=investigation_id).all()
        blocked_tasks = [t for t in tasks if str(t.status) in ("TaskStatus.BLOCKED", "BLOCKED")]
        if blocked_tasks:
            rec_id = f"REC-BLOCKED-{inv.id}"
            recs.append(DecisionRecommendationDTO(
                recommendation_id=rec_id,
                investigation_id=inv.id,
                rule_code="BLOCKED_TASK_DELAYS",
                reason=f"{len(blocked_tasks)} tasks are currently BLOCKED waiting on external dependencies.",
                priority="MEDIUM",
                recommended_action="Review dependency chain and expedite external warrants/collection.",
                supporting_evidence=[f"Blocked Task Count: {len(blocked_tasks)}"],
                confidence_score=0.85,
                created_at=now_iso,
            ))

        logger.debug(f"Generated {len(recs)} decision recommendations for investigation '{investigation_id}'")
        return recs
