"""Immutable data contracts for the Assignment Engine (Phase 8.2, Milestone 1).

These objects define the stable interface that every later milestone depends on:
  - Milestone 2 (scoring)   produces AssignmentScore
  - Milestone 3 (workload)  produces OfficerWorkload / BurnoutAssessment / TeamMetrics
  - Milestone 4 (API)       serializes AssignmentScore / CapacityDetails
  - Milestone 5 (UI)        renders explanation + component_scores
  - Phase 10 (LLM)          consumes WorkloadBreakdown.summary_lines without contract changes

Design rules:
  - Frozen dataclasses (immutable): a score, once computed, is a fact.
  - All component scores are normalized to the closed interval [0.0, 1.0].
  - Every recommendation carries a human-readable `explanation`.
  - `to_dict()` yields a JSON-serializable structure for API/audit/persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# The canonical component weights from the Phase 8.2 specification.
# Sum must equal 1.0. Kept here so scoring (M2) and any consumer agree on the
# contract. Changing a weight is a deliberate, reviewable act.
SCORE_WEIGHTS: Dict[str, float] = {
    "workload": 0.30,
    "skill_match": 0.25,
    "district_match": 0.15,
    "priority_alignment": 0.10,
    "experience": 0.10,
    "recent_case_similarity": 0.05,
    "supervisor_preference": 0.05,
}


def _clamp01(value: float) -> float:
    """Clamp a value into [0.0, 1.0]. Defensive against float drift."""
    if value != value:  # NaN guard
        return 0.0
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


@dataclass(frozen=True)
class AssignmentScore:
    """A deterministic, explainable recommendation score for one officer.

    `overall_score` is the weighted sum of the components using SCORE_WEIGHTS.
    The scoring engine (M1 provides the contract; M2 fills it) is responsible
    for computing components; `build()` composes the weighted total so the
    weighting logic lives in exactly one place.
    """

    officer_id: str
    investigation_id: str

    overall_score: float

    # Component scores — all in [0.0, 1.0]
    workload_score: float
    skill_match_score: float
    district_match_score: float
    priority_alignment_score: float
    experience_score: float
    recent_case_similarity_score: float
    supervisor_preference_score: float

    # Human-readable justification lines (never empty for a real recommendation)
    explanation: List[str] = field(default_factory=list)

    # Optional confidence in [0,1] — how much signal backed the score
    confidence: float = 1.0

    # ── Construction ────────────────────────────────────────────────────────
    @classmethod
    def build(
        cls,
        officer_id: str,
        investigation_id: str,
        *,
        workload: float,
        skill_match: float,
        district_match: float,
        priority_alignment: float,
        experience: float,
        recent_case_similarity: float,
        supervisor_preference: float,
        explanation: Optional[List[str]] = None,
        confidence: float = 1.0,
    ) -> "AssignmentScore":
        """Compose an AssignmentScore, computing the weighted overall score.

        All component inputs are clamped to [0,1] defensively. The weighted
        total uses SCORE_WEIGHTS, guaranteeing overall_score is also in [0,1].
        """
        w = _clamp01(workload)
        s = _clamp01(skill_match)
        d = _clamp01(district_match)
        p = _clamp01(priority_alignment)
        e = _clamp01(experience)
        r = _clamp01(recent_case_similarity)
        sp = _clamp01(supervisor_preference)

        overall = (
            SCORE_WEIGHTS["workload"] * w
            + SCORE_WEIGHTS["skill_match"] * s
            + SCORE_WEIGHTS["district_match"] * d
            + SCORE_WEIGHTS["priority_alignment"] * p
            + SCORE_WEIGHTS["experience"] * e
            + SCORE_WEIGHTS["recent_case_similarity"] * r
            + SCORE_WEIGHTS["supervisor_preference"] * sp
        )

        return cls(
            officer_id=officer_id,
            investigation_id=investigation_id,
            overall_score=round(_clamp01(overall), 4),
            workload_score=round(w, 4),
            skill_match_score=round(s, 4),
            district_match_score=round(d, 4),
            priority_alignment_score=round(p, 4),
            experience_score=round(e, 4),
            recent_case_similarity_score=round(r, 4),
            supervisor_preference_score=round(sp, 4),
            explanation=list(explanation or []),
            confidence=round(_clamp01(confidence), 4),
        )

    # ── Serialization ───────────────────────────────────────────────────────
    def component_scores(self) -> Dict[str, float]:
        """Return the component breakdown as a plain dict (for API/audit/UI)."""
        return {
            "workload": self.workload_score,
            "skill_match": self.skill_match_score,
            "district_match": self.district_match_score,
            "priority_alignment": self.priority_alignment_score,
            "experience": self.experience_score,
            "recent_case_similarity": self.recent_case_similarity_score,
            "supervisor_preference": self.supervisor_preference_score,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Full JSON-serializable representation."""
        return {
            "officer_id": self.officer_id,
            "investigation_id": self.investigation_id,
            "overall_score": self.overall_score,
            "confidence": self.confidence,
            "component_scores": self.component_scores(),
            "explanation": list(self.explanation),
        }


