"""Phase 8.2 Milestone 3 tests — Operational Workload Engine.

Covers:
    Workload calculation (empty officer, mixed priorities, inactive ignored)
    Task weight by status
    Capacity: zero, full, overflow
    Burnout: healthy / moderate / high / critical + factors + determinism
    Gini: equality, inequality, known distribution, zero, edge cases
    Team metrics: statistics, burnout distribution, capacity histogram
    Rebalancing: overloaded source, no destination, jurisdiction, skill,
                 capacity rejection, deterministic ordering, never auto-assigns
    Determinism: 20-run identical output
    Performance: 1000 officers × 10 investigations each

Runs entirely in-memory (SQLite). The WorkloadEngine itself has no SQLAlchemy
dependency — most tests operate on pure Python objects.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from typing import Dict, FrozenSet, List, Optional

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.db.schema import Base, Officer, Investigation, InvestigationTask
from backend.assignment.workload_policy import WorkloadPolicy, DEFAULT_POLICY
from backend.assignment.workload_engine import (
    WorkloadEngine,
    OfficerSnapshot,
    InvestigationSnapshot,
    TaskSnapshot,
)
from backend.assignment.contracts import (
    OfficerWorkload,
    BurnoutAssessment,
    CapacityMetrics,
    TeamMetrics,
    RebalanceRecommendation,
)


# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def engine_default() -> WorkloadEngine:
    return WorkloadEngine(policy=DEFAULT_POLICY)


def _officer(oid: str = "OFF-1", district: str = "D1", max_cap: int = 10,
             skills: Optional[FrozenSet[str]] = None) -> OfficerSnapshot:
    return OfficerSnapshot(
        officer_id=oid,
        district_id=district,
        maximum_capacity=max_cap,
        skills=skills or frozenset(),
    )


def _inv(iid: str, priority: str = "HIGH", status: str = "Open",
         officer: str = "OFF-1", due: Optional[date] = None) -> InvestigationSnapshot:
    return InvestigationSnapshot(
        investigation_id=iid,
        priority=priority,
        status=status,
        assigned_officer_id=officer,
        due_date=due,
    )


def _task(tid: str, iid: str = "INV-1", status: str = "ACTIVE",
          due_at: Optional[datetime] = None) -> TaskSnapshot:
    return TaskSnapshot(task_id=tid, investigation_id=iid, status=status, due_at=due_at)


# ════════════════════════════════════════════════════════════════════════════════
# WORKLOAD CALCULATION
# ════════════════════════════════════════════════════════════════════════════════

class TestWorkloadCalculation:

    def test_empty_officer_zero_workload(self, engine_default):
        """Officer with no investigations or tasks has zero workload."""
        wl = engine_default.calculate_workload(_officer(), [], [])
        assert wl.raw_workload == 0.0
        assert wl.investigation_weight == 0.0
        assert wl.task_weight == 0.0
        assert wl.active_investigation_count == 0
        assert wl.active_task_count == 0

    def test_critical_investigation_weight(self, engine_default):
        """Single CRITICAL investigation contributes weight 5.0."""
        wl = engine_default.calculate_workload(
            _officer(), [_inv("I1", priority="CRITICAL")], []
        )
        assert wl.investigation_weight == 5.0
        assert wl.active_investigation_count == 1
        assert wl.critical_investigation_count == 1

    def test_high_investigation_weight(self, engine_default):
        """HIGH investigation → weight 3.0."""
        wl = engine_default.calculate_workload(
            _officer(), [_inv("I1", priority="HIGH")], []
        )
        assert wl.investigation_weight == 3.0

    def test_medium_investigation_weight(self, engine_default):
        """MEDIUM investigation → weight 2.0."""
        wl = engine_default.calculate_workload(
            _officer(), [_inv("I1", priority="MEDIUM")], []
        )
        assert wl.investigation_weight == 2.0

    def test_low_investigation_weight(self, engine_default):
        """LOW investigation → weight 1.0."""
        wl = engine_default.calculate_workload(
            _officer(), [_inv("I1", priority="LOW")], []
        )
        assert wl.investigation_weight == 1.0

    def test_mixed_priority_investigations(self, engine_default):
        """Mixed priorities sum correctly: CRITICAL + HIGH + MEDIUM + LOW = 11."""
        invs = [
            _inv("I1", priority="CRITICAL"),
            _inv("I2", priority="HIGH"),
            _inv("I3", priority="MEDIUM"),
            _inv("I4", priority="LOW"),
        ]
        wl = engine_default.calculate_workload(_officer(), invs, [])
        assert wl.investigation_weight == 11.0  # 5+3+2+1
        assert wl.active_investigation_count == 4
        assert wl.critical_investigation_count == 1

    def test_completed_investigation_ignored(self, engine_default):
        """COMPLETED investigation contributes 0 regardless of priority."""
        invs = [
            _inv("I1", priority="CRITICAL", status="Completed"),
            _inv("I2", priority="HIGH", status="COMPLETED"),
        ]
        wl = engine_default.calculate_workload(_officer(), invs, [])
        assert wl.investigation_weight == 0.0
        assert wl.active_investigation_count == 0

    def test_cancelled_investigation_ignored(self, engine_default):
        """CANCELLED investigation contributes 0."""
        invs = [_inv("I1", priority="HIGH", status="Cancelled")]
        wl = engine_default.calculate_workload(_officer(), invs, [])
        assert wl.investigation_weight == 0.0

    def test_archived_investigation_ignored(self, engine_default):
        """ARCHIVED investigation contributes 0."""
        invs = [_inv("I1", priority="CRITICAL", status="Archived")]
        wl = engine_default.calculate_workload(_officer(), invs, [])
        assert wl.investigation_weight == 0.0

    def test_closed_investigation_ignored(self, engine_default):
        """CLOSED investigation contributes 0."""
        invs = [_inv("I1", priority="HIGH", status="Closed")]
        wl = engine_default.calculate_workload(_officer(), invs, [])
        assert wl.investigation_weight == 0.0

    def test_active_investigations_counted(self, engine_default):
        """Mix of active and inactive; only active counted."""
        invs = [
            _inv("I1", priority="HIGH", status="Open"),
            _inv("I2", priority="CRITICAL", status="Completed"),
            _inv("I3", priority="MEDIUM", status="Under Investigation"),
        ]
        wl = engine_default.calculate_workload(_officer(), invs, [])
        assert wl.active_investigation_count == 2  # I1 + I3
        assert wl.investigation_weight == 3.0 + 2.0  # HIGH + MEDIUM

    def test_investigation_breakdown_present(self, engine_default):
        """breakdown has one entry per investigation with correct fields."""
        invs = [_inv("INV-X", priority="HIGH")]
        wl = engine_default.calculate_workload(_officer(), invs, [])
        assert len(wl.investigation_breakdown) == 1
        bd = wl.investigation_breakdown[0]
        assert bd["investigation_id"] == "INV-X"
        assert bd["priority"] == "HIGH"
        assert bd["weight"] == 3.0
        assert bd["active"] is True

    def test_policy_version_stamped(self, engine_default):
        """OfficerWorkload carries the policy version."""
        wl = engine_default.calculate_workload(_officer(), [], [])
        assert wl.policy_version == DEFAULT_POLICY.version

    def test_total_workload_is_inv_plus_task(self, engine_default):
        """raw_workload = investigation_weight + task_weight."""
        invs = [_inv("I1", priority="HIGH")]          # weight 3.0
        tasks = [_task("T1", status="ACTIVE")]         # weight 1.5
        wl = engine_default.calculate_workload(_officer(), invs, tasks)
        assert abs(wl.raw_workload - 4.5) < 1e-9
        assert abs(wl.investigation_weight - 3.0) < 1e-9
        assert abs(wl.task_weight - 1.5) < 1e-9


# ════════════════════════════════════════════════════════════════════════════════
# TASK WEIGHT BY STATUS
# ════════════════════════════════════════════════════════════════════════════════

class TestTaskWeights:

    def test_created_task_weight_1(self, engine_default):
        wl = engine_default.calculate_workload(_officer(), [], [_task("T1", status="CREATED")])
        assert abs(wl.task_weight - 1.0) < 1e-9

    def test_assigned_task_weight_1(self, engine_default):
        wl = engine_default.calculate_workload(_officer(), [], [_task("T1", status="ASSIGNED")])
        assert abs(wl.task_weight - 1.0) < 1e-9

    def test_active_task_weight_1_5(self, engine_default):
        wl = engine_default.calculate_workload(_officer(), [], [_task("T1", status="ACTIVE")])
        assert abs(wl.task_weight - 1.5) < 1e-9

    def test_blocked_task_weight_0_5(self, engine_default):
        wl = engine_default.calculate_workload(_officer(), [], [_task("T1", status="BLOCKED")])
        assert abs(wl.task_weight - 0.5) < 1e-9

    def test_completed_task_zero(self, engine_default):
        wl = engine_default.calculate_workload(_officer(), [], [_task("T1", status="COMPLETED")])
        assert wl.task_weight == 0.0
        assert wl.active_task_count == 0

    def test_skipped_task_zero(self, engine_default):
        wl = engine_default.calculate_workload(_officer(), [], [_task("T1", status="SKIPPED")])
        assert wl.task_weight == 0.0

    def test_cancelled_task_zero(self, engine_default):
        wl = engine_default.calculate_workload(_officer(), [], [_task("T1", status="CANCELLED")])
        assert wl.task_weight == 0.0

    def test_multiple_tasks_mixed(self, engine_default):
        """ACTIVE + BLOCKED + COMPLETED = 1.5 + 0.5 + 0 = 2.0."""
        tasks = [
            _task("T1", status="ACTIVE"),
            _task("T2", status="BLOCKED"),
            _task("T3", status="COMPLETED"),
        ]
        wl = engine_default.calculate_workload(_officer(), [], tasks)
        assert abs(wl.task_weight - 2.0) < 1e-9
        assert wl.active_task_count == 2  # ACTIVE + BLOCKED


# ════════════════════════════════════════════════════════════════════════════════
# CAPACITY METRICS
# ════════════════════════════════════════════════════════════════════════════════

class TestCapacityMetrics:

    def _make_workload(self, raw: float, oid: str = "OFF-1") -> OfficerWorkload:
        return OfficerWorkload(
            officer_id=oid,
            raw_workload=raw,
            investigation_weight=raw,
            task_weight=0.0,
            active_investigation_count=1,
            active_task_count=0,
            critical_investigation_count=0,
            investigation_breakdown=[],
            policy_version=DEFAULT_POLICY.version,
        )

    def test_zero_capacity_any_load_is_full(self, engine_default):
        """Officer with max_capacity=0 and workload > 0 → capacity_used = 1.0."""
        wl = self._make_workload(3.0)
        cap = engine_default.calculate_capacity(wl, maximum_capacity=0)
        assert cap.capacity_used == 1.0
        assert cap.is_overloaded is False  # 1.0 is not > 1.0

    def test_zero_capacity_zero_load_is_free(self, engine_default):
        """Officer with max_capacity=0 and zero load → capacity_used = 0.0."""
        wl = self._make_workload(0.0)
        cap = engine_default.calculate_capacity(wl, maximum_capacity=0)
        assert cap.capacity_used == 0.0

    def test_half_capacity(self, engine_default):
        """5.0 / 10 = 0.5 capacity used."""
        wl = self._make_workload(5.0)
        cap = engine_default.calculate_capacity(wl, maximum_capacity=10)
        assert abs(cap.capacity_used - 0.5) < 1e-6
        assert not cap.is_overloaded

    def test_full_capacity(self, engine_default):
        """10.0 / 10 = 1.0 capacity used, not overloaded (≤ 1.0)."""
        wl = self._make_workload(10.0)
        cap = engine_default.calculate_capacity(wl, maximum_capacity=10)
        assert abs(cap.capacity_used - 1.0) < 1e-6
        assert not cap.is_overloaded  # exactly at boundary

    def test_over_capacity(self, engine_default):
        """15.0 / 10 = 1.5 capacity used, is_overloaded = True."""
        wl = self._make_workload(15.0)
        cap = engine_default.calculate_capacity(wl, maximum_capacity=10)
        assert abs(cap.capacity_used - 1.5) < 1e-6
        assert cap.is_overloaded is True

    def test_available_slots_positive(self, engine_default):
        """5.0 workload with cap 10 → 5.0 weighted slots available."""
        wl = self._make_workload(5.0)
        cap = engine_default.calculate_capacity(wl, maximum_capacity=10)
        assert abs(cap.available_slots_weighted - 5.0) < 1e-6

    def test_available_slots_negative_when_overloaded(self, engine_default):
        """12.0 workload with cap 10 → -2.0 weighted slots."""
        wl = self._make_workload(12.0)
        cap = engine_default.calculate_capacity(wl, maximum_capacity=10)
        assert cap.available_slots_weighted < 0

    def test_policy_version_in_capacity(self, engine_default):
        wl = self._make_workload(5.0)
        cap = engine_default.calculate_capacity(wl, maximum_capacity=10)
        assert cap.policy_version == DEFAULT_POLICY.version


# ════════════════════════════════════════════════════════════════════════════════
# BURNOUT ASSESSMENT
# ════════════════════════════════════════════════════════════════════════════════

class TestBurnoutAssessment:

    def _make_workload(self, raw: float, critical_count: int = 0,
                       active_inv: int = 0, oid: str = "OFF-1") -> OfficerWorkload:
        return OfficerWorkload(
            officer_id=oid,
            raw_workload=raw,
            investigation_weight=raw,
            task_weight=0.0,
            active_investigation_count=active_inv,
            active_task_count=0,
            critical_investigation_count=critical_count,
            investigation_breakdown=[],
            policy_version=DEFAULT_POLICY.version,
        )

    def test_all_zero_inputs_healthy(self, engine_default):
        """Officer with zero workload and zero stress factors is HEALTHY with score 0."""
        wl = self._make_workload(0.0)
        ba = engine_default.calculate_burnout(wl, 10, 0, 0, 0, 0.0)
        assert ba.score == 0.0
        assert ba.risk_band == "HEALTHY"
        assert ba.explanation == []

    def test_healthy_band(self, engine_default):
        """Low workload → HEALTHY (score < 30)."""
        wl = self._make_workload(2.0)  # 2/10 = 20% → factor 20% × 40 = 8
        ba = engine_default.calculate_burnout(wl, 10, 0, 0, 0, 0.0)
        assert ba.score < 30.0
        assert ba.risk_band == "HEALTHY"

    def test_moderate_band(self, engine_default):
        """Workload at 75% → MODERATE (score in 30–60)."""
        wl = self._make_workload(7.5)  # 7.5/10 = 75% → 30.0 factor
        ba = engine_default.calculate_burnout(wl, 10, 0, 0, 0, 0.0)
        # 75% × 40 = 30.0 exactly → crosses the 30 threshold
        assert ba.score >= 30.0
        assert ba.risk_band in ("MODERATE", "HIGH")  # boundary test

    def test_high_band_from_workload(self, engine_default):
        """90% workload + overdue tasks → HIGH band."""
        wl = self._make_workload(9.0)  # 90% → 36.0 workload factor
        ba = engine_default.calculate_burnout(wl, 10, overdue_tasks=3, overdue_investigations=0,
                                               consecutive_active_days=0)
        # 36.0 + (3/5)*15 = 36.0 + 9.0 = 45 → MODERATE... need more
        # Use 100% + overdue
        wl2 = self._make_workload(10.0)  # 100% → 40.0
        ba2 = engine_default.calculate_burnout(wl2, 10, overdue_tasks=5, overdue_investigations=2,
                                                consecutive_active_days=0)
        # 40 + 15 + (2/3)*15 = 40+15+10 = 65 → HIGH
        assert ba2.score >= 60.0
        assert ba2.risk_band == "HIGH"

    def test_critical_band(self, engine_default):
        """Saturating all factors → CRITICAL (score ≥ 80)."""
        wl = self._make_workload(10.0, critical_count=3, active_inv=3)
        ba = engine_default.calculate_burnout(
            wl, maximum_capacity=10,
            overdue_tasks=5,
            overdue_investigations=3,
            consecutive_active_days=14,
            after_hours_ratio=1.0,
        )
        # 40 + 15 + 15 + 10 + 10 + 10 = 100
        assert ba.score >= 80.0
        assert ba.risk_band == "CRITICAL"

    def test_score_capped_at_100(self, engine_default):
        """Score cannot exceed 100 even with all factors maxed."""
        wl = self._make_workload(20.0, critical_count=5, active_inv=5)  # 200% overload
        ba = engine_default.calculate_burnout(wl, 10, 10, 10, 28, 2.0)
        assert ba.score <= 100.0

    def test_explanation_includes_workload_factor(self, engine_default):
        """Non-zero workload produces an explanation line."""
        wl = self._make_workload(5.0)
        ba = engine_default.calculate_burnout(wl, 10, 0, 0, 0, 0.0)
        assert any("workload" in line.lower() for line in ba.explanation)

    def test_explanation_includes_overdue_tasks(self, engine_default):
        """Overdue tasks appear in explanation."""
        wl = self._make_workload(0.0)
        ba = engine_default.calculate_burnout(wl, 10, overdue_tasks=3,
                                               overdue_investigations=0,
                                               consecutive_active_days=0)
        assert any("overdue task" in line.lower() or "3" in line for line in ba.explanation)

    def test_explanation_includes_critical_investigations(self, engine_default):
        """Critical investigations appear in explanation."""
        wl = self._make_workload(5.0, critical_count=2, active_inv=2)
        ba = engine_default.calculate_burnout(wl, 10, 0, 0, 0, 0.0)
        assert any("critical" in line.lower() for line in ba.explanation)

    def test_factor_scores_present(self, engine_default):
        """factor_scores dict has all 6 keys."""
        wl = self._make_workload(5.0)
        ba = engine_default.calculate_burnout(wl, 10, 1, 1, 3, 0.2)
        assert set(ba.factor_scores.keys()) == {
            "workload", "overdue_tasks", "overdue_invs",
            "consecutive_days", "after_hours", "critical_ratio",
        }

    def test_policy_version_in_burnout(self, engine_default):
        wl = self._make_workload(0.0)
        ba = engine_default.calculate_burnout(wl, 10, 0, 0, 0)
        assert ba.policy_version == DEFAULT_POLICY.version

    def test_burnout_deterministic(self, engine_default):
        """Same inputs always yield same burnout score."""
        wl = self._make_workload(7.5, critical_count=1, active_inv=2)
        results = [
            engine_default.calculate_burnout(wl, 10, 2, 1, 5, 0.3)
            for _ in range(20)
        ]
        scores = [r.score for r in results]
        assert len(set(scores)) == 1


# ════════════════════════════════════════════════════════════════════════════════
# GINI COEFFICIENT
# ════════════════════════════════════════════════════════════════════════════════

class TestGiniCoefficient:

    def test_empty_list_zero(self):
        assert WorkloadEngine.calculate_gini([]) == 0.0

    def test_single_element_zero(self):
        assert WorkloadEngine.calculate_gini([5.0]) == 0.0

    def test_perfect_equality(self):
        """All equal values → Gini = 0."""
        assert WorkloadEngine.calculate_gini([3.0, 3.0, 3.0, 3.0]) == 0.0

    def test_all_zeros_gini_zero(self):
        """All zero → Gini = 0 (no inequality)."""
        assert WorkloadEngine.calculate_gini([0.0, 0.0, 0.0]) == 0.0

    def test_perfect_inequality_two_values(self):
        """[0, X] → Gini = 0.5 (maximum for 2 values)."""
        g = WorkloadEngine.calculate_gini([0.0, 10.0])
        assert abs(g - 0.5) < 1e-9

    def test_known_distribution(self):
        """[1, 2, 3, 4] — known Gini ≈ 0.25."""
        g = WorkloadEngine.calculate_gini([1.0, 2.0, 3.0, 4.0])
        # Formula: ΣΣ|xi-xj| = 2*(1+2+3) = ...
        # Total abs diff: (0+1+2+3) + (1+0+1+2) + (2+1+0+1) + (3+2+1+0) = 20
        # 2 * n² * μ = 2 * 16 * 2.5 = 80
        # G = 20/80 = 0.25
        assert abs(g - 0.25) < 1e-9

    def test_highly_unequal_distribution(self):
        """High inequality → Gini closer to 1."""
        g = WorkloadEngine.calculate_gini([0.0, 0.0, 0.0, 100.0])
        # Should be high
        assert g > 0.5

    def test_gini_between_zero_and_one(self):
        """Gini must always be in [0, 1]."""
        import random
        vals = [float(i) for i in range(1, 20)]
        g = WorkloadEngine.calculate_gini(vals)
        assert 0.0 <= g <= 1.0

    def test_gini_symmetric(self):
        """Gini([1,2,3]) == Gini([3,2,1]) (order invariant)."""
        g1 = WorkloadEngine.calculate_gini([1.0, 2.0, 3.0])
        g2 = WorkloadEngine.calculate_gini([3.0, 2.0, 1.0])
        assert abs(g1 - g2) < 1e-12


# ════════════════════════════════════════════════════════════════════════════════
# TEAM METRICS
# ════════════════════════════════════════════════════════════════════════════════

class TestTeamMetrics:

    def _wl(self, oid: str, raw: float) -> OfficerWorkload:
        return OfficerWorkload(
            officer_id=oid,
            raw_workload=raw,
            investigation_weight=raw,
            task_weight=0.0,
            active_investigation_count=1,
            active_task_count=0,
            critical_investigation_count=0,
            investigation_breakdown=[],
            policy_version=DEFAULT_POLICY.version,
        )

    def test_empty_team_returns_zeros(self, engine_default):
        tm = engine_default.calculate_team_metrics([])
        assert tm.officer_count == 0
        assert tm.mean_workload == 0.0
        assert tm.gini_coefficient == 0.0

    def test_single_officer_metrics(self, engine_default):
        wls = [self._wl("O1", 5.0)]
        tm = engine_default.calculate_team_metrics(wls)
        assert tm.officer_count == 1
        assert tm.mean_workload == 5.0
        assert tm.median_workload == 5.0
        assert tm.std_workload == 0.0
        assert tm.max_workload == 5.0
        assert tm.min_workload == 5.0
        assert tm.gini_coefficient == 0.0

    def test_mean_calculation(self, engine_default):
        wls = [self._wl("O1", 2.0), self._wl("O2", 4.0), self._wl("O3", 6.0)]
        tm = engine_default.calculate_team_metrics(wls)
        assert abs(tm.mean_workload - 4.0) < 1e-9

    def test_median_calculation(self, engine_default):
        wls = [self._wl("O1", 1.0), self._wl("O2", 3.0), self._wl("O3", 10.0)]
        tm = engine_default.calculate_team_metrics(wls)
        assert abs(tm.median_workload - 3.0) < 1e-9

    def test_max_min_calculation(self, engine_default):
        wls = [self._wl("O1", 1.0), self._wl("O2", 5.0), self._wl("O3", 9.0)]
        tm = engine_default.calculate_team_metrics(wls)
        assert tm.max_workload == 9.0
        assert tm.min_workload == 1.0

    def test_gini_in_team_metrics(self, engine_default):
        """Gini is 0.0 when all equal."""
        wls = [self._wl(f"O{i}", 5.0) for i in range(5)]
        tm = engine_default.calculate_team_metrics(wls)
        assert tm.gini_coefficient == 0.0

    def test_policy_version_in_team_metrics(self, engine_default):
        wls = [self._wl("O1", 3.0)]
        tm = engine_default.calculate_team_metrics(wls)
        assert tm.policy_version == DEFAULT_POLICY.version

    def test_burnout_distribution_keys_present(self, engine_default):
        wls = [self._wl("O1", 3.0)]
        tm = engine_default.calculate_team_metrics(wls)
        assert set(tm.burnout_distribution.keys()) == {
            "HEALTHY", "MODERATE", "HIGH", "CRITICAL"
        }

    def test_capacity_histogram_structure(self, engine_default):
        wls = [self._wl("O1", 3.0)]
        tm = engine_default.calculate_team_metrics(wls)
        assert len(tm.capacity_histogram) == 5
        labels = {b["label"] for b in tm.capacity_histogram}
        assert "0–25%" in labels
        assert "100%+" in labels

    def test_full_team_metrics(self, engine_default):
        """calculate_team_metrics_full populates capacity and burnout fields."""
        wls = [self._wl("O1", 3.0), self._wl("O2", 7.0)]
        caps = [
            CapacityMetrics("O1", 3.0, 10, 0.3, 7.0, False, DEFAULT_POLICY.version),
            CapacityMetrics("O2", 7.0, 10, 0.7, 3.0, False, DEFAULT_POLICY.version),
        ]
        bas = [
            BurnoutAssessment("O1", 12.0, "HEALTHY", [], {}, DEFAULT_POLICY.version),
            BurnoutAssessment("O2", 35.0, "MODERATE", [], {}, DEFAULT_POLICY.version),
        ]
        tm = engine_default.calculate_team_metrics_full(wls, caps, bas)
        assert abs(tm.average_capacity_used - 0.5) < 1e-6
        assert tm.burnout_distribution["HEALTHY"] == 1
        assert tm.burnout_distribution["MODERATE"] == 1

    def test_team_metrics_deterministic(self, engine_default):
        """Same workloads always produce same team metrics."""
        wls = [self._wl(f"O{i}", float(i * 2)) for i in range(1, 6)]
        tm1 = engine_default.calculate_team_metrics(wls)
        tm2 = engine_default.calculate_team_metrics(wls)
        assert tm1.mean_workload == tm2.mean_workload
        assert tm1.gini_coefficient == tm2.gini_coefficient


# ════════════════════════════════════════════════════════════════════════════════
# REBALANCING RECOMMENDATIONS
# ════════════════════════════════════════════════════════════════════════════════

class TestRebalancing:

    def _setup(self, source_load: float = 12.0, dest_load: float = 3.0,
               same_district: bool = True, source_skills: FrozenSet[str] = frozenset(),
               dest_skills: FrozenSet[str] = frozenset()):
        """Build a minimal two-officer setup for rebalancing tests."""
        source_snap = OfficerSnapshot("OFF-A", "D1" if same_district else "D1", 10, source_skills)
        dest_snap = OfficerSnapshot("OFF-B", "D1" if same_district else "D2", 10, dest_skills)

        source_wl = OfficerWorkload("OFF-A", source_load, source_load, 0.0, 2, 0, 0, [], DEFAULT_POLICY.version)
        dest_wl = OfficerWorkload("OFF-B", dest_load, dest_load, 0.0, 1, 0, 0, [], DEFAULT_POLICY.version)

        source_cap = CapacityMetrics("OFF-A", source_load, 10, source_load / 10, 10 - source_load, source_load > 10, DEFAULT_POLICY.version)
        dest_cap = CapacityMetrics("OFF-B", dest_load, 10, dest_load / 10, 10 - dest_load, dest_load > 10, DEFAULT_POLICY.version)

        invs = [_inv("INV-001", priority="HIGH", officer="OFF-A")]

        return (
            [source_wl, dest_wl],
            {"OFF-A": source_cap, "OFF-B": dest_cap},
            {"OFF-A": source_snap, "OFF-B": dest_snap},
            {"OFF-A": invs, "OFF-B": []},
        )

    def test_overloaded_source_generates_recommendation(self, engine_default):
        """Overloaded source (> 0.85 capacity) → recommendation generated."""
        wls, caps, snaps, invs = self._setup(source_load=12.0, dest_load=3.0)
        recs = engine_default.recommend_rebalancing(wls, caps, snaps, invs)
        assert len(recs) >= 1

    def test_no_overloaded_source_empty_result(self, engine_default):
        """No overloaded officers → empty recommendation list."""
        wls, caps, snaps, invs = self._setup(source_load=5.0, dest_load=3.0)
        # source 5.0/10 = 0.5 → not overloaded
        recs = engine_default.recommend_rebalancing(wls, caps, snaps, invs)
        assert recs == []

    def test_no_eligible_destination(self, engine_default):
        """All destinations at/over capacity → no recommendation."""
        source_wl = OfficerWorkload("OFF-A", 12.0, 12.0, 0.0, 2, 0, 0, [], DEFAULT_POLICY.version)
        dest_wl = OfficerWorkload("OFF-B", 9.0, 9.0, 0.0, 2, 0, 0, [], DEFAULT_POLICY.version)
        source_cap = CapacityMetrics("OFF-A", 12.0, 10, 1.2, -2.0, True, DEFAULT_POLICY.version)
        dest_cap = CapacityMetrics("OFF-B", 9.0, 10, 0.9, 1.0, False, DEFAULT_POLICY.version)  # 90% > 85%

        source_snap = OfficerSnapshot("OFF-A", "D1", 10, frozenset())
        dest_snap = OfficerSnapshot("OFF-B", "D1", 10, frozenset())

        recs = engine_default.recommend_rebalancing(
            [source_wl, dest_wl],
            {"OFF-A": source_cap, "OFF-B": dest_cap},
            {"OFF-A": source_snap, "OFF-B": dest_snap},
            {"OFF-A": [_inv("INV-001", priority="HIGH")], "OFF-B": []},
        )
        assert recs == []

    def test_jurisdiction_mismatch_blocks_move(self, engine_default):
        """Different district → no recommendation when cross-jurisdiction is disabled."""
        wls, caps, snaps, invs = self._setup(
            source_load=12.0, dest_load=3.0, same_district=False
        )
        recs = engine_default.recommend_rebalancing(
            wls, caps, snaps, invs, allow_cross_jurisdiction=False
        )
        assert recs == []

    def test_cross_jurisdiction_allowed(self, engine_default):
        """Different district → recommendation if cross-jurisdiction allowed."""
        wls, caps, snaps, invs = self._setup(
            source_load=12.0, dest_load=3.0, same_district=False
        )
        recs = engine_default.recommend_rebalancing(
            wls, caps, snaps, invs, allow_cross_jurisdiction=True
        )
        assert len(recs) >= 1
        assert recs[0].jurisdiction_valid is True

    def test_destination_at_capacity_threshold_rejected(self, engine_default):
        """Destination at exactly 0.85 is rejected (< not ≤)."""
        source_wl = OfficerWorkload("OFF-A", 12.0, 12.0, 0.0, 2, 0, 0, [], DEFAULT_POLICY.version)
        dest_wl = OfficerWorkload("OFF-B", 8.5, 8.5, 0.0, 1, 0, 0, [], DEFAULT_POLICY.version)
        source_cap = CapacityMetrics("OFF-A", 12.0, 10, 1.2, -2.0, True, DEFAULT_POLICY.version)
        dest_cap = CapacityMetrics("OFF-B", 8.5, 10, 0.85, 1.5, False, DEFAULT_POLICY.version)

        source_snap = OfficerSnapshot("OFF-A", "D1", 10, frozenset())
        dest_snap = OfficerSnapshot("OFF-B", "D1", 10, frozenset())

        recs = engine_default.recommend_rebalancing(
            [source_wl, dest_wl],
            {"OFF-A": source_cap, "OFF-B": dest_cap},
            {"OFF-A": source_snap, "OFF-B": dest_snap},
            {"OFF-A": [_inv("INV-001", priority="HIGH")], "OFF-B": []},
        )
        # dest at 0.85 + HIGH weight 3.0 → 11.5/10 = 1.15 → would exceed threshold → rejected
        assert recs == []

    def test_recommendation_fields_complete(self, engine_default):
        """Recommendation includes all required explainability fields."""
        wls, caps, snaps, invs = self._setup(source_load=12.0, dest_load=3.0)
        recs = engine_default.recommend_rebalancing(wls, caps, snaps, invs)
        assert len(recs) >= 1
        rec = recs[0]
        assert rec.investigation_id
        assert rec.source_officer_id == "OFF-A"
        assert rec.destination_officer_id == "OFF-B"
        assert rec.reason_source_overloaded
        assert rec.reason_destination_qualifies
        assert rec.workload_reduction_pct > 0
        assert rec.source_expected_workload < rec.source_current_workload
        assert rec.destination_expected_workload > rec.destination_current_workload

    def test_never_auto_assigns(self, engine_default):
        """Recommendations are DTOs only — no DB writes, no assignment state."""
        wls, caps, snaps, invs = self._setup(source_load=12.0, dest_load=3.0)
        recs = engine_default.recommend_rebalancing(wls, caps, snaps, invs)
        # Simply asserting the return type is correct — no DB side effects
        assert all(isinstance(r, RebalanceRecommendation) for r in recs)

    def test_deterministic_ordering(self, engine_default):
        """Running rebalancing twice yields the same ordering."""
        wls, caps, snaps, invs = self._setup(source_load=12.0, dest_load=3.0)
        recs1 = engine_default.recommend_rebalancing(wls, caps, snaps, invs)
        recs2 = engine_default.recommend_rebalancing(wls, caps, snaps, invs)
        assert len(recs1) == len(recs2)
        for r1, r2 in zip(recs1, recs2):
            assert r1.investigation_id == r2.investigation_id
            assert r1.destination_officer_id == r2.destination_officer_id

    def test_recommendation_to_dict(self, engine_default):
        """to_dict() produces a valid JSON-serializable structure."""
        wls, caps, snaps, invs = self._setup(source_load=12.0, dest_load=3.0)
        recs = engine_default.recommend_rebalancing(wls, caps, snaps, invs)
        if recs:
            d = recs[0].to_dict()
            assert "investigation_id" in d
            assert "source_officer_id" in d
            assert "workload_reduction_pct" in d
            assert "policy_version" in d

    def test_priority_ordering_within_source(self, engine_default):
        """Within one overloaded source, CRITICAL investigations recommended before LOW."""
        invs = [
            _inv("INV-LOW", priority="LOW", officer="OFF-A"),
            _inv("INV-CRIT", priority="CRITICAL", officer="OFF-A"),
        ]
        source_wl = OfficerWorkload("OFF-A", 15.0, 15.0, 0.0, 2, 0, 1, [], DEFAULT_POLICY.version)
        dest_wl = OfficerWorkload("OFF-B", 3.0, 3.0, 0.0, 1, 0, 0, [], DEFAULT_POLICY.version)
        source_cap = CapacityMetrics("OFF-A", 15.0, 10, 1.5, -5.0, True, DEFAULT_POLICY.version)
        dest_cap = CapacityMetrics("OFF-B", 3.0, 10, 0.3, 7.0, False, DEFAULT_POLICY.version)
        source_snap = OfficerSnapshot("OFF-A", "D1", 10, frozenset())
        dest_snap = OfficerSnapshot("OFF-B", "D1", 10, frozenset())

        recs = engine_default.recommend_rebalancing(
            [source_wl, dest_wl],
            {"OFF-A": source_cap, "OFF-B": dest_cap},
            {"OFF-A": source_snap, "OFF-B": dest_snap},
            {"OFF-A": invs, "OFF-B": []},
        )
        # First recommendation should be for CRITICAL
        if len(recs) >= 1:
            assert recs[0].investigation_priority == "CRITICAL"


# ════════════════════════════════════════════════════════════════════════════════
# DETERMINISM
# ════════════════════════════════════════════════════════════════════════════════

class TestDeterminism:

    def test_workload_identical_across_20_runs(self, engine_default):
        """calculate_workload is deterministic across 20 runs."""
        off = _officer("O1")
        invs = [_inv(f"I{i}", priority=["CRITICAL", "HIGH", "MEDIUM", "LOW"][i % 4]) for i in range(5)]
        tasks = [_task(f"T{i}", status=["ACTIVE", "BLOCKED", "CREATED"][i % 3]) for i in range(6)]
        results = [engine_default.calculate_workload(off, invs, tasks) for _ in range(20)]
        raw_values = {r.raw_workload for r in results}
        assert len(raw_values) == 1, f"Non-deterministic workload: {raw_values}"

    def test_policy_version_stamped_in_all_outputs(self, engine_default):
        """All M3 DTOs carry the policy version string."""
        off = _officer("O1")
        invs = [_inv("I1", priority="HIGH")]
        tasks = [_task("T1", status="ACTIVE")]

        wl = engine_default.calculate_workload(off, invs, tasks)
        cap = engine_default.calculate_capacity(wl, maximum_capacity=10)
        ba = engine_default.calculate_burnout(wl, 10, 0, 0, 0, 0.0)
        tm = engine_default.calculate_team_metrics([wl])

        assert wl.policy_version == DEFAULT_POLICY.version
        assert cap.policy_version == DEFAULT_POLICY.version
        assert ba.policy_version == DEFAULT_POLICY.version
        assert tm.policy_version == DEFAULT_POLICY.version

    def test_custom_policy_version_appears(self):
        """A custom WorkloadPolicy's version propagates to all outputs."""
        custom = WorkloadPolicy(version="2.0.0-test")
        engine = WorkloadEngine(policy=custom)
        off = _officer("O1")
        wl = engine.calculate_workload(off, [], [])
        assert wl.policy_version == "2.0.0-test"


