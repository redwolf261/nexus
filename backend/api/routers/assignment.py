"""Assignment API Router (Phase 8.2 Milestone 4).

Exposes REST endpoints for recommendation, validation, assignment, reassignment,
bulk operations, history queries, and completion duration estimation.

JWT protected & RBAC enforced (Supervisor / Admin for assignment mutations).
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.db.schema import User, Role
from backend.auth.deps import get_current_user, require_role
from backend.assignment.assignment_service import AssignmentService
from backend.core.logging import logger

router = APIRouter(prefix="/assignment", tags=["Assignment Service"])


# ── Request / Response Schemas ───────────────────────────────────────────────

class ValidateRequest(BaseModel):
    investigation_id: str
    officer_id: str


class AssignRequest(BaseModel):
    investigation_id: str
    officer_id: str
    reason: Optional[str] = ""
    manual_override: Optional[bool] = False
    override_reason: Optional[str] = None
    expected_version: Optional[int] = None


class ReassignRequest(BaseModel):
    investigation_id: str
    new_officer_id: str
    reason: str
    reassign_type: Optional[str] = "MANUAL"
    manual_override: Optional[bool] = False
    override_reason: Optional[str] = None
    expected_version: Optional[int] = None


class BulkReassignRequest(BaseModel):
    reassignments: List[ReassignRequest]


class RecommendManyRequest(BaseModel):
    investigation_ids: List[str]
    limit_per_case: Optional[int] = 3


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/recommend/{investigation_id}")
def get_recommendations(
    investigation_id: str,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Analyst)),
):
    """GET /assignment/recommend/{investigation_id} — Get ranked officer recommendations."""
    service = AssignmentService(db)
    try:
        ranked = service.recommend(investigation_id, limit=limit)
        return [r.to_dict() for r in ranked]
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate")
def validate_assignment(
    body: ValidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Analyst)),
):
    """POST /assignment/validate — Check operational pre-conditions before assignment."""
    service = AssignmentService(db)
    result = service.validate(body.investigation_id, body.officer_id)
    return result.to_dict()


@router.post("/assign")
def assign_officer(
    body: AssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """POST /assignment/assign — Assign an officer to an investigation (Supervisor only)."""
    service = AssignmentService(db)
    try:
        aggregate = service.assign(
            investigation_id=body.investigation_id,
            officer_id=body.officer_id,
            assigned_by=current_user.id or current_user.username,
            reason=body.reason or "",
            manual_override=body.manual_override or False,
            override_reason=body.override_reason,
            expected_version=body.expected_version,
        )
        return aggregate.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        status_c = 409 if "Optimistic lock" in str(e) else 400
        raise HTTPException(status_code=status_c, detail=str(e))


@router.post("/reassign")
def reassign_officer(
    body: ReassignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """POST /assignment/reassign — Reassign an investigation (Supervisor only)."""
    service = AssignmentService(db)
    try:
        aggregate = service.reassign(
            investigation_id=body.investigation_id,
            new_officer_id=body.new_officer_id,
            assigned_by=current_user.id or current_user.username,
            reason=body.reason,
            reassign_type=body.reassign_type or "MANUAL",
            manual_override=body.manual_override or False,
            override_reason=body.override_reason,
            expected_version=body.expected_version,
        )
        return aggregate.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        status_c = 409 if "Optimistic lock" in str(e) else 400
        raise HTTPException(status_code=status_c, detail=str(e))


@router.post("/bulk-reassign")
def bulk_reassign_officers(
    body: BulkReassignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """POST /assignment/bulk-reassign — Batch reassignments (Supervisor only)."""
    service = AssignmentService(db)
    try:
        reassignments_dict = [r.dict() for r in body.reassignments]
        aggregates = service.bulk_reassign(reassignments_dict, assigned_by=current_user.id or current_user.username)
        return [a.to_dict() for a in aggregates]
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recommend-many")
def recommend_many(
    body: RecommendManyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Analyst)),
):
    """POST /assignment/recommend-many — Get ranked recommendations for multiple investigations."""
    service = AssignmentService(db)
    results = service.recommend_many(body.investigation_ids, limit_per_case=body.limit_per_case or 3)
    return {inv_id: [r.to_dict() for r in recs] for inv_id, recs in results.items()}


@router.get("/history/{investigation_id}")
def get_investigation_history(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET /assignment/history/{investigation_id} — Get immutable assignment history for a case."""
    service = AssignmentService(db)
    history = service.get_history_for_investigation(investigation_id)
    return [h.to_dict() for h in history]


@router.get("/history/officer/{officer_id}")
def get_officer_history(
    officer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET /assignment/history/officer/{officer_id} — Get immutable assignment history for an officer."""
    service = AssignmentService(db)
    history = service.get_history_for_officer(officer_id)
    return [h.to_dict() for h in history]


@router.get("/estimate/{investigation_id}")
def estimate_completion(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET /assignment/estimate/{investigation_id} — Deterministic completion duration estimate."""
    service = AssignmentService(db)
    try:
        estimate = service.estimate_completion(investigation_id)
        return estimate.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
