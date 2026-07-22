"""Milestone 2 tests — Assignment Scoring Engine (Phase 8.2).

Covers:
  - Determinism (same inputs -> identical output, repeatedly)
  - Each of the 7 component scorers in isolation
  - Explainability (every non-neutral component contributes a reason)
  - Recommendation ranking (score order, capacity gate, tie-break)
  - recommend_officer / recommend_multiple surfaces
  - Scale (rank 1000 officers)

In-memory SQLite. No randomness anywhere in the engine, so no test needs seeds.
"""

import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.db.schema import (
    Base, Officer, SkillCode, Specialization, CertificationStatus,
)
from backend.assignment.officer_repository import OfficerRepository
from backend.assignment.scoring_engine import (
    AssignmentScoringEngine, EXPERIENCE_CEILING_YEARS,
    _case_type_skills, _case_type_specialization,
)
from backend.assignment.recommendation_service import RecommendationService
from backend.assignment.contracts import ScoringContext


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _officer(session, oid="OFF-1", status="ON_DUTY", max_cap=10, cases=0,
             district="D1", years=5):
    o = Officer(officer_id=oid, name_en=oid, availability_status=status,
                maximum_capacity=max_cap, current_case_count=cases,
                current_task_count=0, district_id=district, years_experience=years)
    session.add(o)
    session.flush()
    return o


@pytest.fixture
def repo(db_session):
    return OfficerRepository(db_session)


@pytest.fixture
def scorer(db_session):
    return AssignmentScoringEngine(db_session)


@pytest.fixture
def recommender(db_session):
    return RecommendationService(db_session)


# ── Determinism ──────────────────────────────────────────────────────────────

class TestDeterminism:

    def test_identical_rescoring(self, db_session, repo, scorer):
        _officer(db_session)
        repo.add_skill("OFF-1", SkillCode.CYBER_FORENSICS)
        ctx = ScoringContext("INV-1", case_type="CYBER", priority="HIGH",
                             district_id="D1", preferred_skills=["CYBER_FORENSICS"])
        s1 = scorer.score_officer("OFF-1", ctx)
        s2 = scorer.score_officer("OFF-1", ctx)
        assert s1.overall_score == s2.overall_score
        assert s1.component_scores() == s2.component_scores()
        assert s1.explanation == s2.explanation

    def test_no_randomness_across_many_runs(self, db_session, repo, scorer):
        _officer(db_session, cases=4)
        repo.add_skill("OFF-1", SkillCode.HOMICIDE)
        ctx = ScoringContext("INV-1", case_type="MURDER", priority="CRITICAL",
                             district_id="D1", preferred_skills=["HOMICIDE"])
        scores = {scorer.score_officer("OFF-1", ctx).overall_score for _ in range(20)}
        assert len(scores) == 1  # all identical

    def test_overall_in_unit_interval(self, db_session, repo, scorer):
        _officer(db_session)
        ctx = ScoringContext("INV-1", case_type="CYBER", priority="HIGH")
        s = scorer.score_officer("OFF-1", ctx)
        assert 0.0 <= s.overall_score <= 1.0


# ── Component: workload ──────────────────────────────────────────────────────

class TestWorkloadComponent:

    def test_empty_officer_full_workload_score(self, db_session, scorer):
        _officer(db_session, max_cap=10, cases=0)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1"))
        assert s.workload_score == 1.0

    def test_half_loaded(self, db_session, scorer):
        _officer(db_session, max_cap=10, cases=5)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1"))
        assert s.workload_score == 0.5

    def test_full_capacity_zero_workload_score(self, db_session, scorer):
        _officer(db_session, max_cap=10, cases=10)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1"))
        assert s.workload_score == 0.0

    def test_over_capacity_clamped(self, db_session, scorer):
        _officer(db_session, max_cap=5, cases=8)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1"))
        assert s.workload_score == 0.0

    def test_zero_capacity_neutral(self, db_session, scorer):
        _officer(db_session, max_cap=0, cases=0)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1"))
        assert s.workload_score == 0.5


# ── Component: skill match ───────────────────────────────────────────────────

