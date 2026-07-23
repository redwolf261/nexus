import json
import csv
import io
import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from backend.audit.repository import AuditRepository
from backend.audit.schema import AuditLedgerRecord
from backend.audit.audit_models import (
    AuditEntryDTO, AuditFilterDTO, EventCategory, RetentionPolicy, IntegrityReportDTO
)


class AuditService:
    @staticmethod
    def categorize_event_type(event_type: str) -> EventCategory:
        evt = str(event_type).upper()
        if "TASK" in evt:
            return EventCategory.TASK
        elif "ASSIGN" in evt or "WORKLOAD" in evt:
            return EventCategory.ASSIGNMENT
        elif "GOVERN" in evt or "POLICY" in evt:
            return EventCategory.GOVERNANCE
        elif "APPROV" in evt:
            return EventCategory.APPROVAL
        elif "ESCALAT" in evt:
            return EventCategory.ESCALATION
        elif "NOTIF" in evt or "ALERT" in evt or "DIGEST" in evt:
            return EventCategory.NOTIFICATION
        elif "AUTH" in evt or "LOGIN" in evt or "LOGOUT" in evt or "TOKEN" in evt:
            return EventCategory.AUTHENTICATION
        elif "INVESTIGAT" in evt or "CASE" in evt or "WORKSPACE" in evt:
            return EventCategory.INVESTIGATION
        return EventCategory.SYSTEM

    @classmethod
    def log_event(
        cls,
        db: Session,
        event_type: str,
        event_category: Optional[EventCategory] = None,
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
    ) -> AuditEntryDTO:
        if event_category is None:
            event_category = cls.categorize_event_type(event_type)

        record = AuditRepository.append_entry(
            db=db,
            event_type=event_type,
            event_category=event_category,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_version=entity_version,
            actor_id=actor_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            request_id=request_id,
            session_id=session_id,
            previous_state=previous_state,
            new_state=new_state,
            payload=payload,
            retention_policy=retention_policy,
            timestamp=timestamp
        )
        return AuditRepository.record_to_dto(record)

    @classmethod
    def get_history(cls, db: Session, filters: AuditFilterDTO) -> Tuple[List[AuditEntryDTO], int]:
        records, total = AuditRepository.get_history(db, filters)
        return [AuditRepository.record_to_dto(r) for r in records], total

    @classmethod
    def verify_integrity(cls, db: Session) -> IntegrityReportDTO:
        return AuditRepository.verify_chain_integrity(db)

    @classmethod
    def export_audit_log(cls, db: Session, filters: AuditFilterDTO, export_format: str = "json") -> str:
        records, _ = AuditRepository.get_history(db, filters)
        dtos = [AuditRepository.record_to_dto(r) for r in records]

        if export_format.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "sequence", "timestamp", "hash", "prev_hash", "event_type", "event_category",
                "entity_type", "entity_id", "entity_version", "actor_id", "correlation_id", "request_id"
            ])
            for d in dtos:
                writer.writerow([
                    d.sequence, d.timestamp.isoformat(), d.hash, d.prev_hash, d.event_type,
                    d.event_category.value if hasattr(d.event_category, "value") else str(d.event_category),
                    d.entity_type or "", d.entity_id or "", d.entity_version,
                    d.actor_id or "", d.correlation_id or "", d.request_id or ""
                ])
            return output.getvalue()

        elif export_format.lower() == "ndjson":
            lines = [d.model_dump_json() for d in dtos]
            return "\n".join(lines)

        else:  # JSON
            return json.dumps([d.model_dump(mode="json") for d in dtos], indent=2, default=str)
