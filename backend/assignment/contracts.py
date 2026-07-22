"""Immutable data contracts for the Assignment Engine (Phase 8.2, Milestone 1).

These objects define the stable interface that every later milestone depends on:
  - Milestone 2 (scoring)   produces AssignmentScore
  - Milestone 4 (API)       serializes AssignmentScore / CapacityDetails
  - Milestone 5 (UI)        renders explanation + component_scores
  - Phase 10 (LLM)          consumes explanation without contract changes

Design rules:
  - Frozen dataclasses (immutable): a score, once computed, is a fact.
  - All component scores are normalized to the closed interval [0.0, 1.0].
  - Every recommendation carries a human-readable `explanation`.
  - `to_dict()` yields a JSON-serializable structure for API/audit/persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
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

