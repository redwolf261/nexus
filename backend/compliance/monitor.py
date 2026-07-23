import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.audit.schema import AuditLedgerRecord
from backend.compliance.schema import ComplianceScanCheckpointRecord
from backend.compliance.rule_engine import RuleEngine
from backend.compliance.rule_repository import RuleRepository


class ComplianceMonitor:
    """
    Continuous background monitor & incremental compliance evaluator.
    """

    @classmethod
    def scan_incremental(cls, db: Session) -> Dict[str, Any]:
        RuleRepository.seed_default_rules(db)

        checkpoint = db.query(ComplianceScanCheckpointRecord).filter_by(id="audit_ledger_scan").with_for_update().first()
        if not checkpoint:
            checkpoint = ComplianceScanCheckpointRecord(
                id="audit_ledger_scan",
                last_scanned_sequence=0,
                last_scan_time=datetime.datetime.utcnow(),
                total_scanned_items=0
            )
            db.add(checkpoint)
            db.flush()

        last_seq = checkpoint.last_scanned_sequence
        new_entries = db.query(AuditLedgerRecord).filter(
            AuditLedgerRecord.sequence > last_seq
        ).order_by(AuditLedgerRecord.sequence.asc()).limit(1000).all()

        violations_found = 0
        if new_entries:
            for entry in new_entries:
                violation_dicts = RuleEngine.evaluate_audit_entry(entry, db)
                for v_dict in violation_dicts:
                    RuleRepository.save_violation(
                        db=db,
                        rule_id=v_dict["rule_id"],
                        rule_name=v_dict["rule_name"],
                        category=v_dict["category"],
                        severity=v_dict["severity"],
                        explanation=v_dict["explanation"],
                        evidence=v_dict["evidence"],
                        remediation=v_dict["remediation"],
                        violated_entity_type=v_dict.get("violated_entity_type"),
                        violated_entity_id=v_dict.get("violated_entity_id"),
                        actor_id=v_dict.get("actor_id"),
                        district_id=v_dict.get("district_id"),
                        legal_reference=v_dict.get("legal_reference"),
                        timestamp=entry.timestamp
                    )
                    violations_found += 1

            checkpoint.last_scanned_sequence = new_entries[-1].sequence
            checkpoint.last_scan_time = datetime.datetime.utcnow()
            checkpoint.total_scanned_items += len(new_entries)
            db.commit()

        return {
            "scanned_items": len(new_entries),
            "new_violations": violations_found,
            "last_scanned_sequence": checkpoint.last_scanned_sequence,
            "scan_timestamp": checkpoint.last_scan_time.isoformat()
        }

    @classmethod
    def scan_entity(cls, db: Session, entity_type: str, entity_id: str) -> Dict[str, Any]:
        RuleRepository.seed_default_rules(db)
        entries = db.query(AuditLedgerRecord).filter(
            AuditLedgerRecord.entity_type == entity_type,
            AuditLedgerRecord.entity_id == entity_id
        ).all()

        violations_found = 0
        for entry in entries:
            v_dicts = RuleEngine.evaluate_audit_entry(entry, db)
            for v_dict in v_dicts:
                RuleRepository.save_violation(
                    db=db,
                    rule_id=v_dict["rule_id"],
                    rule_name=v_dict["rule_name"],
                    category=v_dict["category"],
                    severity=v_dict["severity"],
                    explanation=v_dict["explanation"],
                    evidence=v_dict["evidence"],
                    remediation=v_dict["remediation"],
                    violated_entity_type=v_dict.get("violated_entity_type"),
                    violated_entity_id=v_dict.get("violated_entity_id"),
                    actor_id=v_dict.get("actor_id"),
                    district_id=v_dict.get("district_id"),
                    legal_reference=v_dict.get("legal_reference")
                )
                violations_found += 1
        db.commit()
        return {"entity_type": entity_type, "entity_id": entity_id, "scanned_items": len(entries), "violations_found": violations_found}
