"""Escalation Policy Engine (Phase 8.4 Milestone 2 Deliverable 3).

Evaluates when escalation occurs, targets authority tiers, handles emergency bypasses,
and resolves acting supervisor and delegation fallback paths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.approval.contracts import ApprovalAggregate, ApprovalType
from backend.approval.escalation import (
    AuthorityTier,
    EscalationAggregate,
    EscalationReason,
)


@dataclass(frozen=True)
class EscalationPolicyResult:
    should_escalate: bool
    target_tier: AuthorityTier
    target_role: str
    bypass_intermediate: bool
    reason: str
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "should_escalate": self.should_escalate,
            "target_tier": self.target_tier.value,
            "target_role": self.target_role,
            "bypass_intermediate": self.bypass_intermediate,
            "reason": self.reason,
            "warnings": list(self.warnings),
        }


class EscalationPolicyEngine:
    """Evaluates rules for escalation routing, authority tier transitions, and emergency overrides."""

    TIER_ROLE_MAP: Dict[AuthorityTier, str] = {
        AuthorityTier.SUPERVISOR: "supervisor",
        AuthorityTier.ACP: "acp",
        AuthorityTier.DCP: "dcp",
        AuthorityTier.COMMISSIONER: "commissioner",
    }

    ROLE_TIER_MAP: Dict[str, AuthorityTier] = {
        "supervisor": AuthorityTier.SUPERVISOR,
        "acp": AuthorityTier.ACP,
        "dcp": AuthorityTier.DCP,
        "commissioner": AuthorityTier.COMMISSIONER,
        "admin": AuthorityTier.COMMISSIONER,
    }

    def determine_escalation_target(
        self,
        approval: ApprovalAggregate,
        reason: EscalationReason | str,
        current_role: str = "supervisor",
        custom_target_role: Optional[str] = None,
    ) -> EscalationPolicyResult:
        """Determines the appropriate next authority tier and role for an escalation."""
        esc_reason = (
            EscalationReason(reason) if isinstance(reason, str) else reason
        )
        warnings: List[str] = []

        # 1. Custom target role requested manually
        if custom_target_role:
            role_clean = str(custom_target_role).lower().replace("role.", "")
            tier = self.ROLE_TIER_MAP.get(role_clean, AuthorityTier.ACP)
            return EscalationPolicyResult(
                should_escalate=True,
                target_tier=tier,
                target_role=role_clean,
                bypass_intermediate=True,
                reason=f"Manual escalation explicitly requested role '{role_clean}'",
            )

        # 2. Emergency Operational Approval Bypass
        if approval.approval_type == ApprovalType.EMERGENCY_OPERATIONAL_APPROVAL or esc_reason == EscalationReason.EMERGENCY:
            warnings.append("Emergency operational bypass triggered: elevating directly to ACP/DCP")
            return EscalationPolicyResult(
                should_escalate=True,
                target_tier=AuthorityTier.ACP,
                target_role="acp",
                bypass_intermediate=True,
                reason="Emergency escalation bypassed intermediate supervisor stage",
                warnings=warnings,
            )

        # 3. Standard Escalation Chain Progression
        cur_role_clean = str(current_role).lower().replace("role.", "")
        cur_tier = self.ROLE_TIER_MAP.get(cur_role_clean, AuthorityTier.SUPERVISOR)

        next_tier_map = {
            AuthorityTier.SUPERVISOR: (AuthorityTier.ACP, "acp"),
            AuthorityTier.ACP: (AuthorityTier.DCP, "dcp"),
            AuthorityTier.DCP: (AuthorityTier.COMMISSIONER, "commissioner"),
            AuthorityTier.COMMISSIONER: (AuthorityTier.COMMISSIONER, "commissioner"),
        }

        next_tier, next_role = next_tier_map.get(cur_tier, (AuthorityTier.ACP, "acp"))
        if cur_tier == AuthorityTier.COMMISSIONER:
            warnings.append("Approval is already at highest authority tier (Commissioner)")

        return EscalationPolicyResult(
            should_escalate=True,
            target_tier=next_tier,
            target_role=next_role,
            bypass_intermediate=False,
            reason=f"Escalating from {cur_tier.value} to {next_tier.value} due to {esc_reason.value}",
            warnings=warnings,
        )

    def is_escalation_allowed(
        self,
        escalation: EscalationAggregate,
        actor_id: str,
        actor_role: str,
    ) -> Tuple[bool, str]:
        """Validates if actor is permitted to acknowledge or resolve an escalation."""
        actor_role_clean = str(actor_role).lower().replace("role.", "")

        # Administrator can handle any escalation
        if actor_role_clean in ("admin", "dcp", "commissioner"):
            return True, ""

        # Check assigned user match
        if escalation.assigned_to_user and escalation.assigned_to_user == actor_id:
            return True, ""

        # Check assigned role match
        assigned_role_clean = str(escalation.assigned_to_role).lower().replace("role.", "")
        if actor_role_clean == assigned_role_clean:
            return True, ""

        return False, f"Role '{actor_role}' does not match assigned escalation role '{escalation.assigned_to_role}'"
