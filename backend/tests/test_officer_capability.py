"""Milestone 1 tests — Officer Capability Foundation (Phase 8.2).

Covers:
  - AssignmentScore contract (determinism, weighting, immutability, clamping)
  - OfficerRepository (skills, specializations, certifications, counters, queries)
  - AvailabilityStateManager (state machine, privilege, audit, leave auto-expire)
  - OfficerCapacityService (capacity rules, explainable rejections, burnout)
  - ReconciliationService (drift detection, correction, audit)

All tests use in-memory SQLite for isolation.
"""

import pytest
from datetime import date, timedelta, datetime
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.db.schema import (
    Base, Officer, FIR, InvestigationTask,
    SkillCode, Specialization, CertificationStatus, AvailabilityStatus,
    TaskPriority, TaskStatus, TaskCategory, BurnoutRisk, Role,
)
from backend.assignment.contracts import AssignmentScore, SCORE_WEIGHTS
from backend.assignment.officer_repository import OfficerRepository
from backend.assignment.availability import (
    AvailabilityStateManager, AvailabilityTransitionError,
)
from backend.assignment.capacity_service import OfficerCapacityService
from backend.assignment.reconciliation import ReconciliationService


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def _make_officer(session, officer_id="OFF-1", status="ON_DUTY",
                  max_capacity=10, cases=0, tasks=0, **kw):
    o = Officer(
        officer_id=officer_id, name_en=kw.get("name", officer_id),
        availability_status=status, maximum_capacity=max_capacity,
        current_case_count=cases, current_task_count=tasks,
        district_id=kw.get("district_id"), years_experience=kw.get("years_experience"),
    )
    session.add(o)
    session.flush()
    return o


@pytest.fixture
def repo(db_session):
    return OfficerRepository(db_session)


@pytest.fixture
def availability(db_session):
    return AvailabilityStateManager(db_session)


@pytest.fixture
def capacity(db_session):
    return OfficerCapacityService(db_session)


@pytest.fixture
def reconciliation(db_session):
    return ReconciliationService(db_session)


# ── AssignmentScore contract ─────────────────────────────────────────────────

class TestAssignmentScoreContract:

    def test_weights_sum_to_one(self):
        assert abs(sum(SCORE_WEIGHTS.values()) - 1.0) < 1e-9

    def test_perfect_score_is_one(self):
        s = AssignmentScore.build(
            "OFF-1", "INV-1", workload=1, skill_match=1, district_match=1,
            priority_alignment=1, experience=1, recent_case_similarity=1,
            supervisor_preference=1,
        )
        assert s.overall_score == 1.0

    def test_zero_score_is_zero(self):
        s = AssignmentScore.build(
            "OFF-1", "INV-1", workload=0, skill_match=0, district_match=0,
            priority_alignment=0, experience=0, recent_case_similarity=0,
            supervisor_preference=0,
        )
        assert s.overall_score == 0.0

    def test_weighted_sum_is_deterministic(self):
        # .30*.5 + .25*.8 + .15*1 + .10*.6 + .10*.4 + .05*.2 + .05*0 = 0.61
        kwargs = dict(
            workload=0.5, skill_match=0.8, district_match=1.0,
            priority_alignment=0.6, experience=0.4,
            recent_case_similarity=0.2, supervisor_preference=0.0,
        )
        s1 = AssignmentScore.build("OFF-1", "INV-1", **kwargs)
        s2 = AssignmentScore.build("OFF-1", "INV-1", **kwargs)
        assert s1.overall_score == s2.overall_score == 0.61

    def test_component_inputs_are_clamped(self):
        s = AssignmentScore.build(
            "OFF-1", "INV-1", workload=5.0, skill_match=-2.0, district_match=1,
            priority_alignment=1, experience=1, recent_case_similarity=1,
            supervisor_preference=1,
        )
        assert s.workload_score == 1.0
        assert s.skill_match_score == 0.0

    def test_score_is_immutable(self):
        s = AssignmentScore.build(
            "OFF-1", "INV-1", workload=0.5, skill_match=0.5, district_match=0.5,
            priority_alignment=0.5, experience=0.5, recent_case_similarity=0.5,
            supervisor_preference=0.5,
        )
        with pytest.raises(Exception):
            s.overall_score = 0.99  # frozen dataclass

    def test_component_scores_dict(self):
        s = AssignmentScore.build(
            "OFF-1", "INV-1", workload=0.5, skill_match=0.8, district_match=1.0,
            priority_alignment=0.6, experience=0.4, recent_case_similarity=0.2,
            supervisor_preference=0.0,
        )
        cs = s.component_scores()
        assert cs["skill_match"] == 0.8
        assert len(cs) == 7

    def test_to_dict_has_explanation(self):
        s = AssignmentScore.build(
            "OFF-1", "INV-1", workload=1, skill_match=1, district_match=1,
            priority_alignment=1, experience=1, recent_case_similarity=1,
            supervisor_preference=1, explanation=["Cyber specialist", "Low load"],
        )
        d = s.to_dict()
        assert d["explanation"] == ["Cyber specialist", "Low load"]
        assert d["overall_score"] == 1.0
        assert "component_scores" in d

    def test_nan_confidence_defaults_safe(self):
        s = AssignmentScore.build(
            "OFF-1", "INV-1", workload=0.5, skill_match=0.5, district_match=0.5,
            priority_alignment=0.5, experience=0.5, recent_case_similarity=0.5,
            supervisor_preference=0.5, confidence=float("nan"),
        )
        assert s.confidence == 0.0