@dataclass(frozen=True)
class RejectionReason:
    """A single, explainable reason an officer cannot take an assignment."""
    code: str          # machine-readable, e.g. "CAPACITY_EXCEEDED"
    message: str       # human-readable

    def to_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class CapacityDetails:
    """Explainable capacity snapshot for one officer.

    `assignable` answers "can this officer take a new case right now?" and
    `rejections` explains why not (empty when assignable).
    """
    officer_id: str
    availability_status: str
    current_case_count: int
    maximum_capacity: int
    available_slots: int
    utilization: float                 # 0.0–1.0 (may exceed 1.0 if over capacity)
    assignable: bool
    rejections: List[RejectionReason] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "officer_id": self.officer_id,
            "availability_status": self.availability_status,
            "current_case_count": self.current_case_count,
            "maximum_capacity": self.maximum_capacity,
            "available_slots": self.available_slots,
            "utilization": round(self.utilization, 4),
            "assignable": self.assignable,
            "rejections": [r.to_dict() for r in self.rejections],
        }


@dataclass(frozen=True)
class CapacityViolation:
    """An officer whose current load exceeds their maximum capacity."""
    officer_id: str
    current_case_count: int
    maximum_capacity: int
    over_by: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "officer_id": self.officer_id,
            "current_case_count": self.current_case_count,
            "maximum_capacity": self.maximum_capacity,
            "over_by": self.over_by,
        }


@dataclass(frozen=True)
class WorkloadSummary:
    """Officer workload snapshot (Milestone 1 provides the shape; M3 enriches)."""
    officer_id: str
    current_case_count: int
    current_task_count: int
    maximum_capacity: int
    utilization: float                 # 0.0–1.0+
    burnout_risk: str                  # BurnoutRisk value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "officer_id": self.officer_id,
            "current_case_count": self.current_case_count,
            "current_task_count": self.current_task_count,
            "maximum_capacity": self.maximum_capacity,
            "utilization": round(self.utilization, 4),
            "burnout_risk": self.burnout_risk,
        }


@dataclass(frozen=True)
class ScoringContext:
    """Immutable description of the investigation being staffed (Milestone 2).

    The caller (M4 API) assembles this from Investigation + FIR data so the
    scoring engine stays decoupled from persistence and deterministic: the same
    ScoringContext + same officer state always yields the same AssignmentScore.

    All fields are optional except `investigation_id` — the engine degrades
    gracefully (a component with no signal contributes a neutral score and says
    so in the explanation) rather than fabricating data.
    """
    investigation_id: str

    # Case classification
    case_type: Optional[str] = None          # e.g. "MURDER", "CYBER" (FIR crime_category / case_type)
    priority: Optional[str] = None           # TaskPriority value: CRITICAL/HIGH/MEDIUM/LOW
    district_id: Optional[str] = None        # Jurisdiction the case belongs to

    # Skill / certification requirements
    required_skill: Optional[str] = None            # SkillCode value — hard gate (capacity layer)
    preferred_skills: List[str] = field(default_factory=list)   # SkillCode values — scoring signal
    required_specialization: Optional[str] = None   # Specialization value — scoring signal
    preferred_cert_skill: Optional[str] = None      # SkillCode — expired → penalty (not gate)

    # Supervisor preference (optional): officer_ids the supervisor favors, in order
    supervisor_preferred_officer_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "case_type": self.case_type,
            "priority": self.priority,
            "district_id": self.district_id,
            "required_skill": self.required_skill,
            "preferred_skills": list(self.preferred_skills),
            "required_specialization": self.required_specialization,
            "preferred_cert_skill": self.preferred_cert_skill,
            "supervisor_preferred_officer_ids": list(self.supervisor_preferred_officer_ids),
        }


