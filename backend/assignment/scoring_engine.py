"""Deterministic assignment scoring engine (Phase 8.2, Milestone 2).

Given a ScoringContext (the case) and an officer, produce an AssignmentScore:
a weighted, fully-explainable recommendation score. No ML, no LLM, no
randomness — the same inputs always yield the same output, and every component
records a human-readable reason.

The seven components (weights defined once in contracts.SCORE_WEIGHTS):

    workload               0.30   lower current load  -> higher score
    skill_match            0.25   preferred skills + required specialization held
    district_match         0.15   officer district == case district
    priority_alignment     0.10   experienced officers for high-priority cases
    experience             0.10   normalized years of experience
    recent_case_similarity 0.05   holds skills/spec matching the case type
    supervisor_preference  0.05   supervisor's explicit preference list

Each `_score_*` method returns (score_in_0_1, explanation_or_None). The engine
composes them via AssignmentScore.build(), which owns the weighting so the maths
lives in exactly one place.

Design contract: this engine is PURE with respect to its inputs. It reads
officer capability via OfficerRepository but performs no writes and no I/O beyond
those reads. Determinism is a tested guarantee (see test_assignment_scoring.py).
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Dict
from datetime import date

from sqlalchemy.orm import Session

from backend.db.schema import (
    Officer, SkillCode, Specialization, TaskPriority,
)
from backend.assignment.officer_repository import OfficerRepository
from backend.assignment.contracts import AssignmentScore, ScoringContext


# Experience normalization ceiling: years at/above this map to experience_score 1.0.
EXPERIENCE_CEILING_YEARS = 25

# Priority rank for alignment scoring (higher = more urgent).
_PRIORITY_RANK: Dict[str, int] = {
    TaskPriority.CRITICAL.value: 4,
    TaskPriority.HIGH.value: 3,
    TaskPriority.MEDIUM.value: 2,
    TaskPriority.LOW.value: 1,
}

# Maps a free-text case_type token to the SkillCodes / Specializations that make
# an officer a natural fit. Deterministic, hand-curated (no fuzzy matching).
# Keys are upper-cased case_type tokens; matching is by substring containment so
# "MURDER", "ATTEMPT_MURDER" both hit HOMICIDE.
_CASE_TYPE_SKILLS: Dict[str, List[SkillCode]] = {
    "CYBER": [SkillCode.CYBER_FORENSICS, SkillCode.DIGITAL_EVIDENCE, SkillCode.OSINT],
    "MURDER": [SkillCode.HOMICIDE, SkillCode.FORENSICS, SkillCode.DNA],
    "HOMICIDE": [SkillCode.HOMICIDE, SkillCode.FORENSICS, SkillCode.DNA],
    "ROBBERY": [SkillCode.ROBBERY, SkillCode.SURVEILLANCE],
    "THEFT": [SkillCode.ROBBERY, SkillCode.SURVEILLANCE],
    "NARCOTIC": [SkillCode.NARCOTICS, SkillCode.SURVEILLANCE],
    "DRUG": [SkillCode.NARCOTICS, SkillCode.SURVEILLANCE],
    "FRAUD": [SkillCode.FINANCIAL_CRIME, SkillCode.FRAUD],
    "FINANC": [SkillCode.FINANCIAL_CRIME, SkillCode.FRAUD],
    "TRAFFICK": [SkillCode.TRAFFICKING, SkillCode.SURVEILLANCE],
    "MISSING": [SkillCode.MISSING_PERSONS, SkillCode.OSINT],
    "GANG": [SkillCode.ORGANIZED_CRIME, SkillCode.SURVEILLANCE],
    "ORGANIZED": [SkillCode.ORGANIZED_CRIME, SkillCode.SURVEILLANCE],
    "TERROR": [SkillCode.TERRORISM, SkillCode.OSINT, SkillCode.SURVEILLANCE],
}

_CASE_TYPE_SPECIALIZATION: Dict[str, Specialization] = {
    "CYBER": Specialization.CYBER_CRIME,
    "MURDER": Specialization.HOMICIDE,
    "HOMICIDE": Specialization.HOMICIDE,
    "NARCOTIC": Specialization.NARCOTICS,
    "DRUG": Specialization.NARCOTICS,
    "FRAUD": Specialization.FINANCIAL_CRIME,
    "FINANC": Specialization.FINANCIAL_CRIME,
    "TRAFFICK": Specialization.ORGANIZED_CRIME,
    "GANG": Specialization.ORGANIZED_CRIME,
    "ORGANIZED": Specialization.ORGANIZED_CRIME,
    "MISSING": Specialization.MISSING_PERSONS,
}


def _case_type_skills(case_type: Optional[str]) -> List[SkillCode]:
    if not case_type:
        return []
    token = case_type.upper()
    for key, skills in _CASE_TYPE_SKILLS.items():
        if key in token:
            return skills
    return []


def _case_type_specialization(case_type: Optional[str]) -> Optional[Specialization]:
    if not case_type:
        return None
    token = case_type.upper()
    for key, spec in _CASE_TYPE_SPECIALIZATION.items():
        if key in token:
            return spec
    return None


class AssignmentScoringEngine:
    """Deterministic, explainable 7-factor scorer for officer↔case fit."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = OfficerRepository(session)

    # ── Public API ────────────────────────────────────────────────────────────
    def score_officer(
        self, officer_id: str, context: ScoringContext, as_of: Optional[date] = None
    ) -> AssignmentScore:
        """Compute the full AssignmentScore for one officer against a case."""
        officer = self.repo.get_officer(officer_id)
        if not officer:
            raise ValueError(f"Officer {officer_id} not found")

        as_of = as_of or date.today()
        skills = {s.skill_code for s in self.repo.get_skills(officer_id)}
        specs = {sp.specialization for sp in self.repo.get_specializations(officer_id)}

        explanation: List[str] = []

        workload, ex = self._score_workload(officer)
        if ex: explanation.append(ex)

        skill_match, ex = self._score_skill_match(context, skills, specs)
        if ex: explanation.append(ex)

        district, ex = self._score_district(officer, context)
        if ex: explanation.append(ex)

        priority, ex = self._score_priority_alignment(officer, context)
        if ex: explanation.append(ex)

        experience, ex = self._score_experience(officer)
        if ex: explanation.append(ex)

        similarity, ex = self._score_recent_similarity(context, skills, specs)
        if ex: explanation.append(ex)

        supervisor, ex = self._score_supervisor_preference(officer_id, context)
        if ex: explanation.append(ex)

        # Confidence reflects how much signal we actually had (how many components
        # produced a non-neutral explanation). Purely a transparency aid.
        signal_components = len(explanation)
        confidence = min(1.0, 0.4 + 0.1 * signal_components)

        return AssignmentScore.build(
            officer_id,
            context.investigation_id,
            workload=workload,
            skill_match=skill_match,
            district_match=district,
            priority_alignment=priority,
            experience=experience,
            recent_case_similarity=similarity,
            supervisor_preference=supervisor,
            explanation=explanation,
            confidence=confidence,
        )

    # ── Component scorers ─────────────────────────────────────────────────────
    def _score_workload(self, officer: Officer) -> Tuple[float, Optional[str]]:
        """Lower utilization → higher score. score = 1 - utilization.

        Uses cached counters (fast). Callers should reconcile before batch runs.
        """
        cases = officer.current_case_count or 0
        max_cap = officer.maximum_capacity or 0
        if max_cap <= 0:
            # No declared capacity — neutral, and say so.
            return 0.5, "No declared capacity; workload treated as neutral"
        utilization = min(1.0, cases / max_cap)
        score = 1.0 - utilization
        pct = round(utilization * 100)
        return score, f"{pct}% workload ({cases}/{max_cap} cases)"

    def _score_skill_match(
        self, context: ScoringContext, skills: set, specs: set
    ) -> Tuple[float, Optional[str]]:
        """Fraction of preferred skills held, plus required-specialization bonus.

        - If preferred_skills given: base = held_fraction of those skills.
        - If required_specialization given and held: contributes strongly.
        - If neither specified: neutral 0.5 (no signal).
        """
        preferred = []
        for s in context.preferred_skills:
            try:
                preferred.append(SkillCode(s))
            except ValueError:
                continue
        req_spec = None
        if context.required_specialization:
            try:
                req_spec = Specialization(context.required_specialization)
            except ValueError:
                req_spec = None

        if not preferred and req_spec is None:
            return 0.5, None  # no skill signal for this case

        parts: List[float] = []
        reasons: List[str] = []

        if preferred:
            held = [sk for sk in preferred if sk in skills]
            frac = len(held) / len(preferred)
            parts.append(frac)
            if held:
                reasons.append(
                    f"{len(held)}/{len(preferred)} preferred skills "
                    f"({', '.join(sk.value for sk in held)})"
                )
            else:
                reasons.append("no preferred skills held")

        if req_spec is not None:
            has_spec = req_spec in specs
            parts.append(1.0 if has_spec else 0.0)
            reasons.append(
                f"{req_spec.value} specialization"
                if has_spec else f"missing {req_spec.value} specialization"
            )

        score = sum(parts) / len(parts)
        return score, "; ".join(reasons) if reasons else None

    def _score_district(
        self, officer: Officer, context: ScoringContext
    ) -> Tuple[float, Optional[str]]:
        """1.0 if officer's district matches the case district, else 0.0.

        Neutral 0.5 when either side is unknown (no jurisdiction signal).
        """
        if not context.district_id or not officer.district_id:
            return 0.5, None
        if officer.district_id == context.district_id:
            return 1.0, "Same jurisdiction"
        return 0.0, "Different jurisdiction"

    def _score_priority_alignment(
        self, officer: Officer, context: ScoringContext
    ) -> Tuple[float, Optional[str]]:
        """Align officer seniority with case urgency.

        High-priority cases score experienced officers higher; low-priority cases
        are neutral to experience (anyone can take them). We combine the case's
        priority rank with the officer's normalized experience so that:
          - CRITICAL/HIGH + experienced  -> high
          - CRITICAL/HIGH + junior        -> lower
          - LOW/MEDIUM                    -> ~neutral regardless
        """
        if not context.priority:
            return 0.5, None
        prank = _PRIORITY_RANK.get(context.priority.upper(), 2)
        # Normalize priority to 0..1 (LOW=0 .. CRITICAL=1)
        pnorm = (prank - 1) / 3.0
        years = officer.years_experience or officer.tenure_years or 0
        enorm = min(1.0, years / EXPERIENCE_CEILING_YEARS)
        # For urgent cases, reward experience; for calm cases, stay neutral.
        score = (1.0 - pnorm) * 0.5 + pnorm * enorm
        if pnorm >= 0.66:
            note = f"High-priority case aligned with {years}y experience"
        else:
            note = None
        return score, note

    def _score_experience(self, officer: Officer) -> Tuple[float, Optional[str]]:
        """Normalized years of experience (0 at 0y, 1.0 at EXPERIENCE_CEILING)."""
        years = officer.years_experience or officer.tenure_years or 0
        score = min(1.0, years / EXPERIENCE_CEILING_YEARS)
        if years > 0:
            return score, f"{years} years experience"
        return score, None

    def _score_recent_similarity(
        self, context: ScoringContext, skills: set, specs: set
    ) -> Tuple[float, Optional[str]]:
        """Proxy for 'has handled similar cases': does the officer hold the skills
        / specialization implied by this case type?

        Milestone 2 uses capability as the similarity proxy (deterministic, no
        history table yet). M3+ may replace this with real completed-case history
        behind the same contract.
        """
        implied_skills = _case_type_skills(context.case_type)
        implied_spec = _case_type_specialization(context.case_type)
        if not implied_skills and implied_spec is None:
            return 0.5, None

        signals = 0
        total = 0
        if implied_skills:
            total += 1
            if any(sk in skills for sk in implied_skills):
                signals += 1
        if implied_spec is not None:
            total += 1
            if implied_spec in specs:
                signals += 1
        score = signals / total if total else 0.5
        if signals:
            return score, f"Handled similar {context.case_type} work"
        return score, None

    def _score_supervisor_preference(
        self, officer_id: str, context: ScoringContext
    ) -> Tuple[float, Optional[str]]:
        """Supervisor's explicit preference list. First choice = 1.0, decaying.

        No preference list -> neutral 0.5 (no signal). Officer not on the list
        when a list exists -> 0.0.
        """
        prefs = context.supervisor_preferred_officer_ids
        if not prefs:
            return 0.5, None
        if officer_id in prefs:
            idx = prefs.index(officer_id)
            # First preference 1.0, each subsequent step down by 1/len.
            score = max(0.0, 1.0 - idx / max(1, len(prefs)))
            return score, "Supervisor-preferred officer"
        return 0.0, None
