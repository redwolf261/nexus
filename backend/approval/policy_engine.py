"""Approval Policy Engine (Phase 8.4 Deliverable 3).

Evaluates deterministic governance policies, segregation of duties, role requirements,
and emergency operational constraints for approval requests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from backend.approval.contracts import (
    ApprovalAggregate,
    ApprovalType,
)


@dataclass(frozen=True)
class PolicyValidationResult:
    valid: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "violations": list(self.violations),
            "warnings": list(self.warnings),
        }


class ApprovalPolicyEngine:
    """Evaluates business rules, role requirements, and policy constraints for approval requests."""

    ROLES_RANK = {
        "read_only": 0,
        "analyst": 1,
        "supervisor": 2,
        "acp": 3,
        "dcp": 4,
        "admin": 5,
    }

    def _normalize_role(self, role: str) -> str:
        r = str(role).lower().replace("role.", "")
        return r

    def validate_request_creation(
        self,
        approval_type: ApprovalType | str,
        requester_id: str,
        requester_role: str,
        district_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PolicyValidationResult:
        """Validates policy constraints prior to request creation."""
        violations: List[str] = []
        warnings: List[str] = []
        app_type = ApprovalType(approval_type) if isinstance(approval_type, str) else approval_type
        role_norm = self._normalize_role(requester_role)
        meta = metadata or {}

        # Requester role minimum check
        if role_norm not in self.ROLES_RANK:
            violations.append(f"Invalid requester role '{requester_role}'")

        if app_type == ApprovalType.ARREST_WARRANT:
            if self.ROLES_RANK.get(role_norm, 0) < self.ROLES_RANK["analyst"]:
                violations.append("Arrest warrant requests require Analyst role or higher")

        elif app_type == ApprovalType.CROSS_DISTRICT_INVESTIGATION:
            if not meta.get("target_district_id"):
                violations.append("Cross-district investigation requires 'target_district_id' in metadata")

        elif app_type == ApprovalType.BUDGET_RESOURCE_REQUEST:
            amount = meta.get("amount", 0)
            if amount <= 0:
                violations.append("Budget request requires positive 'amount' in metadata")
            elif amount > 500000:
                warnings.append("High budget request (> 500,000 INR) will require DCP authorization")

        elif app_type == ApprovalType.EMERGENCY_OPERATIONAL_APPROVAL:
            if not meta.get("emergency_reason"):
                violations.append("Emergency operational approval requires 'emergency_reason' in metadata")

        return PolicyValidationResult(
            valid=len(violations) == 0,
            violations=violations,
            warnings=warnings,
        )

    def validate_action(
        self,
        aggregate: ApprovalAggregate,
        action: str,
        actor_id: str,
        actor_role: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PolicyValidationResult:
        """Validates policy rules when an actor attempts an action (approve, reject, etc.)."""
        violations: List[str] = []
        warnings: List[str] = []
        actor_role_norm = self._normalize_role(actor_role)
        actor_rank = self.ROLES_RANK.get(actor_role_norm, 0)

        # 1. Segregation of duties: requester cannot approve or reject their own request
        if action in ("APPROVE", "REJECT", "RETURN_FOR_REVISION"):
            if actor_id == aggregate.requester_id and aggregate.approval_type != ApprovalType.EMERGENCY_OPERATIONAL_APPROVAL:
                violations.append(
                    f"Actor '{actor_id}' is the requester and cannot perform '{action}' due to segregation of duties policy"
                )

        # 2. Specific approval type policy constraints
        app_type = aggregate.approval_type

        if app_type == ApprovalType.SEARCH_WARRANT:
            if actor_rank < self.ROLES_RANK["supervisor"]:
                violations.append("Search Warrant approval requires Supervisor role or higher")

        elif app_type == ApprovalType.ARREST_WARRANT:
            # Stage 0 requires Supervisor, Stage 1 requires ACP
            current_stage = aggregate.current_stage()
            if current_stage:
                req_role = self._normalize_role(current_stage.required_role)
                if actor_rank < self.ROLES_RANK.get(req_role, self.ROLES_RANK["supervisor"]):
                    violations.append(
                        f"Arrest Warrant stage '{current_stage.stage_name}' requires role '{current_stage.required_role}' or higher"
                    )

        elif app_type == ApprovalType.CROSS_DISTRICT_INVESTIGATION:
            if actor_rank < self.ROLES_RANK["acp"]:
                violations.append("Cross-District Investigation approval requires ACP role or higher")

        elif app_type == ApprovalType.EMERGENCY_OPERATIONAL_APPROVAL:
            warnings.append("Emergency Operational Approval grants temporary authorization subject to 24h auto-expiry")

        return PolicyValidationResult(
            valid=len(violations) == 0,
            violations=violations,
            warnings=warnings,
        )

    def calculate_default_expiration(
        self, approval_type: ApprovalType | str, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Calculates default expiration ISO timestamp based on approval type."""
        app_type = ApprovalType(approval_type) if isinstance(approval_type, str) else approval_type
        now = datetime.now(timezone.utc)

        if app_type == ApprovalType.EMERGENCY_OPERATIONAL_APPROVAL:
            # Emergency approval defaults to 24 hours
            exp = now + timedelta(hours=24)
            return exp.isoformat()
        elif app_type in (ApprovalType.SEARCH_WARRANT, ApprovalType.ARREST_WARRANT):
            # Warrants expire in 7 days by default
            exp = now + timedelta(days=7)
            return exp.isoformat()
        elif app_type == ApprovalType.SURVEILLANCE_REQUEST:
            # Surveillance requests expire in 14 days by default
            exp = now + timedelta(days=14)
            return exp.isoformat()

        # Other types default to 30 days
        exp = now + timedelta(days=30)
        return exp.isoformat()