@dataclass(frozen=True)
class RankedRecommendation:
    """One officer's place in a ranked recommendation list.

    Wraps an AssignmentScore with its rank and whether the officer passed the
    hard capacity gate. Non-assignable officers may still be scored (for
    transparency) but are ranked below all assignable officers.
    """
    rank: int                       # 1-based; 1 = best recommendation
    score: AssignmentScore
    assignable: bool                # passed capacity/availability hard gate
    rejection_summary: List[str] = field(default_factory=list)  # why not assignable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "assignable": self.assignable,
            "rejection_summary": list(self.rejection_summary),
            **self.score.to_dict(),
        }


# ── Phase 8.2 Milestone 3: Workload Engine DTOs ───────────────────────────────
# All DTOs below are immutable (frozen=True) and carry a policy_version field
# so every computed output can be traced back to the WorkloadPolicy that produced it.


@dataclass(frozen=True)
class WorkloadBreakdown:
    """Per-band decomposition of an officer's workload score.

    Answers the supervisor's first question: *Why* is this score so high?

    The score is decomposed into named contribution buckets:
      - Investigation priority bands (critical / high / medium / low)
      - Task status bands (active / blocked / assigned)
      - Penalty terms (overdue tasks, burnout feed-forward)

    `base_weight` equals `OfficerWorkload.raw_workload` (investigations + tasks,
    no penalties). `final_score` = base_weight + overdue_task_penalty +
    burnout_penalty — the enriched metric consumed by the supervisor dashboard
    and Phase 10 LLM explanations.

    `summary_lines` is a ready-to-render list for the UI. `recommendation` is a
    deterministic, single-sentence action hint when load patterns warrant one.

    Example display::

        Officer A — score 18.2
          • 4 Critical cases        (+20.0)
          • 2 High cases            (+6.0)
          • 11 Active tasks         (+16.5)
          • 1 overdue task          (+0.7)
          • Burnout penalty         (+0.3)
        Recommendation: Avoid assigning additional Critical investigations.
    """
    # ── Investigation contributions ──────────────────────────────────────────
    critical_case_weight: float      # CRITICAL investigations × 5.0
    high_case_weight: float          # HIGH investigations × 3.0
    medium_case_weight: float        # MEDIUM investigations × 2.0
    low_case_weight: float           # LOW investigations × 1.0

    # ── Task contributions ───────────────────────────────────────────────────
    active_task_weight: float        # ACTIVE tasks × 1.5
    blocked_task_weight: float       # BLOCKED tasks × 0.5
    assigned_task_weight: float      # CREATED + ASSIGNED tasks × 1.0

    # ── Penalty terms ────────────────────────────────────────────────────────
    overdue_task_penalty: float      # overdue_count × policy.overdue_task_penalty_per_task
    burnout_penalty: float           # feed-forward from BurnoutAssessment (default 0.0)

    # ── Counts (for dashboard display) ──────────────────────────────────────
    critical_case_count: int
    high_case_count: int
    medium_case_count: int
    low_case_count: int
    active_task_count: int
    blocked_task_count: int
    assigned_task_count: int
    overdue_task_count: int

    # ── Composite score ──────────────────────────────────────────────────────
    base_weight: float               # raw_workload (investigations + tasks, no penalties)
    final_score: float               # base_weight + overdue_task_penalty + burnout_penalty

    # ── Human-readable explainability ────────────────────────────────────────
    summary_lines: List[str]         # One line per non-zero contribution
    recommendation: Optional[str]    # Deterministic action hint (None if no pattern)

    def to_dict(self) -> Dict[str, Any]:
        return {
            # Investigation bands
            "critical_case_weight": self.critical_case_weight,
            "high_case_weight": self.high_case_weight,
            "medium_case_weight": self.medium_case_weight,
            "low_case_weight": self.low_case_weight,
            # Task bands
            "active_task_weight": self.active_task_weight,
            "blocked_task_weight": self.blocked_task_weight,
            "assigned_task_weight": self.assigned_task_weight,
            # Penalties
            "overdue_task_penalty": self.overdue_task_penalty,
            "burnout_penalty": self.burnout_penalty,
            # Counts
            "critical_case_count": self.critical_case_count,
            "high_case_count": self.high_case_count,
            "medium_case_count": self.medium_case_count,
            "low_case_count": self.low_case_count,
            "active_task_count": self.active_task_count,
            "blocked_task_count": self.blocked_task_count,
            "assigned_task_count": self.assigned_task_count,
            "overdue_task_count": self.overdue_task_count,
            # Scores
            "base_weight": self.base_weight,
            "final_score": self.final_score,
            # Explainability
            "summary_lines": list(self.summary_lines),
            "recommendation": self.recommendation,
        }


