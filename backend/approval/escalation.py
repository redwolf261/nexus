"""Escalation Domain Models and Aggregate Root (Phase 8.4 Milestone 2).

Defines escalation reasons, authority tiers, escalation levels, escalation chains,
escalation events, and the EscalationAggregate domain model.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EscalationReason(str, Enum):
    SLA_TIMEOUT = "SLA_TIMEOUT"
    OFFICER_UNAVAILABLE = "OFFICER_UNAVAILABLE"
    SUPERVISOR_UNAVAILABLE = "SUPERVISOR_UNAVAILABLE"
    MANUAL_ESCALATION = "MANUAL_ESCALATION"
    EMERGENCY = "EMERGENCY"
    JURISDICTION_CONFLICT = "JURISDICTION_CONFLICT"
    POLICY_VIOLATION = "POLICY_VIOLATION"


class EscalationStatus(str, Enum):
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class AuthorityTier(str, Enum):
    SUPERVISOR = "SUPERVISOR"
    ACP = "ACP"
    DCP = "DCP"
    COMMISSIONER = "COMMISSIONER"


class InvalidEscalationStateError(Exception):
    """Raised when an illegal escalation state transition is attempted."""
    pass


@dataclass
class EscalationLevel:
    level_order: int
    authority_tier: AuthorityTier
    role_name: str
    timeout_hours: float = 24.0
    auto_escalate: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level_order": self.level_order,
            "authority_tier": self.authority_tier.value if isinstance(self.authority_tier, Enum) else str(self.authority_tier),
            "role_name": self.role_name,
            "timeout_hours": self.timeout_hours,
            "auto_escalate": self.auto_escalate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EscalationLevel:
        return cls(
            level_order=data["level_order"],
            authority_tier=AuthorityTier(data["authority_tier"]),
            role_name=data["role_name"],
            timeout_hours=data.get("timeout_hours", 24.0),
            auto_escalate=data.get("auto_escalate", True),
        )


@dataclass
class EscalationChain:
    chain_id: str
    approval_type: str
    levels: List[EscalationLevel] = field(default_factory=list)
    default_reason: str = "SLA timeout escalation chain"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "approval_type": self.approval_type,
            "levels": [lvl.to_dict() for lvl in self.levels],
            "default_reason": self.default_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EscalationChain:
        return cls(
            chain_id=data["chain_id"],
            approval_type=data["approval_type"],
            levels=[EscalationLevel.from_dict(lvl) for lvl in data.get("levels", [])],
            default_reason=data.get("default_reason", "SLA timeout escalation chain"),
        )


@dataclass
class EscalationRule:
    rule_id: str
    rule_name: str
    trigger_reason: EscalationReason
    target_tier: AuthorityTier
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "trigger_reason": self.trigger_reason.value if isinstance(self.trigger_reason, Enum) else str(self.trigger_reason),
            "target_tier": self.target_tier.value if isinstance(self.target_tier, Enum) else str(self.target_tier),
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EscalationRule:
        return cls(
            rule_id=data["rule_id"],
            rule_name=data["rule_name"],
            trigger_reason=EscalationReason(data["trigger_reason"]),
            target_tier=AuthorityTier(data["target_tier"]),
            is_active=data.get("is_active", True),
        )


@dataclass(frozen=True)
class EscalationEvent:
    event_id: str
    escalation_id: str
    approval_id: str
    reason: str
    from_role: str
    to_role: str
    from_user: Optional[str] = None
    to_user: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "escalation_id": self.escalation_id,
            "approval_id": self.approval_id,
            "reason": self.reason,
            "from_role": self.from_role,
            "to_role": self.to_role,
            "from_user": self.from_user,
            "to_user": self.to_user,
            "details": dict(self.details),
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EscalationEvent:
        return cls(
            event_id=data["event_id"],
            escalation_id=data["escalation_id"],
            approval_id=data["approval_id"],
            reason=data["reason"],
            from_role=data["from_role"],
            to_role=data["to_role"],
            from_user=data.get("from_user"),
            to_user=data.get("to_user"),
            details=data.get("details", {}),
            timestamp=data.get("timestamp", _utc_now_iso()),
        )


class EscalationAggregate:
    """Domain aggregate root for managing an escalation process lifecycle."""

    def __init__(
        self,
        escalation_id: str,
        approval_id: str,
        reason: EscalationReason | str,
        status: EscalationStatus | str = EscalationStatus.PENDING,
        current_level_index: int = 0,
        chain: Optional[EscalationChain] = None,
        assigned_to_user: Optional[str] = None,
        assigned_to_role: str = "supervisor",
        acknowledged_by: Optional[str] = None,
        acknowledged_at: Optional[str] = None,
        resolved_by: Optional[str] = None,
        resolved_at: Optional[str] = None,
        events: Optional[List[EscalationEvent]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        version: int = 1,
    ) -> None:
        self.escalation_id = escalation_id
        self.approval_id = approval_id
        self.reason = (
            EscalationReason(reason) if isinstance(reason, str) else reason
        )
        self.status = (
            EscalationStatus(status) if isinstance(status, str) else status
        )
        self.current_level_index = current_level_index
        self.chain = chain or EscalationChain(
            chain_id="default_chain",
            approval_type="GENERAL",
            levels=[
                EscalationLevel(1, AuthorityTier.SUPERVISOR, "supervisor", 24.0),
                EscalationLevel(2, AuthorityTier.ACP, "acp", 12.0),
                EscalationLevel(3, AuthorityTier.DCP, "dcp", 6.0),
                EscalationLevel(4, AuthorityTier.COMMISSIONER, "commissioner", 2.0),
            ],
        )
        self.assigned_to_user = assigned_to_user
        self.assigned_to_role = assigned_to_role
        self.acknowledged_by = acknowledged_by
        self.acknowledged_at = acknowledged_at
        self.resolved_by = resolved_by
        self.resolved_at = resolved_at
        self.events = events or []
        self.metadata = metadata or {}
        self.created_at = created_at or _utc_now_iso()
        self.updated_at = updated_at or _utc_now_iso()
        self.version = version

    def record_event(
        self,
        reason: str,
        from_role: str,
        to_role: str,
        from_user: Optional[str] = None,
        to_user: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> EscalationEvent:
        event = EscalationEvent(
            event_id=f"esc_evt_{uuid.uuid4().hex[:12]}",
            escalation_id=self.escalation_id,
            approval_id=self.approval_id,
            reason=reason,
            from_role=from_role,
            to_role=to_role,
            from_user=from_user,
            to_user=to_user,
            details=details or {},
            timestamp=_utc_now_iso(),
        )
        self.events.append(event)
        self.updated_at = event.timestamp
        self.version += 1
        return event

    def acknowledge(self, actor_id: str, actor_role: str) -> None:
        if self.status not in (EscalationStatus.PENDING, EscalationStatus.ACKNOWLEDGED):
            raise InvalidEscalationStateError(
                f"Cannot acknowledge escalation in status '{self.status.value}'"
            )

        prev_status = self.status.value
        self.status = EscalationStatus.ACKNOWLEDGED
        self.acknowledged_by = actor_id
        self.acknowledged_at = _utc_now_iso()

        self.record_event(
            reason="ACKNOWLEDGE",
            from_role=self.assigned_to_role,
            to_role=actor_role,
            from_user=self.assigned_to_user,
            to_user=actor_id,
            details={"previous_status": prev_status},
        )

    def resolve(self, actor_id: str, actor_role: str, notes: str = "") -> None:
        if self.status in (EscalationStatus.RESOLVED, EscalationStatus.EXPIRED, EscalationStatus.CANCELLED):
            raise InvalidEscalationStateError(
                f"Cannot resolve escalation in terminal status '{self.status.value}'"
            )

        prev_status = self.status.value
        self.status = EscalationStatus.RESOLVED
        self.resolved_by = actor_id
        self.resolved_at = _utc_now_iso()

        self.record_event(
            reason="RESOLVE",
            from_role=self.assigned_to_role,
            to_role=actor_role,
            from_user=self.assigned_to_user,
            to_user=actor_id,
            details={"previous_status": prev_status, "notes": notes},
        )

    def escalate_next_level(self, reason: str, actor_id: str, actor_role: str) -> bool:
        """Escalates to the next level in the escalation chain. Returns True if next level exists."""
        if self.current_level_index + 1 >= len(self.chain.levels):
            # Already at highest level (e.g., Commissioner)
            self.record_event(
                reason=f"MAX_ESCALATION_REACHED: {reason}",
                from_role=self.assigned_to_role,
                to_role=self.assigned_to_role,
                from_user=self.assigned_to_user,
                to_user=actor_id,
                details={"max_level_reached": True},
            )
            return False

        old_level = self.chain.levels[self.current_level_index]
        self.current_level_index += 1
        new_level = self.chain.levels[self.current_level_index]

        from_role = self.assigned_to_role
        self.assigned_to_role = new_level.role_name
        self.assigned_to_user = None

        self.record_event(
            reason=reason,
            from_role=from_role,
            to_role=new_level.role_name,
            from_user=actor_id,
            to_user=None,
            details={
                "from_tier": old_level.authority_tier.value,
                "to_tier": new_level.authority_tier.value,
            },
        )
        return True

    def reassign(self, target_user_id: str, actor_id: str, actor_role: str, reason: str = "") -> None:
        prev_user = self.assigned_to_user
        self.assigned_to_user = target_user_id

        self.record_event(
            reason=f"REASSIGN: {reason}",
            from_role=self.assigned_to_role,
            to_role=self.assigned_to_role,
            from_user=prev_user,
            to_user=target_user_id,
            details={"reassigned_by": actor_id, "reassigned_role": actor_role},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "escalation_id": self.escalation_id,
            "approval_id": self.approval_id,
            "reason": self.reason.value,
            "status": self.status.value,
            "current_level_index": self.current_level_index,
            "chain": self.chain.to_dict(),
            "assigned_to_user": self.assigned_to_user,
            "assigned_to_role": self.assigned_to_role,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at,
            "events": [evt.to_dict() for evt in self.events],
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EscalationAggregate:
        return cls(
            escalation_id=data["escalation_id"],
            approval_id=data["approval_id"],
            reason=data["reason"],
            status=data.get("status", EscalationStatus.PENDING.value),
            current_level_index=data.get("current_level_index", 0),
            chain=EscalationChain.from_dict(data["chain"]) if "chain" in data else None,
            assigned_to_user=data.get("assigned_to_user"),
            assigned_to_role=data.get("assigned_to_role", "supervisor"),
            acknowledged_by=data.get("acknowledged_by"),
            acknowledged_at=data.get("acknowledged_at"),
            resolved_by=data.get("resolved_by"),
            resolved_at=data.get("resolved_at"),
            events=[EscalationEvent.from_dict(evt) for evt in data.get("events", [])],
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            version=data.get("version", 1),
        )