class TestSkillMatchComponent:

    def test_all_preferred_skills_held(self, db_session, repo, scorer):
        _officer(db_session)
        repo.add_skill("OFF-1", SkillCode.CYBER_FORENSICS)
        repo.add_skill("OFF-1", SkillCode.OSINT)
        ctx = ScoringContext("INV-1", preferred_skills=["CYBER_FORENSICS", "OSINT"])
        s = scorer.score_officer("OFF-1", ctx)
        assert s.skill_match_score == 1.0

    def test_half_preferred_skills_held(self, db_session, repo, scorer):
        _officer(db_session)
        repo.add_skill("OFF-1", SkillCode.CYBER_FORENSICS)
        ctx = ScoringContext("INV-1", preferred_skills=["CYBER_FORENSICS", "OSINT"])
        s = scorer.score_officer("OFF-1", ctx)
        assert s.skill_match_score == 0.5

    def test_no_skill_signal_is_neutral(self, db_session, scorer):
        _officer(db_session)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1"))
        assert s.skill_match_score == 0.5

    def test_required_specialization_held(self, db_session, repo, scorer):
        _officer(db_session)
        repo.add_specialization("OFF-1", Specialization.CYBER_CRIME)
        ctx = ScoringContext("INV-1", required_specialization="CYBER_CRIME")
        s = scorer.score_officer("OFF-1", ctx)
        assert s.skill_match_score == 1.0

    def test_required_specialization_missing(self, db_session, scorer):
        _officer(db_session)
        ctx = ScoringContext("INV-1", required_specialization="CYBER_CRIME")
        s = scorer.score_officer("OFF-1", ctx)
        assert s.skill_match_score == 0.0

    def test_skills_and_spec_combined(self, db_session, repo, scorer):
        _officer(db_session)
        repo.add_skill("OFF-1", SkillCode.CYBER_FORENSICS)  # 1/1 skills = 1.0
        # missing spec = 0.0 -> average = 0.5
        ctx = ScoringContext("INV-1", preferred_skills=["CYBER_FORENSICS"],
                             required_specialization="CYBER_CRIME")
        s = scorer.score_officer("OFF-1", ctx)
        assert s.skill_match_score == 0.5

    def test_invalid_skill_ignored(self, db_session, repo, scorer):
        _officer(db_session)
        repo.add_skill("OFF-1", SkillCode.OSINT)
        ctx = ScoringContext("INV-1", preferred_skills=["NOT_A_SKILL", "OSINT"])
        s = scorer.score_officer("OFF-1", ctx)
        assert s.skill_match_score == 1.0  # only valid OSINT counted, held


# ── Component: district ──────────────────────────────────────────────────────

class TestDistrictComponent:

    def test_same_district(self, db_session, scorer):
        _officer(db_session, district="D1")
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1", district_id="D1"))
        assert s.district_match_score == 1.0

    def test_different_district(self, db_session, scorer):
        _officer(db_session, district="D2")
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1", district_id="D1"))
        assert s.district_match_score == 0.0

    def test_unknown_district_neutral(self, db_session, scorer):
        _officer(db_session, district="D1")
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1"))  # no case district
        assert s.district_match_score == 0.5


# ── Component: priority alignment ────────────────────────────────────────────

class TestPriorityAlignmentComponent:

    def test_critical_with_senior_scores_high(self, db_session, scorer):
        _officer(db_session, years=25)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1", priority="CRITICAL"))
        assert s.priority_alignment_score >= 0.9

    def test_critical_with_junior_scores_lower(self, db_session, scorer):
        _officer(db_session, years=0)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1", priority="CRITICAL"))
        assert s.priority_alignment_score <= 0.1

    def test_low_priority_neutralish(self, db_session, scorer):
        _officer(db_session, years=0)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1", priority="LOW"))
        # pnorm=0 -> score = 0.5 regardless of experience
        assert s.priority_alignment_score == 0.5

    def test_no_priority_neutral(self, db_session, scorer):
        _officer(db_session, years=10)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1"))
        assert s.priority_alignment_score == 0.5


# ── Component: experience ────────────────────────────────────────────────────