@dataclass(frozen=True)
class OfficerWorkload:
    """Weighted workload snapshot for one officer.

    `raw_workload` is the sum of investigation priority weights (filtered by
    status) plus task status weights, as defined by the active WorkloadPolicy.
    This is the canonical "how busy is this officer?" metric consumed by the
    Assignment Recommendation Engine (M2) and the rebalancing recommender (M3).

    `investigation_breakdown` gives per-investigation detail for explainability
    and audit. Its presence means every workload figure can be traced to
    individual cases — there is no black-box aggregation.

    `breakdown` (added in M3 enrichment) provides the per-band decomposition
    that feeds the supervisor dashboard, workload balancing UI, and Phase 10
    LLM explanations. `breakdown.final_score` is the enriched total that
    includes overdue-task penalty and burnout feed-forward terms.
    """
    officer_id: str
    raw_workload: float                        # Total weighted workload (investigations + tasks)
    investigation_weight: float                # Investigation contribution
    task_weight: float                         # Task contribution
    active_investigation_count: int            # Non-terminal investigations
    active_task_count: int                     # Non-terminal tasks (weight > 0)
    critical_investigation_count: int          # CRITICAL priority active investigations
    investigation_breakdown: List[Dict[str, Any]]  # Per-investigation detail
    policy_version: str                        # WorkloadPolicy.version that produced this
    breakdown: Optional[WorkloadBreakdown] = None  # Per-band decomposition (None = legacy)

    @property
    def final_score(self) -> float:
        """Enriched score including overdue and burnout penalties.

        Falls back to raw_workload when no breakdown is available (backward
        compatibility with code that constructs OfficerWorkload directly).
        """
        if self.breakdown is not None:
            return self.breakdown.final_score
        return self.raw_workload

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "officer_id": self.officer_id,
            "raw_workload": self.raw_workload,
            "final_score": self.final_score,
            "investigation_weight": self.investigation_weight,
            "task_weight": self.task_weight,
            "active_investigation_count": self.active_investigation_count,
            "active_task_count": self.active_task_count,
            "critical_investigation_count": self.critical_investigation_count,
            "investigation_breakdown": list(self.investigation_breakdown),
            "policy_version": self.policy_version,
        }
        if self.breakdown is not None:
            d["breakdown"] = self.breakdown.to_dict()
        return d


