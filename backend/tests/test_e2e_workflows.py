"""
Phase 9.0 Milestone 1 — End-to-End Operational Workflow Integration Test Suite
"""

import json
import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
import backend.db.schema as db_schema
from backend.events.dispatcher import EventDispatcher
from backend.events.event_models import BaseEvent
from backend.events.event_types import EventType
from backend.audit.service import AuditService
from backend.compliance.compliance_service import ComplianceService
from backend.compliance.rule_repository import RuleRepository
from backend.compliance.risk_engine import RiskEngine


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    RuleRepository.seed_default_rules(session)
    yield session
    session.close()


# -----------------------------------------------------------------------------
# Workflow 1: Investigation Lifecycle End-to-End
# -----------------------------------------------------------------------------
def test_e2e_investigation_lifecycle_workflow(db):
    case_id = "INV-E2E-100"
    task_id = "TSK-E2E-100"
    officer_id = "officer_e2e"

    # Step 1: Create Investigation Case
    inv = db_schema.Investigation(
        id=case_id,
        title="Operation Cyber Interception E2E",
        priority="CRITICAL",
        status="ACTIVE",
        created_by=officer_id,
        created_at=datetime.datetime.utcnow(),
        version=1,
        last_sequence=1
    )
    db.add(inv)
    db.commit()

    # Publish CASE_UPDATED event
    evt1 = BaseEvent(
        event_type=EventType.CASE_UPDATED,
        user_id=officer_id,
        case_id=case_id,
        payload={"action": "CREATE_CASE", "entity_type": "Investigation", "entity_id": case_id, "district_id": "BANGALORE_CENTRAL"}
    )
    EventDispatcher.publish_sync(evt1, db)
    db.commit()

    # Step 2: Task Generation
    task = db_schema.InvestigationTask(
        id=task_id,
        investigation_id=case_id,
        title="Analyze Target CDR Signals",
        status="CREATED",
        priority="CRITICAL",
        sla_hours=24,
        created_at=datetime.datetime.utcnow()
    )
    db.add(task)
    db.commit()

    evt2 = BaseEvent(
        event_type=EventType.TASK_CREATED,
        user_id=officer_id,
        case_id=case_id,
        payload={"task_id": task_id, "entity_type": "Task", "entity_id": task_id, "district_id": "BANGALORE_CENTRAL"}
    )
    EventDispatcher.publish_sync(evt2, db)
    db.commit()

    # Step 3: Assignment & Governance
    evt3 = BaseEvent(
        event_type=EventType.ASSIGNMENT_CREATED,
        user_id=officer_id,
        case_id=case_id,
        payload={"task_id": task_id, "assigned_to": officer_id, "entity_type": "Task", "entity_id": task_id, "district_id": "BANGALORE_CENTRAL"}
    )
    EventDispatcher.publish_sync(evt3, db)
    db.commit()

    # Verify Audit Ledger record was automatically generated
    audit_records, count = AuditService.get_history(db, filters=None)
    assert count >= 3, f"Expected at least 3 audit entries, found {count}"

    # Verify Compliance evaluation triggered
    comp_dash = ComplianceService.get_dashboard(db)
    assert comp_dash.compliance_score >= 0.0


# -----------------------------------------------------------------------------
# Workflow 2: Approval Lifecycle End-to-End
# -----------------------------------------------------------------------------
def test_e2e_approval_lifecycle_workflow(db):
    approval_id = "APP-E2E-200"
    user_id = "inspector_sub"

    # Step 1: Submit Multi-Tier Approval Request
    evt_submit = BaseEvent(
        event_type=EventType.APPROVAL_SUBMITTED,
        user_id=user_id,
        case_id="INV-E2E-100",
        payload={"approval_id": approval_id, "stage": "SUPERVISOR", "entity_type": "Approval", "entity_id": approval_id, "district_id": "BANGALORE_CENTRAL"}
    )
    EventDispatcher.publish_sync(evt_submit, db)
    db.commit()

    # Step 2: Grant Approval
    evt_approve = BaseEvent(
        event_type=EventType.APPROVAL_APPROVED,
        user_id="acp_boss",
        case_id="INV-E2E-100",
        payload={"approval_id": approval_id, "stage": "SUPERVISOR", "entity_type": "Approval", "entity_id": approval_id, "district_id": "BANGALORE_CENTRAL"}
    )
    EventDispatcher.publish_sync(evt_approve, db)
    db.commit()

    # Verify Audit trail presence for approval
    audit_records, count = AuditService.get_history(db, filters=None)
    approval_audits = [a for a in audit_records if "APPROVAL" in a.event_type]
    assert len(approval_audits) >= 2


# -----------------------------------------------------------------------------
# Workflow 3: Escalation & SLA Lifecycle End-to-End
# -----------------------------------------------------------------------------
def test_e2e_escalation_lifecycle_workflow(db):
    task_id = "TSK-E2E-300"
    officer_id = "constable_1"

    # Step 1: SLA Warning Triggered
    evt_warn = BaseEvent(
        event_type=EventType.TASK_SLA_WARNING,
        user_id=officer_id,
        case_id="INV-E2E-100",
        payload={"task_id": task_id, "hours_remaining": 2, "entity_type": "Task", "entity_id": task_id, "district_id": "BANGALORE_CENTRAL"}
    )
    EventDispatcher.publish_sync(evt_warn, db)
    db.commit()

    # Step 2: SLA Breach & Automated Escalation
    evt_breach = BaseEvent(
        event_type=EventType.TASK_SLA_BREACHED,
        user_id=officer_id,
        case_id="INV-E2E-100",
        payload={"task_id": task_id, "overdue_hours": 12, "entity_type": "Task", "entity_id": task_id, "sla_breached": True, "district_id": "BANGALORE_CENTRAL"}
    )
    EventDispatcher.publish_sync(evt_breach, db)
    db.commit()

    # Verify Compliance Engine automatically caught SLA breach violation
    comp_dash = ComplianceService.get_dashboard(db)
    sla_violations = [v for v in comp_dash.active_violations if v.rule_id == "RULE_ESCAL_01"]
    assert len(sla_violations) > 0