# ── OfficerRepository ────────────────────────────────────────────────────────

class TestOfficerRepositorySkills:

    def test_add_and_get_skill(self, db_session, repo):
        _make_officer(db_session)
        repo.add_skill("OFF-1", SkillCode.CYBER_FORENSICS, proficiency=5)
        skills = repo.get_skills("OFF-1")
        assert len(skills) == 1
        assert skills[0].skill_code == SkillCode.CYBER_FORENSICS
        assert skills[0].proficiency == 5

    def test_add_skill_is_idempotent(self, db_session, repo):
        _make_officer(db_session)
        repo.add_skill("OFF-1", SkillCode.OSINT, proficiency=3)
        repo.add_skill("OFF-1", SkillCode.OSINT, proficiency=5)  # update, not duplicate
        skills = repo.get_skills("OFF-1")
        assert len(skills) == 1
        assert skills[0].proficiency == 5

    def test_list_officers_by_skill(self, db_session, repo):
        _make_officer(db_session, "OFF-1")
        _make_officer(db_session, "OFF-2")
        repo.add_skill("OFF-1", SkillCode.HOMICIDE)
        repo.add_skill("OFF-2", SkillCode.NARCOTICS)
        result = repo.list_officers_by_skill(SkillCode.HOMICIDE)
        assert len(result) == 1
        assert result[0].officer_id == "OFF-1"

    def test_multiple_skills_per_officer(self, db_session, repo):
        _make_officer(db_session)
        repo.add_skill("OFF-1", SkillCode.CYBER_FORENSICS)
        repo.add_skill("OFF-1", SkillCode.OSINT)
        repo.add_skill("OFF-1", SkillCode.DIGITAL_EVIDENCE)
        assert len(repo.get_skills("OFF-1")) == 3