class TestExperienceComponent:

    def test_zero_experience(self, db_session, scorer):
        _officer(db_session, years=0)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1"))
        assert s.experience_score == 0.0

    def test_ceiling_experience(self, db_session, scorer):
        _officer(db_session, years=EXPERIENCE_CEILING_YEARS)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1"))
        assert s.experience_score == 1.0

    def test_above_ceiling_clamped(self, db_session, scorer):
        _officer(db_session, years=50)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1"))
        assert s.experience_score == 1.0

    def test_falls_back_to_tenure_years(self, db_session, scorer):
        o = _officer(db_session, years=None)
        o.tenure_years = 10
        db_session.flush()
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1"))
        assert s.experience_score == 10 / EXPERIENCE_CEILING_YEARS


# ── Component: recent similarity ─────────────────────────────────────────────

class TestRecentSimilarityComponent:

    def test_holds_case_type_skills(self, db_session, repo, scorer):
        _officer(db_session)
        repo.add_skill("OFF-1", SkillCode.CYBER_FORENSICS)
        repo.add_specialization("OFF-1", Specialization.CYBER_CRIME)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1", case_type="CYBER"))
        assert s.recent_case_similarity_score == 1.0

    def test_no_relevant_capability(self, db_session, scorer):
        _officer(db_session)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1", case_type="CYBER"))
        assert s.recent_case_similarity_score == 0.0

    def test_unknown_case_type_neutral(self, db_session, scorer):
        _officer(db_session)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1", case_type="PARKING"))
        assert s.recent_case_similarity_score == 0.5


# ── Component: supervisor preference ─────────────────────────────────────────

class TestSupervisorPreferenceComponent:

    def test_first_preference_max(self, db_session, scorer):
        _officer(db_session, "OFF-1")
        ctx = ScoringContext("INV-1", supervisor_preferred_officer_ids=["OFF-1", "OFF-2"])
        s = scorer.score_officer("OFF-1", ctx)
        assert s.supervisor_preference_score == 1.0

    def test_second_preference_lower(self, db_session, scorer):
        _officer(db_session, "OFF-2")
        ctx = ScoringContext("INV-1", supervisor_preferred_officer_ids=["OFF-1", "OFF-2"])
        s = scorer.score_officer("OFF-2", ctx)
        assert 0.0 < s.supervisor_preference_score < 1.0

    def test_not_preferred_zero(self, db_session, scorer):
        _officer(db_session, "OFF-9")
        ctx = ScoringContext("INV-1", supervisor_preferred_officer_ids=["OFF-1"])
        s = scorer.score_officer("OFF-9", ctx)
        assert s.supervisor_preference_score == 0.0

    def test_no_preference_list_neutral(self, db_session, scorer):
        _officer(db_session, "OFF-1")
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1"))
        assert s.supervisor_preference_score == 0.5


# ── Explainability ───────────────────────────────────────────────────────────

class TestExplainability:

    def test_strong_candidate_has_rich_explanation(self, db_session, repo, scorer):
        _officer(db_session, cases=3, district="D1", years=12)
        repo.add_skill("OFF-1", SkillCode.CYBER_FORENSICS)
        repo.add_specialization("OFF-1", Specialization.CYBER_CRIME)
        ctx = ScoringContext("INV-1", case_type="CYBER", priority="HIGH",
                             district_id="D1", preferred_skills=["CYBER_FORENSICS"],
                             required_specialization="CYBER_CRIME",
                             supervisor_preferred_officer_ids=["OFF-1"])
        s = scorer.score_officer("OFF-1", ctx)
        # Expect reasons covering workload, skill, district, experience, similarity, supervisor
        assert len(s.explanation) >= 5
        joined = " ".join(s.explanation).lower()
        assert "workload" in joined
        assert "jurisdiction" in joined
        assert "supervisor" in joined

    def test_explanation_lines_are_strings(self, db_session, scorer):
        _officer(db_session)
        s = scorer.score_officer("OFF-1", ScoringContext("INV-1", case_type="CYBER"))
        assert all(isinstance(line, str) for line in s.explanation)

    def test_missing_officer_raises(self, scorer):
        with pytest.raises(ValueError, match="not found"):
            scorer.score_officer("NOPE", ScoringContext("INV-1"))


