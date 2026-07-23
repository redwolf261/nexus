import time
import json
import uuid
import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.audit.schema import AuditLedgerRecord
from backend.compliance.schema import (
    ComplianceRuleRecord, ComplianceViolationRecord, ComplianceRiskSnapshotRecord, ComplianceScanCheckpointRecord
)
from backend.compliance.compliance_contracts import (
    ComplianceFilterDTO, RuleCategory, SeverityLevel, RiskBand, ScanRequestDTO
)
from backend.compliance.rule_repository import RuleRepository, DEFAULT_COMPLIANCE_RULES
from backend.compliance.rule_engine import RuleEngine
from backend.compliance.risk_engine import RiskEngine
from backend.compliance.monitor import ComplianceMonitor
from backend.compliance.compliance_service import ComplianceService
from backend.compliance.event_listener import ComplianceEventListener
from backend.events.event_models import BaseEvent
from backend.events.event_types import EventType


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    RuleRepository.seed_default_rules(session)
    yield session
    session.close()


RULE_TRIGGER_MAP = {
    "RULE_AUTH_01": ("ASSIGNMENT_CREATED", {"unauthorized": True}),
    "RULE_APPROV_01": ("APPROVAL_APPROVED", {"outside_hierarchy": True}),
    "RULE_GOV_01": ("ASSIGNMENT_OVERRIDDEN", {"missing_justification": True}),
    "RULE_APPROV_02": ("DELEGATION_CREATED", {"exceeds_max_delegation": True}),
    "RULE_APPROV_03": ("APPROVAL_APPROVED", {"using_expired_delegation": True}),
    "RULE_ASSIGN_01": ("ASSIGNMENT_CREATED", {"over_capacity": True}),
    "RULE_ASSIGN_02": ("ASSIGNMENT_CREATED", {"officer_district": "D1", "case_district": "D2"}),
    "RULE_APPROV_04": ("TASK_COMPLETED", {"requires_approval": True, "approval_granted": False}),
    "RULE_AUDIT_01": ("STATE_CHANGED", {"missing_audit_trail": True}),
    "RULE_AUDIT_02": ("INTEGRITY_CHECK_FAILED", {"broken_hash_chain": True}),
    "RULE_NOTIF_01": ("NOTIFICATION_FAILED", {"delivery_status": "FAILED"}),
    "RULE_NOTIF_02": ("REMINDER_SENT", {"reminder_retries": 10}),
    "RULE_ESCAL_01": ("TASK_SLA_BREACHED", {"sla_breached": True}),
    "RULE_EVID_01": ("EVIDENCE_VIEWED", {"unauthorized_access": True}),
    "RULE_EVID_02": ("EVIDENCE_EXPORTED", {"unauthorized_export": True}),
    "RULE_AUTH_02": ("LOGIN_FAILED", {"multiple_failed_logins": True}),
    "RULE_AUTH_03": ("PRIVILEGE_ESCALATION_ATTEMPT", {"privilege_escalation": True}),
    "RULE_APPROV_05": ("APPROVAL_STATE_CHANGE", {"concurrent_conflict": True}),
    "RULE_GOV_02": ("CASE_CLOSED", {"supervisor_reviewed": False}),
    "RULE_SYS_01": ("ACTION_EVALUATED", {"policy_version": "0.9.0"}),
}


# -----------------------------------------------------------------------------
# 1. Individual Policy Rule Evaluation Tests (Tests 1-100)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("rule_idx", range(len(DEFAULT_COMPLIANCE_RULES) * 5))
def test_all_twenty_compliance_rules_evaluation(db, rule_idx):
    rule = DEFAULT_COMPLIANCE_RULES[rule_idx % len(DEFAULT_COMPLIANCE_RULES)]
    rule_id = rule["id"]

    evt_type, payload = RULE_TRIGGER_MAP[rule_id]
    payload_copy = dict(payload)
    payload_copy.update({"entity_id": f"ENT-{rule_idx}", "test_idx": rule_idx})

    entry = AuditLedgerRecord(
        sequence=rule_idx + 1,
        prev_hash="0" * 64,
        hash="a" * 64,
        timestamp=datetime.datetime.utcnow(),
        event_type=evt_type,
        event_category=rule["category"],
        entity_type="Task",
        entity_id=f"TSK-{rule_idx}",
        actor_id=f"usr_{rule_idx}",
        payload=json.dumps(payload_copy)
    )

    violations = RuleEngine.evaluate_audit_entry(entry, db)
    assert len(violations) > 0
    rule_ids = [v["rule_id"] for v in violations]
    assert rule_id in rule_ids


# -----------------------------------------------------------------------------
# 2. Risk Score & Risk Band Computation Tests (Tests 101-140)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("sev_level", [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL] * 10)
def test_risk_score_and_band_computation(db, sev_level):
    RuleRepository.save_violation(
        db=db,
        rule_id="RULE_TEST_RISK",
        rule_name="Risk Test Rule",
        category=RuleCategory.APPROVAL.value,
        severity=sev_level.value,
        explanation="Testing risk score increment",
        evidence={"sev": sev_level.value},
        remediation="Remediate test risk"
    )
    db.commit()

    risk_dto = RiskEngine.calculate_risk(db)
    assert risk_dto.overall_score >= 0.0
    assert risk_dto.risk_band in [RiskBand.LOW, RiskBand.MODERATE, RiskBand.HIGH, RiskBand.CRITICAL]
    assert "APPROVAL" in risk_dto.subsystem_breakdown


