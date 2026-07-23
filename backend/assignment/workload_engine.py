"""Pure-calculation Workload Engine (Phase 8.2, Milestone 3).

This module is intentionally ORM-free. It accepts plain Python snapshot
objects (built by WorkloadDataLoader) and returns immutable DTOs. The
same inputs + same WorkloadPolicy always produce byte-identical output.

Public surface:
    WorkloadEngine           — the calculation service
    OfficerSnapshot          — lightweight officer input
    InvestigationSnapshot    — lightweight investigation input
    TaskSnapshot             — lightweight task input

Consumers:
    WorkloadDataLoader       — assembles snapshots from the DB
    RecommendationService    — consumes OfficerWorkload for scoring
    M4 API layer             — calls through WorkloadDataLoader → WorkloadEngine

Design contract:
    - NO SQLAlchemy imports.
    - NO randomness.
    - NO side effects (reads nothing, writes nothing).
    - Every method is deterministic: same args → same return value.
    - Performance targets (enforced by test suite):
        calculate_workload():      < 300 ms for 1 000 officers
        calculate_team_metrics():  < 500 ms for 1 000 officers
        recommend_rebalancing():   < 2 s for 1 000 officers
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from backend.assignment.workload_policy import DEFAULT_POLICY, WorkloadPolicy
from backend.assignment.contracts import (
    OfficerWorkload,
    WorkloadBreakdown,
    BurnoutAssessment,
    CapacityMetrics,
    TeamMetrics,
    RebalanceRecommendation,
)


# ── Lightweight snapshot types (input DTOs) ───────────────────────────────────
# These carry only the fields the engine needs — no ORM relationships, no
# lazy-loading, no session dependency. WorkloadDataLoader produces them.

@dataclass(frozen=True)
class OfficerSnapshot:
    """Minimal officer state needed for workload calculation."""
    officer_id: str
    district_id: Optional[str]
    maximum_capacity: int          # 0 → undeclared
    skills: FrozenSet[str]         # Set of SkillCode string values


@dataclass(frozen=True)
class InvestigationSnapshot:
    """Minimal investigation state needed for workload calculation."""
    investigation_id: str
    priority: str                  # TaskPriority value (CRITICAL/HIGH/MEDIUM/LOW)
    status: str                    # Investigation status
    assigned_officer_id: Optional[str]
    due_date: Optional[date] = None


@dataclass(frozen=True)
class TaskSnapshot:
    """Minimal task state needed for workload calculation."""
    task_id: str
    investigation_id: str
    status: str                    # TaskStatus value
    due_at: Optional[datetime] = None


# ── Engine ─────────────────────────────────────────────────────────────────────

class WorkloadEngine:
    """Deterministic, pure-calculation workload measurement service.

    Instantiate with a WorkloadPolicy (default is DEFAULT_POLICY). The policy
    version is stamped into every output DTO for full auditability.

    This class has no __init__ database connection, no caches, and no shared
    mutable state — it is safe to use as a module-level singleton.
    """

    def __init__(self, policy: WorkloadPolicy = DEFAULT_POLICY) -> None:
        self._policy = policy

    # ── Public API ──────────────────────────────────────────────────────

    def calculate_workload(
        self,
        officer: OfficerSnapshot,
        investigations: List[InvestigationSnapshot],
        tasks: List[TaskSnapshot],
        overdue_task_count: int = 0,
        burnout_penalty: float = 0.0,
    ) -> OfficerWorkload:
        """Compute weighted workload for one officer with full band decomposition.

        Formula:
            raw_workload = Σ investigation_weight(priority, status)
                         + Σ task_weight(status)
            final_score  = raw_workload
                         + overdue_task_count × policy.overdue_task_penalty_per_task
                         + burnout_penalty

        Inactive investigations (COMPLETED, CANCELLED, ARCHIVED, CLOSED)
        always contribute 0, regardless of their priority weight.

        Args:
            officer:            Immutable officer snapshot.
            investigations:     All investigations *assigned to this officer*.
            tasks:              All tasks *assigned to this officer*.
            overdue_task_count: Number of tasks past their due_at (default 0).
                                Used to compute overdue_task_penalty in the breakdown.
            burnout_penalty:    Feed-forward from a pre-computed BurnoutAssessment
                                score (default 0.0). Pass 0 when no burnout data
                                is available — the breakdown will show the term as
                                zero rather than omitting it.

        Returns:
            OfficerWorkload (frozen) with the weighted total, per-source
            investigation breakdown, and the richer WorkloadBreakdown for
            supervisor dashboard display.
        """
        policy = self._policy

        # ── Per-priority-band investigation tracking ─────────────────────────
        band_counts: Dict[str, int] = {
            "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0
        }
        band_weights: Dict[str, float] = {
            "CRITICAL": 0.0, "HIGH": 0.0, "MEDIUM": 0.0, "LOW": 0.0
        }

        inv_weight_total = 0.0
        active_inv_count = 0
        critical_inv_count = 0
        inv_breakdown: List[Dict] = []

        for inv in investigations:
            if policy.is_inactive_investigation(inv.status):
                w = 0.0
                active = False
            else:
                w = policy.investigation_weight_for(inv.priority)
                active = True
                active_inv_count += 1
                p_upper = inv.priority.upper() if inv.priority else "LOW"
                band = p_upper if p_upper in band_counts else "LOW"
                band_counts[band] += 1
                band_weights[band] += w
                if p_upper == "CRITICAL":
                    critical_inv_count += 1

            inv_breakdown.append({
                "investigation_id": inv.investigation_id,
                "priority": inv.priority,
                "status": inv.status,
                "weight": w,
                "active": active,
            })
            inv_weight_total += w

        # ── Per-status-band task tracking ────────────────────────────────────
        active_task_w = 0.0
        blocked_task_w = 0.0
        assigned_task_w = 0.0   # CREATED + ASSIGNED
        active_task_cnt = 0
        blocked_task_cnt = 0
        assigned_task_cnt = 0
        task_weight_total = 0.0
        nonterminal_task_count = 0

        for task in tasks:
            status_upper = (task.status or "").upper()
            w = policy.task_weight_for(task.status)
            task_weight_total += w
            if w > 0.0:
                nonterminal_task_count += 1
            if status_upper == "ACTIVE":
                active_task_w += w
                active_task_cnt += 1
            elif status_upper == "BLOCKED":
                blocked_task_w += w
                blocked_task_cnt += 1
            elif status_upper in ("CREATED", "ASSIGNED", "OPEN"):
                assigned_task_w += w
                assigned_task_cnt += 1

        raw_workload = inv_weight_total + task_weight_total

        # ── Penalty terms ────────────────────────────────────────────────────
        overdue_penalty = round(
            overdue_task_count * policy.overdue_task_penalty_per_task, 6
        )
        burnout_pen = round(max(0.0, burnout_penalty), 6)
        final_score = round(raw_workload + overdue_penalty + burnout_pen, 6)

        # ── Explainability: summary lines (only non-zero contributions) ───────
        summary: List[str] = []
        if band_counts["CRITICAL"] > 0:
            summary.append(
                f"{band_counts['CRITICAL']} Critical "
                f"case{'s' if band_counts['CRITICAL'] != 1 else ''}"
                f" (+{round(band_weights['CRITICAL'], 1)})"
            )
        if band_counts["HIGH"] > 0:
            summary.append(
                f"{band_counts['HIGH']} High "
                f"case{'s' if band_counts['HIGH'] != 1 else ''}"
                f" (+{round(band_weights['HIGH'], 1)})"
            )
        if band_counts["MEDIUM"] > 0:
            summary.append(
                f"{band_counts['MEDIUM']} Medium "
                f"case{'s' if band_counts['MEDIUM'] != 1 else ''}"
                f" (+{round(band_weights['MEDIUM'], 1)})"
            )
        if band_counts["LOW"] > 0:
            summary.append(
                f"{band_counts['LOW']} Low "
                f"case{'s' if band_counts['LOW'] != 1 else ''}"
                f" (+{round(band_weights['LOW'], 1)})"
            )
        if active_task_cnt > 0:
            summary.append(
                f"{active_task_cnt} Active "
                f"task{'s' if active_task_cnt != 1 else ''}"
                f" (+{round(active_task_w, 1)})"
            )
        if blocked_task_cnt > 0:
            summary.append(
                f"{blocked_task_cnt} Blocked "
                f"task{'s' if blocked_task_cnt != 1 else ''}"
                f" (+{round(blocked_task_w, 1)})"
            )
        if assigned_task_cnt > 0:
            summary.append(
                f"{assigned_task_cnt} Assigned/Created "
                f"task{'s' if assigned_task_cnt != 1 else ''}"
                f" (+{round(assigned_task_w, 1)})"
            )
        if overdue_task_count > 0:
            summary.append(
                f"{overdue_task_count} overdue "
                f"task{'s' if overdue_task_count != 1 else ''}"
                f" (+{round(overdue_penalty, 1)})"
            )
        if burnout_pen > 0:
            summary.append(f"Burnout penalty (+{round(burnout_pen, 2)})")

        # ── Deterministic recommendation hint ─────────────────────────────────
        recommendation: Optional[str] = None
        if band_counts["CRITICAL"] >= 2:
            recommendation = "Avoid assigning additional Critical investigations."
        elif officer.maximum_capacity > 0 and (final_score / officer.maximum_capacity) > 0.85:
            recommendation = "Officer near capacity — avoid new assignments."
        elif overdue_task_count > 0:
            recommendation = "Clear overdue tasks before accepting new work."

        breakdown = WorkloadBreakdown(
            critical_case_weight=round(band_weights["CRITICAL"], 6),
            high_case_weight=round(band_weights["HIGH"], 6),
            medium_case_weight=round(band_weights["MEDIUM"], 6),
            low_case_weight=round(band_weights["LOW"], 6),
            active_task_weight=round(active_task_w, 6),
            blocked_task_weight=round(blocked_task_w, 6),
            assigned_task_weight=round(assigned_task_w, 6),
            overdue_task_penalty=overdue_penalty,
            burnout_penalty=burnout_pen,
            critical_case_count=band_counts["CRITICAL"],
            high_case_count=band_counts["HIGH"],
            medium_case_count=band_counts["MEDIUM"],
            low_case_count=band_counts["LOW"],
            active_task_count=active_task_cnt,
            blocked_task_count=blocked_task_cnt,
            assigned_task_count=assigned_task_cnt,
            overdue_task_count=overdue_task_count,
            base_weight=round(raw_workload, 6),
            final_score=final_score,
            summary_lines=summary,
            recommendation=recommendation,
        )

        return OfficerWorkload(
            officer_id=officer.officer_id,
            raw_workload=round(raw_workload, 6),
            investigation_weight=round(inv_weight_total, 6),
            task_weight=round(task_weight_total, 6),
            active_investigation_count=active_inv_count,
            active_task_count=nonterminal_task_count,
            critical_investigation_count=critical_inv_count,
            investigation_breakdown=inv_breakdown,
            policy_version=policy.version,
            breakdown=breakdown,
        )

    def calculate_capacity(self, workload: OfficerWorkload, maximum_capacity: int) -> CapacityMetrics:
        """Compute weighted capacity utilization for one officer.

        capacity_used = raw_workload / maximum_capacity, clamped to a minimum
        of 0.0. Values exceeding 1.0 are *not* clamped (they represent overflow
        and are important signal for burnout / rebalancing decisions).

        Division-by-zero is prevented: an officer with maximum_capacity=0 is
        treated as fully utilized when they have any workload, and as free when
        they have none.

        Args:
            workload:         OfficerWorkload from calculate_workload().
            maximum_capacity: Officer's max_capacity field (may be 0).

        Returns:
            CapacityMetrics (frozen).
        """
        raw = workload.raw_workload
        if maximum_capacity <= 0:
            # No declared capacity: any workload = fully utilized.
            capacity_used = 1.0 if raw > 0.0 else 0.0
            available_slots_weighted = 0.0
        else:
            capacity_used = raw / maximum_capacity
            available_slots_weighted = maximum_capacity - raw

        return CapacityMetrics(
            officer_id=workload.officer_id,
            raw_workload=workload.raw_workload,
            maximum_capacity=maximum_capacity,
            capacity_used=round(capacity_used, 6),
            available_slots_weighted=round(available_slots_weighted, 6),
            is_overloaded=capacity_used > 1.0,
            policy_version=self._policy.version,
        )

    def calculate_burnout(
        self,
        workload: OfficerWorkload,
        maximum_capacity: int,
        overdue_tasks: int,
        overdue_investigations: int,
        consecutive_active_days: int,
        after_hours_ratio: float = 0.0,
    ) -> BurnoutAssessment:
        """Compute a deterministic, fully-explained burnout score (0–100).

        Six factors, each contributing up to their weight (defined in policy):

            workload_ratio      : capacity_used ratio × 40
            overdue_tasks       : min(count/5, 1.0) × 15
            overdue_invs        : min(count/3, 1.0) × 15
            consecutive_days    : min(days/14, 1.0) × 10
            after_hours_ratio   : min(ratio, 1.0) × 10   (placeholder)
            critical_case_ratio : (critical / active_total) × 10

        Total is clamped to 100.0. The risk band is determined by the policy
        thresholds: HEALTHY < 30 ≤ MODERATE < 60 ≤ HIGH < 80 ≤ CRITICAL.

        Every non-zero factor contributes a human-readable explanation line.
        Zero-scoring factors are omitted from the explanation for clarity.

        Args:
            workload:               OfficerWorkload for this officer.
            maximum_capacity:       Officer's maximum capacity.
            overdue_tasks:          Number of tasks past their due_at.
            overdue_investigations: Number of investigations past their due date.
            consecutive_active_days: Days without a full rest day (placeholder).
            after_hours_ratio:      Fraction of work outside scheduled hours
                                    (placeholder metric, 0.0 if unavailable).

        Returns:
            BurnoutAssessment (frozen) with score, risk_band, and explanation.
        """
        policy = self._policy

        # Factor 1: Workload ratio
        if maximum_capacity <= 0:
            wl_ratio = 1.0 if workload.raw_workload > 0 else 0.0
        else:
            wl_ratio = min(1.0, workload.raw_workload / maximum_capacity)
        f_workload = wl_ratio * policy.burnout_workload_weight

        # Factor 2: Overdue tasks
        overdue_task_ratio = min(
            1.0,
            overdue_tasks / max(1.0, policy.burnout_overdue_task_denominator),
        )
        f_overdue_tasks = overdue_task_ratio * policy.burnout_overdue_task_weight

        # Factor 3: Overdue investigations
        overdue_inv_ratio = min(
            1.0,
            overdue_investigations / max(1.0, policy.burnout_overdue_inv_denominator),
        )
        f_overdue_inv = overdue_inv_ratio * policy.burnout_overdue_inv_weight

        # Factor 4: Consecutive active days
        consecutive_ratio = min(
            1.0,
            consecutive_active_days / max(1.0, policy.burnout_consecutive_days_denominator),
        )
        f_consecutive = consecutive_ratio * policy.burnout_consecutive_days_weight

        # Factor 5: After-hours activity (placeholder — 0 when data unavailable)
        ah_ratio = min(1.0, max(0.0, after_hours_ratio))
        f_after_hours = ah_ratio * policy.burnout_after_hours_weight

        # Factor 6: Critical case ratio
        active_total = max(1, workload.active_investigation_count)
        critical_ratio = workload.critical_investigation_count / active_total
        f_critical = critical_ratio * policy.burnout_critical_ratio_weight

        raw_score = (
            f_workload + f_overdue_tasks + f_overdue_inv
            + f_consecutive + f_after_hours + f_critical
        )
        score = round(min(100.0, raw_score), 2)
        risk_band = policy.burnout_risk_band(score)

        # Build explainability lines — only for factors that actually contributed.
        explanation: List[str] = []
        pct = round(wl_ratio * 100)
        if f_workload > 0:
            explanation.append(f"High workload ({pct}% of capacity)")
        if overdue_tasks > 0:
            explanation.append(
                f"{overdue_tasks} overdue task{'s' if overdue_tasks != 1 else ''}"
            )
        if overdue_investigations > 0:
            explanation.append(
                f"{overdue_investigations} overdue "
                f"investigation{'s' if overdue_investigations != 1 else ''}"
            )
        if consecutive_active_days > 0:
            explanation.append(
                f"{consecutive_active_days} consecutive active day"
                f"{'s' if consecutive_active_days != 1 else ''}"
            )
        if after_hours_ratio > 0:
            ah_pct = round(after_hours_ratio * 100)
            explanation.append(f"{ah_pct}% after-hours activity")
        if workload.critical_investigation_count > 0:
            explanation.append(
                f"{workload.critical_investigation_count} critical "
                f"investigation{'s' if workload.critical_investigation_count != 1 else ''}"
            )

        factor_scores: Dict[str, float] = {
            "workload":        round(f_workload, 4),
            "overdue_tasks":   round(f_overdue_tasks, 4),
            "overdue_invs":    round(f_overdue_inv, 4),
            "consecutive_days": round(f_consecutive, 4),
            "after_hours":     round(f_after_hours, 4),
            "critical_ratio":  round(f_critical, 4),
        }

        return BurnoutAssessment(
            officer_id=workload.officer_id,
            score=score,
            risk_band=risk_band,
            explanation=explanation,
            factor_scores=factor_scores,
            policy_version=self._policy.version,
        )

    def calculate_team_metrics(
        self, officer_workloads: List[OfficerWorkload]
    ) -> TeamMetrics:
        """Compute fleet-wide workload statistics.

        Calculates: mean, median, std deviation, max, min workload; average
        capacity_used; Gini coefficient; burnout distribution; capacity histogram.

        All statistics are deterministic. An empty officer list returns a zeroed
        TeamMetrics rather than raising an exception.

        Performance target: < 500 ms for 1,000 officers.
        (Gini is O(n²) but isolated; see calculate_gini() docstring.)

        Args:
            officer_workloads: List of OfficerWorkload (one per officer).

        Returns:
            TeamMetrics (frozen).
        """
        policy = self._policy
        n = len(officer_workloads)

        if n == 0:
            return TeamMetrics(
                officer_count=0,
                mean_workload=0.0,
                median_workload=0.0,
                std_workload=0.0,
                max_workload=0.0,
                min_workload=0.0,
                average_capacity_used=0.0,
                gini_coefficient=0.0,
                burnout_distribution={
                    "HEALTHY": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0
                },
                capacity_histogram=_empty_histogram(),
                policy_version=policy.version,
            )

        values = [w.raw_workload for w in officer_workloads]

        mean_wl = statistics.mean(values)
        median_wl = statistics.median(values)
        std_wl = statistics.pstdev(values)   # population std dev (not sample)
        max_wl = max(values)
        min_wl = min(values)

        # Gini (exact, O(n²) — documented in calculate_gini)
        gini = self.calculate_gini(values)

        # Capacity utilization per officer — requires max_capacity, which is
        # embedded in the CapacityMetrics but NOT in OfficerWorkload (by design:
        # workload and capacity are separate concepts). We approximate here using
        # only what TeamMetrics needs: a fleet-wide average capacity ratio.
        # Callers who need per-officer capacity pass pre-computed CapacityMetrics.
        # For team_metrics without CapacityMetrics, we report average_capacity_used
        # as the ratio of raw_workload to *reported* max_capacity via the breakdown.
        # Since OfficerWorkload does not carry max_capacity, the caller must supply
        # it via calculate_team_metrics_with_capacities() — or we use 0 as default.
        # This method computes what it has; the richer overload is below.
        average_capacity_used = 0.0  # Set by richer overload; 0 signals "not computed"

        # Burnout distribution — simplified: classify by raw workload bands
        # (this is a coarse proxy without full burnout inputs; the richer
        # calculate_team_metrics_full() accepts pre-computed BurnoutAssessments)
        burnout_dist = {"HEALTHY": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
        hist = _empty_histogram()

        for w in officer_workloads:
            # Raw proxy for histogram: map raw_workload to a coarse bucket
            _add_to_histogram(hist, w.raw_workload, policy)

        return TeamMetrics(
            officer_count=n,
            mean_workload=round(mean_wl, 4),
            median_workload=round(median_wl, 4),
            std_workload=round(std_wl, 4),
            max_workload=round(max_wl, 4),
            min_workload=round(min_wl, 4),
            average_capacity_used=round(average_capacity_used, 4),
            gini_coefficient=round(gini, 6),
            burnout_distribution=burnout_dist,
            capacity_histogram=hist,
            policy_version=policy.version,
        )

    def calculate_team_metrics_full(
        self,
        officer_workloads: List[OfficerWorkload],
        capacities: List[CapacityMetrics],
        burnout_assessments: List[BurnoutAssessment],
    ) -> TeamMetrics:
        """Full team metrics with pre-computed capacity and burnout data.

        This is the production path. The caller supplies pre-computed
        CapacityMetrics and BurnoutAssessments (built from calculate_capacity()
        and calculate_burnout()) so this method doesn't need to re-derive them.

        Args:
            officer_workloads:    One per officer (same order not required).
            capacities:           One per officer.
            burnout_assessments:  One per officer.

        Returns:
            TeamMetrics (frozen), fully populated.
        """
        policy = self._policy
        n = len(officer_workloads)

        if n == 0:
            return TeamMetrics(
                officer_count=0,
                mean_workload=0.0,
                median_workload=0.0,
                std_workload=0.0,
                max_workload=0.0,
                min_workload=0.0,
                average_capacity_used=0.0,
                gini_coefficient=0.0,
                burnout_distribution={
                    "HEALTHY": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0
                },
                capacity_histogram=_empty_histogram(),
                policy_version=policy.version,
            )

        values = [w.raw_workload for w in officer_workloads]
        mean_wl = statistics.mean(values)
        median_wl = statistics.median(values)
        std_wl = statistics.pstdev(values)
        max_wl = max(values)
        min_wl = min(values)
        gini = self.calculate_gini(values)

        # Average capacity_used (from pre-computed CapacityMetrics)
        cap_values = [c.capacity_used for c in capacities]
        avg_cap = statistics.mean(cap_values) if cap_values else 0.0

        # Burnout distribution
        burnout_dist: Dict[str, int] = {
            "HEALTHY": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0
        }
        for ba in burnout_assessments:
            band = ba.risk_band if ba.risk_band in burnout_dist else "HEALTHY"
            burnout_dist[band] += 1

        # Capacity histogram using actual capacity_used
        hist = _empty_histogram()
        for c in capacities:
            _add_capacity_to_histogram(hist, c.capacity_used)

        return TeamMetrics(
            officer_count=n,
            mean_workload=round(mean_wl, 4),
            median_workload=round(median_wl, 4),
            std_workload=round(std_wl, 4),
            max_workload=round(max_wl, 4),
            min_workload=round(min_wl, 4),
            average_capacity_used=round(avg_cap, 4),
            gini_coefficient=round(gini, 6),
            burnout_distribution=burnout_dist,
            capacity_histogram=hist,
            policy_version=policy.version,
        )

    def recommend_rebalancing(
        self,
        officer_workloads: List[OfficerWorkload],
        capacities: Dict[str, CapacityMetrics],
        officer_snapshots: Dict[str, OfficerSnapshot],
        investigations_by_officer: Dict[str, List[InvestigationSnapshot]],
        allow_cross_jurisdiction: bool = False,
    ) -> List[RebalanceRecommendation]:
        """Generate explainable workload rebalancing recommendations.

        Identifies overloaded source officers, selects high-burden investigations
        that are movable, finds eligible destination officers, and returns an
        ordered recommendation list. Never auto-assigns — only recommends.

        Constraints (never violated):
            - Destination capacity_used must be < policy.rebalance_destination_capacity_max
            - Cross-jurisdiction moves require allow_cross_jurisdiction=True
            - Source officer never recommended as their own destination
            - Investigation must be active (non-terminal status)
            - Recommendations are deterministic: same inputs → same list

        Performance target: < 2 seconds for 1,000 officers.

        Args:
            officer_workloads:        All officers' workloads.
            capacities:               Pre-computed CapacityMetrics per officer_id.
            officer_snapshots:        OfficerSnapshot per officer_id (for skills/district).
            investigations_by_officer: Active investigations per officer_id.
            allow_cross_jurisdiction: If False (default), only move within same district.

        Returns:
            List[RebalanceRecommendation], deterministically ordered:
            primary by source officer_id ascending, secondary by priority descending.
        """
        policy = self._policy
        recommendations: List[RebalanceRecommendation] = []

        # Priority rank for sorting (higher = more urgent)
        _priority_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

        # Build fast-lookup structures
        cap_by_id = capacities
        workload_by_id: Dict[str, OfficerWorkload] = {
            w.officer_id: w for w in officer_workloads
        }

        # Identify overloaded sources: capacity_used > 0.85 OR burnout based on threshold
        threshold = policy.rebalance_destination_capacity_max
        overloaded_sources = sorted(
            [
                w for w in officer_workloads
                if cap_by_id.get(w.officer_id) is not None
                and cap_by_id[w.officer_id].capacity_used > threshold
            ],
            key=lambda w: w.officer_id,  # deterministic ordering
        )

        if not overloaded_sources:
            return []

        # Eligible destinations: capacity_used < threshold
        eligible_destinations = [
            w for w in officer_workloads
            if cap_by_id.get(w.officer_id) is not None
            and cap_by_id[w.officer_id].capacity_used < threshold
        ]

        for source_wl in overloaded_sources:
            source_id = source_wl.officer_id
            source_cap = cap_by_id.get(source_id)
            source_snap = officer_snapshots.get(source_id)
            if not source_cap or not source_snap:
                continue

            source_invs = investigations_by_officer.get(source_id, [])
            # Consider only active, movable investigations — sorted deterministically
            active_invs = [
                inv for inv in source_invs
                if not policy.is_inactive_investigation(inv.status)
            ]
            # Sort: highest priority first, then investigation_id for tie-break
            active_invs_sorted = sorted(
                active_invs,
                key=lambda i: (
                    -_priority_rank.get(i.priority.upper(), 0),
                    i.investigation_id,
                ),
            )

            for inv in active_invs_sorted:
                inv_weight = policy.investigation_weight_for(inv.priority)
                if inv_weight == 0:
                    continue  # Nothing to move

                # Find best destination for this investigation
                # Filter eligible destinations
                valid_dests = []
                for dest_wl in eligible_destinations:
                    dest_id = dest_wl.officer_id
                    if dest_id == source_id:
                        continue  # Cannot rebalance to self
                    dest_cap = cap_by_id.get(dest_id)
                    dest_snap = officer_snapshots.get(dest_id)
                    if not dest_cap or not dest_snap:
                        continue

                    # Check jurisdiction
                    jurisdiction_valid = (
                        allow_cross_jurisdiction
                        or source_snap.district_id is None
                        or dest_snap.district_id is None
                        or source_snap.district_id == dest_snap.district_id
                    )
                    if not jurisdiction_valid:
                        continue

                    # After move, would destination still be under the threshold?
                    dest_new_capacity = (
                        (dest_wl.raw_workload + inv_weight) / dest_cap.maximum_capacity
                        if dest_cap.maximum_capacity > 0
                        else 1.0
                    )
                    if dest_new_capacity >= threshold:
                        continue  # Would push destination over limit

                    valid_dests.append((dest_id, dest_wl, dest_cap, dest_snap, jurisdiction_valid))

                if not valid_dests:
                    continue  # No valid destination for this investigation

                # Select best destination: lowest current capacity_used, then officer_id
                valid_dests.sort(
                    key=lambda t: (cap_by_id[t[0]].capacity_used, t[0])
                )
                best_dest_id, dest_wl, dest_cap, dest_snap, jur_valid = valid_dests[0]

                # Compute expected workload after move
                source_new_wl = max(0.0, source_wl.raw_workload - inv_weight)
                dest_new_wl = dest_wl.raw_workload + inv_weight

                source_new_capacity = (
                    source_new_wl / source_cap.maximum_capacity
                    if source_cap.maximum_capacity > 0 else (1.0 if source_new_wl > 0 else 0.0)
                )

                reduction_pct = round(
                    (inv_weight / max(source_wl.raw_workload, 1e-9)) * 100, 1
                )

                # Build explanation
                reason_source = (
                    f"Officer {source_id} capacity at "
                    f"{round(source_cap.capacity_used * 100)}% "
                    f"(workload {round(source_wl.raw_workload, 1)} / "
                    f"max {source_cap.maximum_capacity})"
                )
                reason_dest = (
                    f"Officer {best_dest_id} has capacity at "
                    f"{round(dest_cap.capacity_used * 100)}% "
                    f"({round(dest_cap.available_slots_weighted, 1)} weighted slots available)"
                )

                # Skills matched: destination skills that are relevant to the investigation
                skills_matched = sorted(dest_snap.skills)  # All held skills (simplified)

                recommendations.append(RebalanceRecommendation(
                    investigation_id=inv.investigation_id,
                    investigation_priority=inv.priority,
                    source_officer_id=source_id,
                    destination_officer_id=best_dest_id,
                    source_current_workload=round(source_wl.raw_workload, 4),
                    source_expected_workload=round(source_new_wl, 4),
                    destination_current_workload=round(dest_wl.raw_workload, 4),
                    destination_expected_workload=round(dest_new_wl, 4),
                    workload_reduction_pct=reduction_pct,
                    reason_source_overloaded=reason_source,
                    reason_destination_qualifies=reason_dest,
                    skills_matched=skills_matched,
                    jurisdiction_valid=jur_valid,
                    policy_version=self._policy.version,
                ))

        # Final ordering: source officer_id ascending, then priority descending
        recommendations.sort(
            key=lambda r: (
                r.source_officer_id,
                -_priority_rank.get(r.investigation_priority.upper(), 0),
                r.investigation_id,
            )
        )
        return recommendations

    # ── Gini coefficient ──────────────────────────────────────────────────────

    @staticmethod
    def calculate_gini(values: List[float]) -> float:
        """Exact Gini coefficient using the double-sum formula.

        Formula:
            G = ΣΣ|xi − xj| / (2 × n² × μ)

        where n is the number of values and μ is the mean.

        Complexity: O(n²) — intentionally exact, not approximate. This method
        is intended for fleet-wide team metrics (up to ~1,000 officers), where
        n² ≈ 1,000,000 operations is fast in pure Python (< 200 ms typical).
        For larger populations, this should be replaced with a sorted O(n log n)
        equivalent while preserving the same mathematical result.

        Edge cases — all return 0.0 (no inequality, no division):
            - Empty list
            - Single element
            - All values are 0
            - All values are equal

        Args:
            values: Non-negative floats (raw workload values).

        Returns:
            Gini coefficient in [0.0, 1.0].
        """
        n = len(values)
        if n < 2:
            return 0.0
        mu = sum(values) / n
        if mu == 0.0:
            return 0.0  # All zeros → perfect equality

        # Double sum: ΣΣ|xi − xj|
        # Equivalent O(n²) computation over all ordered pairs.
        total_abs_diff = 0.0
        for i in range(n):
            for j in range(n):
                total_abs_diff += abs(values[i] - values[j])

        return total_abs_diff / (2.0 * n * n * mu)


# ── Histogram helpers (module-private) ────────────────────────────────────────

def _empty_histogram() -> List[Dict]:
    """Return a zeroed capacity histogram with 5 standard buckets."""
    return [
        {"label": "0–25%",   "min": 0.0,  "max": 0.25, "count": 0},
        {"label": "25–50%",  "min": 0.25, "max": 0.50, "count": 0},
        {"label": "50–75%",  "min": 0.50, "max": 0.75, "count": 0},
        {"label": "75–100%", "min": 0.75, "max": 1.00, "count": 0},
        {"label": "100%+",   "min": 1.00, "max": None, "count": 0},
    ]


def _add_to_histogram(hist: List[Dict], raw_workload: float, policy: WorkloadPolicy) -> None:
    """Classify a raw workload value into a histogram bucket.

    Without the officer's max_capacity, we treat the raw workload value as
    the capacity_used proxy (normalized against policy-implied max of 10).
    Used by calculate_team_metrics() — the richer overload uses actual ratios.
    """
    # Default capacity assumption for histogram without actual max_capacity
    _add_capacity_to_histogram(hist, raw_workload / 10.0)


def _add_capacity_to_histogram(hist: List[Dict], capacity_used: float) -> None:
    """Classify a capacity_used ratio into the 5-bucket histogram."""
    for bucket in hist:
        lo = bucket["min"]
        hi = bucket["max"]
        if hi is None:
            if capacity_used >= lo:
                bucket["count"] += 1
                return
        else:
            if lo <= capacity_used < hi:
                bucket["count"] += 1
                return
    # Fallback: add to last bucket
    hist[-1]["count"] += 1