@dataclass(frozen=True)
class BurnoutAssessment:
    """Deterministic burnout risk assessment for one officer.

    `score` is a 0–100 value computed from six weighted factors (workload ratio,
    overdue tasks, overdue investigations, consecutive active days, after-hours
    activity, critical case ratio). The `risk_band` maps the score to a named
    category. Every non-zero factor contributes a human-readable line to
    `explanation`.

    Risk bands (default thresholds, configurable via WorkloadPolicy):
        HEALTHY   : 0–29
        MODERATE  : 30–59
        HIGH      : 60–79
        CRITICAL  : 80–100
    """
    officer_id: str
    score: float                               # 0–100 (inclusive)
    risk_band: str                             # HEALTHY / MODERATE / HIGH / CRITICAL
    explanation: List[str]                     # Factor-by-factor human-readable reasons
    factor_scores: Dict[str, float]            # Component breakdown for audit/UI
    policy_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "officer_id": self.officer_id,
            "score": self.score,
            "risk_band": self.risk_band,
            "explanation": list(self.explanation),
            "factor_scores": dict(self.factor_scores),
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True)
class CapacityMetrics:
    """Weighted capacity utilization for one officer.

    `capacity_used` = raw_workload / maximum_capacity. Unlike the M1
    `CapacityDetails` (which uses simple case-count / max_capacity), this
    metric uses the *weighted* workload, giving a more accurate picture of
    actual operational burden.

    Values exceeding 1.0 represent overflow (officer is over capacity) and are
    intentionally not clamped — the rebalancing engine uses the raw ratio.
    """
    officer_id: str
    raw_workload: float
    maximum_capacity: int
    capacity_used: float                       # May exceed 1.0 for overloaded officers
    available_slots_weighted: float            # maximum_capacity - raw_workload (may be negative)
    is_overloaded: bool
    policy_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "officer_id": self.officer_id,
            "raw_workload": self.raw_workload,
            "maximum_capacity": self.maximum_capacity,
            "capacity_used": round(self.capacity_used, 4),
            "capacity_used_pct": round(self.capacity_used * 100, 1),
            "available_slots_weighted": self.available_slots_weighted,
            "is_overloaded": self.is_overloaded,
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True)
class TeamMetrics:
    """Fleet-wide workload statistics for a group of officers.

    Provides the distributional view supervisors need to detect systemic
    imbalance. The Gini coefficient is the primary inequality metric.
    All values are deterministic given the same set of OfficerWorkloads.
    """
    officer_count: int
    mean_workload: float
    median_workload: float
    std_workload: float
    max_workload: float
    min_workload: float
    average_capacity_used: float               # 0.0 if capacity data not provided
    gini_coefficient: float                    # 0 = perfect equality, 1 = perfect inequality
    burnout_distribution: Dict[str, int]       # risk_band → officer count
    capacity_histogram: List[Dict[str, Any]]   # Buckets: 0-25%, 25-50%, 50-75%, 75-100%, 100%+
    policy_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "officer_count": self.officer_count,
            "mean_workload": self.mean_workload,
            "median_workload": self.median_workload,
            "std_workload": self.std_workload,
            "max_workload": self.max_workload,
            "min_workload": self.min_workload,
            "average_capacity_used": self.average_capacity_used,
            "gini_coefficient": self.gini_coefficient,
            "burnout_distribution": dict(self.burnout_distribution),
            "capacity_histogram": list(self.capacity_histogram),
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True)
class RebalanceRecommendation:
    """A single explainable workload transfer recommendation.

    Recommends moving one investigation from an overloaded officer to an
    eligible destination officer. Contains full explainability: current and
    expected workload values, why the source is overloaded, why the destination
    qualifies, jurisdiction validity, and skills matched.

    IMPORTANT: This is a *recommendation only*. It does not trigger any
    assignment change. Human approval via the supervisor UI (M5) is required.
    Every recommendation is deterministic and reproducible.
    """
    investigation_id: str
    investigation_priority: str
    source_officer_id: str
    destination_officer_id: str

    # Workload values before and after the proposed move
    source_current_workload: float
    source_expected_workload: float
    destination_current_workload: float
    destination_expected_workload: float
    workload_reduction_pct: float              # % reduction for source officer

    # Explainability
    reason_source_overloaded: str             # Why source needs to shed work
    reason_destination_qualifies: str         # Why destination is a good fit
    skills_matched: List[str]                 # Destination skills relevant to the case
    jurisdiction_valid: bool                  # True if same district or cross-jur allowed

    policy_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "investigation_priority": self.investigation_priority,
            "source_officer_id": self.source_officer_id,
            "destination_officer_id": self.destination_officer_id,
            "source_current_workload": self.source_current_workload,
            "source_expected_workload": self.source_expected_workload,
            "destination_current_workload": self.destination_current_workload,
            "destination_expected_workload": self.destination_expected_workload,
            "workload_reduction_pct": self.workload_reduction_pct,
            "reason_source_overloaded": self.reason_source_overloaded,
            "reason_destination_qualifies": self.reason_destination_qualifies,
            "skills_matched": list(self.skills_matched),
            "jurisdiction_valid": self.jurisdiction_valid,
            "policy_version": self.policy_version,
        }


# ── Phase 8.2 Milestone 4 DTOs ───────────────────────────────────────────────