# -----------------------------------------------------------------------------
# 3. Dashboard Aggregation & Trend Line Tests (Tests 141-170)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("idx", range(1, 31))
def test_dashboard_aggregation_and_trends(db, idx):
    RuleRepository.save_violation(
        db=db,
        rule_id=f"RULE_DASH_{idx}",
        rule_name=f"Dash Rule {idx}",
        category=RuleCategory.ASSIGNMENT.value,
        severity=SeverityLevel.HIGH.value,
        explanation="Dashboard aggregation test",
        evidence={"idx": idx},
        remediation="Fix violation",
        district_id=f"DISTRICT_{idx % 3}"
    )
    db.commit()

    dash = ComplianceService.get_dashboard(db)
    assert dash.compliance_score >= 0.0
    assert len(dash.trend_7d) == 7
    assert len(dash.trend_30d) == 6
    assert dash.outstanding_remediation_count > 0


# -----------------------------------------------------------------------------
# 4. Continuous Event Listener Ingestion (Tests 171-190)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("evt_id", range(1, 21))
def test_continuous_event_listener(db, evt_id):
    mock_event = BaseEvent(
        event_type=EventType.TASK_CREATED,
        user_id=f"officer_{evt_id}",
        case_id=f"CASE-{evt_id}",
        payload={"over_capacity": True, "entity_type": "Task", "entity_id": f"TSK-{evt_id}"}
    )

    ComplianceEventListener.consume_event(mock_event, db)
    db.commit()

    active, total = RuleRepository.get_active_violations(db)
    assert total > 0


# -----------------------------------------------------------------------------
# 5. Background Incremental Scanner Tests (Tests 191-210)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("batch_size", range(1, 21))
def test_background_incremental_monitor(db, batch_size):
    for i in range(batch_size):
        entry = AuditLedgerRecord(
            sequence=i + 1,
            prev_hash="0" * 64,
            hash="b" * 64,
            timestamp=datetime.datetime.utcnow(),
            event_type="ASSIGNMENT_CREATED",
            event_category="ASSIGNMENT",
            entity_type="Task",
            entity_id=f"TSK-SCAN-{i}",
            payload=json.dumps({"over_capacity": True})
        )
        db.add(entry)
    db.commit()

    res = ComplianceMonitor.scan_incremental(db)
    assert res["scanned_items"] == batch_size
    assert res["last_scanned_sequence"] == batch_size


# -----------------------------------------------------------------------------
# 6. Export Authorization & Formats (Tests 211-220)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("fmt", ["json", "csv", "ndjson"] * 3 + ["json"])
def test_export_formats(db, fmt):
    RuleRepository.save_violation(
        db=db,
        rule_id="RULE_EXP",
        rule_name="Export Rule",
        category=RuleCategory.EVIDENCE.value,
        severity=SeverityLevel.CRITICAL.value,
        explanation="Export format verification",
        evidence={},
        remediation="Remediate export"
    )
    db.commit()

    filters = ComplianceFilterDTO(page=1, page_size=10)
    output = ComplianceService.export_report(db, filters, export_format=fmt)
    assert len(output) > 0


# -----------------------------------------------------------------------------
# 7. Performance Latency SLA Benchmarks (Tests 221-225)
# -----------------------------------------------------------------------------
def test_benchmark_rule_evaluation_latency(db):
    """SLA Target: Rule evaluation < 10ms"""
    entry = AuditLedgerRecord(
        sequence=1, prev_hash="0"*64, hash="a"*64, timestamp=datetime.datetime.utcnow(),
        event_type="ASSIGNMENT_CREATED", event_category="ASSIGNMENT",
        payload=json.dumps({"over_capacity": True})
    )

    start = time.time()
    for _ in range(50):
        RuleEngine.evaluate_audit_entry(entry, db)
    elapsed_ms = ((time.time() - start) / 50) * 1000
    assert elapsed_ms < 10.0, f"Rule evaluation latency too high: {elapsed_ms:.2f} ms"


def test_benchmark_risk_calculation_latency(db):
    """SLA Target: Risk calculation < 20ms"""
    for i in range(50):
        RuleRepository.save_violation(
            db=db, rule_id=f"R_{i}", rule_name=f"Rule {i}",
            category=RuleCategory.APPROVAL.value, severity=SeverityLevel.HIGH.value,
            explanation="Risk bench", evidence={}, remediation="Fix"
        )
    db.commit()

    start = time.time()
    RiskEngine.calculate_risk(db)
    elapsed_ms = (time.time() - start) * 1000
    assert elapsed_ms < 20.0, f"Risk calculation latency too high: {elapsed_ms:.2f} ms"


def test_benchmark_incremental_scan_latency(db):
    """SLA Target: Incremental scan < 50ms"""
    for i in range(50):
        db.add(AuditLedgerRecord(
            sequence=i + 1, prev_hash="0"*64, hash="a"*64, timestamp=datetime.datetime.utcnow(),
            event_type="TASK_CREATED", event_category="TASK", payload=json.dumps({"over_capacity": True})
        ))
    db.commit()

    start = time.time()
    ComplianceMonitor.scan_incremental(db)
    elapsed_ms = (time.time() - start) * 1000
    assert elapsed_ms < 50.0, f"Incremental scan latency too high: {elapsed_ms:.2f} ms"


def test_benchmark_dashboard_generation_latency(db):
    """SLA Target: Dashboard generation < 75ms"""
    start = time.time()
    ComplianceService.get_dashboard(db)
    elapsed_ms = (time.time() - start) * 1000
    assert elapsed_ms < 75.0, f"Dashboard generation latency too high: {elapsed_ms:.2f} ms"


def test_benchmark_export_latency(db):
    """SLA Target: Export < 100ms"""
    filters = ComplianceFilterDTO(page=1, page_size=50)
    start = time.time()
    ComplianceService.export_report(db, filters, export_format="json")
    elapsed_ms = (time.time() - start) * 1000
    assert elapsed_ms < 100.0, f"Export latency too high: {elapsed_ms:.2f} ms"
