"""Versioned workload policy configuration (Phase 8.2, Milestone 3).

WorkloadPolicy is the single, frozen source of truth for every weight and
threshold used by the WorkloadEngine. Two design goals:

  1. Determinism: a WorkloadPolicy is immutable once created. The same policy
     applied to the same data always yields the same result.
  2. Auditability: every OfficerWorkload / BurnoutAssessment / TeamMetrics /
     RebalanceRecommendation carries the policy's version string, so a
     supervisor can always ask "which policy produced this?"

Changing operational policy (e.g., recalibrating burnout weights for the next
fiscal year) means constructing a new WorkloadPolicy with an incremented version
— not editing business logic. The old policy can be preserved for historical
comparisons.

Usage::

    from backend.assignment.workload_policy import DEFAULT_POLICY, WorkloadPolicy

    # Use the platform default.
    engine = WorkloadEngine(policy=DEFAULT_POLICY)

    # Override for a specific unit (e.g., task-heavy counter-terrorism team).
    ct_policy = WorkloadPolicy(
        version="1.1.0-ct",
        task_weights={**DEFAULT_POLICY.task_weights, "ACTIVE": 2.0},
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet


# ── Investigation statuses that contribute ZERO weight ───────────────────────
# Investigations in these states are finished and must not burden any officer.
# Any status not in this list and not in the weight map gets the LOW weight
# as a conservative default (we would rather over-count than silently ignore
# an active case).
_DEFAULT_INACTIVE_STATUSES: FrozenSet[str] = frozenset({
    "COMPLETED",
    "CANCELLED",
    "ARCHIVED",
    "CLOSED",
    # Alternate casing variants from the dataset (defensive):
    "Completed",
    "Cancelled",
    "Archived",
    "Closed",
})

# ── Default investigation priority weights ────────────────────────────────────
_DEFAULT_INVESTIGATION_WEIGHTS: Dict[str, float] = {
    "CRITICAL": 5.0,
    "HIGH":     3.0,
    "MEDIUM":   2.0,
    "LOW":      1.0,
}

# ── Default task status weights ───────────────────────────────────────────────
# CREATED / ASSIGNED map to the spec's "OPEN" (1.0).
# ACTIVE tasks demand more attention (1.5).
# BLOCKED tasks still require monitoring but less effort (0.5).
# Terminal statuses (COMPLETED, SKIPPED, CANCELLED) contribute nothing.
_DEFAULT_TASK_WEIGHTS: Dict[str, float] = {
    "CREATED":   1.0,
    "ASSIGNED":  1.0,
    "OPEN":      1.0,   # synonym guard — should not appear but handled
    "ACTIVE":    1.5,
    "BLOCKED":   0.5,
    "COMPLETED": 0.0,
    "SKIPPED":   0.0,
    "CANCELLED": 0.0,
}


@dataclass(frozen=True)
class WorkloadPolicy:
    """Immutable operational policy for the WorkloadEngine.

    All engine callers receive this object and stamp its version into their
    output DTOs. Constructing a custom policy (e.g., for a pilot unit) does
    not require any code changes — only a new instance with an incremented
    version string.

    Attributes:
        version: Semantic version string. Increment on any weight/threshold
            change so downstream consumers can detect policy drift.
        investigation_weights: Priority label → workload contribution.
            A missing key falls back to the LOW weight (1.0) as a safe default.
        task_weights: TaskStatus label → workload contribution.
            A missing key defaults to 0.0 (unrecognized statuses ignored).
        inactive_investigation_statuses: Statuses that contribute 0 workload
            regardless of priority weight.
        rebalance_destination_capacity_max: Hard ceiling on capacity_used for
            any officer receiving a rebalancing recommendation. Must be in (0, 1].
        burnout_workload_weight: Points contributed at 100% capacity usage.
        burnout_overdue_task_weight: Max points from overdue tasks.
        burnout_overdue_inv_weight: Max points from overdue investigations.
        burnout_consecutive_days_weight: Max points from consecutive active days.
        burnout_after_hours_weight: Max points from after-hours activity ratio.
        burnout_critical_ratio_weight: Max points from fraction of critical cases.
        burnout_overdue_task_denominator: Task count that saturates the overdue factor.
        burnout_overdue_inv_denominator: Investigation count that saturates the factor.
        burnout_consecutive_days_denominator: Days that saturate the consecutive factor.
        burnout_moderate_threshold: Score at/above which risk = MODERATE.
        burnout_high_threshold: Score at/above which risk = HIGH.
        burnout_critical_threshold: Score at/above which risk = CRITICAL.
    """

    version: str = "1.0.0"

    # Investigation priority → workload weight
    investigation_weights: Dict[str, float] = field(
        default_factory=lambda: dict(_DEFAULT_INVESTIGATION_WEIGHTS)
    )

    # TaskStatus label → workload weight
    task_weights: Dict[str, float] = field(
        default_factory=lambda: dict(_DEFAULT_TASK_WEIGHTS)
    )

    # Statuses that unconditionally contribute 0 investigation weight
    inactive_investigation_statuses: FrozenSet[str] = field(
        default_factory=lambda: frozenset(_DEFAULT_INACTIVE_STATUSES)
    )

    # Rebalancing: never recommend a move to an officer at/above this utilization
    rebalance_destination_capacity_max: float = 0.85

    # ── Burnout scoring coefficients ─────────────────────────────────────────
    # Each coefficient is the maximum points that factor can contribute.
    # Points = coefficient × min(ratio, 1.0), where ratio = metric / denominator.
    # Total is clamped to 100.
    burnout_workload_weight:         float = 40.0
    burnout_overdue_task_weight:     float = 15.0
    burnout_overdue_inv_weight:      float = 15.0
    burnout_consecutive_days_weight: float = 10.0
    burnout_after_hours_weight:      float = 10.0
    burnout_critical_ratio_weight:   float = 10.0

    # Denominators for saturation (ratio = metric / denominator, capped at 1.0)
    burnout_overdue_task_denominator:     float = 5.0   # 5 overdue tasks → factor maxes out
    burnout_overdue_inv_denominator:      float = 3.0   # 3 overdue investigations → factor maxes
    burnout_consecutive_days_denominator: float = 14.0  # 2 weeks straight → factor maxes

    # ── Burnout risk band thresholds ─────────────────────────────────────────
    # score < moderate_threshold       → HEALTHY
    # moderate_threshold <= score < high_threshold → MODERATE
    # high_threshold <= score < critical_threshold → HIGH
    # score >= critical_threshold      → CRITICAL
    burnout_moderate_threshold: float = 30.0
    burnout_high_threshold:     float = 60.0
    burnout_critical_threshold: float = 80.0

    # ── Workload penalty (feeds WorkloadBreakdown) ────────────────────────────
    # Each overdue task adds this weight to the officer's final_score (above
    # raw_workload). This is separate from burnout — it's a direct workload
    # signal visible on the supervisor dashboard without a full burnout calc.
    overdue_task_penalty_per_task: float = 0.7

    def __post_init__(self) -> None:
        """Validate invariants on construction."""
        if not (0.0 < self.rebalance_destination_capacity_max <= 1.0):
            raise ValueError(
                f"rebalance_destination_capacity_max must be in (0, 1], "
                f"got {self.rebalance_destination_capacity_max}"
            )
        total_burnout_weight = (
            self.burnout_workload_weight
            + self.burnout_overdue_task_weight
            + self.burnout_overdue_inv_weight
            + self.burnout_consecutive_days_weight
            + self.burnout_after_hours_weight
            + self.burnout_critical_ratio_weight
        )
        # Weights should sum to 100 (each is "max points out of 100").
        if abs(total_burnout_weight - 100.0) > 1e-6:
            raise ValueError(
                f"Burnout weights must sum to 100.0; got {total_burnout_weight:.4f}"
            )
        if not (0 <= self.burnout_moderate_threshold
                <= self.burnout_high_threshold
                <= self.burnout_critical_threshold <= 100):
            raise ValueError("Burnout thresholds must satisfy 0 ≤ moderate ≤ high ≤ critical ≤ 100")

    def investigation_weight_for(self, priority: str) -> float:
        """Return the workload weight for an investigation priority.

        Falls back to the LOW weight (1.0) for unrecognized priorities so
        that new priority labels added in future migrations don't silently
        zero out workload.
        """
        return self.investigation_weights.get(
            priority.upper() if priority else "",
            self.investigation_weights.get("LOW", 1.0),
        )

    def task_weight_for(self, status: str) -> float:
        """Return the workload weight for a task status.

        Defaults to 0.0 for unrecognized statuses (unknown = assume done).
        """
        return self.task_weights.get(status.upper() if status else "", 0.0)

    def is_inactive_investigation(self, status: str) -> bool:
        """True if the investigation status contributes zero workload."""
        return status in self.inactive_investigation_statuses

    def burnout_risk_band(self, score: float) -> str:
        """Map a 0–100 burnout score to a named risk band."""
        if score >= self.burnout_critical_threshold:
            return "CRITICAL"
        if score >= self.burnout_high_threshold:
            return "HIGH"
        if score >= self.burnout_moderate_threshold:
            return "MODERATE"
        return "HEALTHY"


# ── Singleton default ─────────────────────────────────────────────────────────
# Import and use this unless a specific deployment requires a custom policy.
DEFAULT_POLICY: WorkloadPolicy = WorkloadPolicy()