@dataclass(frozen=True)
class AssignmentValidationResult:
    """Explainable result of pre-assignment validation gate check (M4)."""
    investigation_id: str
    officer_id: str
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks: Dict[str, bool] = field(default_factory=dict)
    checked_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "officer_id": self.officer_id,
            "is_valid": self.is_valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "checks": dict(self.checks),
            "checked_at": self.checked_at,
        }


@dataclass(frozen=True)
class CompletionEstimate:
    """Deterministic completion duration heuristic for an investigation (M4)."""
    investigation_id: str
    earliest_days: float
    expected_days: float
    latest_days: float
    estimated_completion_date: str
    factors: Dict[str, Any] = field(default_factory=dict)
    policy_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "earliest_days": round(self.earliest_days, 1),
            "expected_days": round(self.expected_days, 1),
            "latest_days": round(self.latest_days, 1),
            "estimated_completion_date": self.estimated_completion_date,
            "factors": dict(self.factors),
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True)
class BulkRecommendationItem:
    """Ranked recommendations for one investigation in a bulk query (M4)."""
    investigation_id: str
    ranked_officers: List[RankedRecommendation]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "ranked_officers": [r.to_dict() for r in self.ranked_officers],
        }


@dataclass(frozen=True)
class AssignmentRecordDTO:
    """Serializable snapshot of an assignment history entry (M4)."""
    id: str
    assignment_id: str
    investigation_id: str
    officer_id: str
    assigned_by: str
    timestamp: str
    reason: Optional[str] = None
    recommendation_score: Optional[float] = None
    policy_version: Optional[str] = None
    manual_override: bool = False
    override_reason: Optional[str] = None
    previous_officer: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "investigation_id": self.investigation_id,
            "officer_id": self.officer_id,
            "assigned_by": self.assigned_by,
            "timestamp": self.timestamp,
            "reason": self.reason,
            "recommendation_score": self.recommendation_score,
            "policy_version": self.policy_version,
            "manual_override": self.manual_override,
            "override_reason": self.override_reason,
            "previous_officer": self.previous_officer,
        }


# ── Phase 8.2 Milestone 5 DTOs ───────────────────────────────────────────────

@dataclass(frozen=True)
class GovernanceMetricsDTO:
    """Fleet-wide supervisor decision and operational governance metrics (M5)."""
    total_decisions: int
    acceptance_rate_pct: float
    override_rate_pct: float
    rejection_rate_pct: float
    deferral_rate_pct: float
    avg_approval_latency_seconds: float
    policy_violation_count: int
    escalation_count: int
    capacity_override_pct: float
    cross_jurisdiction_override_pct: float
    manual_assignment_pct: float
    policy_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_decisions": self.total_decisions,
            "acceptance_rate_pct": round(self.acceptance_rate_pct, 1),
            "override_rate_pct": round(self.override_rate_pct, 1),
            "rejection_rate_pct": round(self.rejection_rate_pct, 1),
            "deferral_rate_pct": round(self.deferral_rate_pct, 1),
            "avg_approval_latency_seconds": round(self.avg_approval_latency_seconds, 2),
            "policy_violation_count": self.policy_violation_count,
            "escalation_count": self.escalation_count,
            "capacity_override_pct": round(self.capacity_override_pct, 1),
            "cross_jurisdiction_override_pct": round(self.cross_jurisdiction_override_pct, 1),
            "manual_assignment_pct": round(self.manual_assignment_pct, 1),
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True)
class EscalationItemDTO:
    """Serializable snapshot of a pending ACP / DCP escalation queue item (M5)."""
    id: str
    decision_id: str
    investigation_id: str
    required_role: str
    status: str
    approver_id: Optional[str]
    approved_at: Optional[str]
    comments: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "decision_id": self.decision_id,
            "investigation_id": self.investigation_id,
            "required_role": self.required_role,
            "status": self.status,
            "approver_id": self.approver_id,
            "approved_at": self.approved_at,
            "comments": self.comments,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class SnapshotDTO:
    """Serializable recommendation snapshot for legal reproducibility (M5)."""
    id: str
    investigation_id: str
    policy_version: str
    rankings: List[Dict[str, Any]]
    workload_snapshot: Dict[str, Any]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "investigation_id": self.investigation_id,
            "policy_version": self.policy_version,
            "rankings": list(self.rankings),
            "workload_snapshot": dict(self.workload_snapshot),
            "created_at": self.created_at,
        }


