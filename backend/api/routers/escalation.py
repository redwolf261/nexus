"""Escalation & SLA Governance API Router (Phase 8.4 Milestone 2 Deliverable 6).

Exposes REST API endpoints for querying escalations, acknowledging, resolving, delegating,
reassigning, and reviewing SLA escalation histories.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.api.dependencies import get_current_user
from backend.approval.contracts import InvalidApprovalStateError, OptimisticLockError
from backend.approval.delegation_engine import DelegationType
from backend.approval.escalation import EscalationReason, EscalationStatus, InvalidEscalationStateError
from backend.approval.escalation_service import EscalationService
from backend.db.schema import User


router = APIRouter(prefix="/api/approval", tags=["Escalation & SLA Governance"])

_escalation_service = EscalationService()


def get_escalation_service() -> EscalationService:
    return _escalation_service


# Request Schemas
class DelegateRequest(BaseModel):
    delegatee_id: str = Field(..., max_length=100)
    delegatee_role: str = Field("supervisor", max_length=50)
    delegation_type: str = Field("TEMPORARY_ACTING", max_length=50)
    duration_hours: float = Field(24.0, ge=0.5, le=720.0)
    reason: str = Field("", max_length=1000)


class ReassignRequest(BaseModel):
    target_user_id: str = Field(..., max_length=100)
    reason: str = Field("", max_length=1000)
    expected_version: Optional[int] = None


class ResolveEscalationRequest(BaseModel):
    notes: str = Field("", max_length=2000)
    expected_version: Optional[int] = None


class AcknowledgeEscalationRequest(BaseModel):
    expected_version: Optional[int] = None


@router.get("/escalations")
def list_escalations(
    status_filter: Optional[str] = Query(None, alias="status"),
    reason_filter: Optional[str] = Query(None, alias="reason"),
    assigned_role: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: EscalationService = Depends(get_escalation_service),
):
    """Queries escalation aggregates matching filters."""
    items = service.repository.find(
        status=status_filter,
        reason=reason_filter,
        assigned_role=assigned_role,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [item.to_dict() for item in items],
        "count": len(items),
        "limit": limit,
        "offset": offset,
    }


@router.get("/escalations/pending")
def list_pending_escalations(
    assigned_role: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: EscalationService = Depends(get_escalation_service),
):
    """Queries pending escalations requiring immediate attention."""
    role_to_check = assigned_role or (current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role))
    items = service.pending(actor_role=role_to_check, limit=limit, offset=offset)
    return {
        "items": [item.to_dict() for item in items],
        "count": len(items),
        "limit": limit,
        "offset": offset,
    }


@router.post("/{id}/acknowledge")
def acknowledge_escalation(
    id: str,
    body: AcknowledgeEscalationRequest = AcknowledgeEscalationRequest(),
    current_user: User = Depends(get_current_user),
    service: EscalationService = Depends(get_escalation_service),
):
    """Acknowledges an active escalation."""
    try:
        role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        # Try lookup by escalation_id first, then fallback to approval_id
        esc = service.repository.get_by_id(id) or service.repository.get_by_approval_id(id)
        if not esc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Escalation for ID '{id}' not found")

        agg = service.acknowledge(
            escalation_id=esc.escalation_id,
            actor_id=current_user.username,
            actor_role=role_str,
            expected_version=body.expected_version,
        )
        return agg.to_dict()
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidEscalationStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/resolve")
def resolve_escalation(
    id: str,
    body: ResolveEscalationRequest = ResolveEscalationRequest(),
    current_user: User = Depends(get_current_user),
    service: EscalationService = Depends(get_escalation_service),
):
    """Resolves an active escalation."""
    try:
        role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        esc = service.repository.get_by_id(id) or service.repository.get_by_approval_id(id)
        if not esc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Escalation for ID '{id}' not found")

        agg = service.resolve(
            escalation_id=esc.escalation_id,
            actor_id=current_user.username,
            actor_role=role_str,
            notes=body.notes,
            expected_version=body.expected_version,
        )
        return agg.to_dict()
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidEscalationStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/delegate")
def delegate_authority(
    id: str,
    body: DelegateRequest,
    current_user: User = Depends(get_current_user),
    service: EscalationService = Depends(get_escalation_service),
):
    """Creates a temporary delegation of authority for an approval or escalation context."""
    try:
        role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        record = service.delegate(
            delegator_id=current_user.username,
            delegatee_id=body.delegatee_id,
            delegator_role=role_str,
            delegatee_role=body.delegatee_role,
            delegation_type=body.delegation_type,
            duration_hours=body.duration_hours,
            reason=body.reason,
        )
        return record.to_dict()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/reassign")
def reassign_escalation(
    id: str,
    body: ReassignRequest,
    current_user: User = Depends(get_current_user),
    service: EscalationService = Depends(get_escalation_service),
):
    """Reassigns an escalation to a specific authority user."""
    try:
        role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        esc = service.repository.get_by_id(id) or service.repository.get_by_approval_id(id)
        if not esc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Escalation for ID '{id}' not found")

        agg = service.reassign(
            escalation_id=esc.escalation_id,
            target_user_id=body.target_user_id,
            actor_id=current_user.username,
            actor_role=role_str,
            reason=body.reason,
            expected_version=body.expected_version,
        )
        return agg.to_dict()
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidEscalationStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{id}/escalation-history")
def get_escalation_history(
    id: str,
    current_user: User = Depends(get_current_user),
    service: EscalationService = Depends(get_escalation_service),
):
    """Gets history events for an escalation process."""
    try:
        esc = service.repository.get_by_id(id) or service.repository.get_by_approval_id(id)
        if not esc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Escalation for ID '{id}' not found")

        events = service.history(esc.escalation_id)
        return {
            "escalation_id": esc.escalation_id,
            "approval_id": esc.approval_id,
            "events": [evt.to_dict() for evt in events],
        }
    except InvalidEscalationStateError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