# ── Case-type mapping helpers ────────────────────────────────────────────────

class TestCaseTypeMapping:

    def test_cyber_maps_to_cyber_skills(self):
        skills = _case_type_skills("CYBER")
        assert SkillCode.CYBER_FORENSICS in skills

    def test_substring_match(self):
        # "ATTEMPT_MURDER" should still hit HOMICIDE via "MURDER"
        assert SkillCode.HOMICIDE in _case_type_skills("ATTEMPT_MURDER")

    def test_unknown_type_empty(self):
        assert _case_type_skills("PARKING_TICKET") == []

    def test_specialization_mapping(self):
        assert _case_type_specialization("CYBER") == Specialization.CYBER_CRIME
        assert _case_type_specialization("PARKING") is None


# ── Recommendation ranking ───────────────────────────────────────────────────

class TestRecommendationRanking:

    def _seed_pool(self, db_session, repo):
        # B: specialist, low load, same district -> best
        _officer(db_session, "OFF-B", max_cap=13, cases=3, district="D1", years=12)
        repo.add_skill("OFF-B", SkillCode.CYBER_FORENSICS)
        repo.add_specialization("OFF-B", Specialization.CYBER_CRIME)
        # C: specialist, high load -> good but loaded
        _officer(db_session, "OFF-C", max_cap=10, cases=9, district="D1", years=8)
        repo.add_skill("OFF-C", SkillCode.CYBER_FORENSICS)
        repo.add_specialization("OFF-C", Specialization.CYBER_CRIME)
        # A: no cyber, low load, diff district -> weak
        _officer(db_session, "OFF-A", max_cap=10, cases=1, district="D2", years=5)

    def _ctx(self):
        return ScoringContext("INV-1", case_type="CYBER", priority="HIGH",
                              district_id="D1", preferred_skills=["CYBER_FORENSICS"],
                              required_specialization="CYBER_CRIME")

    def test_specialist_ranked_first(self, db_session, repo, recommender):
        self._seed_pool(db_session, repo)
        ranked = recommender.rank_officers(self._ctx())
        assert ranked[0].score.officer_id == "OFF-B"
        assert ranked[0].rank == 1

    def test_descending_score_order(self, db_session, repo, recommender):
        self._seed_pool(db_session, repo)
        ranked = recommender.rank_officers(self._ctx())
        scores = [r.score.overall_score for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_gated_officer_ranked_below_assignable(self, db_session, repo, recommender):
        self._seed_pool(db_session, repo)
        # X: strong score but at capacity -> must rank below assignable
        _officer(db_session, "OFF-X", max_cap=5, cases=5, district="D1", years=20)
        repo.add_skill("OFF-X", SkillCode.CYBER_FORENSICS)
        repo.add_specialization("OFF-X", Specialization.CYBER_CRIME)
        ranked = recommender.rank_officers(self._ctx())
        assert ranked[-1].score.officer_id == "OFF-X"
        assert ranked[-1].assignable is False
        assert ranked[-1].rejection_summary  # has a reason

    def test_recommend_officer_returns_best_assignable(self, db_session, repo, recommender):
        self._seed_pool(db_session, repo)
        best = recommender.recommend_officer(self._ctx())
        assert best.assignable
        assert best.score.officer_id == "OFF-B"

    def test_recommend_officer_none_when_all_gated(self, db_session, repo, recommender):
        # Single officer, at capacity
        _officer(db_session, "OFF-1", max_cap=3, cases=3, district="D1")
        best = recommender.recommend_officer(self._ctx())
        assert best is None

    def test_recommend_multiple_top_n(self, db_session, repo, recommender):
        self._seed_pool(db_session, repo)
        top2 = recommender.recommend_multiple(self._ctx(), top_n=2)
        assert len(top2) == 2
        assert [r.rank for r in top2] == [1, 2]
        assert top2[0].score.officer_id == "OFF-B"

    def test_recommend_multiple_excludes_gated_by_default(self, db_session, repo, recommender):
        self._seed_pool(db_session, repo)
        _officer(db_session, "OFF-X", max_cap=5, cases=5, district="D1")
        recs = recommender.recommend_multiple(self._ctx(), top_n=10)
        assert all(r.assignable for r in recs)
        assert "OFF-X" not in [r.score.officer_id for r in recs]

    def test_recommend_multiple_can_include_gated(self, db_session, repo, recommender):
        self._seed_pool(db_session, repo)
        _officer(db_session, "OFF-X", max_cap=5, cases=5, district="D1")
        recs = recommender.recommend_multiple(self._ctx(), top_n=10,
                                              include_non_assignable=True)
        assert "OFF-X" in [r.score.officer_id for r in recs]

    def test_deterministic_ranking(self, db_session, repo, recommender):
        self._seed_pool(db_session, repo)
        r1 = [r.score.officer_id for r in recommender.rank_officers(self._ctx())]
        r2 = [r.score.officer_id for r in recommender.rank_officers(self._ctx())]
        assert r1 == r2

    def test_tie_break_by_officer_id(self, db_session, repo, recommender):
        # Two identical officers -> tie broken by officer_id ascending
        _officer(db_session, "OFF-ZZZ", max_cap=10, cases=5, district="D1", years=5)
        _officer(db_session, "OFF-AAA", max_cap=10, cases=5, district="D1", years=5)
        ctx = ScoringContext("INV-1", district_id="D1")  # no skill signal, identical
        ranked = recommender.rank_officers(ctx)
        # Both same score -> AAA before ZZZ
        ids = [r.score.officer_id for r in ranked]
        assert ids.index("OFF-AAA") < ids.index("OFF-ZZZ")

    def test_only_available_officers_considered(self, db_session, repo, recommender):
        self._seed_pool(db_session, repo)
        _officer(db_session, "OFF-LEAVE", max_cap=10, cases=0, district="D1",
                 status="LEAVE")
        ranked_ids = [r.score.officer_id for r in recommender.rank_officers(self._ctx())]
        assert "OFF-LEAVE" not in ranked_ids

    def test_explicit_officer_ids_restrict_pool(self, db_session, repo, recommender):
        self._seed_pool(db_session, repo)
        ranked = recommender.rank_officers(self._ctx(), officer_ids=["OFF-A"])
        assert [r.score.officer_id for r in ranked] == ["OFF-A"]


# ── Certification-aware ranking (expired preferred cert) ─────────────────────

class TestCertificationInRanking:

    def test_expired_required_cert_does_not_gate_when_only_preferred(
        self, db_session, repo, recommender
    ):
        # preferred_cert_skill is a scoring concern, not a gate: officer stays assignable
        _officer(db_session, "OFF-1", max_cap=10, cases=0, district="D1")
        repo.add_certification("OFF-1", "Cyber", skill_code=SkillCode.CYBER_FORENSICS,
                               expiry_date=date.today() - timedelta(days=1))
        ctx = ScoringContext("INV-1", case_type="CYBER", district_id="D1",
                             preferred_cert_skill="CYBER_FORENSICS")
        best = recommender.recommend_officer(ctx)
        assert best is not None and best.assignable


# ── Scale ────────────────────────────────────────────────────────────────────

class TestScale:

    def test_rank_1000_officers(self, db_session, repo, recommender):
        import time
        for i in range(1000):
            _officer(db_session, f"OFF-{i:04d}", max_cap=10, cases=i % 10,
                     district="D1", years=i % 25)
            if i % 3 == 0:
                repo.add_skill(f"OFF-{i:04d}", SkillCode.CYBER_FORENSICS)
        ctx = ScoringContext("INV-1", case_type="CYBER", priority="HIGH",
                             district_id="D1", preferred_skills=["CYBER_FORENSICS"])
        start = time.time()
        ranked = recommender.rank_officers(ctx)
        elapsed = time.time() - start
        assert len(ranked) == 1000
        # Deterministic + sorted
        scores = [r.score.overall_score for r in ranked if r.assignable]
        assert scores == sorted(scores, reverse=True)
        assert elapsed < 5.0, f"ranking 1000 officers took {elapsed}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
