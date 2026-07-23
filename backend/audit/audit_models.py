from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class EventCategory(str, Enum):
    AUTHENTICATION = "AUTHENTICATION"
    TASK = "TASK"
    ASSIGNMENT = "ASSIGNMENT"
    GOVERNANCE = "GOVERNANCE"
    APPROVAL = "APPROVAL"
    ESCALATION = "ESCALATION"
    NOTIFICATION = "NOTIFICATION"
    INVESTIGATION = "INVESTIGATION"
    SYSTEM = "SYSTEM"


class RetentionPolicy(str, Enum):
    STANDARD_1_YEAR = "STANDARD_1_YEAR"
    COMPLIANCE_7_YEARS = "COMPLIANCE_7_YEARS"
    LEGAL_HOLD_PERMANENT = "LEGAL_HOLD_PERMANENT"


class AuditEntryDTO(BaseModel):
    id: str
    sequence: int
    prev_hash: str
    hash: str
    timestamp: datetime
    event_type: str
    event_category: EventCategory
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    entity_version: int = 1
    actor_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
    retention_policy: RetentionPolicy = RetentionPolicy.STANDARD_1_YEAR


class AuditAggregateDTO(BaseModel):
    aggregate_type: str
    aggregate_key: str
    total_events: int
    first_event_at: datetime
    last_event_at: datetime
    last_sequence: int
    last_hash: str
    version: int


class IntegrityReportDTO(BaseModel):
    is_valid: bool
    total_records_scanned: int
    verified_sequences: int
    corrupted_sequence: Optional[int] = None
    error_message: Optional[str] = None
    verified_at: datetime = Field(default_factory=datetime.utcnow)
    genesis_hash: str
    latest_hash: str


class AuditFilterDTO(BaseModel):
    event_category: Optional[EventCategory] = None
    event_type: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    actor_id: Optional[str] = None
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = 1
    page_size: int = 50


class AuditExportRequestDTO(BaseModel):
    format: str = "json"  # json, csv, ndjson
    filters: Optional[AuditFilterDTO] = None
    include_payloads: bool = True
