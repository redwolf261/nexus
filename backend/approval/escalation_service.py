"""Escalation Service (Phase 8.4 Milestone 2 Deliverable 5).

Orchestrates escalation lifecycles, SLA timer evaluations, authority delegations,
audit logging, optimistic concurrency, and WebSocket event dispatching.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.approval.approval_service import ApprovalService
from backend.approval.contracts import ApprovalAggregate, InvalidApprovalStateError, OptimisticLockError
from backend.approval.delegation_engine import DelegationEngine, DelegationRecord, DelegationType
from backend.approval.escalation import (
    AuthorityTier,
    EscalationAggregate,
    EscalationEvent,
    EscalationReason,
    EscalationStatus,
    InvalidEscalationStateError,
)
from backend.approval.escalation_policy import EscalationPolicyEngine
from backend.approval.escalation_repository import EscalationRepository
from backend.approval.sla_engine import SLAEngine, SLATimerResult
from backend.events.dispatcher import EventDispatcher
from backend.events.event_types import EventType

logger = logging.getLogger("nexus.escalation_service")


class EscalationService:
    """Core domain service for Escalation Management, SLA Governance, and Temporary Delegation."""

    def __init__(
        self,
        repository: Optional[EscalationRepository] = None,
        approval_service: Optional[ApprovalService] = None,
        sla_engine: Optional[SLAEngine] = None,
        policy_engine: Optional[EscalationPolicyEngine] = None,
        delegation_engine: Optional[DelegationEngine] = None,
        dispatcher: Optional[EventDispatcher] = None,
    ) -> None:
        self.repository = repository or EscalationRepository()
        self.approval_service = approval_service or ApprovalService()
        self.sla_engine = sla_engine or SLAEngine()
        self.policy_engine = policy_engine or EscalationPolicyEngine()
        self.delegation_engine = delegation_engine or DelegationEngine()
        self.dispatcher = dispatcher or EventDispatcher()

    def _publish_event(self, event_type: EventType, payload: Dict[str, Any], entity_id: str) -> None:
        try:
            if hasattr(self.dispatcher, "dispatch"):
                self.dispatcher.dispatch(event_type=event_type, payload=payload, entity_id=entity_id)
            elif hasattr(self.dispatcher, "publish_sync"):
                logger.info(f"Published event {event_type.value} for entity {entity_id}")
        except Exception as e:
            logger.warning(f"Failed to dispatch WebSocket event {event_type.value}: {e}")

    def evaluate(self, approval_id: str, now_dt: Optional[datetime] = None) -> Tuple[SLATimerResult, Optional[EscalationAggregate]]:
        """Evaluates SLA timer state and auto-escalation triggers for an approval request."""
        approval = self.approval_service.repository.get_by_id(approval_id)
        if not approval:
            raise InvalidApprovalStateError(f"Approval request '{approval_id}' not found")

        sla_res = self.sla_engine.evaluate_sla(approval, now_dt=now_dt)

        escalation = self.repository.get_by_approval_id(approval_id)

        # Dispatch SLA Warning / Breach events if triggered
        if sla_res.is_warning and not sla_res.is_breached:
            self._publish_event(
                EventType.SLA_WARNING,
                {"approval_id": approval_id, "time_remaining_seconds": sla_res.time_remaining_seconds},
                entity_id=approval_id,
            )
        elif sla_res.is_breached:
            self._publish_event(
                EventType.SLA_BREACHED,
                {"approval_id": approval_id, "elapsed_seconds": sla_res.elapsed_seconds},
                entity_id=approval_id,
            )

        # Auto-escalate if escalation is due and no active escalation exists
        if sla_res.is_escalation_due and not escalation:
            escalation = self.escalate(
                approval_id=approval_id,
                reason=EscalationReason.SLA_TIMEOUT,
                actor_id="SYSTEM_SLA",
                actor_role="SYSTEM",
            )

        return sla_res, escalation

    def escalate(
        self,
        approval_id: str,
        reason: EscalationReason | str = EscalationReason.MANUAL_ESCALATION,
        actor_id: str = "SYSTEM",
        actor_role: str = "supervisor",
        target_role: Optional[str] = None,
        expected_version: Optional[int] = None,
    ) -> EscalationAggregate:
        """Triggers or advances an escalation process for an approval request."""
        approval = self.approval_service.repository.get_by_id(approval_id)
        if not approval:
            raise InvalidApprovalStateError(f"Approval request '{approval_id}' not found")

        esc_reason = EscalationReason(reason) if isinstance(reason, str) else reason

        # Policy evaluation for target tier & role
        current_role = approval.current_stage().required_role if approval.current_stage() else "supervisor"
        policy_res = self.policy_engine.determine_escalation_target(
            approval=approval,
            reason=esc_reason,
            current_role=current_role,
            custom_target_role=target_role,
        )

        existing = self.repository.get_by_approval_id(approval_id)
        if existing:
            # Advance existing escalation to next level
            existing.escalate_next_level(
                reason=policy_res.reason,
                actor_id=actor_id,
                actor_role=actor_role,
            )
            saved = self.repository.save(existing, expected_version=expected_version)
            # Update approval aggregate status to ESCALATED
            self.approval_service.escalate(
                approval_id=approval_id,
                actor_id=actor_id,
                actor_role=actor_role,
                reason=policy_res.reason,
                target_role=policy_res.target_role,
            )
            self._publish_event(EventType.APPROVAL_ESCALATED, saved.to_dict(), entity_id=approval_id)
            return saved

        # Create new escalation aggregate
        esc_id = f"esc_{uuid.uuid4().hex[:12]}"
        aggregate = EscalationAggregate(
            escalation_id=esc_id,
            approval_id=approval_id,
            reason=esc_reason,
            status=EscalationStatus.PENDING,
            assigned_to_role=policy_res.target_role,
            version=1,
        )
        aggregate.record_event(
            reason=policy_res.reason,
            from_role=current_role,
            to_role=policy_res.target_role,
            from_user=actor_id,
            details={"policy_warnings": policy_res.warnings},
        )

        saved = self.repository.save(aggregate)
        # Update approval aggregate state to ESCALATED
        try:
            self.approval_service.escalate(
                approval_id=approval_id,
                actor_id=actor_id,
                actor_role=actor_role,
                reason=policy_res.reason,
                target_role=policy_res.target_role,
            )
        except Exception:
            pass

        self._publish_event(EventType.APPROVAL_ESCALATION_CREATED, saved.to_dict(), entity_id=esc_id)
        return saved

    def acknowledge(
        self,
        escalation_id: str,
        actor_id: str,
        actor_role: str,
        expected_version: Optional[int] = None,
    ) -> EscalationAggregate:
        """Acknowledges a pending escalation."""
        esc = self.repository.get_by_id(escalation_id)
        if not esc:
            raise InvalidEscalationStateError(f"Escalation '{escalation_id}' not found")

        allowed, reason = self.policy_engine.is_escalation_allowed(esc, actor_id, actor_role)
        if not allowed:
            raise InvalidEscalationStateError(f"Actor not authorized to acknowledge escalation: {reason}")

        esc.acknowledge(actor_id=actor_id, actor_role=actor_role)
        saved = self.repository.save(esc, expected_version=expected_version)
        self._publish_event(EventType.APPROVAL_ESCALATION_ACKNOWLEDGED, saved.to_dict(), entity_id=escalation_id)
        return saved

    def resolve(
        self,
        escalation_id: str,
        actor_id: str,
        actor_role: str,
        notes: str = "",
        expected_version: Optional[int] = None,
    ) -> EscalationAggregate:
        """Resolves an active escalation."""
        esc = self.repository.get_by_id(escalation_id)
        if not esc:
            raise InvalidEscalationStateError(f"Escalation '{escalation_id}' not found")

        allowed, reason = self.policy_engine.is_escalation_allowed(esc, actor_id, actor_role)
        if not allowed:
            raise InvalidEscalationStateError(f"Actor not authorized to resolve escalation: {reason}")

        esc.resolve(actor_id=actor_id, actor_role=actor_role, notes=notes)
        saved = self.repository.save(esc, expected_version=expected_version)
        self._publish_event(EventType.APPROVAL_ESCALATION_RESOLVED, saved.to_dict(), entity_id=escalation_id)
        return saved

    def delegate(
        self,
        delegator_id: str,
        delegatee_id: str,
        delegator_role: str,
        delegatee_role: str,
        delegation_type: DelegationType | str = DelegationType.TEMPORARY_ACTING,
        duration_hours: float = 24.0,
        reason: str = "",
    ) -> DelegationRecord:
        """Creates a temporary delegation assignment."""
        record = self.delegation_engine.create_delegation(
            delegator_id=delegator_id,
            delegatee_id=delegatee_id,
            delegator_role=delegator_role,
            delegatee_role=delegatee_role,
            delegation_type=delegation_type,
            duration_hours=duration_hours,
            reason=reason,
        )
        self._publish_event(EventType.APPROVAL_DELEGATED, record.to_dict(), entity_id=record.delegation_id)
        return record

    def reassign(
        self,
        escalation_id: str,
        target_user_id: str,
        actor_id: str,
        actor_role: str,
        reason: str = "",
        expected_version: Optional[int] = None,
    ) -> EscalationAggregate:
        """Reassigns an escalation to a specific user."""
        esc = self.repository.get_by_id(escalation_id)
        if not esc:
            raise InvalidEscalationStateError(f"Escalation '{escalation_id}' not found")

        esc.reassign(target_user_id=target_user_id, actor_id=actor_id, actor_role=actor_role, reason=reason)
        saved = self.repository.save(esc, expected_version=expected_version)
        self._publish_event(EventType.APPROVAL_REASSIGNED, saved.to_dict(), entity_id=escalation_id)
        return saved

    def pending(
        self,
        actor_role: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EscalationAggregate]:
        """Queries pending or acknowledged escalations."""
        return self.repository.find(
            status=EscalationStatus.PENDING,
            assigned_role=actor_role,
            limit=limit,
            offset=offset,
        )

    def history(self, escalation_id: str) -> List[EscalationEvent]:
        """Queries history events for an escalation aggregate."""
        esc = self.repository.get_by_id(escalation_id)
        if not esc:
            raise InvalidEscalationStateError(f"Escalation '{escalation_id}' not found")
        return list(esc.events)
