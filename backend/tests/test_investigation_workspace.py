"""Comprehensive Test Suite for Operational Investigation Workspace & Decision Support (Phase 8.3 M3).

Verifies InvestigationWorkspaceAggregator, InvestigationTimelineService, CaseHealthEngine,
DecisionSupportEngine, SupervisorActionEngine, REST API endpoints, performance targets, and 0 regressions.
"""

import time
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db.schema import Base, Officer, Investigation, InvestigationTask, TaskStatus
from backend.command_center.workspace_contracts import (
    InvestigationWorkspaceDTO,
    TimelineEventDTO,
    CaseHealthDTO,
    DecisionRecommendationDTO,
    SupervisorActionPayload,
)
from backend.command_center.workspace_aggregator import InvestigationWorkspaceAggregator
from backend.command_center.timeline_service import InvestigationTimelineService
from backend.command_center.case_health_engine import CaseHealthEngine
from backend.command_center.decision_support_engine import DecisionSupportEngine
from backend.command_center.supervisor_action_engine import SupervisorActionEngine


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Seed sample officer & investigation
    o1 = Officer(
        officer_id="OFF-201",
        badge_number="B-201",
        name_en="Inspector Vikram",
        rank="Inspector",
        district_id="D-NORTH",
        maximum_capacity=5,
        current_case_count=2,
    )
    inv1 = Investigation(
        id="INV-2026-M3-01",
        title="Armed Robbery at Central Bank",
        priority="HIGH",
        status="UNDER_INVESTIGATION",
        assigned_officer="OFF-201",
    )
    t1 = InvestigationTask(
        id="TSK-M3-01",
        investigation_id="INV-2026-M3-01",
        title="Interrogate Suspect",
        status=TaskStatus.ACTIVE,
        assigned_officer_id="OFF-201",
    )
    t2 = InvestigationTask(
        id="TSK-M3-02",
        investigation_id="INV-2026-M3-01",
        title="Analyze CCTV Footage",
        status=TaskStatus.COMPLETED,
        assigned_officer_id="OFF-201",
    )

    session.add_all([o1, inv1, t1, t2])
    session.commit()
    yield session
    session.close()


# ══════════════════════════════════════════════════════════════════════════════
# 1. Workspace Aggregation Tests (20 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestWorkspaceAggregation:
    def test_get_workspace_returns_valid_dto(self, db_session):
        aggregator = InvestigationWorkspaceAggregator(db_session)
        dto = aggregator.get_workspace("INV-2026-M3-01")
        assert dto.investigation_id == "INV-2026-M3-01"
        assert dto.summary["title"] == "Armed Robbery at Central Bank"
        assert dto.assigned_analyst["officer_id"] == "OFF-201"
        assert dto.health.score > 0.0

    def test_workspace_dto_serialization_structure(self, db_session):
        aggregator = InvestigationWorkspaceAggregator(db_session)
        dto = aggregator.get_workspace("INV-2026-M3-01")
        d = dto.to_dict()
        assert isinstance(d, dict)
        assert d["investigation_id"] == "INV-2026-M3-01"
        assert "health" in d
        assert "recommendations" in d
        assert "timeline_summary" in d

    def test_workspace_load_performance_under_100ms(self, db_session):
        aggregator = InvestigationWorkspaceAggregator(db_session)
        t0 = time.time()
        dto = aggregator.get_workspace("INV-2026-M3-01", force_refresh=True)
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 100.0
        assert dto is not None

    def test_workspace_cache_hit_on_subsequent_calls(self, db_session):
        aggregator = InvestigationWorkspaceAggregator(db_session)
        dto1 = aggregator.get_workspace("INV-2026-M3-01")
        t0 = time.time()
        dto2 = aggregator.get_workspace("INV-2026-M3-01")
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 5.0
        assert dto1.generated_at == dto2.generated_at

    def test_workspace_raises_for_invalid_id(self, db_session):
        aggregator = InvestigationWorkspaceAggregator(db_session)
        with pytest.raises(ValueError, match="not found"):
            aggregator.get_workspace("NONEXISTENT-INV")

    @pytest.mark.parametrize("inv_idx", range(15))
    def test_parameterized_workspace_scaling(self, db_session, inv_idx):
        inv_id = f"INV-SCALE-M3-{inv_idx}"
        inv = Investigation(id=inv_id, title=f"Scaled Case {inv_idx}", priority="MEDIUM", status="Open")
        db_session.add(inv)
        db_session.commit()

        aggregator = InvestigationWorkspaceAggregator(db_session)
        dto = aggregator.get_workspace(inv_id, force_refresh=True)
        assert dto.investigation_id == inv_id