class TestOfficerRepositorySpecializations:

    def test_add_and_get_specialization(self, db_session, repo):
        _make_officer(db_session)
        repo.add_specialization("OFF-1", Specialization.CYBER_CRIME, is_primary=True)
        specs = repo.get_specializations("OFF-1")
        assert len(specs) == 1
        assert specs[0].is_primary is True

    def test_specialization_idempotent(self, db_session, repo):
        _make_officer(db_session)
        repo.add_specialization("OFF-1", Specialization.HOMICIDE)
        repo.add_specialization("OFF-1", Specialization.HOMICIDE, is_primary=True)
        specs = repo.get_specializations("OFF-1")
        assert len(specs) == 1
        assert specs[0].is_primary is True

    def test_list_officers_by_specialization(self, db_session, repo):
        _make_officer(db_session, "OFF-1")
        _make_officer(db_session, "OFF-2")
        repo.add_specialization("OFF-1", Specialization.FORENSICS)
        result = repo.list_officers_by_specialization(Specialization.FORENSICS)
        assert [o.officer_id for o in result] == ["OFF-1"]


class TestOfficerRepositoryCertifications:

    def test_add_certification(self, db_session, repo):
        _make_officer(db_session)
        cert = repo.add_certification(
            "OFF-1", "Cyber Cert", skill_code=SkillCode.CYBER_FORENSICS,
            issuing_authority="NFSU", expiry_date=date.today() + timedelta(days=365),
        )
        assert cert.status == CertificationStatus.ACTIVE
        assert len(repo.get_certifications("OFF-1")) == 1

    def test_valid_certifications_excludes_expired(self, db_session, repo):
        _make_officer(db_session)
        repo.add_certification("OFF-1", "Valid", expiry_date=date.today() + timedelta(days=1))
        repo.add_certification("OFF-1", "Expired", expiry_date=date.today() - timedelta(days=1))
        valid = repo.get_valid_certifications("OFF-1")
        assert len(valid) == 1
        assert valid[0].name == "Valid"

    def test_valid_certifications_includes_no_expiry(self, db_session, repo):
        _make_officer(db_session)
        repo.add_certification("OFF-1", "Permanent", expiry_date=None)
        valid = repo.get_valid_certifications("OFF-1")
        assert len(valid) == 1

    def test_valid_certifications_excludes_revoked(self, db_session, repo):
        _make_officer(db_session)
        repo.add_certification("OFF-1", "Revoked", status=CertificationStatus.REVOKED,
                               expiry_date=date.today() + timedelta(days=365))
        assert len(repo.get_valid_certifications("OFF-1")) == 0

    def test_mark_expired_certifications(self, db_session, repo):
        _make_officer(db_session)
        repo.add_certification("OFF-1", "A", expiry_date=date.today() - timedelta(days=5))
        repo.add_certification("OFF-1", "B", expiry_date=date.today() + timedelta(days=5))
        n = repo.mark_expired_certifications()
        assert n == 1
        statuses = {c.name: c.status for c in repo.get_certifications("OFF-1")}
        assert statuses["A"] == CertificationStatus.EXPIRED
        assert statuses["B"] == CertificationStatus.ACTIVE


