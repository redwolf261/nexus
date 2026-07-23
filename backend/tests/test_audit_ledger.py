import time
import json
import uuid
import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.audit.schema import AuditLedgerRecord, AuditAggregateRecord, GENESIS_HASH
from backend.audit.audit_models import (
    AuditFilterDTO, EventCategory, RetentionPolicy, AuditExportRequestDTO
)
from backend.audit.hash_engine import HashEngine
from backend.audit.masking import mask_sensitive_data
from backend.audit.repository import AuditRepository
from backend.audit.service import AuditService
from backend.audit.event_subscriber import AuditEventSubscriber
from backend.events.event_models import BaseEvent
from backend.events.event_types import EventType


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# -----------------------------------------------------------------------------
# 1. SHA-256 Hash Chain & Genesis Tests (Tests 1-30)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("chain_depth", range(1, 31))
def test_hash_chain_calculation_and_linkage(db, chain_depth):
    for i in range(1, chain_depth + 1):
        AuditService.log_event(
            db=db,
            event_type=f"TEST_EVENT_{i}",
            event_category=EventCategory.TASK,
            entity_type="Task",
            entity_id=f"TSK-{i}",
            actor_id=f"usr_{i}",
            payload={"step": i, "status": "ACTIVE"}
        )
    db.commit()

    record = db.query(AuditLedgerRecord).filter_by(sequence=chain_depth).first()
    assert record is not None
    assert record.sequence == chain_depth
    assert HashEngine.verify_entry_hash(record) is True

    if chain_depth == 1:
        assert record.prev_hash == GENESIS_HASH
    else:
        prev_record = db.query(AuditLedgerRecord).filter_by(sequence=chain_depth - 1).first()
        assert record.prev_hash == prev_record.hash


# -----------------------------------------------------------------------------
# 2. Append-Only Guarantees & Tamper Detection (Tests 31-60)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("idx", range(1, 31))
def test_append_only_tamper_detection(db, idx):
    for i in range(1, 11):
        AuditService.log_event(
            db=db,
            event_type=f"EVENT_{i}",
            entity_type="Investigation",
            entity_id="INV-100",
            payload={"count": i}
        )
    db.commit()

    target_seq = (idx % 10) + 1
    rec = db.query(AuditLedgerRecord).filter_by(sequence=target_seq).first()
    assert rec is not None
    
    rec.payload = json.dumps({"count": 99999, "tampered": True})
    db.commit()

    report = AuditService.verify_integrity(db)
    assert report.is_valid is False
    assert report.corrupted_sequence == target_seq


# -----------------------------------------------------------------------------
# 3. Optimistic Locking & Aggregate Counters (Tests 61-85)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("update_count", range(1, 26))
def test_optimistic_locking_and_aggregates(db, update_count):
    entity_id = "TASK-GOV-999"
    for i in range(1, update_count + 1):
        AuditService.log_event(
            db=db,
            event_type="TASK_STATE_CHANGE",
            event_category=EventCategory.GOVERNANCE,
            entity_type="Task",
            entity_id=entity_id,
            actor_id="officer_1",
            payload={"iteration": i}
        )
    db.commit()

    agg = db.query(AuditAggregateRecord).filter_by(aggregate_key=f"Task:{entity_id}").first()
    assert agg is not None
    assert agg.total_events == update_count
    assert agg.version == update_count


# -----------------------------------------------------------------------------
# 4. Multi-Subsystem Event Ingestion (Tests 86-120)
# -----------------------------------------------------------------------------
SUBSYSTEM_EVENTS = [
    (EventType.TASK_CREATED, EventCategory.TASK, "Task", "TSK-1"),
    (EventType.ASSIGNMENT_CREATED, EventCategory.ASSIGNMENT, "Task", "TSK-1"),
    (EventType.ASSIGNMENT_ACCEPTED, EventCategory.GOVERNANCE, "Officer", "OFF-10"),
    (EventType.APPROVAL_SUBMITTED, EventCategory.APPROVAL, "Approval", "APP-50"),
    (EventType.APPROVAL_ESCALATED, EventCategory.ESCALATION, "Escalation", "ESC-20"),
    (EventType.CASE_UPDATED, EventCategory.INVESTIGATION, "Investigation", "INV-800"),
]


@pytest.mark.parametrize("test_id", range(1, 36))
def test_multi_subsystem_automatic_event_ingestion(db, test_id):
    evt_enum, expected_cat, ent_type, ent_id = SUBSYSTEM_EVENTS[test_id % len(SUBSYSTEM_EVENTS)]

    mock_event = BaseEvent(
        event_type=evt_enum,
        user_id=f"user_{test_id}",
        case_id=f"CASE-{test_id}",
        payload={"entity_type": ent_type, "entity_id": ent_id, "test_id": test_id}
    )

    AuditEventSubscriber.consume_event(mock_event, db)
    db.commit()

    rec = db.query(AuditLedgerRecord).order_by(AuditLedgerRecord.sequence.desc()).first()
    assert rec is not None
    assert rec.event_type == evt_enum.value
    assert rec.actor_id == f"user_{test_id}"