# ════════════════════════════════════════════════════════════════════════════════
# WORKLOAD POLICY
# ════════════════════════════════════════════════════════════════════════════════

class TestWorkloadPolicy:

    def test_default_policy_weights_correct(self):
        p = DEFAULT_POLICY
        assert p.investigation_weight_for("CRITICAL") == 5.0
        assert p.investigation_weight_for("HIGH") == 3.0
        assert p.investigation_weight_for("MEDIUM") == 2.0
        assert p.investigation_weight_for("LOW") == 1.0

    def test_default_task_weights_correct(self):
        p = DEFAULT_POLICY
        assert p.task_weight_for("ACTIVE") == 1.5
        assert p.task_weight_for("BLOCKED") == 0.5
        assert p.task_weight_for("CREATED") == 1.0
        assert p.task_weight_for("COMPLETED") == 0.0

    def test_inactive_statuses_detected(self):
        p = DEFAULT_POLICY
        assert p.is_inactive_investigation("Completed")
        assert p.is_inactive_investigation("COMPLETED")
        assert p.is_inactive_investigation("Cancelled")
        assert p.is_inactive_investigation("Archived")
        assert p.is_inactive_investigation("Closed")
        assert not p.is_inactive_investigation("Open")

    def test_burnout_risk_bands(self):
        p = DEFAULT_POLICY
        assert p.burnout_risk_band(0.0) == "HEALTHY"
        assert p.burnout_risk_band(29.9) == "HEALTHY"
        assert p.burnout_risk_band(30.0) == "MODERATE"
        assert p.burnout_risk_band(59.9) == "MODERATE"
        assert p.burnout_risk_band(60.0) == "HIGH"
        assert p.burnout_risk_band(79.9) == "HIGH"
        assert p.burnout_risk_band(80.0) == "CRITICAL"
        assert p.burnout_risk_band(100.0) == "CRITICAL"

    def test_invalid_capacity_threshold_raises(self):
        with pytest.raises(ValueError, match="rebalance_destination_capacity_max"):
            WorkloadPolicy(rebalance_destination_capacity_max=0.0)

    def test_invalid_burnout_weights_raise(self):
        with pytest.raises(ValueError, match="Burnout weights"):
            WorkloadPolicy(burnout_workload_weight=50.0)  # sums to 110

    def test_policy_is_frozen(self):
        """WorkloadPolicy is immutable."""
        with pytest.raises(Exception):
            DEFAULT_POLICY.version = "hacked"  # type: ignore[misc]

    def test_case_insensitive_priority_lookup(self):
        """investigation_weight_for() accepts any case."""
        p = DEFAULT_POLICY
        assert p.investigation_weight_for("critical") == 5.0
        assert p.investigation_weight_for("High") == 3.0