class TestOfficerRepositoryCounters:

    def test_update_counters_increment(self, db_session, repo):
        _make_officer(db_session, cases=1, tasks=1)
        repo.update_workload_counters("OFF-1", case_delta=2, task_delta=3)
        o = repo.get_officer("OFF-1")
        assert o.current_case_count == 3
        assert o.current_task_count == 4

    def test_update_counters_clamps_at_zero(self, db_session, repo):
        _make_officer(db_session, cases=1)
        repo.update_workload_counters("OFF-1", case_delta=-5)
        assert repo.get_officer("OFF-1").current_case_count == 0

    def test_set_counters(self, db_session, repo):
        _make_officer(db_session, cases=99)
        repo.set_workload_counters("OFF-1", case_count=7, task_count=2)
        o = repo.get_officer("OFF-1")
        assert o.current_case_count == 7 and o.current_task_count == 2

    def test_update_counters_missing_officer_raises(self, repo):
        with pytest.raises(ValueError, match="not found"):
            repo.update_workload_counters("NOPE", case_delta=1)

    def test_count_open_cases_from_source(self, db_session, repo):
        _make_officer(db_session)
        db_session.add(FIR(fir_id="F1", investigating_officer_id="OFF-1", status="Open"))
        db_session.add(FIR(fir_id="F2", investigating_officer_id="OFF-1", status="Under Investigation"))
        db_session.add(FIR(fir_id="F3", investigating_officer_id="OFF-1", status="Closed"))
        db_session.flush()
        assert repo.count_open_cases_from_source("OFF-1") == 2

    def test_count_active_tasks_from_source(self, db_session, repo):
        _make_officer(db_session)
        for i, st in enumerate([TaskStatus.ACTIVE, TaskStatus.ASSIGNED,
                                TaskStatus.COMPLETED, TaskStatus.CANCELLED]):
            db_session.add(InvestigationTask(
                id=f"T{i}", investigation_id="INV-1", assigned_officer_id="OFF-1",
                status=st, title="t", category=TaskCategory.ANALYSIS,
                priority=TaskPriority.LOW,
            ))
        db_session.flush()
        # ACTIVE + ASSIGNED count; COMPLETED + CANCELLED do not
        assert repo.count_active_tasks_from_source("OFF-1") == 2


class TestOfficerRepositoryAvailabilityFilter:

    def test_list_available_officers(self, db_session, repo):
        _make_officer(db_session, "OFF-1", status="ON_DUTY")
        _make_officer(db_session, "OFF-2", status="LEAVE")
        _make_officer(db_session, "OFF-3", status="FIELD")
        _make_officer(db_session, "OFF-4", status="SUSPENDED")
        avail = {o.officer_id for o in repo.list_available_officers()}
        assert avail == {"OFF-1", "OFF-3"}


# ── AvailabilityStateManager ─────────────────────────────────────────────────

class TestAvailabilityStateMachine:

    def test_valid_transition_on_duty_to_break(self, db_session, availability):
        _make_officer(db_session, status="ON_DUTY")
        availability.transition("OFF-1", "BREAK", reason="lunch", actor_id="U1")
        assert db_session.query(Officer).filter_by(officer_id="OFF-1").first().availability_status == "BREAK"

    def test_return_from_break_to_on_duty(self, db_session, availability):
        _make_officer(db_session, status="BREAK")
        availability.transition("OFF-1", "ON_DUTY", actor_id="U1")
        assert db_session.query(Officer).filter_by(officer_id="OFF-1").first().availability_status == "ON_DUTY"

    def test_illegal_transition_rejected(self, db_session, availability):
        _make_officer(db_session, status="BREAK")
        # BREAK can only go to ON_DUTY, not FIELD
        with pytest.raises(AvailabilityTransitionError, match="Illegal transition"):
            availability.transition("OFF-1", "FIELD", actor_id="U1")

    def test_suspended_cannot_self_lift(self, db_session, availability):
        _make_officer(db_session, status="SUSPENDED")
        with pytest.raises(AvailabilityTransitionError, match="requires"):
            availability.transition("OFF-1", "ON_DUTY", actor_id="U1", actor_role=Role.Analyst)

    def test_admin_can_lift_suspension(self, db_session, availability):
        _make_officer(db_session, status="SUSPENDED")
        availability.transition("OFF-1", "ON_DUTY", actor_id="ADMIN", actor_role=Role.Admin)
        assert db_session.query(Officer).filter_by(officer_id="OFF-1").first().availability_status == "ON_DUTY"

    def test_supervisor_can_lift_suspension(self, db_session, availability):
        _make_officer(db_session, status="SUSPENDED")
        availability.transition("OFF-1", "ON_DUTY", actor_id="SUP", actor_role=Role.Supervisor)
        assert db_session.query(Officer).filter_by(officer_id="OFF-1").first().availability_status == "ON_DUTY"

    def test_noop_transition_rejected(self, db_session, availability):
        _make_officer(db_session, status="ON_DUTY")
        with pytest.raises(AvailabilityTransitionError, match="no transition needed"):
            availability.transition("OFF-1", "ON_DUTY", actor_id="U1")

    def test_unknown_status_raises(self, db_session, availability):
        _make_officer(db_session)
        with pytest.raises(ValueError, match="Unknown availability status"):
            availability.transition("OFF-1", "VACATIONING", actor_id="U1")

    def test_transition_missing_officer(self, availability):
        with pytest.raises(ValueError, match="not found"):
            availability.transition("NOPE", "BREAK", actor_id="U1")

    def test_every_transition_is_audited(self, db_session, availability):
        _make_officer(db_session, status="ON_DUTY")
        availability.transition("OFF-1", "FIELD", reason="patrol", actor_id="U1")
        availability.transition("OFF-1", "ON_DUTY", actor_id="U1")
        hist = availability.get_history("OFF-1")
        assert len(hist) == 2
        assert hist[0].from_status == "ON_DUTY" and hist[0].to_status == "FIELD"
        assert hist[0].reason == "patrol" and hist[0].actor_id == "U1"

    def test_can_transition_pure_check(self):
        assert AvailabilityStateManager.can_transition("ON_DUTY", "SUSPENDED")
        assert not AvailabilityStateManager.can_transition("BREAK", "FIELD")
        assert not AvailabilityStateManager.can_transition("SUSPENDED", "LEAVE")

    def test_state_machine_rules_exposed(self):
        rules = AvailabilityStateManager.get_state_machine_rules()
        assert "SUSPENDED" in rules["ON_DUTY"]
        assert rules["SUSPENDED"] == ["ON_DUTY"]