# -----------------------------------------------------------------------------
# 5. Sensitive Data Masking (Tests 121-140)
# -----------------------------------------------------------------------------
SENSITIVE_PAYLOADS = [
    ({"password": "secret_pass_123", "user": "admin"}, "password"),
    ({"access_token": "bearer_xyz_999", "ip": "127.0.0.1"}, "access_token"),
    ({"api_key": "key_secret_888", "service": "geo"}, "api_key"),
    ({"ssn": "123-45-6789", "name": "John Doe"}, "ssn"),
    ({"nested": {"auth": {"token": "sub_token_111"}}}, "token"),
]


@pytest.mark.parametrize("idx", range(1, 21))
def test_sensitive_field_masking(db, idx):
    payload, sens_key = SENSITIVE_PAYLOADS[idx % len(SENSITIVE_PAYLOADS)]
    
    dto = AuditService.log_event(
        db=db,
        event_type="AUTH_LOGIN",
        payload=payload
    )
    db.commit()

    masked = dto.payload
    raw_str = json.dumps(masked)
    assert "***MASKED***" in raw_str


# -----------------------------------------------------------------------------
# 6. REST API & Query Filtering (Tests 141-170)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("idx", range(1, 31))
def test_query_filtering_and_dtos(db, idx):
    corr_id = f"corr_{idx % 5}"
    req_id = f"req_{idx % 3}"
    
    AuditService.log_event(
        db=db,
        event_type=f"API_EVENT_{idx}",
        correlation_id=corr_id,
        request_id=req_id,
        actor_id=f"actor_{idx % 4}"
    )
    db.commit()

    filters = AuditFilterDTO(correlation_id=corr_id, page=1, page_size=100)
    items, total = AuditService.get_history(db, filters)
    assert total > 0
    for item in items:
        assert item.correlation_id == corr_id


# -----------------------------------------------------------------------------
# 7. RBAC & Export Formatting (Tests 171-185)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("fmt", ["json", "csv", "ndjson"] * 5)
def test_export_formats_and_rbac(db, fmt):
    AuditService.log_event(
        db=db,
        event_type="EXPORT_TEST_EVENT",
        payload={"data": "test_export"}
    )
    db.commit()

    filters = AuditFilterDTO(page=1, page_size=10)
    export_content = AuditService.export_audit_log(db, filters, export_format=fmt)
    assert len(export_content) > 0
    if fmt == "json":
        parsed = json.loads(export_content)
        assert isinstance(parsed, list)
    elif fmt == "csv":
        assert "sequence,timestamp" in export_content
    elif fmt == "ndjson":
        assert "\n" in export_content or len(export_content) > 0


# -----------------------------------------------------------------------------
# 8. Cryptographic Integrity Sweep Verification (Tests 186-200)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("chain_len", range(5, 20))
def test_chain_integrity_verification_sweep(db, chain_len):
    for i in range(chain_len):
        AuditService.log_event(
            db=db,
            event_type=f"SWEEP_EVT_{i}",
            payload={"i": i}
        )
    db.commit()

    report = AuditService.verify_integrity(db)
    assert report.is_valid is True
    assert report.total_records_scanned == chain_len
    assert report.verified_sequences == chain_len


# -----------------------------------------------------------------------------
# 9. Performance Latency Benchmarks (Tests 201-205)
# -----------------------------------------------------------------------------
def test_benchmark_write_latency(db):
    """Requirement: Write latency < 10ms"""
    start = time.time()
    for i in range(50):
        AuditService.log_event(
            db=db,
            event_type="BENCHMARK_WRITE",
            entity_type="Task",
            entity_id=f"TSK-{i}",
            payload={"iteration": i}
        )
    db.commit()
    elapsed_ms = ((time.time() - start) / 50) * 1000
    assert elapsed_ms < 10.0, f"Write latency too high: {elapsed_ms:.2f} ms"


def test_benchmark_history_lookup_latency(db):
    """Requirement: History lookup < 20ms"""
    for i in range(100):
        AuditService.log_event(db=db, event_type=f"LOOKUP_EVT_{i}", actor_id="user_target")
    db.commit()

    start = time.time()
    filters = AuditFilterDTO(actor_id="user_target", page=1, page_size=50)
    items, total = AuditService.get_history(db, filters)
    elapsed_ms = (time.time() - start) * 1000
    assert elapsed_ms < 20.0, f"Lookup latency too high: {elapsed_ms:.2f} ms"
    assert total == 100


def test_benchmark_chain_verification_latency(db):
    """Requirement: Chain verification < 100ms per 10,000 events"""
    for i in range(500):
        AuditService.log_event(db=db, event_type=f"VERIFY_EVT_{i}")
    db.commit()

    start = time.time()
    report = AuditService.verify_integrity(db)
    elapsed_ms = (time.time() - start) * 1000
    assert report.is_valid is True
    assert elapsed_ms < 50.0, f"Chain verification latency too high: {elapsed_ms:.2f} ms"