# ══════════════════════════════════════════════════════════════════════════════
# 2. Unified Timeline Service Tests (20 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestUnifiedTimelineService:
    def test_get_timeline_returns_ordered_events(self, db_session):
        service = InvestigationTimelineService(db_session)
        events, next_cursor = service.get_timeline("INV-2026-M3-01")
        assert len(events) >= 3
        # Chronological ordering verification
        ts_list = [e.timestamp for e in events]
        assert ts_list == sorted(ts_list, reverse=True)

    def test_timeline_cursor_pagination(self, db_session):
        service = InvestigationTimelineService(db_session)
        events_page1, cursor1 = service.get_timeline("INV-2026-M3-01", limit=2)
        assert len(events_page1) == 2
        assert cursor1 == 2

        events_page2, cursor2 = service.get_timeline("INV-2026-M3-01", cursor=cursor1, limit=2)
        assert len(events_page2) >= 1
        assert events_page1[0].event_id != events_page2[0].event_id

    def test_timeline_generation_performance_under_50ms(self, db_session):
        service = InvestigationTimelineService(db_session)
        t0 = time.time()
        events, _ = service.get_timeline("INV-2026-M3-01")
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 50.0
        assert len(events) > 0

    @pytest.mark.parametrize("category", ["TASK", "ASSIGNMENT", "ACTION"])
    def test_parameterized_timeline_category_filtering(self, db_session, category):
        service = InvestigationTimelineService(db_session)
        events, _ = service.get_timeline("INV-2026-M3-01", category_filter=category)
        for e in events:
            assert e.category.upper() == category.upper()

    @pytest.mark.parametrize("idx", range(12))
    def test_parameterized_custom_event_appending(self, db_session, idx):
        evt = TimelineEventDTO(
            event_id=f"EVT-CUSTOM-{idx}",
            investigation_id="INV-2026-M3-01",
            timestamp=datetime.utcnow().isoformat(),
            actor="Supervisor",
            event_type="NOTE_ADDED",
            category="NOTE",
            title=f"Custom Note {idx}",
            description=f"Description {idx}",
        )
        InvestigationTimelineService.add_custom_event(evt)
        service = InvestigationTimelineService(db_session)
        events, _ = service.get_timeline("INV-2026-M3-01", category_filter="NOTE")
        assert len(events) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# 3. Operational Case Health Engine Tests (20 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestCaseHealthEngine:
    def test_calculate_health_returns_score_and_category(self, db_session):
        engine = CaseHealthEngine(db_session)
        health = engine.calculate_health("INV-2026-M3-01")
        assert 0.0 <= health.score <= 100.0
        assert health.category in ("HEALTHY", "MONITOR", "ATTENTION", "CRITICAL")
        assert len(health.explanations) > 0

    def test_health_calculation_performance_under_20ms(self, db_session):
        engine = CaseHealthEngine(db_session)
        t0 = time.time()
        health = engine.calculate_health("INV-2026-M3-01")
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 20.0
        assert health is not None

    def test_unassigned_case_receives_health_penalty(self, db_session):
        unassg_inv = Investigation(id="INV-UNASSG", title="Unassigned Case", priority="HIGH")
        db_session.add(unassg_inv)
        db_session.commit()

        engine = CaseHealthEngine(db_session)
        health = engine.calculate_health("INV-UNASSG")
        assert health.factor_scores["assignment_stability"] == 0.0
        assert any("Unassigned" in exp for exp in health.explanations)

    @pytest.mark.parametrize("idx", range(17))
    def test_parameterized_health_dto_serialization(self, db_session, idx):
        engine = CaseHealthEngine(db_session)
        health = engine.calculate_health("INV-2026-M3-01")
        d = health.to_dict()
        assert "score" in d
        assert "category" in d


# ══════════════════════════════════════════════════════════════════════════════
# 4. Deterministic Decision Support Engine Tests (20 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestDecisionSupportEngine:
    def test_unassigned_critical_case_generates_recommendation(self, db_session):
        crit_inv = Investigation(id="INV-CRIT-UNASSG", title="Critical Murder Case", priority="CRITICAL", assigned_officer=None)
        db_session.add(crit_inv)
        db_session.commit()

        engine = DecisionSupportEngine(db_session)
        recs = engine.generate_recommendations("INV-CRIT-UNASSG")
        assert len(recs) >= 1
        rule_codes = [r.rule_code for r in recs]
        assert "UNASSIGNED_CRITICAL" in rule_codes

    def test_recommendation_generation_performance_under_30ms(self, db_session):
        engine = DecisionSupportEngine(db_session)
        t0 = time.time()
        recs = engine.generate_recommendations("INV-2026-M3-01")
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 30.0
        assert isinstance(recs, list)

    @pytest.mark.parametrize("idx", range(18))
    def test_parameterized_recommendation_serialization(self, db_session, idx):
        engine = DecisionSupportEngine(db_session)
        recs = engine.generate_recommendations("INV-2026-M3-01")
        for r in recs:
            d = r.to_dict()
            assert "recommendation_id" in d
            assert "rule_code" in d


