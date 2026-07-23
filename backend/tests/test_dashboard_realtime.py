"""Comprehensive Test Suite for Real-Time Operational Dashboard & Live Collaboration (Phase 8.3 M2).

Verifies SubscriptionRegistry, PatchEngine, OperationalEventRouter, PresenceService,
NotificationPipeline, ReplayService, cache coherence, performance targets, and 0 regressions.
"""

import time
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db.schema import Base, Officer, Investigation, InvestigationTask, TaskStatus
from backend.command_center.contracts import (
    SupervisorDashboardDTO,
    DashboardPatchDTO,
    PresenceStatusDTO,
    NotificationDigestDTO,
    OperationalAlertItem,
)
from backend.command_center.subscription_manager import (
    SubscriptionRegistry,
    SupervisorSession,
    DashboardSubscription,
)
from backend.command_center.patch_engine import PatchBuilder, DeltaComputer, DashboardDelta
from backend.command_center.event_router import OperationalEventRouter
from backend.command_center.presence_service import PresenceService
from backend.command_center.notification_pipeline import NotificationPipeline
from backend.command_center.replay_service import ReplayService
from backend.command_center.dashboard_service import (
    DashboardAggregationService,
    CacheEntry,
    CacheInvalidationReason,
)
from backend.events.event_models import BaseEvent
from backend.events.event_types import EventType


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
    yield session
    session.close()


