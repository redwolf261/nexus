from typing import Any
from sqlalchemy.orm import Session

from backend.compliance.rule_engine import RuleEngine
from backend.compliance.rule_repository import RuleRepository


class ComplianceEventListener:
    @staticmethod
    def consume_event(event: Any, db: Session) -> None:
        """
        Consumes events published across Task, Assignment, Governance, Approval, Escalation,
        Notification, Authentication, Audit, Workspace subsystems and triggers compliance checks.
        """
        if not event:
            return

        RuleRepository.seed_default_rules(db)
        violation_dicts = RuleEngine.evaluate_audit_entry(event, db)

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
                legal_reference=v_dict.get("legal_reference")
            )
        db.flush()
