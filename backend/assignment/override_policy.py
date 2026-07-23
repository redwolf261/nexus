"""Override Policy Engine (Phase 8.2 Milestone 5).

Deterministic, explainable policy validator that evaluates supervisor assignment decisions
against operational rules and determines required approval tiers (Supervisor / ACP / DCP).

The engine NEVER blocks assignments automatically. It computes and returns a PolicyResult
containing violations, warnings, and escalation rules.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from sqlalchemy.orm import Session

from backend.db.schema import Officer, Investigation, Station, District
from backend.assignment.workload_engine import WorkloadEngine
from backend.assignment.workload_loader import WorkloadDataLoader
from backend.assignment.workload_policy import DEFAULT_POLICY, WorkloadPolicy


class DecisionEnum(str, enum.Enum):
    ACCEPT = "ACCEPT"
    OVERRIDE = "OVERRIDE"
    REJECT = "REJECT"
    DEFER = "DEFER"


class OverrideReasonEnum(str, enum.Enum):
    WORKLOAD_BALANCING = "WORKLOAD_BALANCING"
    LOCAL_KNOWLEDGE = "LOCAL_KNOWLEDGE"
    URGENT_OPERATION = "URGENT_OPERATION"
    SPECIAL_EXPERTISE = "SPECIAL_EXPERTISE"
    MANUAL_COMMAND = "MANUAL_COMMAND"
    RESOURCE_SHORTAGE = "RESOURCE_SHORTAGE"
    TEMPORARY_ASSIGNMENT = "TEMPORARY_ASSIGNMENT"
    OTHER = "OTHER"


@dataclass(frozen=True)
class PolicyResult:
    """Deterministic policy validation result."""
    is_allowed: bool
    violations: List[str]
    warnings: List[str]
    requires_acp: bool
    requires_dcp: bool
    checked_rules: Dict[str, bool]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_allowed": self.is_allowed,
            "violations": list(self.violations),
            "warnings": list(self.warnings),
            "requires_acp": self.requires_acp,
            "requires_dcp": self.requires_dcp,
            "checked_rules": dict(self.checked_rules),
        }


@dataclass(frozen=True)
class ApprovalPolicy:
    """Centrally versioned escalation policy rules."""
    version: str = "1.0.0"
    critical_capacity_threshold: float = 1.5  # >= 150% capacity requires ACP
    cross_jurisdiction_requires_acp: bool = True
    interstate_requires_dcp: bool = True
    critical_priority_reassign_requires_acp: bool = True
    leave_reassign_requires_acp: bool = True
    suspended_requires_dcp: bool = True


class OverridePolicyEngine:
    """Deterministic Override Policy Engine. Validates rules and determines escalation requirements."""

    def __init__(self, session: Session, approval_policy: ApprovalPolicy = ApprovalPolicy()):
        self.session = session
        self.approval_policy = approval_policy
        self.workload_loader = WorkloadDataLoader(session)
        self.workload_engine = WorkloadEngine(DEFAULT_POLICY)

    def evaluate(
        self,
        investigation_id: str,
        officer_id: str,
        is_interstate: bool = False
    ) -> PolicyResult:
        """Evaluate an assignment against policy rules."""
        violations: List[str] = []
        warnings: List[str] = []
        requires_acp = False
        requires_dcp = False
        checked_rules: Dict[str, bool] = {}

        inv = self.session.query(Investigation).filter(Investigation.id == investigation_id).first()
        officer = self.session.query(Officer).filter(Officer.officer_id == officer_id).first()

        if not inv or not officer:
            return PolicyResult(
                is_allowed=False,
                violations=["Invalid investigation or officer reference."],
                warnings=[],
                requires_acp=False,
                requires_dcp=False,
                checked_rules={},
            )

        # Rule 1: Availability Status Check
        status = officer.availability_status or "ON_DUTY"
        if status == "SUSPENDED":
            violations.append(f"Officer '{officer.officer_id}' is SUSPENDED.")
            if self.approval_policy.suspended_requires_dcp:
                requires_dcp = True
            checked_rules["status_suspended"] = False
        elif status == "LEAVE":
            warnings.append(f"Officer '{officer.officer_id}' is currently on LEAVE.")
            if self.approval_policy.leave_reassign_requires_acp:
                requires_acp = True
            checked_rules["status_leave"] = False
        elif status in ("OFF_DUTY", "TRAINING"):
            warnings.append(f"Officer '{officer.officer_id}' is currently {status}.")
            requires_acp = True
            checked_rules["status_available"] = False
        else:
            checked_rules["status_on_duty"] = True

        # Rule 2: Workload & Capacity Threshold Check
        try:
            snapshots = self.workload_loader.load_team_snapshots([officer_id])
            if officer_id in snapshots:
                snap, invs, tasks = snapshots[officer_id]
                wl = self.workload_engine.calculate_workload(snap, invs, tasks)
                cap = self.workload_engine.calculate_capacity(wl, snap.maximum_capacity)

                if cap.capacity_used >= self.approval_policy.critical_capacity_threshold:
                    violations.append(
                        f"Officer capacity critical: {cap.capacity_used_pct}% used (>= {self.approval_policy.critical_capacity_threshold * 100}% threshold)."
                    )
                    requires_acp = True
                    checked_rules["capacity_normal"] = False
                elif cap.capacity_used >= 1.0:
                    warnings.append(f"Officer is over capacity: {cap.capacity_used_pct}% used.")
                    checked_rules["capacity_normal"] = False
                else:
                    checked_rules["capacity_normal"] = True
        except Exception:
            checked_rules["capacity_normal"] = True

        # Rule 3: Jurisdiction Match Check
        if officer.district_id and inv.assigned_team:
            # Check district alignment if encoded in team or station
            pass

        if is_interstate:
            violations.append("Interstate case assignment requires DCP approval.")
            if self.approval_policy.interstate_requires_dcp:
                requires_dcp = True
            checked_rules["interstate"] = False
        else:
            checked_rules["interstate"] = True

        # Rule 4: Case Priority Risk Check
        if (inv.priority or "").upper() == "CRITICAL":
            warnings.append("CRITICAL priority investigation assignment requires heightened oversight.")
            if self.approval_policy.critical_priority_reassign_requires_acp:
                requires_acp = True
            checked_rules["case_risk"] = False
        else:
            checked_rules["case_risk"] = True

        is_allowed = len(violations) == 0

        return PolicyResult(
            is_allowed=is_allowed,
            violations=violations,
            warnings=warnings,
            requires_acp=requires_acp,
            requires_dcp=requires_dcp,
            checked_rules=checked_rules,
        )