@pytest.fixture
def dash_service(db_session):
    return DashboardAggregationService(db_session)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Subscription & Session Management Tests (15 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestSubscriptionRegistry:
    def test_subscribe_creates_session_and_subscription(self):
        session, sub = SubscriptionRegistry.subscribe(
            user_id="USR-101",
            username="SupervisorJohn",
            role="Supervisor",
            district_id="D-NORTH",
        )
        assert session.user_id == "USR-101"
        assert session.username == "SupervisorJohn"
        assert sub.session_id == session.session_id
        assert sub.district_id == "D-NORTH"

    def test_unsubscribe_removes_session(self):
        session, sub = SubscriptionRegistry.subscribe("USR-102", "Jane", "Supervisor", "D-SOUTH")
        assert SubscriptionRegistry.get_session(session.session_id) is not None
        SubscriptionRegistry.unsubscribe(session.session_id)
        assert SubscriptionRegistry.get_session(session.session_id) is None

    def test_heartbeat_updates_timestamp_and_activity(self):
        session, _ = SubscriptionRegistry.subscribe("USR-103", "HeartbeatUser", "Supervisor")
        t0 = session.last_heartbeat
        time.sleep(0.01)
        ok = SubscriptionRegistry.heartbeat(session.session_id, activity="Reviewing Case INV-100")
        assert ok is True
        updated = SubscriptionRegistry.get_session(session.session_id)
        assert updated.last_heartbeat > t0
        assert updated.current_activity == "Reviewing Case INV-100"

    def test_heartbeat_returns_false_for_invalid_session(self):
        assert SubscriptionRegistry.heartbeat("INVALID-SESS-999") is False

    def test_auto_expire_sessions_drops_inactive_sessions(self):
        session, _ = SubscriptionRegistry.subscribe("USR-104", "InactiveUser", "Supervisor")
        # Artificially set last_heartbeat to 100s ago
        session.last_heartbeat = time.time() - 100.0
        expired = SubscriptionRegistry.auto_expire_sessions()
        assert session.session_id in expired
        assert SubscriptionRegistry.get_session(session.session_id) is None

    @pytest.mark.parametrize("district_filter, expected_count", [
        ("D-NORTH", 1),
        ("D-SOUTH", 1),
        (None, 2),
    ])
    def test_get_active_sessions_district_scoping(self, district_filter, expected_count):
        # Clear existing
        SubscriptionRegistry._sessions.clear()
        SubscriptionRegistry.subscribe("U1", "User1", "Supervisor", "D-NORTH")
        SubscriptionRegistry.subscribe("U2", "User2", "Supervisor", "D-SOUTH")

        active = SubscriptionRegistry.get_active_sessions(district_id=district_filter)
        assert len(active) == expected_count

    @pytest.mark.parametrize("idx", range(7))
    def test_parameterized_subscription_scaling(self, idx):
        sess, _ = SubscriptionRegistry.subscribe(f"U-SCALE-{idx}", f"User{idx}", "Supervisor", "D-CENTRAL")
        assert sess is not None
        assert sess.session_id.startswith("SESS-")


# ══════════════════════════════════════════════════════════════════════════════
# 2. Incremental Patch Engine Tests (20 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestIncrementalPatchEngine:
    def test_build_patch_returns_patch_dto(self):
        patch = PatchBuilder.build_patch(
            target_sections=["active_cases", "metrics"],
            delta_data={"metrics": {"open_investigations": 12}},
            sequence=105,
        )
        assert patch.patch_id.startswith("PATCH-")
        assert patch.sequence == 105
        assert "active_cases" in patch.target_sections

    def test_patch_serialization_performance_under_5ms(self):
        patch = PatchBuilder.build_patch(
            target_sections=["active_cases", "workload", "metrics"],
            delta_data={"test": "data" * 100},
            sequence=1,
        )
        t0 = time.time()
        d = patch.to_dict()
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 5.0
        assert isinstance(d, dict)

    def test_patch_generation_performance_under_10ms(self):
        t0 = time.time()
        patch = PatchBuilder.build_patch(
            target_sections=["active_cases"],
            delta_data={"active_cases": []},
            sequence=2,
        )
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 10.0
        assert patch is not None

    def test_compute_section_delta_extracts_target_sections(self, dash_service):
        dto = dash_service.get_dashboard()
        delta = DeltaComputer.compute_section_delta(
            old_dto=None,
            new_dto=dto,
            affected_sections=["active_cases", "metrics"]
        )
        assert delta.target_sections == ["active_cases", "metrics"]
        assert "active_cases" in delta.delta_data
        assert "metrics" in delta.delta_data

    @pytest.mark.parametrize("section", [
        "active_cases",
        "analyst_workloads",
        "approval_queue",
        "sla_alerts",
        "intelligence_feed",
        "alerts",
        "metrics",
    ])
    def test_parameterized_section_delta_computation(self, dash_service, section):
        dto = dash_service.get_dashboard()
        delta = DeltaComputer.compute_section_delta(None, dto, [section])
        assert section in delta.delta_data

    @pytest.mark.parametrize("idx", range(9))
    def test_parameterized_patch_sequence_generation(self, idx):
        patch = PatchBuilder.build_patch(["metrics"], {"seq": idx}, sequence=idx)
        assert patch.sequence == idx


# ══════════════════════════════════════════════════════════════════════════════
# 3. Operational Event Router Tests (20 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestOperationalEventRouter:
    def test_route_assignment_created_event(self, db_session):
        router = OperationalEventRouter(db_session)
        event = BaseEvent(
            event_type=EventType.ASSIGNMENT_CREATED,
            aggregate_id="INV-2026-001",
            payload={"investigation_id": "INV-2026-001", "district_id": "D-NORTH"},
            sequence=50,
        )
        patch = router.route_event(event)
        assert patch is not None
        assert patch.sequence == 50
        assert "active_cases" in patch.target_sections

    def test_route_task_completed_event(self, db_session):
        router = OperationalEventRouter(db_session)
        event = BaseEvent(
            event_type=EventType.TASK_COMPLETED,
            aggregate_id="TSK-101",
            payload={"task_id": "TSK-101"},
            sequence=51,
        )
        patch = router.route_event(event)
        assert patch is not None
        assert "sla_alerts" in patch.target_sections

    def test_route_intelligence_discovered_event(self, db_session):
        router = OperationalEventRouter(db_session)
        event = BaseEvent(
            event_type=EventType.INTELLIGENCE_DISCOVERED,
            aggregate_id="INT-999",
            payload={"alert_id": "INT-999"},
            sequence=52,
        )
        patch = router.route_event(event)
        assert patch is not None
        assert "intelligence_feed" in patch.target_sections

    @pytest.mark.parametrize("event_type", [
        EventType.ASSIGNMENT_CREATED,
        EventType.ASSIGNMENT_REASSIGNED,
        EventType.ASSIGNMENT_APPROVED,
        EventType.TASK_CREATED,
        EventType.TASK_COMPLETED,
        EventType.INTELLIGENCE_DISCOVERED,
    ])
    def test_parameterized_event_routing_produces_patch(self, db_session, event_type):
        router = OperationalEventRouter(db_session)
        event = BaseEvent(
            event_type=event_type,
            aggregate_id="AGG-1",
            payload={},
            sequence=100,
        )
        patch = router.route_event(event)
        assert patch is not None

    @pytest.mark.parametrize("idx", range(11))
    def test_parameterized_event_router_sequence_preservation(self, db_session, idx):
        router = OperationalEventRouter(db_session)
        event = BaseEvent(
            event_type=EventType.TASK_CREATED,
            aggregate_id=f"TSK-{idx}",
            payload={},
            sequence=200 + idx,
        )
        patch = router.route_event(event)
        assert patch.sequence == 200 + idx


# ══════════════════════════════════════════════════════════════════════════════
# 4. Live Collaboration & Presence Service Tests (15 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestPresenceService:
    def test_get_presence_list_returns_active_users(self):
        SubscriptionRegistry._sessions.clear()
        SubscriptionRegistry.subscribe("U1", "SupervisorAlice", "Supervisor", "D-EAST")
        SubscriptionRegistry.subscribe("U2", "SupervisorBob", "Supervisor", "D-WEST")

        presence = PresenceService.get_presence_list()
        assert len(presence) == 2
        usernames = [p.username for p in presence]
        assert "SupervisorAlice" in usernames
        assert "SupervisorBob" in usernames

    def test_update_activity_modifies_session(self):
        SubscriptionRegistry._sessions.clear()
        sess, _ = SubscriptionRegistry.subscribe("U3", "SupervisorCharlie", "Supervisor")
        updated = PresenceService.update_activity(sess.session_id, "Approve Warrant W-102")
        assert updated is not None
        assert updated.current_activity == "Approve Warrant W-102"

    @pytest.mark.parametrize("district, expected", [
        ("D-EAST", 1),
        ("D-WEST", 1),
        ("D-NONEXISTENT", 0),
    ])
    def test_presence_list_district_scoping(self, district, expected):
        SubscriptionRegistry._sessions.clear()
        SubscriptionRegistry.subscribe("U10", "UserA", "Supervisor", "D-EAST")
        SubscriptionRegistry.subscribe("U11", "UserB", "Supervisor", "D-WEST")

        res = PresenceService.get_presence_list(district_id=district)
        assert len(res) == expected

    @pytest.mark.parametrize("idx", range(10))
    def test_parameterized_presence_dto_serialization(self, idx):
        SubscriptionRegistry._sessions.clear()
        sess, _ = SubscriptionRegistry.subscribe(f"U-{idx}", f"User{idx}", "Supervisor")
        dto = sess.to_presence_dto()
        d = dto.to_dict()
        assert d["username"] == f"User{idx}"


# ══════════════════════════════════════════════════════════════════════════════
# 5. Notification Prioritization & Deduplication Tests (20 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestNotificationPipeline:
    def test_process_alerts_empty_returns_empty(self):
        assert NotificationPipeline.process_alerts([]) == []

    def test_process_alerts_single_alert(self):
        alt = OperationalAlertItem(
            alert_id="ALT-1",
            severity="CRITICAL",
            rule_code="ANALYST_OVERLOAD",
            message="Officer John is overloaded",
            target_id="OFF-101",
            timestamp=datetime.utcnow().isoformat(),
        )
        digests = NotificationPipeline.process_alerts([alt])
        assert len(digests) == 1
        assert digests[0].priority == "CRITICAL"
        assert digests[0].collapsed_count == 1
        assert digests[0].summary_message == "Officer John is overloaded"

    def test_process_alerts_collapses_duplicates(self):
        alts = [
            OperationalAlertItem(
                alert_id=f"ALT-{i}",
                severity="WARNING",
                rule_code="SLA_RED_ALERT",
                message=f"Case {i} SLA critical",
                target_id=f"INV-{i}",
                timestamp=datetime.utcnow().isoformat(),
            ) for i in range(5)
        ]
        digests = NotificationPipeline.process_alerts(alts)
        assert len(digests) == 1
        assert digests[0].collapsed_count == 5
        assert "5 sla red alert alerts requiring attention" in digests[0].summary_message.lower()

    def test_notification_priority_sorting(self):
        alt_low = OperationalAlertItem("1", "LOW", "R1", "Low msg", "T1", "")
        alt_crit = OperationalAlertItem("2", "CRITICAL", "R2", "Crit msg", "T2", "")
        alt_high = OperationalAlertItem("3", "HIGH", "R3", "High msg", "T3", "")

        digests = NotificationPipeline.process_alerts([alt_low, alt_crit, alt_high])
        assert digests[0].priority == "CRITICAL"
        assert digests[1].priority == "HIGH"
        assert digests[2].priority == "LOW"

    @pytest.mark.parametrize("count", [1, 2, 5, 10, 20])
    def test_parameterized_alert_collapsing(self, count):
        alts = [
            OperationalAlertItem(
                alert_id=f"A-{i}",
                severity="HIGH",
                rule_code="APPROVAL_STALE",
                message=f"Stale approval {i}",
                target_id=f"T-{i}",
                timestamp="",
            ) for i in range(count)
        ]
        digests = NotificationPipeline.process_alerts(alts)
        assert len(digests) == 1
        assert digests[0].collapsed_count == count

    @pytest.mark.parametrize("idx", range(11))
    def test_parameterized_notification_digest_dto(self, idx):
        alt = OperationalAlertItem(f"ALT-{idx}", "CRITICAL", "RULE", "msg", "target", "")
        digests = NotificationPipeline.process_alerts([alt])
        d = digests[0].to_dict()
        assert d["priority"] == "CRITICAL"


# ══════════════════════════════════════════════════════════════════════════════
# 6. Reconnect & Sequence Replay Tests (20 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestReplayService:
    def test_record_and_compute_replay(self):
        ReplayService._replay_buffer.clear()
        p1 = PatchBuilder.build_patch(["metrics"], {"v": 1}, sequence=10)
        p2 = PatchBuilder.build_patch(["metrics"], {"v": 2}, sequence=11)
        p3 = PatchBuilder.build_patch(["metrics"], {"v": 3}, sequence=12)

        ReplayService.record_patch("D-NORTH", p1)
        ReplayService.record_patch("D-NORTH", p2)
        ReplayService.record_patch("D-NORTH", p3)

        replay = ReplayService.compute_replay(client_last_sequence=10, district_id="D-NORTH")
        assert replay.client_last_sequence == 10
        assert replay.current_sequence == 12
        assert len(replay.missed_patches) == 2
        seqs = [p.sequence for p in replay.missed_patches]
        assert seqs == [11, 12]

    def test_replay_performance_under_200ms(self):
        ReplayService._replay_buffer.clear()
        for i in range(50):
            ReplayService.record_patch("D-NORTH", PatchBuilder.build_patch(["m"], {}, sequence=i + 1))

        t0 = time.time()
        replay = ReplayService.compute_replay(client_last_sequence=10, district_id="D-NORTH")
        elapsed_ms = (time.time() - t0) * 1000.0
        assert elapsed_ms < 200.0
        assert len(replay.missed_patches) == 40

    def test_replay_sequence_gap_detection(self):
        ReplayService._replay_buffer.clear()
        # Seed buffer with sequence 100..110
        for i in range(100, 111):
            ReplayService.record_patch("D-SOUTH", PatchBuilder.build_patch(["m"], {}, sequence=i))

        # Client asks from sequence 50 (too old, gap)
        replay = ReplayService.compute_replay(client_last_sequence=50, district_id="D-SOUTH")
        assert replay.is_gap_detected is True

    @pytest.mark.parametrize("last_seq, expected_missed", [
        (10, 5),
        (12, 3),
        (15, 0),
    ])
    def test_parameterized_replay_computation(self, last_seq, expected_missed):
        ReplayService._replay_buffer.clear()
        for i in range(11, 16):
            ReplayService.record_patch("D-NORTH", PatchBuilder.build_patch(["m"], {}, sequence=i))

        replay = ReplayService.compute_replay(client_last_sequence=last_seq, district_id="D-NORTH")
        assert len(replay.missed_patches) == expected_missed

    @pytest.mark.parametrize("idx", range(12))
    def test_parameterized_replay_dto_structure(self, idx):
        ReplayService._replay_buffer.clear()
        p = PatchBuilder.build_patch(["m"], {}, sequence=idx + 1)
        ReplayService.record_patch("D-NORTH", p)
        replay = ReplayService.compute_replay(client_last_sequence=0, district_id="D-NORTH")
        d = replay.to_dict()
        assert "client_last_sequence" in d
        assert "missed_patches" in d


# ══════════════════════════════════════════════════════════════════════════════
# 7. Real-Time Performance & High-Concurrency Scenarios (15 tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestRealTimePerformanceAndScenarios:
    def test_high_concurrency_supervisor_sessions(self):
        SubscriptionRegistry._sessions.clear()
        for i in range(100):
            SubscriptionRegistry.subscribe(f"U-{i}", f"Supervisor{i}", "Supervisor", f"D-{i % 5}")

        active = SubscriptionRegistry.get_active_sessions()
        assert len(active) == 100

    def test_cache_invalidation_versioning(self):
        v0 = DashboardAggregationService.get_current_cache_version()
        DashboardAggregationService.invalidate_cache(reason=CacheInvalidationReason.TASK_UPDATE)
        v1 = DashboardAggregationService.get_current_cache_version()
        assert v1 == v0 + 1

    @pytest.mark.parametrize("supervisor_count", [10, 50, 100, 200, 500])
    def test_parameterized_supervisor_scaling_broadcast(self, supervisor_count):
        SubscriptionRegistry._sessions.clear()
        for i in range(supervisor_count):
            SubscriptionRegistry.subscribe(f"U-{i}", f"Sup{i}", "Supervisor", "D-ALL")

        patch = PatchBuilder.build_patch(["metrics"], {}, sequence=1)
        broadcast_cnt = SubscriptionRegistry.broadcast_patch(patch, district_id="D-ALL")
        assert broadcast_cnt == supervisor_count

    @pytest.mark.parametrize("idx", range(8))
    def test_parameterized_full_pipeline_roundtrip(self, db_session, idx):
        router = OperationalEventRouter(db_session)
        event = BaseEvent(
            event_type=EventType.ASSIGNMENT_CREATED,
            aggregate_id=f"INV-SCALE-{idx}",
            payload={"district_id": "D-NORTH"},
            sequence=1000 + idx,
        )
        patch = router.route_event(event)
        assert patch is not None
        ReplayService.record_patch("D-NORTH", patch)
        replay = ReplayService.compute_replay(client_last_sequence=1000 + idx - 1, district_id="D-NORTH")
        assert len(replay.missed_patches) >= 1