class TestAvailabilityLeave:

    def test_schedule_leave_sets_end_date(self, db_session, availability):
        _make_officer(db_session, status="ON_DUTY")
        end = date.today() + timedelta(days=7)
        availability.schedule_leave("OFF-1", ends_on=end, reason="vacation", actor_id="U1")
        o = db_session.query(Officer).filter_by(officer_id="OFF-1").first()
        assert o.availability_status == "LEAVE"
        assert o.leave_ends_on == end

    def test_auto_expire_leave_returns_due_officers(self, db_session, availability):
        _make_officer(db_session, "OFF-1", status="ON_DUTY")
        _make_officer(db_session, "OFF-2", status="ON_DUTY")
        availability.schedule_leave("OFF-1", ends_on=date.today() - timedelta(days=1), actor_id="U1")
        availability.schedule_leave("OFF-2", ends_on=date.today() + timedelta(days=5), actor_id="U1")
        returned = availability.auto_expire_leave()
        assert returned == ["OFF-1"]
        assert db_session.query(Officer).filter_by(officer_id="OFF-1").first().availability_status == "ON_DUTY"
        assert db_session.query(Officer).filter_by(officer_id="OFF-2").first().availability_status == "LEAVE"

    def test_auto_expire_clears_leave_end(self, db_session, availability):
        _make_officer(db_session, status="ON_DUTY")
        availability.schedule_leave("OFF-1", ends_on=date.today() - timedelta(days=1), actor_id="U1")
        availability.auto_expire_leave()
        assert db_session.query(Officer).filter_by(officer_id="OFF-1").first().leave_ends_on is None

    def test_auto_expire_audited_as_system(self, db_session, availability):
        _make_officer(db_session, status="ON_DUTY")
        availability.schedule_leave("OFF-1", ends_on=date.today() - timedelta(days=1), actor_id="U1")
        availability.auto_expire_leave()
        hist = availability.get_history("OFF-1")
        # last entry is the auto-return
        assert hist[-1].to_status == "ON_DUTY"
        assert hist[-1].actor_id == "SYSTEM"


# ── OfficerCapacityService ───────────────────────────────────────────────────