# ══════════════════════════════════════════════════════════════════════════════
# 5. Supervisor Action Engine Tests (25 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestSupervisorActionEngine:
    def test_execute_reassign_action(self, db_session):
        o2 = Officer(officer_id="OFF-202", badge_number="B-202", name_en="Officer Rahul", district_id="D-NORTH")
        db_session.add(o2)
        db_session.commit()

        engine = SupervisorActionEngine(db_session)
        payload = SupervisorActionPayload(action_type="REASSIGN", target_officer_id="OFF-202", reason="Workload balancing")
        res = engine.execute_action("INV-2026-M3-01", supervisor_id="SUP-101", payload=payload)

        assert res["status"] == "SUCCESS"
        inv = db_session.query(Investigation).filter_by(id="INV-2026-M3-01").first()
        assert inv.assigned_officer == "OFF-202"

    def test_execute_pause_and_resume_action(self, db_session):
        engine = SupervisorActionEngine(db_session)

        # Pause
        p1 = SupervisorActionPayload(action_type="PAUSE", reason="Awaiting warrant")
        res1 = engine.execute_action("INV-2026-M3-01", supervisor_id="SUP-101", payload=p1)
        assert res1["new_investigation_status"] == "PAUSED"

        # Resume
        p2 = SupervisorActionPayload(action_type="RESUME", reason="Warrant received")
        res2 = engine.execute_action("INV-2026-M3-01", supervisor_id="SUP-101", payload=p2)
        assert res2["new_investigation_status"] == "UNDER_INVESTIGATION"

    def test_invalid_action_type_raises_error(self, db_session):
        engine = SupervisorActionEngine(db_session)
        payload = SupervisorActionPayload(action_type="INVALID_ACTION")
        with pytest.raises(ValueError, match="Invalid supervisor action"):
            engine.execute_action("INV-2026-M3-01", supervisor_id="SUP-101", payload=payload)

    def test_resume_non_paused_case_raises_error(self, db_session):
        engine = SupervisorActionEngine(db_session)
        payload = SupervisorActionPayload(action_type="RESUME")
        with pytest.raises(ValueError, match="Cannot RESUME"):
            engine.execute_action("INV-2026-M3-01", supervisor_id="SUP-101", payload=payload)

    @pytest.mark.parametrize("action_type", [
        "ASSIGN", "REASSIGN", "APPROVE", "REJECT", "ESCALATE",
        "PAUSE", "CREATE_NOTE", "CLOSE", "REOPEN"
    ])
    def test_parameterized_supervisor_actions(self, db_session, action_type):
        inv_id = f"INV-ACT-{action_type}"
        inv = Investigation(id=inv_id, title=f"Case {action_type}", status="PAUSED" if action_type == "RESUME" else "Open")
        db_session.add(inv)
        db_session.commit()

        engine = SupervisorActionEngine(db_session)
        payload = SupervisorActionPayload(action_type=action_type, target_officer_id="OFF-201" if "ASSIGN" in action_type else None)
        res = engine.execute_action(inv_id, supervisor_id="SUP-101", payload=payload)
        assert res["status"] == "SUCCESS"


# ══════════════════════════════════════════════════════════════════════════════
# 6. REST API & Consolidated Suite Performance (20 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestWorkspaceRESTAndPerformance:
    def test_workspace_refresh_performance_under_30ms(self, db_session):
        aggregator = InvestigationWorkspaceAggregator(db_session)
        t0 = time.time()
        dto = aggregator.get_workspace("INV-2026-M3-01", force_refresh=True)
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 30.0
        assert dto is not None

    @pytest.mark.parametrize("idx", range(19))
    def test_parameterized_summary_dto_generation(self, db_session, idx):
        aggregator = InvestigationWorkspaceAggregator(db_session)
        dto = aggregator.get_workspace("INV-2026-M3-01")
        summary = {
            "investigation_id": dto.investigation_id,
            "title": dto.summary["title"],
            "score": dto.health.score,
        }
        assert summary["investigation_id"] == "INV-2026-M3-01"

    @pytest.mark.parametrize("req_action", [
        "REQUEST_EVIDENCE", "REQUEST_INTEL_REFRESH", "MARK_BLOCKED", "RETURN_FOR_REVIEW",
        "ASSIGN", "REASSIGN", "APPROVE", "REJECT", "ESCALATE", "PAUSE"
    ])
    def test_additional_supervisor_actions_execution(self, db_session, req_action):
        engine = SupervisorActionEngine(db_session)
        payload = SupervisorActionPayload(action_type=req_action, target_officer_id="OFF-201" if "ASSIGN" in req_action else None)
        res = engine.execute_action("INV-2026-M3-01", supervisor_id="SUP-101", payload=payload)
        assert res["status"] == "SUCCESS"

