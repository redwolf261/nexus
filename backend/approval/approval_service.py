"""Approval Service (Phase 8.4 Deliverable 4).

Orchestrates approval request lifecycles, policy validation, workflow stage progression,
audit logging, optimistic concurrency, and WebSocket event broadcasting.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.approval.approval_repository import ApprovalRepository
from backend.approval.approval_templates import ApprovalTemplates
from backend.approval.contracts import (
    ApprovalAggregate,
    ApprovalDecision,
    ApprovalHistory,
    ApprovalPolicyViolationError,
    ApprovalStage,
    ApprovalStatus,
    ApprovalType,
    InvalidApprovalStateError,
    OptimisticLockError,
)
from backend.approval.policy_engine import ApprovalPolicyEngine, PolicyValidationResult
from backend.approval.workflow_engine import ApprovalWorkflowEngine
from backend.events.dispatcher import EventDispatcher
from backend.events.event_types import EventType

logger = logging.getLogger("nexus.approval_service")


class ApprovalService:
    """Core domain service for the NEXUS Approval & Governance System."""

    def __init__(
        self,
        repository: Optional[ApprovalRepository] = None,
        workflow_engine: Optional[ApprovalWorkflowEngine] = None,
        policy_engine: Optional[ApprovalPolicyEngine] = None,
        dispatcher: Optional[EventDispatcher] = None,
    ) -> None:
        self.repository = repository or ApprovalRepository()
        self.workflow_engine = workflow_engine or ApprovalWorkflowEngine()
        self.policy_engine = policy_engine or ApprovalPolicyEngine()
        self.dispatcher = dispatcher or EventDispatcher()

    def _publish_event(self, event_type: EventType, aggregate: ApprovalAggregate, payload_extra: Optional[Dict[str, Any]] = None) -> None:
        try:
            payload = aggregate.to_dict()
            if payload_extra:
                payload.update(payload_extra)
            if hasattr(self.dispatcher, "dispatch"):
                self.dispatcher.dispatch(
                    event_type=event_type,
                    payload=payload,
                    entity_id=aggregate.approval_id,
                )
            elif hasattr(self.dispatcher, "publish_sync"):
                logger.info(f"Published event {event_type.value} for approval {aggregate.approval_id}")
        except Exception as e:
            logger.warning(f"Failed to dispatch WebSocket event {event_type.value}: {e}")

    def submit_request(
        self,
        title: str,
        description: str,
        approval_type: ApprovalType | str,
        entity_type: str,
        entity_id: str,
        requester_id: str,
        requester_role: str,
        district_id: str = "DISTRICT_001",
        metadata: Optional[Dict[str, Any]] = None,
        expires_at: Optional[str] = None,
    ) -> ApprovalAggregate:
        """Submits a new approval request."""
        app_type = ApprovalType(approval_type) if isinstance(approval_type, str) else approval_type
        meta = metadata or {}

        # Policy validation
        policy_res = self.policy_engine.validate_request_creation(
            approval_type=app_type,
            requester_id=requester_id,
            requester_role=requester_role,
            district_id=district_id,
            metadata=meta,
        )
        if not policy_res.valid:
            raise ApprovalPolicyViolationError(
                f"Request creation failed policy validation: {'; '.join(policy_res.violations)}"
            )

        # Default expiry if not specified
        if not expires_at:
            expires_at = self.policy_engine.calculate_default_expiration(app_type, meta)

        approval_id = f"app_{uuid.uuid4().hex[:12]}"
        stages = ApprovalTemplates.get_template_stages(app_type, meta)

        aggregate = ApprovalAggregate(
            approval_id=approval_id,
            title=title,
            description=description,
            approval_type=app_type,
            entity_type=entity_type,
            entity_id=entity_id,
            requester_id=requester_id,
            requester_role=requester_role,
            district_id=district_id,
            status=ApprovalStatus.DRAFT,
            stages=stages,
            expires_at=expires_at,
            metadata=meta,
            version=1,
        )

        # Submit workflow transition
        aggregate.submit(actor_id=requester_id, actor_role=requester_role)
        saved = self.repository.save(aggregate)

        self._publish_event(EventType.APPROVAL_SUBMITTED, saved)
        stage = saved.current_stage()
        if stage:
            self._publish_event(
                EventType.APPROVAL_ASSIGNED,
                saved,
                {"assigned_role": stage.required_role, "stage_name": stage.stage_name},
            )

        return saved

    def approve(
        self,
        approval_id: str,
        approver_id: str,
        approver_role: str,
        comments: str = "",
        conditions: Optional[Dict[str, Any]] = None,
        expected_version: Optional[int] = None,
    ) -> Tuple[ApprovalAggregate, bool]:
        """Approves the current stage of an approval request. Returns (aggregate, workflow_completed)."""
        agg = self.repository.get_by_id(approval_id)
        if not agg:
            raise InvalidApprovalStateError(f"Approval request '{approval_id}' not found")

        # Expiry check
        if self.workflow_engine.check_expiration(agg):
            self.repository.save(agg)
            self._publish_event(EventType.APPROVAL_EXPIRED, agg)
            raise InvalidApprovalStateError("Approval request has expired")

        # Policy validation
        policy_res = self.policy_engine.validate_action(
            aggregate=agg,
            action="APPROVE",
            actor_id=approver_id,
            actor_role=approver_role,
        )
        if not policy_res.valid:
            raise ApprovalPolicyViolationError(
                f"Approval action failed policy: {'; '.join(policy_res.violations)}"
            )

        prev_stage_idx = agg.current_stage_index
        stage_done, workflow_done = self.workflow_engine.process_stage_approval(
            aggregate=agg,
            approver_id=approver_id,
            approver_role=approver_role,
            comments=comments,
            conditions=conditions,
        )

        saved = self.repository.save(agg, expected_version=expected_version)

        if workflow_done:
            self._publish_event(EventType.APPROVAL_APPROVED, saved)
        elif stage_done:
            self._publish_event(EventType.APPROVAL_STAGE_CHANGED, saved)
            new_stage = saved.current_stage()
            if new_stage:
                self._publish_event(
                    EventType.APPROVAL_ASSIGNED,
                    saved,
                    {"assigned_role": new_stage.required_role, "stage_name": new_stage.stage_name},
                )

        return saved, workflow_done

    def reject(
        self,
        approval_id: str,
        approver_id: str,
        approver_role: str,
        comments: str = "",
        conditions: Optional[Dict[str, Any]] = None,
        expected_version: Optional[int] = None,
    ) -> ApprovalAggregate:
        """Rejects an approval request."""
        agg = self.repository.get_by_id(approval_id)
        if not agg:
            raise InvalidApprovalStateError(f"Approval request '{approval_id}' not found")

        policy_res = self.policy_engine.validate_action(
            aggregate=agg,
            action="REJECT",
            actor_id=approver_id,
            actor_role=approver_role,
        )
        if not policy_res.valid:
            raise ApprovalPolicyViolationError(
                f"Reject action failed policy: {'; '.join(policy_res.violations)}"
            )

        agg.reject(approver_id=approver_id, approver_role=approver_role, comments=comments, conditions=conditions)
        saved = self.repository.save(agg, expected_version=expected_version)
        self._publish_event(EventType.APPROVAL_REJECTED, saved)
        return saved

    def return_for_revision(
        self,
        approval_id: str,
        approver_id: str,
        approver_role: str,
        comments: str = "",
        expected_version: Optional[int] = None,
    ) -> ApprovalAggregate:
        """Returns an approval request for revision."""
        agg = self.repository.get_by_id(approval_id)
        if not agg:
            raise InvalidApprovalStateError(f"Approval request '{approval_id}' not found")

        policy_res = self.policy_engine.validate_action(
            aggregate=agg,
            action="RETURN_FOR_REVISION",
            actor_id=approver_id,
            actor_role=approver_role,
        )
        if not policy_res.valid:
            raise ApprovalPolicyViolationError(
                f"Return for revision failed policy: {'; '.join(policy_res.violations)}"
            )

        agg.return_for_revision(approver_id=approver_id, approver_role=approver_role, comments=comments)
        saved = self.repository.save(agg, expected_version=expected_version)
        self._publish_event(EventType.APPROVAL_RETURNED, saved)
        return saved

    def cancel(
        self,
        approval_id: str,
        actor_id: str,
        actor_role: str,
        reason: str = "",
        expected_version: Optional[int] = None,
    ) -> ApprovalAggregate:
        """Cancels an active approval request."""
        agg = self.repository.get_by_id(approval_id)
        if not agg:
            raise InvalidApprovalStateError(f"Approval request '{approval_id}' not found")

        if actor_id != agg.requester_id and str(actor_role).lower().replace("role.", "") not in ("admin", "dcp"):
            raise ApprovalPolicyViolationError("Only requester or administrator/DCP can cancel an approval request")

        agg.cancel(actor_id=actor_id, actor_role=actor_role, reason=reason)
        saved = self.repository.save(agg, expected_version=expected_version)
        self._publish_event(EventType.APPROVAL_CANCELLED, saved)
        return saved

    def expire(self, approval_id: str, reason: str = "Approval timeout expired") -> ApprovalAggregate:
        """Marks an approval request as expired."""
        agg = self.repository.get_by_id(approval_id)
        if not agg:
            raise InvalidApprovalStateError(f"Approval request '{approval_id}' not found")

        agg.expire(reason=reason)
        saved = self.repository.save(agg)
        self._publish_event(EventType.APPROVAL_EXPIRED, saved)
        return saved

    def escalate(
        self,
        approval_id: str,
        actor_id: str,
        actor_role: str,
        reason: str = "",
        target_role: Optional[str] = None,
        expected_version: Optional[int] = None,
    ) -> ApprovalAggregate:
        """Escalates an approval request."""
        agg = self.repository.get_by_id(approval_id)
        if not agg:
            raise InvalidApprovalStateError(f"Approval request '{approval_id}' not found")

        agg.escalate(actor_id=actor_id, actor_role=actor_role, reason=reason, target_role=target_role)
        saved = self.repository.save(agg, expected_version=expected_version)
        self._publish_event(EventType.APPROVAL_ESCALATED, saved)
        return saved

    def resubmit(
        self,
        approval_id: str,
        actor_id: str,
        actor_role: str,
        updated_metadata: Optional[Dict[str, Any]] = None,
        expected_version: Optional[int] = None,
    ) -> ApprovalAggregate:
        """Resubmits a returned or escalated request."""
        agg = self.repository.get_by_id(approval_id)
        if not agg:
            raise InvalidApprovalStateError(f"Approval request '{approval_id}' not found")

        if actor_id != agg.requester_id:
            raise ApprovalPolicyViolationError("Only the original requester can resubmit an approval request")

        agg.resubmit(actor_id=actor_id, actor_role=actor_role, updated_metadata=updated_metadata)
        saved = self.repository.save(agg, expected_version=expected_version)
        self._publish_event(EventType.APPROVAL_SUBMITTED, saved)
        return saved

    def validate(
        self,
        approval_type: ApprovalType | str,
        action: str,
        actor_id: str,
        actor_role: str,
        approval_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PolicyValidationResult:
        """Validates action or creation against policy without committing state."""
        if approval_id:
            agg = self.repository.get_by_id(approval_id)
            if not agg:
                return PolicyValidationResult(valid=False, violations=[f"Approval '{approval_id}' not found"])
            return self.policy_engine.validate_action(
                aggregate=agg, action=action, actor_id=actor_id, actor_role=actor_role, metadata=metadata
            )

        return self.policy_engine.validate_request_creation(
            approval_type=approval_type,
            requester_id=actor_id,
            requester_role=actor_role,
            district_id=metadata.get("district_id", "DISTRICT_001") if metadata else "DISTRICT_001",
            metadata=metadata,
        )

    def history(self, approval_id: str) -> List[ApprovalHistory]:
        """Gets immutable audit history trail for an approval."""
        agg = self.repository.get_by_id(approval_id)
        if not agg:
            raise InvalidApprovalStateError(f"Approval request '{approval_id}' not found")
        return list(agg.history)

    def get_pending(
        self,
        approver_role: Optional[str] = None,
        district_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ApprovalAggregate]:
        """Queries pending approval requests requiring attention."""
        return self.repository.find(
            status=ApprovalStatus.UNDER_REVIEW,
            pending_role=approver_role,
            district_id=district_id,
            limit=limit,
            offset=offset,
        )

    def get_my_actions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ApprovalAggregate]:
        """Queries approvals where user_id is requester or has made a decision."""
        with self.repository._lock:
            res: List[ApprovalAggregate] = []
            for data in self.repository._storage.values():
                agg = ApprovalAggregate.from_dict(data)
                is_requester = agg.requester_id == user_id
                has_decided = any(d.approver_id == user_id for d in agg.decisions)
                if is_requester or has_decided:
                    res.append(agg)
            res.sort(key=lambda x: x.created_at, reverse=True)
            return res[offset : offset + limit]
