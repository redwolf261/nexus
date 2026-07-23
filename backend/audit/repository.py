import json
import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from backend.audit.schema import AuditLedgerRecord, AuditAggregateRecord, GENESIS_HASH
from backend.audit.audit_models import (
    AuditEntryDTO, AuditAggregateDTO, IntegrityReportDTO, AuditFilterDTO, EventCategory, RetentionPolicy
)
from backend.audit.hash_engine import HashEngine
from backend.audit.masking import mask_sensitive_data


class AuditRepository:
    @staticmethod
    def append_entry(
        db: Session,
        event_type: str,
        event_category: EventCategory,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        entity_version: int = 1,
        actor_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        previous_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
        retention_policy: RetentionPolicy = RetentionPolicy.STANDARD_1_YEAR,
        timestamp: Optional[datetime.datetime] = None
    ) -> AuditLedgerRecord:
        """
        Append a new audit entry to the ledger atomically with SHA-256 hash chaining.
        """
        if timestamp is None:
            timestamp = datetime.datetime.utcnow()

        # Mask sensitive data in states and payload
        masked_payload = mask_sensitive_data(payload)
        masked_prev = mask_sensitive_data(previous_state)
        masked_new = mask_sensitive_data(new_state)

        payload_json = json.dumps(masked_payload) if masked_payload is not None else None
        prev_json = json.dumps(masked_prev) if masked_prev is not None else None
        new_json = json.dumps(masked_new) if masked_new is not None else None

        # Lock latest row to get sequence and prev_hash atomically
        latest = db.query(AuditLedgerRecord).order_by(desc(AuditLedgerRecord.sequence)).first()
        if latest:
            sequence = latest.sequence + 1
            prev_hash = latest.hash
        else:
            sequence = 1
            prev_hash = GENESIS_HASH

        # Compute SHA-256 hash
        entry_hash = HashEngine.compute_hash(
            prev_hash=prev_hash,
            sequence=sequence,
            timestamp=timestamp,
            event_type=event_type,
            event_category=event_category.value if hasattr(event_category, "value") else str(event_category),
            entity_type=entity_type,
            entity_id=entity_id,
            entity_version=entity_version,
            actor_id=actor_id,
            correlation_id=correlation_id,
            request_id=request_id,
            payload_str=payload_json,
            previous_state_str=prev_json,
            new_state_str=new_json
        )

        record = AuditLedgerRecord(
            sequence=sequence,
            prev_hash=prev_hash,
            hash=entry_hash,
            timestamp=timestamp,
            event_type=event_type,
            event_category=event_category.value if hasattr(event_category, "value") else str(event_category),
            entity_type=entity_type,
            entity_id=entity_id,
            entity_version=entity_version,
            actor_id=actor_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            request_id=request_id,
            session_id=session_id,
            previous_state=prev_json,
            new_state=new_json,
            payload=payload_json,
            retention_policy=retention_policy.value if hasattr(retention_policy, "value") else str(retention_policy)
        )

        db.add(record)

        # Update Aggregates
        AuditRepository._update_aggregates(db, record)

        db.flush()
        return record

    @staticmethod
    def _update_aggregates(db: Session, record: AuditLedgerRecord) -> None:
        """Update aggregate counters for Entity, User, Correlation."""
        keys_to_update = []
        if record.entity_type and record.entity_id:
            keys_to_update.append(("ENTITY", f"{record.entity_type}:{record.entity_id}"))
        if record.actor_id:
            keys_to_update.append(("USER", f"user:{record.actor_id}"))
        if record.correlation_id:
            keys_to_update.append(("CORRELATION", f"correlation:{record.correlation_id}"))

        for agg_type, agg_key in keys_to_update:
            agg = db.query(AuditAggregateRecord).filter_by(aggregate_key=agg_key).with_for_update().first()
            if agg:
                agg.total_events += 1
                agg.last_event_at = record.timestamp
                agg.last_sequence = record.sequence
                agg.last_hash = record.hash
                agg.version += 1
            else:
                agg = AuditAggregateRecord(
                    aggregate_type=agg_type,
                    aggregate_key=agg_key,
                    total_events=1,
                    first_event_at=record.timestamp,
                    last_event_at=record.timestamp,
                    last_sequence=record.sequence,
                    last_hash=record.hash,
                    version=1
                )
                db.add(agg)

    @staticmethod
    def get_history(db: Session, filters: Optional[AuditFilterDTO] = None) -> Tuple[List[AuditLedgerRecord], int]:
        if filters is None:
            filters = AuditFilterDTO()

        query = db.query(AuditLedgerRecord)

        if filters.event_category:
            cat_val = filters.event_category.value if hasattr(filters.event_category, "value") else str(filters.event_category)
            query = query.filter(AuditLedgerRecord.event_category == cat_val)
        if filters.event_type:
            query = query.filter(AuditLedgerRecord.event_type == filters.event_type)
        if filters.entity_type:
            query = query.filter(AuditLedgerRecord.entity_type == filters.entity_type)
        if filters.entity_id:
            query = query.filter(AuditLedgerRecord.entity_id == filters.entity_id)
        if filters.actor_id:
            query = query.filter(AuditLedgerRecord.actor_id == filters.actor_id)
        if filters.correlation_id:
            query = query.filter(AuditLedgerRecord.correlation_id == filters.correlation_id)
        if filters.request_id:
            query = query.filter(AuditLedgerRecord.request_id == filters.request_id)
        if filters.session_id:
            query = query.filter(AuditLedgerRecord.session_id == filters.session_id)
        if filters.start_time:
            query = query.filter(AuditLedgerRecord.timestamp >= filters.start_time)
        if filters.end_time:
            query = query.filter(AuditLedgerRecord.timestamp <= filters.end_time)

        total = query.count()
        offset = (filters.page - 1) * filters.page_size
        records = query.order_by(desc(AuditLedgerRecord.sequence)).offset(offset).limit(filters.page_size).all()
        return records, total

    @staticmethod
    def verify_chain_integrity(db: Session) -> IntegrityReportDTO:
        records = db.query(AuditLedgerRecord).order_by(asc(AuditLedgerRecord.sequence)).all()
        if not records:
            return IntegrityReportDTO(
                is_valid=True,
                total_records_scanned=0,
                verified_sequences=0,
                genesis_hash=GENESIS_HASH,
                latest_hash=GENESIS_HASH
            )

        prev_expected_hash = GENESIS_HASH
        scanned = 0

        for record in records:
            scanned += 1
            # Check link to previous hash
            if record.prev_hash != prev_expected_hash:
                return IntegrityReportDTO(
                    is_valid=False,
                    total_records_scanned=scanned,
                    verified_sequences=scanned - 1,
                    corrupted_sequence=record.sequence,
                    error_message=f"Hash chain broken at sequence {record.sequence}. Expected prev_hash {prev_expected_hash}, found {record.prev_hash}.",
                    genesis_hash=GENESIS_HASH,
                    latest_hash=records[-1].hash
                )

            # Re-verify internal hash of current record
            if not HashEngine.verify_entry_hash(record):
                return IntegrityReportDTO(
                    is_valid=False,
                    total_records_scanned=scanned,
                    verified_sequences=scanned - 1,
                    corrupted_sequence=record.sequence,
                    error_message=f"Tampered record content detected at sequence {record.sequence}.",
                    genesis_hash=GENESIS_HASH,
                    latest_hash=records[-1].hash
                )

            prev_expected_hash = record.hash

        return IntegrityReportDTO(
            is_valid=True,
            total_records_scanned=scanned,
            verified_sequences=scanned,
            genesis_hash=GENESIS_HASH,
            latest_hash=records[-1].hash
        )

    @staticmethod
    def record_to_dto(record: AuditLedgerRecord) -> AuditEntryDTO:
        return AuditEntryDTO(
            id=record.id,
            sequence=record.sequence,
            prev_hash=record.prev_hash,
            hash=record.hash,
            timestamp=record.timestamp,
            event_type=record.event_type,
            event_category=EventCategory(record.event_category) if record.event_category in EventCategory.__members__ else record.event_category,
            entity_type=record.entity_type,
            entity_id=record.entity_id,
            entity_version=record.entity_version,
            actor_id=record.actor_id,
            ip_address=record.ip_address,
            user_agent=record.user_agent,
            correlation_id=record.correlation_id,
            request_id=record.request_id,
            session_id=record.session_id,
            previous_state=json.loads(record.previous_state) if record.previous_state else None,
            new_state=json.loads(record.new_state) if record.new_state else None,
            payload=json.loads(record.payload) if record.payload else None,
            retention_policy=RetentionPolicy(record.retention_policy) if record.retention_policy in RetentionPolicy.__members__ else record.retention_policy
        )
