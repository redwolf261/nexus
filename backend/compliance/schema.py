import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Index
from backend.database import Base


class ComplianceRuleRecord(Base):
    __tablename__ = "compliance_rules"

    id = Column(String(64), primary_key=True)  # e.g., RULE_ASSIGNMENT_01
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(64), nullable=False, index=True)
    severity = Column(String(32), nullable=False, index=True)
    enabled = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    policy_version = Column(String(32), default="1.0.0", nullable=False)
    evaluation_scope = Column(String(32), default="SYSTEM", nullable=False)
    remediation = Column(Text, nullable=False)
    legal_reference = Column(String(256), nullable=True)


class ComplianceViolationRecord(Base):
    __tablename__ = "compliance_violations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String(64), nullable=False, index=True)
    rule_name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False, index=True)
    severity = Column(String(32), nullable=False, index=True)
    
    violated_entity_type = Column(String(128), nullable=True, index=True)
    violated_entity_id = Column(String(128), nullable=True, index=True)
    actor_id = Column(String(128), nullable=True, index=True)
    district_id = Column(String(128), nullable=True, index=True)
    
    explanation = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)      # JSON string
    remediation = Column(Text, nullable=False)
    legal_reference = Column(String(256), nullable=True)
    
    resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(128), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_comp_viol_entity", "violated_entity_type", "violated_entity_id"),
        Index("idx_comp_viol_actor", "actor_id"),
        Index("idx_comp_viol_district", "district_id"),
    )


class ComplianceRiskSnapshotRecord(Base):
    __tablename__ = "compliance_risk_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    overall_score = Column(Float, nullable=False)
    risk_band = Column(String(32), nullable=False)
    subsystem_breakdown = Column(Text, nullable=False)  # JSON string
    contributing_factors = Column(Text, nullable=False) # JSON string
    total_active_violations = Column(Integer, nullable=False)
    calculated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)


class ComplianceScanCheckpointRecord(Base):
    __tablename__ = "compliance_scan_checkpoints"

    id = Column(String(64), primary_key=True)  # checkpoint_name e.g. "audit_ledger_scan"
    last_scanned_sequence = Column(Integer, default=0, nullable=False)
    last_scan_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    total_scanned_items = Column(Integer, default=0, nullable=False)