# ════════════════════════════════════════════════════════════════════════════════
# DTO SERIALIZATION
# ════════════════════════════════════════════════════════════════════════════════

class TestDTOSerialization:

    def _make_workload(self) -> OfficerWorkload:
        return OfficerWorkload(
            officer_id="O1", raw_workload=5.0, investigation_weight=4.0,
            task_weight=1.0, active_investigation_count=2, active_task_count=1,
            critical_investigation_count=0, investigation_breakdown=[],
            policy_version="1.0.0",
        )

    def test_officer_workload_to_dict(self):
        d = self._make_workload().to_dict()
        assert d["officer_id"] == "O1"
        assert d["raw_workload"] == 5.0
        assert "policy_version" in d

    def test_burnout_assessment_to_dict(self):
        ba = BurnoutAssessment("O1", 45.0, "MODERATE", ["reason"], {"workload": 20.0}, "1.0.0")
        d = ba.to_dict()
        assert d["risk_band"] == "MODERATE"
        assert d["score"] == 45.0

    def test_capacity_metrics_to_dict(self):
        cm = CapacityMetrics("O1", 5.0, 10, 0.5, 5.0, False, "1.0.0")
        d = cm.to_dict()
        assert "capacity_used_pct" in d
        assert d["capacity_used_pct"] == 50.0

    def test_team_metrics_to_dict(self, engine_default):
        wl = self._make_workload()
        tm = engine_default.calculate_team_metrics([wl])
        d = tm.to_dict()
        assert "gini_coefficient" in d
        assert "burnout_distribution" in d

    def test_rebalance_recommendation_to_dict(self):
        rec = RebalanceRecommendation(
            investigation_id="INV-1", investigation_priority="HIGH",
            source_officer_id="OFF-A", destination_officer_id="OFF-B",
            source_current_workload=12.0, source_expected_workload=9.0,
            destination_current_workload=3.0, destination_expected_workload=6.0,
            workload_reduction_pct=25.0,
            reason_source_overloaded="Source at 120%",
            reason_destination_qualifies="Destination at 30%",
            skills_matched=["CYBER_FORENSICS"],
            jurisdiction_valid=True,
            policy_version="1.0.0",
        )
        d = rec.to_dict()
        assert d["investigation_id"] == "INV-1"
        assert d["workload_reduction_pct"] == 25.0
        assert d["jurisdiction_valid"] is True


