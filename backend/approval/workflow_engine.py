"""Approval Workflow Engine (Phase 8.4 Deliverable 2).

Manages stage transitions, stage progression validation, timeouts, sequential/parallel approver checking,
and escalation triggers for Approval Aggregates.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.approval.contracts import (
    ApprovalAggregate,
    ApprovalStage,
    ApprovalStageStatus,
    ApprovalStatus,
    ApprovalType,
    InvalidApprovalStateError,
)


class ApprovalWorkflowEngine:
    """Deterministic Workflow Engine enforcing sequential and parallel stage execution rules."""

    ALLOWED_TRANSITIONS: Dict[ApprovalStatus, List[ApprovalStatus]] = {
        ApprovalStatus.DRAFT: [ApprovalStatus.SUBMITTED, ApprovalStatus.CANCELLED],
        ApprovalStatus.SUBMITTED: [ApprovalStatus.UNDER_REVIEW, ApprovalStatus.CANCELLED],
        ApprovalStatus.UNDER_REVIEW: [
            ApprovalStatus.UNDER_REVIEW,
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.RETURNED,
            ApprovalStatus.ESCALATED,
            ApprovalStatus.EXPIRED,
            ApprovalStatus.CANCELLED,
        ],
        ApprovalStatus.RETURNED: [ApprovalStatus.UNDER_REVIEW, ApprovalStatus.CANCELLED],
        ApprovalStatus.ESCALATED: [
            ApprovalStatus.UNDER_REVIEW,
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.CANCELLED,
        ],
        ApprovalStatus.APPROVED: [],  # Terminal
        ApprovalStatus.REJECTED: [],  # Terminal
        ApprovalStatus.CANCELLED: [],  # Terminal
        ApprovalStatus.EXPIRED: [],  # Terminal
    }

    def validate_transition(
        self, aggregate: ApprovalAggregate, target_status: ApprovalStatus
    ) -> None:
        """Validates that target_status is a valid deterministic transition from aggregate.status."""
        allowed = self.ALLOWED_TRANSITIONS.get(aggregate.status, [])
        if target_status not in allowed:
            raise InvalidApprovalStateError(
                f"Invalid workflow transition from '{aggregate.status.value}' to '{target_status.value}'"
            )

    def can_actor_approve_stage(
        self, aggregate: ApprovalAggregate, stage: ApprovalStage, actor_id: str, actor_role: str
    ) -> Tuple[bool, str]:
        """Validates whether an actor can approve the specified stage."""
        # 1. Segregation of duties: requester cannot approve own request (unless emergency policy permits, checked in policy engine)
        if actor_id == aggregate.requester_id:
            return False, "Requester cannot approve their own request (segregation of duties)"

        # 2. Check role requirement
        roles_hierarchy = ["read_only", "analyst", "supervisor", "acp", "dcp", "admin"]
        actor_role_clean = str(actor_role).lower().replace("role.", "")
        req_role_clean = str(stage.required_role).lower().replace("role.", "")

        if actor_role_clean in roles_hierarchy and req_role_clean in roles_hierarchy:
            actor_lvl = roles_hierarchy.index(actor_role_clean)
            req_lvl = roles_hierarchy.index(req_role_clean)
            if actor_lvl < req_lvl:
                return False, f"Role '{actor_role}' does not satisfy required stage role '{stage.required_role}'"
        elif actor_role_clean != req_lvl if 'req_lvl' in locals() else actor_role_clean != req_role_clean:
            if actor_role_clean not in ("admin", "dcp"):
                return False, f"Role '{actor_role}' does not match required stage role '{stage.required_role}'"

        # 3. Check if actor already approved this stage
        if actor_id in stage.approved_by:
            return False, f"Actor '{actor_id}' has already approved stage '{stage.stage_name}'"

        return True, ""

    def process_stage_approval(
        self,
        aggregate: ApprovalAggregate,
        approver_id: str,
        approver_role: str,
        comments: str = "",
        conditions: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, bool]:
        """Processes an approval decision on the aggregate's active stage.
        
        Returns: (stage_completed: bool, workflow_completed: bool)
        """
        self.validate_transition(aggregate, ApprovalStatus.APPROVED if aggregate.current_stage_index == len(aggregate.stages) - 1 else ApprovalStatus.UNDER_REVIEW)

        current_stage = aggregate.current_stage()
        if not current_stage:
            raise InvalidApprovalStateError("No current active stage found in workflow")

        can_approve, reason = self.can_actor_approve_stage(aggregate, current_stage, approver_id, approver_role)
        if not can_approve:
            raise InvalidApprovalStateError(f"Approval stage validation failed: {reason}")

        workflow_completed = aggregate.approve_stage(
            approver_id=approver_id,
            approver_role=approver_role,
            comments=comments,
            conditions=conditions,
        )
        stage_completed = current_stage.status == ApprovalStageStatus.APPROVED
        return stage_completed, workflow_completed

    def check_expiration(self, aggregate: ApprovalAggregate) -> bool:
        """Checks if aggregate has passed its expires_at timestamp. Returns True if expired."""
        if not aggregate.expires_at:
            return False

        if aggregate.status in (
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.CANCELLED,
            ApprovalStatus.EXPIRED,
        ):
            return False

        try:
            exp_dt = datetime.fromisoformat(aggregate.expires_at.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            if now_dt >= exp_dt:
                aggregate.expire(reason=f"Approval expired at {aggregate.expires_at}")
                return True
        except Exception:
            pass

        return False
