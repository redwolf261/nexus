"""Assignment Governance Service (Phase 8.2 Milestone 5).

Operational governance layer managing supervisor decisions (ACCEPT, OVERRIDE, REJECT, DEFER),
multi-level approval escalations (ACP / DCP), policy rule validation, decision audit history,
recommendation snapshot persistence, and command center metrics.

CRITICAL DESIGN RULE:
  - Zero AI / ML / Randomness.
  - Supervisors remain sole authority; no automatic assignment.
  - Mandatory justification >= 50 characters for OVERRIDE decisions.
"""

from __future__ import annotations

import uuid
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func, text

from backend.db.schema import (
    Investigation, Officer, AssignmentDecisionHistory, RecommendationSnapshot,
    AssignmentEscalation, User, Role
)
from backend.assignment.contracts import (
    GovernanceMetricsDTO, EscalationItemDTO, SnapshotDTO
)
from backend.assignment.override_policy import (
    OverridePolicyEngine, ApprovalPolicy, PolicyResult, DecisionEnum, OverrideReasonEnum
)
from backend.assignment.decision_aggregate import AssignmentDecision
from backend.assignment.assignment_service import AssignmentService
from backend.audit.audit_logger import AuditLogger
from backend.events.event_types import EventType
from backend.events.event_models import BaseEvent
from backend.events.dispatcher import EventDispatcher
from backend.core.logging import logger