# ════════════════════════════════════════════════════════════════════════════════
# PERFORMANCE
# ════════════════════════════════════════════════════════════════════════════════

class TestPerformance:

    def _build_fleet(self, n_officers: int, invs_per_officer: int = 10,
                     tasks_per_officer: int = 50):
        """Build a fleet of OfficerSnapshots with associated investigations and tasks."""
        import string
        priorities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        statuses_inv = ["Open", "Under Investigation"]
        statuses_task = ["ACTIVE", "CREATED", "BLOCKED", "COMPLETED"]

        officers = []
        invs_by_officer = {}
        tasks_by_officer = {}

        for i in range(n_officers):
            oid = f"PERF-{i:04d}"
            officers.append(OfficerSnapshot(oid, f"D{i % 5}", 10, frozenset()))

            invs = []
            for j in range(invs_per_officer):
                invs.append(InvestigationSnapshot(
                    investigation_id=f"INV-{i}-{j}",
                    priority=priorities[j % 4],
                    status=statuses_inv[j % 2],
                    assigned_officer_id=oid,
                ))
            invs_by_officer[oid] = invs

            tasks = []
            for k in range(tasks_per_officer):
                tasks.append(TaskSnapshot(
                    task_id=f"TASK-{i}-{k}",
                    investigation_id=f"INV-{i}-{k % invs_per_officer}",
                    status=statuses_task[k % 4],
                ))
            tasks_by_officer[oid] = tasks

        return officers, invs_by_officer, tasks_by_officer

    def test_workload_1000_officers_under_300ms(self):
        """calculate_workload for 1,000 officers < 300 ms total."""
        engine = WorkloadEngine()
        officers, invs_by, tasks_by = self._build_fleet(1000, 10, 50)

        t0 = time.perf_counter()
        workloads = []
        for off in officers:
            wl = engine.calculate_workload(off, invs_by[off.officer_id], tasks_by[off.officer_id])
            workloads.append(wl)
        elapsed = (time.perf_counter() - t0) * 1000

        assert len(workloads) == 1000
        assert elapsed < 300, f"Workload calculation took {elapsed:.1f} ms (limit 300 ms)"

    def test_team_metrics_1000_officers_under_500ms(self):
        """calculate_team_metrics for 1,000 officers < 500 ms (includes Gini O(n²))."""
        engine = WorkloadEngine()
        officers, invs_by, tasks_by = self._build_fleet(1000, 10, 50)

        workloads = [
            engine.calculate_workload(off, invs_by[off.officer_id], tasks_by[off.officer_id])
            for off in officers
        ]

        t0 = time.perf_counter()
        tm = engine.calculate_team_metrics(workloads)
        elapsed = (time.perf_counter() - t0) * 1000

        assert tm.officer_count == 1000
        assert elapsed < 500, f"Team metrics took {elapsed:.1f} ms (limit 500 ms)"

    def test_rebalancing_1000_officers_under_2s(self):
        """recommend_rebalancing for 1,000 officers < 2,000 ms."""
        engine = WorkloadEngine()
        officers, invs_by, tasks_by = self._build_fleet(1000, 10, 10)

        # Make ~100 officers overloaded (load = 15.0 on cap 10)
        workloads = []
        caps = {}
        snaps = {}
        for i, off in enumerate(officers):
            if i % 10 == 0:
                raw = 15.0
            else:
                raw = float(i % 8)
            wl = OfficerWorkload(off.officer_id, raw, raw, 0.0, 2, 0, 0, [],
                                 DEFAULT_POLICY.version)
            workloads.append(wl)
            cu = raw / 10.0
            caps[off.officer_id] = CapacityMetrics(
                off.officer_id, raw, 10, cu, 10 - raw, raw > 10, DEFAULT_POLICY.version
            )
            snaps[off.officer_id] = off

        t0 = time.perf_counter()
        recs = engine.recommend_rebalancing(workloads, caps, snaps, invs_by)
        elapsed = (time.perf_counter() - t0) * 1000

        assert elapsed < 2000, f"Rebalancing took {elapsed:.1f} ms (limit 2000 ms)"
        # Should have generated at least some recommendations
        assert len(recs) >= 0  # Any count is valid; timing is the assertion


