"""Assignment Decision Aggregate (Phase 8.2 Milestone 5).

DDD Aggregate representing a supervisor decision (ACCEPT, OVERRIDE, REJECT, DEFER).
Encapsulates decision metadata, policy snapshot, approval chain, and status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from backend.assignment.override_policy import DecisionEnum, OverrideReasonEnum, PolicyResult


@dataclass
class AssignmentDecision:
    """DDD Aggregate for Supervisor Assignment Decision."""

    decision_id: str
    investigation_id: str
    recommendation_id: Optional[str]
    supervisor_id: str
    decision: DecisionEnum
    chosen_officer_id: Optional[str]
    justification: Optional[str]
    override_reason: Optional[OverrideReasonEnum]
    policy_result: PolicyResult
    approval_chain: List[Dict[str, Any]]
    status: str  # COMPLETED / PENDING_ACP / PENDING_DCP / REJECTED
    policy_version: str
    timestamp: datetime
    version: int

    @property
    def is_override(self) -> bool:
        return self.decision == DecisionEnum.OVERRIDE

    @property
    def is_escalated(self) -> bool:
        return self.status in ("PENDING_ACP", "PENDING_DCP")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "investigation_id": self.investigation_id,
            "recommendation_id": self.recommendation_id,
            "supervisor_id": self.supervisor_id,
            "decision": self.decision.value if isinstance(self.decision, DecisionEnum) else str(self.decision),
            "chosen_officer_id": self.chosen_officer_id,
            "justification": self.justification,
            "override_reason": self.override_reason.value if isinstance(self.override_reason, OverrideReasonEnum) else str(self.override_reason) if self.override_reason else None,
            "policy_result": self.policy_result.to_dict(),
            "approval_chain": list(self.approval_chain),
            "status": self.status,
            "policy_version": self.policy_version,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "version": self.version,
            "is_override": self.is_override,
            "is_escalated": self.is_escalated,
        }