class TestCapacityService:

    def test_assignable_officer(self, db_session, capacity):
        _make_officer(db_session, max_capacity=10, cases=3)
        cd = capacity.get_capacity_details("OFF-1")
        assert cd.assignable
        assert cd.available_slots == 7
        assert cd.rejections == []

    def test_capacity_exceeded_rejection(self, db_session, capacity):
        _make_officer(db_session, max_capacity=5, cases=5)
        cd = capacity.get_capacity_details("OFF-1")
        assert not cd.assignable
        assert any(r.code == "CAPACITY_EXCEEDED" for r in cd.rejections)

    def test_unavailable_officer_rejected(self, db_session, capacity):
        _make_officer(db_session, status="LEAVE", max_capacity=10, cases=0)
        cd = capacity.get_capacity_details("OFF-1")
        assert not cd.assignable
        assert any(r.code == "UNAVAILABLE" for r in cd.rejections)

    def test_off_duty_rejected(self, db_session, capacity):
        _make_officer(db_session, status="OFF_DUTY", max_capacity=10)
        assert not capacity.can_assign_case("OFF-1")

    def test_field_officer_critical_only(self, db_session, capacity):
        _make_officer(db_session, status="FIELD", max_capacity=10, cases=0)
        assert not capacity.can_assign_case("OFF-1", priority=TaskPriority.MEDIUM)
        assert capacity.can_assign_case("OFF-1", priority=TaskPriority.CRITICAL)

    def test_missing_skill_rejection(self, db_session, repo, capacity):
        _make_officer(db_session, max_capacity=10)
        cd = capacity.get_capacity_details("OFF-1", required_skill=SkillCode.CYBER_FORENSICS)
        assert not cd.assignable
        assert any(r.code == "MISSING_SKILL" for r in cd.rejections)

    def test_present_skill_passes(self, db_session, repo, capacity):
        _make_officer(db_session, max_capacity=10)
        repo.add_skill("OFF-1", SkillCode.CYBER_FORENSICS)
        assert capacity.can_assign_case("OFF-1", required_skill=SkillCode.CYBER_FORENSICS)

    def test_expired_certification_rejection(self, db_session, repo, capacity):
        _make_officer(db_session, max_capacity=10)
        repo.add_certification("OFF-1", "Cyber", skill_code=SkillCode.CYBER_FORENSICS,
                               expiry_date=date.today() - timedelta(days=1))
        cd = capacity.get_capacity_details("OFF-1", required_cert_skill=SkillCode.CYBER_FORENSICS)
        assert not cd.assignable
        assert any(r.code == "MISSING_CERTIFICATION" for r in cd.rejections)

    def test_valid_certification_passes(self, db_session, repo, capacity):
        _make_officer(db_session, max_capacity=10)
        repo.add_certification("OFF-1", "Cyber", skill_code=SkillCode.CYBER_FORENSICS,
                               expiry_date=date.today() + timedelta(days=30))
        assert capacity.can_assign_case("OFF-1", required_cert_skill=SkillCode.CYBER_FORENSICS)

    def test_multiple_rejections_accumulate(self, db_session, capacity):
        _make_officer(db_session, status="LEAVE", max_capacity=5, cases=5)
        cd = capacity.get_capacity_details("OFF-1", required_skill=SkillCode.HOMICIDE)
        codes = {r.code for r in cd.rejections}
        assert "UNAVAILABLE" in codes
        assert "CAPACITY_EXCEEDED" in codes
        assert "MISSING_SKILL" in codes

    def test_missing_officer_raises(self, capacity):
        with pytest.raises(ValueError, match="not found"):
            capacity.get_capacity_details("NOPE")

    def test_utilization_calculation(self, db_session, capacity):
        _make_officer(db_session, max_capacity=10, cases=6)
        ws = capacity.get_workload_summary("OFF-1")
        assert ws.utilization == 0.6

    def test_burnout_low(self, db_session, capacity):
        _make_officer(db_session, max_capacity=10, cases=3)
        assert capacity.get_workload_summary("OFF-1").burnout_risk == BurnoutRisk.LOW.value

    def test_burnout_medium(self, db_session, capacity):
        _make_officer(db_session, max_capacity=10, cases=7)
        assert capacity.get_workload_summary("OFF-1").burnout_risk == BurnoutRisk.MEDIUM.value

    def test_burnout_high(self, db_session, capacity):
        _make_officer(db_session, max_capacity=10, cases=9)
        assert capacity.get_workload_summary("OFF-1").burnout_risk == BurnoutRisk.HIGH.value

    def test_burnout_critical(self, db_session, capacity):
        _make_officer(db_session, max_capacity=10, cases=10)
        assert capacity.get_workload_summary("OFF-1").burnout_risk == BurnoutRisk.CRITICAL.value

    def test_zero_capacity_utilization(self, db_session, capacity):
        _make_officer(db_session, max_capacity=0, cases=0)
        ws = capacity.get_workload_summary("OFF-1")
        assert ws.utilization == 0.0

    def test_list_capacity_violations(self, db_session, capacity):
        _make_officer(db_session, "OFF-1", max_capacity=5, cases=8)
        _make_officer(db_session, "OFF-2", max_capacity=5, cases=3)
        _make_officer(db_session, "OFF-3", max_capacity=10, cases=12)
        viols = {v.officer_id: v.over_by for v in capacity.list_capacity_violations()}
        assert viols == {"OFF-1": 3, "OFF-3": 2}