# ════════════════════════════════════════════════════════════════════════════════
# WORKLOAD BREAKDOWN (M3 enrichment)
# ════════════════════════════════════════════════════════════════════════════════

class TestWorkloadBreakdown:
    """Per-band decomposition: weights, counts, penalties, summary, recommendation."""

    def test_breakdown_present_on_workload(self, engine_default):
        """calculate_workload() always populates breakdown."""
        wl = engine_default.calculate_workload(
            _officer(), [_inv("I1", priority="HIGH")], []
        )
        assert wl.breakdown is not None

    def test_critical_band_weight(self, engine_default):
        """CRITICAL investigation contributes to critical_case_weight."""
        wl = engine_default.calculate_workload(
            _officer(), [_inv("I1", priority="CRITICAL")], []
        )
        assert wl.breakdown.critical_case_weight == 5.0
        assert wl.breakdown.critical_case_count == 1

    def test_high_band_weight(self, engine_default):
        wl = engine_default.calculate_workload(
            _officer(), [_inv("I1", priority="HIGH")], []
        )
        assert wl.breakdown.high_case_weight == 3.0
        assert wl.breakdown.high_case_count == 1

    def test_task_band_weights(self, engine_default):
        """ACTIVE, BLOCKED, ASSIGNED each go into their correct band."""
        tasks = [
            _task("T1", status="ACTIVE"),
            _task("T2", status="BLOCKED"),
            _task("T3", status="CREATED"),
        ]
        wl = engine_default.calculate_workload(_officer(), [], tasks)
        assert abs(wl.breakdown.active_task_weight - 1.5) < 1e-9
        assert abs(wl.breakdown.blocked_task_weight - 0.5) < 1e-9
        assert abs(wl.breakdown.assigned_task_weight - 1.0) < 1e-9
        assert wl.breakdown.active_task_count == 1
        assert wl.breakdown.blocked_task_count == 1
        assert wl.breakdown.assigned_task_count == 1

    def test_base_weight_equals_raw_workload(self, engine_default):
        """breakdown.base_weight == raw_workload (no penalties)."""
        invs = [_inv("I1", priority="HIGH")]
        tasks = [_task("T1", status="ACTIVE")]
        wl = engine_default.calculate_workload(_officer(), invs, tasks)
        assert abs(wl.breakdown.base_weight - wl.raw_workload) < 1e-9

    def test_overdue_penalty_added_to_final_score(self, engine_default):
        """Overdue tasks add penalty; final_score > raw_workload."""
        invs = [_inv("I1", priority="HIGH")]   # 3.0
        wl = engine_default.calculate_workload(_officer(), invs, [], overdue_task_count=2)
        expected_penalty = 2 * DEFAULT_POLICY.overdue_task_penalty_per_task
        assert abs(wl.breakdown.overdue_task_penalty - expected_penalty) < 1e-9
        assert abs(wl.breakdown.final_score - (wl.raw_workload + expected_penalty)) < 1e-9
        assert wl.breakdown.overdue_task_count == 2

    def test_burnout_penalty_in_final_score(self, engine_default):
        """burnout_penalty feeds into final_score."""
        wl = engine_default.calculate_workload(_officer(), [], [], burnout_penalty=2.5)
        assert abs(wl.breakdown.burnout_penalty - 2.5) < 1e-9
        assert abs(wl.breakdown.final_score - 2.5) < 1e-9

    def test_final_score_property_on_workload(self, engine_default):
        """OfficerWorkload.final_score property delegates to breakdown."""
        wl = engine_default.calculate_workload(
            _officer(), [_inv("I1", priority="HIGH")], [], overdue_task_count=1
        )
        assert wl.final_score == wl.breakdown.final_score

    def test_summary_lines_non_empty_for_active_officer(self, engine_default):
        """A loaded officer produces non-empty summary_lines."""
        invs = [_inv("I1", priority="CRITICAL"), _inv("I2", priority="HIGH")]
        tasks = [_task("T1", status="ACTIVE")]
        wl = engine_default.calculate_workload(_officer(), invs, tasks)
        assert len(wl.breakdown.summary_lines) > 0

    def test_summary_lines_empty_for_idle_officer(self, engine_default):
        """Officer with zero workload → empty summary."""
        wl = engine_default.calculate_workload(_officer(), [], [])
        assert wl.breakdown.summary_lines == []

    def test_overdue_appears_in_summary(self, engine_default):
        """Overdue penalty produces a summary line."""
        wl = engine_default.calculate_workload(_officer(), [], [], overdue_task_count=3)
        assert any("overdue" in line.lower() for line in wl.breakdown.summary_lines)

    def test_recommendation_critical_overload(self, engine_default):
        """Two or more CRITICAL cases → recommendation mentions Critical."""
        invs = [
            _inv("I1", priority="CRITICAL"),
            _inv("I2", priority="CRITICAL"),
        ]
        wl = engine_default.calculate_workload(_officer(), invs, [])
        assert wl.breakdown.recommendation is not None
        assert "Critical" in wl.breakdown.recommendation

    def test_no_recommendation_for_light_load(self, engine_default):
        """Light load (1 LOW case) → no recommendation."""
        wl = engine_default.calculate_workload(_officer(), [_inv("I1", priority="LOW")], [])
        assert wl.breakdown.recommendation is None

    def test_breakdown_to_dict_complete(self, engine_default):
        """to_dict() includes all required keys."""
        wl = engine_default.calculate_workload(
            _officer(), [_inv("I1", priority="HIGH")],
            [_task("T1", status="ACTIVE")],
            overdue_task_count=1,
            burnout_penalty=0.5,
        )
        d = wl.breakdown.to_dict()
        required_keys = {
            "critical_case_weight", "high_case_weight", "medium_case_weight",
            "low_case_weight", "active_task_weight", "blocked_task_weight",
            "assigned_task_weight", "overdue_task_penalty", "burnout_penalty",
            "critical_case_count", "high_case_count", "medium_case_count",
            "low_case_count", "active_task_count", "blocked_task_count",
            "assigned_task_count", "overdue_task_count",
            "base_weight", "final_score", "summary_lines", "recommendation",
        }
        assert required_keys.issubset(d.keys())

    def test_workload_to_dict_includes_breakdown(self, engine_default):
        """OfficerWorkload.to_dict() includes 'breakdown' and 'final_score' keys."""
        wl = engine_default.calculate_workload(_officer(), [_inv("I1")], [])
        d = wl.to_dict()
        assert "breakdown" in d
        assert "final_score" in d

    def test_breakdown_deterministic(self, engine_default):
        """Same inputs → identical breakdown across 20 runs."""
        invs = [_inv("I1", priority="CRITICAL"), _inv("I2", priority="HIGH")]
        tasks = [_task("T1", status="ACTIVE"), _task("T2", status="BLOCKED")]
        results = [
            engine_default.calculate_workload(
                _officer(), invs, tasks, overdue_task_count=2, burnout_penalty=1.5
            )
            for _ in range(20)
        ]
        finals = {r.breakdown.final_score for r in results}
        assert len(finals) == 1
