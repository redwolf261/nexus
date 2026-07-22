"""Recommendation ranking service (Phase 8.2, Milestone 2).

Turns per-officer AssignmentScores into a ranked recommendation list, combining
the deterministic scoring engine (M2) with the hard capacity/availability gate
(M1 OfficerCapacityService).

Ranking policy (fully deterministic — no randomness, stable tie-break):
  1. Officers that PASS the capacity gate rank above those that fail it.
  2. Within each group, order by overall_score descending.
  3. Ties broken by officer_id ascending (lexicographic) so the ordering is
     stable and reproducible across runs and machines.

Crucially, this service NEVER assigns. It recommends. Human approval (M4/M5)
remains the only path to an actual assignment. `recommend_officer()` returns the
top candidate and the full ranked list so a supervisor always sees alternatives.
"""

from __future__ import annotations

from typing import List, Optional
from datetime import date

from sqlalchemy.orm import Session

from backend.db.schema import Officer, SkillCode, TaskPriority
from backend.assignment.officer_repository import OfficerRepository
from backend.assignment.capacity_service import OfficerCapacityService
from backend.assignment.scoring_engine import AssignmentScoringEngine
from backend.assignment.contracts import (
    AssignmentScore, ScoringContext, RankedRecommendation,
)


class RecommendationService:
    """Ranks officers for a case. Recommends only — never auto-assigns."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = OfficerRepository(session)
        self.capacity = OfficerCapacityService(session)
        self.scorer = AssignmentScoringEngine(session)

    # ── Candidate pool ────────────────────────────────────────────────────────
    def _candidate_officers(self, context: ScoringContext) -> List[Officer]:
        """Officers eligible to be *considered*.

        We consider all available officers (ON_DUTY / FIELD). Availability and
        capacity are applied as the hard gate during ranking so that even a
        gated officer can be shown (ranked below) for transparency.
        """
        return self.repo.list_available_officers()

    def _resolve_gate_args(self, context: ScoringContext):
        """Translate ScoringContext string fields into typed capacity args."""
        priority = None
        if context.priority:
            try:
                priority = TaskPriority(context.priority.upper())
            except ValueError:
                priority = None
        required_skill = None
        if context.required_skill:
            try:
                required_skill = SkillCode(context.required_skill)
            except ValueError:
                required_skill = None
        required_cert_skill = None
        if context.preferred_cert_skill:
            # preferred cert is a scoring concern, not a gate; only a *required*
            # cert would gate. Kept None here by design.
            required_cert_skill = None
        return priority, required_skill, required_cert_skill

    # ── Ranking ───────────────────────────────────────────────────────────────
    def rank_officers(
        self,
        context: ScoringContext,
        officer_ids: Optional[List[str]] = None,
        as_of: Optional[date] = None,
    ) -> List[RankedRecommendation]:
        """Score and rank officers for a case.

        Args:
            context: The case description.
            officer_ids: Restrict to these officers; if None, use the available pool.
            as_of: Date for certification validity (defaults today).

        Returns:
            RankedRecommendation list, best first, deterministic ordering.
        """
        as_of = as_of or date.today()
        priority, required_skill, required_cert_skill = self._resolve_gate_args(context)

        if officer_ids is not None:
            officers = [o for o in (self.repo.get_officer(oid) for oid in officer_ids) if o]
        else:
            officers = self._candidate_officers(context)

        scored: List[tuple] = []  # (assignable, score, rejection_summary)
        for officer in officers:
            score = self.scorer.score_officer(officer.officer_id, context, as_of=as_of)
            details = self.capacity.get_capacity_details(
                officer.officer_id,
                priority=priority,
                required_skill=required_skill,
                required_cert_skill=required_cert_skill,
                as_of=as_of,
            )
            rejection_summary = [r.message for r in details.rejections]
            scored.append((details.assignable, score, rejection_summary))

        # Deterministic sort:
        #   assignable first (True sorts before False → invert),
        #   then overall_score descending,
        #   then officer_id ascending (stable tie-break).
        scored.sort(
            key=lambda t: (not t[0], -t[1].overall_score, t[1].officer_id)
        )

        return [
            RankedRecommendation(
                rank=i + 1,
                score=score,
                assignable=assignable,
                rejection_summary=rejection_summary,
            )
            for i, (assignable, score, rejection_summary) in enumerate(scored)
        ]

    # ── Recommendation surface (consumed by M4 API) ───────────────────────────
    def recommend_officer(
        self,
        context: ScoringContext,
        officer_ids: Optional[List[str]] = None,
        as_of: Optional[date] = None,
    ) -> Optional[RankedRecommendation]:
        """Return the single best ASSIGNABLE recommendation, or None if none pass.

        The full ranked list is available via rank_officers(); this convenience
        returns the top assignable candidate a supervisor would approve.
        """
        ranked = self.rank_officers(context, officer_ids=officer_ids, as_of=as_of)
        for rec in ranked:
            if rec.assignable:
                return rec
        return None

    def recommend_multiple(
        self,
        context: ScoringContext,
        top_n: int = 3,
        officer_ids: Optional[List[str]] = None,
        include_non_assignable: bool = False,
        as_of: Optional[date] = None,
    ) -> List[RankedRecommendation]:
        """Return the top-N recommendations.

        By default only assignable officers are returned (what a supervisor can
        act on). Set include_non_assignable=True to show gated officers too
        (for transparency / "why not them?").
        """
        ranked = self.rank_officers(context, officer_ids=officer_ids, as_of=as_of)
        if not include_non_assignable:
            ranked = [r for r in ranked if r.assignable]
            # Re-rank contiguously after filtering.
            ranked = [
                RankedRecommendation(
                    rank=i + 1,
                    score=r.score,
                    assignable=r.assignable,
                    rejection_summary=r.rejection_summary,
                )
                for i, r in enumerate(ranked)
            ]
        return ranked[:top_n]