# ── ReconciliationService ────────────────────────────────────────────────────

class TestReconciliation:

    def _seed_cases(self, db_session, officer_id, n_open, n_closed=0):
        for i in range(n_open):
            db_session.add(FIR(fir_id=f"{officer_id}-OPEN-{i}",
                               investigating_officer_id=officer_id, status="Open"))
        for i in range(n_closed):
            db_session.add(FIR(fir_id=f"{officer_id}-CLOSED-{i}",
                               investigating_officer_id=officer_id, status="Closed"))
        db_session.flush()

    def test_reconcile_detects_case_drift(self, db_session, repo, reconciliation):
        _make_officer(db_session, cases=99, tasks=0)  # wildly wrong cache
        self._seed_cases(db_session, "OFF-1", n_open=3, n_closed=2)
        report = reconciliation.reconcile_officer_workload("OFF-1")
        assert report["mismatch_count"] == 1  # only cases drifted (tasks 0==0)
        assert repo.get_officer("OFF-1").current_case_count == 3

    def test_reconcile_corrects_task_drift(self, db_session, repo, reconciliation):
        _make_officer(db_session, cases=0, tasks=50)
        db_session.add(InvestigationTask(
            id="T1", investigation_id="INV-1", assigned_officer_id="OFF-1",
            status=TaskStatus.ACTIVE, title="t", category=TaskCategory.ANALYSIS,
            priority=TaskPriority.LOW))
        db_session.flush()
        report = reconciliation.reconcile_officer_workload("OFF-1")
        assert report["mismatch_count"] == 1
        assert repo.get_officer("OFF-1").current_task_count == 1

    def test_reconcile_no_drift_no_corrections(self, db_session, reconciliation):
        _make_officer(db_session, cases=0, tasks=0)
        report = reconciliation.reconcile_officer_workload("OFF-1")
        assert report["mismatch_count"] == 0
        assert report["corrections"] == []

    def test_reconcile_writes_audit_rows(self, db_session, reconciliation):
        _make_officer(db_session, cases=99, tasks=99)
        self._seed_cases(db_session, "OFF-1", n_open=1)
        reconciliation.reconcile_officer_workload("OFF-1")
        hist = reconciliation.get_reconciliation_history("OFF-1")
        assert len(hist) == 2  # both case and task counters drifted
        fields = {h.field for h in hist}
        assert fields == {"current_case_count", "current_task_count"}

    def test_reconcile_all_aggregates(self, db_session, reconciliation):
        _make_officer(db_session, "OFF-1", cases=99)
        _make_officer(db_session, "OFF-2", cases=0)  # correct
        self._seed_cases(db_session, "OFF-1", n_open=2)
        report = reconciliation.reconcile_all_workloads()
        assert report["officers_checked"] == 2
        assert report["officers_corrected"] == 1
        assert report["total_corrections"] == 1

    def test_reconcile_missing_officer_raises(self, reconciliation):
        with pytest.raises(ValueError, match="not found"):
            reconciliation.reconcile_officer_workload("NOPE")