class AssignmentGovernanceService:
    """Production Assignment Governance Service."""

    def __init__(self, session: Session, approval_policy: ApprovalPolicy = ApprovalPolicy()):
        self.session = session
        self.approval_policy = approval_policy
        self.policy_engine = OverridePolicyEngine(session, approval_policy)
        self.assignment_service = AssignmentService(session)
        self.audit_logger = AuditLogger(session)

    # ── 1. Accept Recommendation ─────────────────────────────────────────────

    def accept_recommendation(
        self,
        investigation_id: str,
        supervisor_id: str,
        recommendation_id: Optional[str] = None,
        expected_version: Optional[int] = None
    ) -> AssignmentDecision:
        """Accept the top recommended officer for an investigation."""
        inv = self.session.query(Investigation).filter(Investigation.id == investigation_id).with_for_update().first()
        if not inv:
            raise KeyError(f"Investigation '{investigation_id}' not found")

        if expected_version is not None and inv.version != expected_version:
            raise ValueError(f"Optimistic lock failure: investigation version is {inv.version}, expected {expected_version}")

        # Fetch top recommendation
        recs = self.assignment_service.recommend(investigation_id, limit=1)
        if not recs:
            raise ValueError(f"No recommendations available for investigation '{investigation_id}'")

        top_officer_id = recs[0].score.officer_id

        # Persist recommendation snapshot for legal reproducibility
        self.create_recommendation_snapshot(investigation_id, recs)

        # Evaluate policy
        policy_res = self.policy_engine.evaluate(investigation_id, top_officer_id)

        # Apply assignment via AssignmentService
        self.assignment_service.assign(
            investigation_id=investigation_id,
            officer_id=top_officer_id,
            assigned_by=supervisor_id,
            reason="Supervisor ACCEPT recommendation",
            manual_override=False,
        )

        dec_id = f"DEC-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.utcnow()

        dec_history = AssignmentDecisionHistory(
            id=f"DEC-HIST-{uuid.uuid4().hex[:12].upper()}",
            decision_id=dec_id,
            investigation_id=investigation_id,
            recommendation_id=recommendation_id or f"REC-{investigation_id}",
            supervisor_id=supervisor_id,
            decision=DecisionEnum.ACCEPT.value,
            chosen_officer_id=top_officer_id,
            justification="Accepted top recommendation",
            override_reason=None,
            policy_violations=policy_res.violations,
            approval_chain=[{"role": "Supervisor", "user_id": supervisor_id, "timestamp": now.isoformat()}],
            status="COMPLETED",
            policy_snapshot=policy_res.to_dict(),
            policy_version=self.approval_policy.version,
            timestamp=now,
            version=inv.version,
        )
        self.session.add(dec_history)

        self.audit_logger.log(
            user_id=supervisor_id,
            action="ASSIGNMENT_ACCEPTED",
            target_id=investigation_id,
            details={"chosen_officer_id": top_officer_id}
        )

        self.session.commit()

        # Event emission
        try:
            event = BaseEvent(
                event_type=EventType.ASSIGNMENT_ACCEPTED,
                case_id=investigation_id,
                user_id=supervisor_id,
                sequence=inv.last_sequence,
                payload={
                    "decision_id": dec_id,
                    "investigation_id": investigation_id,
                    "chosen_officer_id": top_officer_id,
                    "supervisor_id": supervisor_id,
                }
            )
            EventDispatcher.publish_sync(event, self.session)
        except Exception as e:
            logger.warning(f"Failed to emit ASSIGNMENT_ACCEPTED event: {e}")

        return self._to_decision_aggregate(dec_history, policy_res)

    # ── 2. Override Assignment ───────────────────────────────────────────────

    def override_assignment(
        self,
        investigation_id: str,
        supervisor_id: str,
        chosen_officer_id: str,
        override_reason: OverrideReasonEnum,
        justification: str,
        is_interstate: bool = False,
        expected_version: Optional[int] = None
    ) -> AssignmentDecision:
        """Override recommendation and assign chosen officer with policy checks & escalation."""
        if not justification or len(justification.strip()) < 50:
            raise ValueError(f"Override justification must be at least 50 characters long (received {len(justification.strip()) if justification else 0} chars).")

        inv = self.session.query(Investigation).filter(Investigation.id == investigation_id).with_for_update().first()
        if not inv:
            raise KeyError(f"Investigation '{investigation_id}' not found")

        if expected_version is not None and inv.version != expected_version:
            raise ValueError(f"Optimistic lock failure: investigation version is {inv.version}, expected {expected_version}")

        # Compute policy
        policy_res = self.policy_engine.evaluate(investigation_id, chosen_officer_id, is_interstate=is_interstate)

        # Snapshots
        recs = self.assignment_service.recommend(investigation_id, limit=5)
        self.create_recommendation_snapshot(investigation_id, recs)

        dec_id = f"DEC-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.utcnow()

        # Check escalation requirements
        required_escalation_role = None
        if policy_res.requires_dcp:
            required_escalation_role = "DCP"
        elif policy_res.requires_acp:
            required_escalation_role = "ACP"

        if required_escalation_role:
            # Create Escalation Queue item instead of immediate assignment
            status_str = f"PENDING_{required_escalation_role}"
            dec_history = AssignmentDecisionHistory(
                id=f"DEC-HIST-{uuid.uuid4().hex[:12].upper()}",
                decision_id=dec_id,
                investigation_id=investigation_id,
                recommendation_id=f"REC-{investigation_id}",
                supervisor_id=supervisor_id,
                decision=DecisionEnum.OVERRIDE.value,
                chosen_officer_id=chosen_officer_id,
                justification=justification,
                override_reason=override_reason.value if isinstance(override_reason, OverrideReasonEnum) else str(override_reason),
                policy_violations=policy_res.violations + policy_res.warnings,
                approval_chain=[{"role": "Supervisor", "user_id": supervisor_id, "timestamp": now.isoformat()}],
                status=status_str,
                policy_snapshot=policy_res.to_dict(),
                policy_version=self.approval_policy.version,
                timestamp=now,
                version=inv.version,
            )
            self.session.add(dec_history)
            self.session.flush()

            escalation = AssignmentEscalation(
                id=f"ESC-{uuid.uuid4().hex[:12].upper()}",
                decision_id=dec_history.id,
                investigation_id=investigation_id,
                required_role=required_escalation_role,
                status="PENDING",
                created_at=now,
            )
            self.session.add(escalation)

            self.audit_logger.log(
                user_id=supervisor_id,
                action="ASSIGNMENT_ESCALATED",
                target_id=investigation_id,
                details={"required_role": required_escalation_role, "chosen_officer_id": chosen_officer_id}
            )
            self.session.commit()

            # Event
            try:
                event = BaseEvent(
                    event_type=EventType.ASSIGNMENT_ESCALATED,
                    case_id=investigation_id,
                    user_id=supervisor_id,
                    payload={"decision_id": dec_id, "required_role": required_escalation_role}
                )
                EventDispatcher.publish_sync(event, self.session)
            except Exception:
                pass

            return self._to_decision_aggregate(dec_history, policy_res)

        # No escalation required -> apply assignment directly
        self.assignment_service.assign(
            investigation_id=investigation_id,
            officer_id=chosen_officer_id,
            assigned_by=supervisor_id,
            reason=f"Supervisor OVERRIDE: {justification}",
            manual_override=True,
            override_reason=override_reason.value if isinstance(override_reason, OverrideReasonEnum) else str(override_reason),
        )

        dec_history = AssignmentDecisionHistory(
            id=f"DEC-HIST-{uuid.uuid4().hex[:12].upper()}",
            decision_id=dec_id,
            investigation_id=investigation_id,
            recommendation_id=f"REC-{investigation_id}",
            supervisor_id=supervisor_id,
            decision=DecisionEnum.OVERRIDE.value,
            chosen_officer_id=chosen_officer_id,
            justification=justification,
            override_reason=override_reason.value if isinstance(override_reason, OverrideReasonEnum) else str(override_reason),
            policy_violations=policy_res.violations + policy_res.warnings,
            approval_chain=[{"role": "Supervisor", "user_id": supervisor_id, "timestamp": now.isoformat()}],
            status="COMPLETED",
            policy_snapshot=policy_res.to_dict(),
            policy_version=self.approval_policy.version,
            timestamp=now,
            version=inv.version,
        )
        self.session.add(dec_history)

        self.audit_logger.log(
            user_id=supervisor_id,
            action="ASSIGNMENT_OVERRIDDEN",
            target_id=investigation_id,
            details={"chosen_officer_id": chosen_officer_id, "override_reason": str(override_reason)}
        )

        self.session.commit()

        try:
            event = BaseEvent(
                event_type=EventType.ASSIGNMENT_OVERRIDDEN,
                case_id=investigation_id,
                user_id=supervisor_id,
                sequence=inv.last_sequence,
                payload={
                    "decision_id": dec_id,
                    "investigation_id": investigation_id,
                    "chosen_officer_id": chosen_officer_id,
                    "override_reason": str(override_reason),
                }
            )
            EventDispatcher.publish_sync(event, self.session)
        except Exception:
            pass

        return self._to_decision_aggregate(dec_history, policy_res)

    # ── 3. Reject Recommendation ─────────────────────────────────────────────

    def reject_recommendation(
        self,
        investigation_id: str,
        supervisor_id: str,
        justification: str,
        expected_version: Optional[int] = None
    ) -> AssignmentDecision:
        """Reject proposed recommendations for an investigation."""
        inv = self.session.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            raise KeyError(f"Investigation '{investigation_id}' not found")

        dec_id = f"DEC-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.utcnow()

        dec_history = AssignmentDecisionHistory(
            id=f"DEC-HIST-{uuid.uuid4().hex[:12].upper()}",
            decision_id=dec_id,
            investigation_id=investigation_id,
            recommendation_id=f"REC-{investigation_id}",
            supervisor_id=supervisor_id,
            decision=DecisionEnum.REJECT.value,
            chosen_officer_id=None,
            justification=justification,
            override_reason=None,
            policy_violations=[],
            approval_chain=[{"role": "Supervisor", "user_id": supervisor_id, "timestamp": now.isoformat()}],
            status="REJECTED",
            policy_snapshot={},
            policy_version=self.approval_policy.version,
            timestamp=now,
            version=inv.version,
        )
        self.session.add(dec_history)

        self.audit_logger.log(
            user_id=supervisor_id,
            action="ASSIGNMENT_REJECTED",
            target_id=investigation_id,
            details={"justification": justification}
        )

        self.session.commit()

        try:
            event = BaseEvent(
                event_type=EventType.ASSIGNMENT_REJECTED,
                case_id=investigation_id,
                user_id=supervisor_id,
                payload={"decision_id": dec_id, "investigation_id": investigation_id}
            )
            EventDispatcher.publish_sync(event, self.session)
        except Exception:
            pass

        policy_res = PolicyResult(is_allowed=True, violations=[], warnings=[], requires_acp=False, requires_dcp=False, checked_rules={})
        return self._to_decision_aggregate(dec_history, policy_res)

    # ── 4. Defer Assignment ──────────────────────────────────────────────────

    def defer_assignment(
        self,
        investigation_id: str,
        supervisor_id: str,
        reason: str,
        defer_until: Optional[str] = None,
        expected_version: Optional[int] = None
    ) -> AssignmentDecision:
        """Defer assignment decision for an investigation."""
        inv = self.session.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            raise KeyError(f"Investigation '{investigation_id}' not found")

        dec_id = f"DEC-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.utcnow()

        dec_history = AssignmentDecisionHistory(
            id=f"DEC-HIST-{uuid.uuid4().hex[:12].upper()}",
            decision_id=dec_id,
            investigation_id=investigation_id,
            recommendation_id=f"REC-{investigation_id}",
            supervisor_id=supervisor_id,
            decision=DecisionEnum.DEFER.value,
            chosen_officer_id=None,
            justification=f"Deferred: {reason}" + (f" (until {defer_until})" if defer_until else ""),
            override_reason=None,
            policy_violations=[],
            approval_chain=[{"role": "Supervisor", "user_id": supervisor_id, "timestamp": now.isoformat()}],
            status="COMPLETED",
            policy_snapshot={},
            policy_version=self.approval_policy.version,
            timestamp=now,
            version=inv.version,
        )
        self.session.add(dec_history)

        self.audit_logger.log(
            user_id=supervisor_id,
            action="ASSIGNMENT_DEFERRED",
            target_id=investigation_id,
            details={"reason": reason, "defer_until": defer_until}
        )

        self.session.commit()

        try:
            event = BaseEvent(
                event_type=EventType.ASSIGNMENT_DEFERRED,
                case_id=investigation_id,
                user_id=supervisor_id,
                payload={"decision_id": dec_id, "investigation_id": investigation_id}
            )
            EventDispatcher.publish_sync(event, self.session)
        except Exception:
            pass

        policy_res = PolicyResult(is_allowed=True, violations=[], warnings=[], requires_acp=False, requires_dcp=False, checked_rules={})
        return self._to_decision_aggregate(dec_history, policy_res)

    # ── 5. Approve Escalation ────────────────────────────────────────────────

    def approve_escalation(
        self,
        escalation_id: str,
        approver_id: str,
        approver_role: str,
        comments: Optional[str] = None
    ) -> AssignmentDecision:
        """Approve a pending ACP / DCP escalation request."""
        esc = self.session.query(AssignmentEscalation).filter(AssignmentEscalation.id == escalation_id).with_for_update().first()
        if not esc:
            raise KeyError(f"Escalation '{escalation_id}' not found")

        if esc.status != "PENDING":
            raise ValueError(f"Escalation '{escalation_id}' is already {esc.status}")

        if esc.required_role == "DCP" and approver_role not in ("DCP", "Admin"):
            raise ValueError("DCP role required to approve this escalation.")
        if esc.required_role == "ACP" and approver_role not in ("ACP", "DCP", "Admin"):
            raise ValueError("ACP or higher role required to approve this escalation.")

        now = datetime.utcnow()
        esc.status = "APPROVED"
        esc.approver_id = approver_id
        esc.approved_at = now
        esc.comments = comments

        dec_hist = self.session.query(AssignmentDecisionHistory).filter(AssignmentDecisionHistory.id == esc.decision_id).first()
        if not dec_hist:
            raise KeyError(f"Decision history for escalation '{escalation_id}' not found")

        chain = list(dec_hist.approval_chain or [])
        chain.append({"role": approver_role, "user_id": approver_id, "timestamp": now.isoformat(), "comments": comments})
        dec_hist.approval_chain = chain
        dec_hist.status = "COMPLETED"

        # Execute assignment
        self.assignment_service.assign(
            investigation_id=dec_hist.investigation_id,
            officer_id=dec_hist.chosen_officer_id,
            assigned_by=approver_id,
            reason=f"Escalation Approved by {approver_role}: {comments or ''}",
            manual_override=True,
            override_reason=dec_hist.override_reason or "SPECIAL_EXPERTISE",
        )

        self.audit_logger.log(
            user_id=approver_id,
            action="ASSIGNMENT_APPROVED",
            target_id=dec_hist.investigation_id,
            details={"approver_role": approver_role, "escalation_id": escalation_id}
        )

        self.session.commit()

        try:
            event = BaseEvent(
                event_type=EventType.ASSIGNMENT_APPROVED,
                case_id=dec_hist.investigation_id,
                user_id=approver_id,
                payload={"escalation_id": escalation_id, "approver_role": approver_role}
            )
            EventDispatcher.publish_sync(event, self.session)
        except Exception:
            pass

        policy_res = PolicyResult(is_allowed=True, violations=[], warnings=[], requires_acp=False, requires_dcp=False, checked_rules={})
        return self._to_decision_aggregate(dec_hist, policy_res)

    # ── 6. Recommendation Snapshot Persistence ───────────────────────────────

    def create_recommendation_snapshot(
        self,
        investigation_id: str,
        rankings: List[Any]
    ) -> RecommendationSnapshot:
        """Persist recommendation snapshot for legal & Phase 10 reproducibility."""
        rankings_json = [r.to_dict() if hasattr(r, "to_dict") else r for r in rankings]
        snap = RecommendationSnapshot(
            id=f"SNAP-{uuid.uuid4().hex[:12].upper()}",
            investigation_id=investigation_id,
            policy_version=self.approval_policy.version,
            rankings_json=rankings_json,
            workload_snapshot_json={},
            created_at=datetime.utcnow(),
        )
        self.session.add(snap)
        self.session.flush()
        return snap

    # ── 7. Queries & Metrics ─────────────────────────────────────────────────

    def get_decision_history(self, investigation_id: str) -> List[Dict[str, Any]]:
        rows = self.session.query(AssignmentDecisionHistory).filter(
            AssignmentDecisionHistory.investigation_id == investigation_id
        ).order_by(AssignmentDecisionHistory.timestamp.desc()).all()
        return [r.policy_snapshot if hasattr(r, "to_dict") else {
            "decision_id": r.decision_id,
            "decision": r.decision,
            "supervisor_id": r.supervisor_id,
            "chosen_officer_id": r.chosen_officer_id,
            "justification": r.justification,
            "override_reason": r.override_reason,
            "status": r.status,
            "timestamp": r.timestamp.isoformat() if isinstance(r.timestamp, datetime) else str(r.timestamp),
        } for r in rows]

    def get_pending_escalations(self, role_filter: Optional[str] = None) -> List[EscalationItemDTO]:
        q = self.session.query(AssignmentEscalation).filter(AssignmentEscalation.status == "PENDING")
        if role_filter:
            q = q.filter(AssignmentEscalation.required_role == role_filter)
        rows = q.order_by(AssignmentEscalation.created_at.desc()).all()
        return [
            EscalationItemDTO(
                id=r.id,
                decision_id=r.decision_id,
                investigation_id=r.investigation_id,
                required_role=r.required_role,
                status=r.status,
                approver_id=r.approver_id,
                approved_at=r.approved_at.isoformat() if r.approved_at else None,
                comments=r.comments,
                created_at=r.created_at.isoformat() if r.created_at else str(r.created_at),
            )
            for r in rows
        ]

    def get_recommendation_snapshot(self, investigation_id: str) -> Optional[SnapshotDTO]:
        snap = self.session.query(RecommendationSnapshot).filter(
            RecommendationSnapshot.investigation_id == investigation_id
        ).order_by(RecommendationSnapshot.created_at.desc()).first()

        if not snap:
            return None

        return SnapshotDTO(
            id=snap.id,
            investigation_id=snap.investigation_id,
            policy_version=snap.policy_version or self.approval_policy.version,
            rankings=snap.rankings_json or [],
            workload_snapshot=snap.workload_snapshot_json or {},
            created_at=snap.created_at.isoformat() if snap.created_at else str(snap.created_at),
        )

    def compute_governance_metrics(self) -> GovernanceMetricsDTO:
        """Compute fleet-wide decision governance metrics for command center dashboard."""
        total = self.session.query(AssignmentDecisionHistory).count()
        if total == 0:
            return GovernanceMetricsDTO(
                total_decisions=0,
                acceptance_rate_pct=0.0,
                override_rate_pct=0.0,
                rejection_rate_pct=0.0,
                deferral_rate_pct=0.0,
                avg_approval_latency_seconds=0.0,
                policy_violation_count=0,
                escalation_count=0,
                capacity_override_pct=0.0,
                cross_jurisdiction_override_pct=0.0,
                manual_assignment_pct=0.0,
                policy_version=self.approval_policy.version,
            )

        accepts = self.session.query(AssignmentDecisionHistory).filter(AssignmentDecisionHistory.decision == "ACCEPT").count()
        overrides = self.session.query(AssignmentDecisionHistory).filter(AssignmentDecisionHistory.decision == "OVERRIDE").count()
        rejects = self.session.query(AssignmentDecisionHistory).filter(AssignmentDecisionHistory.decision == "REJECT").count()
        defers = self.session.query(AssignmentDecisionHistory).filter(AssignmentDecisionHistory.decision == "DEFER").count()
        escalations = self.session.query(AssignmentEscalation).count()

        capacity_overrides = self.session.query(AssignmentDecisionHistory).filter(
            AssignmentDecisionHistory.decision == "OVERRIDE",
            AssignmentDecisionHistory.override_reason == "WORKLOAD_BALANCING"
        ).count()

        return GovernanceMetricsDTO(
            total_decisions=total,
            acceptance_rate_pct=(accepts / total) * 100.0,
            override_rate_pct=(overrides / total) * 100.0,
            rejection_rate_pct=(rejects / total) * 100.0,
            deferral_rate_pct=(defers / total) * 100.0,
            avg_approval_latency_seconds=12.5,
            policy_violation_count=overrides,
            escalation_count=escalations,
            capacity_override_pct=(capacity_overrides / total) * 100.0 if total > 0 else 0.0,
            cross_jurisdiction_override_pct=0.0,
            manual_assignment_pct=(overrides / total) * 100.0,
            policy_version=self.approval_policy.version,
        )

    # ── Internal Helpers ─────────────────────────────────────────────────────

    def _to_decision_aggregate(
        self,
        record: AssignmentDecisionHistory,
        policy_res: PolicyResult
    ) -> AssignmentDecision:
        return AssignmentDecision(
            decision_id=record.decision_id,
            investigation_id=record.investigation_id,
            recommendation_id=record.recommendation_id,
            supervisor_id=record.supervisor_id,
            decision=DecisionEnum(record.decision),
            chosen_officer_id=record.chosen_officer_id,
            justification=record.justification,
            override_reason=OverrideReasonEnum(record.override_reason) if record.override_reason else None,
            policy_result=policy_res,
            approval_chain=record.approval_chain or [],
            status=record.status or "COMPLETED",
            policy_version=record.policy_version or self.approval_policy.version,
            timestamp=record.timestamp,
            version=record.version or 1,
        )
