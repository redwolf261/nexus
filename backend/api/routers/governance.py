"""Assignment Governance Router (Phase 8.2 Milestone 5).

REST endpoints for supervisor decision workflow, override governance, escalation approvals,
decision audit history, recommendation snapshots, and command center metrics.

Protected by JWT & RBAC (Supervisor, ACP, DCP, Admin).
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.db.schema import User, Role
from backend.auth.deps import get_current_user, require_role
from backend.assignment.governance_service import AssignmentGovernanceService
from backend.assignment.override_policy import OverrideReasonEnum
from backend.core.logging import logger

router = APIRouter(prefix="/assignment", tags=["Assignment Governance"])


# ── Request Models ───────────────────────────────────────────────────────────

class AcceptRequest(BaseModel):
    recommendation_id: Optional[str] = None
    expected_version: Optional[int] = None


class OverrideRequest(BaseModel):
    chosen_officer_id: str
    override_reason: OverrideReasonEnum
    justification: str = Field(..., min_length=50, description="Mandatory minimum 50 characters justification")
    is_interstate: Optional[bool] = False
    expected_version: Optional[int] = None


class RejectRequest(BaseModel):
    justification: str
    expected_version: Optional[int] = None


class DeferRequest(BaseModel):
    reason: str
    defer_until: Optional[str] = None
    expected_version: Optional[int] = None


class ApproveEscalationRequest(BaseModel):
    comments: Optional[str] = None


# ── Decision Endpoints ───────────────────────────────────────────────────────

@router.post("/{investigation_id}/accept")
def accept_recommendation(
    investigation_id: str,
    body: AcceptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """POST /assignment/{id}/accept — Accept top recommendation (Supervisor only)."""
    service = AssignmentGovernanceService(db)
    try:
        agg = service.accept_recommendation(
            investigation_id=investigation_id,
            supervisor_id=current_user.id or current_user.username,
            recommendation_id=body.recommendation_id,
            expected_version=body.expected_version,
        )
        return agg.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        status_c = 409 if "Optimistic lock" in str(e) else 400
        raise HTTPException(status_code=status_c, detail=str(e))


@router.post("/{investigation_id}/override")
def override_assignment(
    investigation_id: str,
    body: OverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """POST /assignment/{id}/override — Override recommendation with justification & policy checks."""
    service = AssignmentGovernanceService(db)
    try:
        agg = service.override_assignment(
            investigation_id=investigation_id,
            supervisor_id=current_user.id or current_user.username,
            chosen_officer_id=body.chosen_officer_id,
            override_reason=body.override_reason,
            justification=body.justification,
            is_interstate=body.is_interstate or False,
            expected_version=body.expected_version,
        )
        return agg.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        status_c = 409 if "Optimistic lock" in str(e) else 400
        raise HTTPException(status_code=status_c, detail=str(e))


@router.post("/{investigation_id}/reject")
def reject_recommendation(
    investigation_id: str,
    body: RejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """POST /assignment/{id}/reject — Reject proposed recommendations."""
    service = AssignmentGovernanceService(db)
    try:
        agg = service.reject_recommendation(
            investigation_id=investigation_id,
            supervisor_id=current_user.id or current_user.username,
            justification=body.justification,
            expected_version=body.expected_version,
        )
        return agg.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{investigation_id}/defer")
def defer_assignment(
    investigation_id: str,
    body: DeferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """POST /assignment/{id}/defer — Defer assignment decision."""
    service = AssignmentGovernanceService(db)
    try:
        agg = service.defer_assignment(
            investigation_id=investigation_id,
            supervisor_id=current_user.id or current_user.username,
            reason=body.reason,
            defer_until=body.defer_until,
            expected_version=body.expected_version,
        )
        return agg.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Audit, History & Snapshots ───────────────────────────────────────────────

@router.get("/{investigation_id}/decision-history")
def get_decision_history(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET /assignment/{id}/decision-history — Get decision audit history for an investigation."""
    service = AssignmentGovernanceService(db)
    return service.get_decision_history(investigation_id)


@router.get("/{investigation_id}/policy")
def evaluate_policy(
    investigation_id: str,
    officer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Analyst)),
):
    """GET /assignment/{id}/policy — Check deterministic override policy rules for an officer."""
    service = AssignmentGovernanceService(db)
    result = service.policy_engine.evaluate(investigation_id, officer_id)
    return result.to_dict()


@router.get("/{investigation_id}/recommendation-snapshot")
def get_recommendation_snapshot(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET /assignment/{id}/recommendation-snapshot — Fetch byte-exact persisted snapshot for legal audit."""
    service = AssignmentGovernanceService(db)
    snap = service.get_recommendation_snapshot(investigation_id)
    if not snap:
        raise HTTPException(status_code=404, detail=f"No recommendation snapshot found for '{investigation_id}'")
    return snap.to_dict()


# ── Escalation Queue ─────────────────────────────────────────────────────────

@router.get("/escalations")
def get_pending_escalations(
    role_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ACP)),
):
    """GET /assignment/escalations — Get pending ACP / DCP approval queue."""
    service = AssignmentGovernanceService(db)
    escalations = service.get_pending_escalations(role_filter=role_filter)
    return [e.to_dict() for e in escalations]


@router.post("/escalations/{escalation_id}/approve")
def approve_escalation(
    escalation_id: str,
    body: ApproveEscalationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ACP)),
):
    """POST /assignment/escalations/{id}/approve — Approve escalation (ACP / DCP required)."""
    service = AssignmentGovernanceService(db)
    try:
        agg = service.approve_escalation(
            escalation_id=escalation_id,
            approver_id=current_user.id or current_user.username,
            approver_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
            comments=body.comments,
        )
        return agg.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/metrics")
def get_governance_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /assignment/metrics — Fleet-wide supervisor decision and operational metrics."""
    service = AssignmentGovernanceService(db)
    metrics = service.compute_governance_metrics()
    return metrics.to_dict()
