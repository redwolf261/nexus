"""SLA Timer Engine (Phase 8.4 Milestone 2 Deliverable 2).

Evaluates approval deadlines, reminder thresholds, escalation deadlines, and expiration bounds
deterministically without background scheduler assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from backend.approval.contracts import ApprovalAggregate, ApprovalStatus, ApprovalType


@dataclass(frozen=True)
class SLATimerResult:
    is_warning: bool
    is_breached: bool
    is_escalation_due: bool
    is_expired: bool
    time_remaining_seconds: float
    elapsed_seconds: float
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_warning": self.is_warning,
            "is_breached": self.is_breached,
            "is_escalation_due": self.is_escalation_due,
            "is_expired": self.is_expired,
            "time_remaining_seconds": round(self.time_remaining_seconds, 2),
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "recommended_action": self.recommended_action,
        }


class SLAEngine:
    """Deterministic SLA evaluation engine for operational approval requests."""

    # Canonical SLA configurations per ApprovalType (Total hours allowed for completion)
    SLA_CONFIGS: Dict[ApprovalType, float] = {
        ApprovalType.EMERGENCY_OPERATIONAL_APPROVAL: 24.0,
        ApprovalType.SEARCH_WARRANT: 72.0,
        ApprovalType.ARREST_WARRANT: 72.0,
        ApprovalType.SURVEILLANCE_REQUEST: 168.0,       # 7 Days
        ApprovalType.CROSS_DISTRICT_INVESTIGATION: 168.0, # 7 Days
        ApprovalType.BUDGET_RESOURCE_REQUEST: 168.0,     # 7 Days
        ApprovalType.EVIDENCE_COLLECTION: 360.0,         # 15 Days
        ApprovalType.INVESTIGATION_CLOSURE: 720.0,       # 30 Days
        ApprovalType.COLD_CASE_ARCHIVAL: 720.0,         # 30 Days
        ApprovalType.CASE_REOPENING: 360.0,              # 15 Days
    }

    def get_sla_hours(self, approval_type: ApprovalType | str) -> float:
        app_type = ApprovalType(approval_type) if isinstance(approval_type, str) else approval_type
        return self.SLA_CONFIGS.get(app_type, 72.0)

    def evaluate_sla(
        self,
        aggregate: ApprovalAggregate,
        now_dt: Optional[datetime] = None,
    ) -> SLATimerResult:
        """Evaluates SLA timer status for an approval aggregate.
        
        SLA Rules:
          - Warning Threshold: 70% of total SLA hours elapsed.
          - Escalation Threshold: 85% of total SLA hours elapsed.
          - Breach Threshold: 100% of total SLA hours elapsed.
          - Expiry Threshold: Past expires_at or 120% of SLA hours elapsed.
        """
        ref_now = now_dt or datetime.now(timezone.utc)
        if ref_now.tzinfo is None:
            ref_now = ref_now.replace(tzinfo=timezone.utc)

        # Parse created_at
        created_dt = datetime.fromisoformat(aggregate.created_at.replace("Z", "+00:00"))
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)

        elapsed_sec = max(0.0, (ref_now - created_dt).total_seconds())

        # Determine total SLA duration
        sla_hours = self.get_sla_hours(aggregate.approval_type)
        total_sla_sec = sla_hours * 3600.0

        # Override total SLA if aggregate has explicit expires_at
        if aggregate.expires_at:
            try:
                exp_dt = datetime.fromisoformat(aggregate.expires_at.replace("Z", "+00:00"))
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                custom_sla_sec = (exp_dt - created_dt).total_seconds()
                if custom_sla_sec > 0:
                    total_sla_sec = custom_sla_sec
            except Exception:
                pass

        time_remaining_sec = total_sla_sec - elapsed_sec

        # Terminal statuses don't trigger SLAs
        if aggregate.status in (
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.CANCELLED,
            ApprovalStatus.EXPIRED,
        ):
            return SLATimerResult(
                is_warning=False,
                is_breached=False,
                is_escalation_due=False,
                is_expired=aggregate.status == ApprovalStatus.EXPIRED,
                time_remaining_seconds=max(0.0, time_remaining_sec),
                elapsed_seconds=elapsed_sec,
                recommended_action=f"Workflow terminal state: {aggregate.status.value}",
            )

        ratio = elapsed_sec / total_sla_sec if total_sla_sec > 0 else 1.0

        is_expired = ratio >= 1.20 or aggregate.status == ApprovalStatus.EXPIRED
        is_breached = time_remaining_sec <= 0.0 or ratio >= 1.00
        is_escalation_due = ratio >= 0.85
        is_warning = ratio >= 0.70

        rec_action = "NO_ACTION"
        if is_expired:
            rec_action = "EXPIRE_REQUEST"
        elif is_breached:
            rec_action = "ESCALATE_IMMEDIATELY"
        elif is_escalation_due:
            rec_action = "TRIGGER_AUTOMATIC_ESCALATION"
        elif is_warning:
            rec_action = "SEND_SLA_REMINDER"

        return SLATimerResult(
            is_warning=is_warning,
            is_breached=is_breached,
            is_escalation_due=is_escalation_due,
            is_expired=is_expired,
            time_remaining_seconds=time_remaining_sec,
            elapsed_seconds=elapsed_sec,
            recommended_action=rec_action,
        )
