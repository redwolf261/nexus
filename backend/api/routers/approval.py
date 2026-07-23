"""Approval API Router (Phase 8.4 Deliverable 6).

Exposes REST API endpoints for submitting, approving, rejecting, returning, escalating,
and inspecting approval requests.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.api.dependencies import get_current_user
from backend.approval.approval_service import ApprovalService
from backend.approval.contracts import (
    ApprovalPolicyViolationError,
    ApprovalType,
    InvalidApprovalStateError,
    OptimisticLockError,
)
from backend.db.schema import User


router = APIRouter(prefix="/api/approval", tags=["Approval & Governance"])

# Singleton service instance across API requests
_approval_service = ApprovalService()


def get_approval_service() -> ApprovalService:
    return _approval_service


# Request & Response Schemas
class CreateApprovalRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field("", max_length=2000)
    approval_type: str = Field(..., description="Approval type enum name")
    entity_type: str = Field(..., max_length=100)
    entity_id: str = Field(..., max_length=100)
    district_id: str = Field("DISTRICT_001", max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    expires_at: Optional[str] = None


class ActionApprovalRequest(BaseModel):
    comments: str = Field("", max_length=2000)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    expected_version: Optional[int] = None
    target_role: Optional[str] = None
    reason: Optional[str] = None
    updated_metadata: Optional[Dict[str, Any]] = None


@router.post("/request", status_code=status.HTTP_201_CREATED)
def submit_approval_request(
    body: CreateApprovalRequest,
    current_user: User = Depends(get_current_user),
    service: ApprovalService = Depends(get_approval_service),
):
    """Submits a new operational approval request."""
    try:
        agg = service.submit_request(
            title=body.title,
            description=body.description,
            approval_type=body.approval_type,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            requester_id=current_user.username,
            requester_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
            district_id=body.district_id,
            metadata=body.metadata,
            expires_at=body.expires_at,
        )
        return agg.to_dict()
    except ApprovalPolicyViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidApprovalStateError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{approval_id}/approve")
def approve_request(
    approval_id: str,
    body: ActionApprovalRequest = ActionApprovalRequest(),
    current_user: User = Depends(get_current_user),
    service: ApprovalService = Depends(get_approval_service),
):
    """Approves the current stage of an approval request."""
    try:
        role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        agg, completed = service.approve(
            approval_id=approval_id,
            approver_id=current_user.username,
            approver_role=role_str,
            comments=body.comments,
            conditions=body.conditions,
            expected_version=body.expected_version,
        )
        res = agg.to_dict()
        res["workflow_completed"] = completed
        return res
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ApprovalPolicyViolationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidApprovalStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{approval_id}/reject")
def reject_request(
    approval_id: str,
    body: ActionApprovalRequest = ActionApprovalRequest(),
    current_user: User = Depends(get_current_user),
    service: ApprovalService = Depends(get_approval_service),
):
    """Rejects an approval request."""
    try:
        role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        agg = service.reject(
            approval_id=approval_id,
            approver_id=current_user.username,
            approver_role=role_str,
            comments=body.comments,
            conditions=body.conditions,
            expected_version=body.expected_version,
        )
        return agg.to_dict()
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ApprovalPolicyViolationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidApprovalStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{approval_id}/return")
def return_request_for_revision(
    approval_id: str,
    body: ActionApprovalRequest = ActionApprovalRequest(),
    current_user: User = Depends(get_current_user),
    service: ApprovalService = Depends(get_approval_service),
):
    """Returns an approval request for revision."""
    try:
        role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        agg = service.return_for_revision(
            approval_id=approval_id,
            approver_id=current_user.username,
            approver_role=role_str,
            comments=body.comments,
            expected_version=body.expected_version,
        )
        return agg.to_dict()
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ApprovalPolicyViolationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidApprovalStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{approval_id}/cancel")
def cancel_request(
    approval_id: str,
    body: ActionApprovalRequest = ActionApprovalRequest(),
    current_user: User = Depends(get_current_user),
    service: ApprovalService = Depends(get_approval_service),
):
    """Cancels an active approval request."""
    try:
        role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        agg = service.cancel(
            approval_id=approval_id,
            actor_id=current_user.username,
            actor_role=role_str,
            reason=body.reason or body.comments,
            expected_version=body.expected_version,
        )
        return agg.to_dict()
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ApprovalPolicyViolationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidApprovalStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{approval_id}/escalate")
def escalate_request(
    approval_id: str,
    body: ActionApprovalRequest = ActionApprovalRequest(),
    current_user: User = Depends(get_current_user),
    service: ApprovalService = Depends(get_approval_service),
):
    """Escalates an approval request to a higher authority."""
    try:
        role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        agg = service.escalate(
            approval_id=approval_id,
            actor_id=current_user.username,
            actor_role=role_str,
            reason=body.reason or body.comments,
            target_role=body.target_role,
            expected_version=body.expected_version,
        )
        return agg.to_dict()
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidApprovalStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{approval_id}/resubmit")
def resubmit_request(
    approval_id: str,
    body: ActionApprovalRequest = ActionApprovalRequest(),
    current_user: User = Depends(get_current_user),
    service: ApprovalService = Depends(get_approval_service),
):
    """Resubmits a returned approval request."""
    try:
        role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        agg = service.resubmit(
            approval_id=approval_id,
            actor_id=current_user.username,
            actor_role=role_str,
            updated_metadata=body.updated_metadata,
            expected_version=body.expected_version,
        )
        return agg.to_dict()
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ApprovalPolicyViolationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidApprovalStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/pending")
def get_pending_approvals(
    approver_role: Optional[str] = Query(None),
    district_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: ApprovalService = Depends(get_approval_service),
):
    """Queries pending approval requests requiring decision."""
    role_to_check = approver_role or (current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role))
    items = service.get_pending(
        approver_role=role_to_check,
        district_id=district_id,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [item.to_dict() for item in items],
        "count": len(items),
        "limit": limit,
        "offset": offset,
    }


@router.get("/my-actions")
def get_my_approval_actions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: ApprovalService = Depends(get_approval_service),
):
    """Queries approvals initiated by or acted upon by current user."""
    items = service.get_my_actions(user_id=current_user.username, limit=limit, offset=offset)
    return {
        "items": [item.to_dict() for item in items],
        "count": len(items),
        "limit": limit,
        "offset": offset,
    }


@router.get("/{approval_id}")
def get_approval_details(
    approval_id: str,
    current_user: User = Depends(get_current_user),
    service: ApprovalService = Depends(get_approval_service),
):
    """Gets details for a specific approval request."""
    agg = service.repository.get_by_id(approval_id)
    if not agg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Approval '{approval_id}' not found")
    return agg.to_dict()


@router.get("/{approval_id}/history")
def get_approval_history(
    approval_id: str,
    current_user: User = Depends(get_current_user),
    service: ApprovalService = Depends(get_approval_service),
):
    """Gets immutable audit history trail for an approval request."""
    try:
        hist = service.history(approval_id)
        return {"approval_id": approval_id, "history": [h.to_dict() for h in hist]}
    except InvalidApprovalStateError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
