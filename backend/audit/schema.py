import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, Index, UniqueConstraint
from backend.database import Base

GENESIS_HASH = "0" * 64

class AuditLedgerRecord(Base):
    __tablename__ = "audit_ledger"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sequence = Column(Integer, nullable=False, unique=True, index=True)
    prev_hash = Column(String(64), nullable=False)
    hash = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    
    event_type = Column(String(128), nullable=False, index=True)
    event_category = Column(String(64), nullable=False, index=True)
    
    entity_type = Column(String(128), nullable=True, index=True)
    entity_id = Column(String(128), nullable=True, index=True)
    entity_version = Column(Integer, default=1, nullable=False)
    
    actor_id = Column(String(128), nullable=True, index=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(256), nullable=True)
    
    correlation_id = Column(String(128), nullable=True, index=True)
    request_id = Column(String(128), nullable=True, index=True)
    session_id = Column(String(128), nullable=True, index=True)
    
    previous_state = Column(Text, nullable=True)  # JSON string
    new_state = Column(Text, nullable=True)       # JSON string
    payload = Column(Text, nullable=True)         # JSON string
    
    retention_policy = Column(String(64), default="STANDARD_1_YEAR", nullable=False, index=True)

    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_actor_time", "actor_id", "timestamp"),
        Index("idx_audit_correlation", "correlation_id"),
    )


class AuditAggregateRecord(Base):
    __tablename__ = "audit_aggregates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    aggregate_type = Column(String(64), nullable=False, index=True) # ENTITY, USER, REQUEST, CORRELATION
    aggregate_key = Column(String(256), nullable=False, unique=True, index=True)
    total_events = Column(Integer, default=0, nullable=False)
    first_event_at = Column(DateTime, nullable=False)
    last_event_at = Column(DateTime, nullable=False)
    last_sequence = Column(Integer, default=0, nullable=False)
    last_hash = Column(String(64), nullable=False)
    version = Column(Integer, default=1, nullable=False) # Optimistic locking counter