# ── Performance / scale (Deliverable acceptance: 1000 officers) ───────────────

class TestScale:

    def test_capacity_violations_scale_1000_officers(self, db_session, capacity):
        import time
        for i in range(1000):
            _make_officer(db_session, f"OFF-{i}", max_capacity=5,
                          cases=(8 if i % 10 == 0 else 2))
        start = time.time()
        viols = capacity.list_capacity_violations()
        elapsed = time.time() - start
        assert len(viols) == 100  # every 10th officer is over
        assert elapsed < 0.5, f"violation scan took {elapsed}s"

    def test_reconcile_all_scale(self, db_session, reconciliation):
        for i in range(200):
            _make_officer(db_session, f"OFF-{i}", cases=0, tasks=0)
        report = reconciliation.reconcile_all_workloads()
        assert report["officers_checked"] == 200
        assert report["officers_corrected"] == 0


# ── Migration (Phase 8.2 M1) ─────────────────────────────────────────────────

class TestMigration:
    """Verify the standalone migration adds columns + tables and is idempotent."""

    def _legacy_engine(self):
        # A pre-Phase-8.2 officers table: only the original dataset columns.
        from sqlalchemy import create_engine, text
        eng = create_engine("sqlite:///:memory:")
        with eng.begin() as c:
            c.execute(text(
                "CREATE TABLE officers ("
                "officer_id VARCHAR PRIMARY KEY, name_en VARCHAR, "
                "tenure_years INTEGER, specialization VARCHAR);"
            ))
            c.execute(text(
                "INSERT INTO officers (officer_id, name_en, tenure_years) "
                "VALUES ('OFF-1','Alice',7);"
            ))
        return eng

    def test_migration_adds_columns_and_tables(self):
        from sqlalchemy import inspect
        from backend.db.migrate_phase_8_2 import migrate
        eng = self._legacy_engine()
        report = migrate(eng)
        cols = {c["name"] for c in inspect(eng).get_columns("officers")}
        for expected in ["subdivision", "years_experience", "maximum_capacity",
                         "availability_status", "current_case_count",
                         "current_task_count", "leave_ends_on", "capability_version"]:
            assert expected in cols
        tables = set(inspect(eng).get_table_names())
        for t in ["officer_skills", "officer_certifications", "officer_specializations",
                  "officer_availability_logs", "officer_workload_reconciliation",
                  "assignment_records"]:
            assert t in tables

    def test_migration_backfills_defaults(self):
        from sqlalchemy import text
        from backend.db.migrate_phase_8_2 import migrate
        eng = self._legacy_engine()
        migrate(eng)
        with eng.connect() as c:
            row = c.execute(text(
                "SELECT availability_status, maximum_capacity, current_case_count, "
                "years_experience FROM officers WHERE officer_id='OFF-1';"
            )).fetchone()
        assert row[0] == "ON_DUTY"
        assert row[1] == 10
        assert row[2] == 0
        assert row[3] == 7  # backfilled from tenure_years

    def test_migration_is_idempotent(self):
        from backend.db.migrate_phase_8_2 import migrate
        eng = self._legacy_engine()
        migrate(eng)
        report2 = migrate(eng)
        assert report2["columns_added"] == []
        assert len(report2["skipped"]) == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
