import json
import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from backend.compliance.schema import (
    ComplianceRuleRecord, ComplianceViolationRecord, ComplianceRiskSnapshotRecord, ComplianceScanCheckpointRecord
)
from backend.compliance.compliance_contracts import (
    ComplianceRuleDTO, ComplianceViolationDTO, ComplianceRiskDTO, ComplianceFilterDTO,
    RuleCategory, SeverityLevel, RiskBand
)

# Standard 20 Compliance Policy Rules Reference Data
DEFAULT_COMPLIANCE_RULES = [
    {
        "id": "RULE_AUTH_01",
        "name": "Assignment Without Authority",
        "description": "Task assigned to or by an officer lacking requisite rank or role permissions.",
        "category": RuleCategory.ASSIGNMENT.value,
        "severity": SeverityLevel.HIGH.value,
        "remediation": "Revoke assignment and reassign to an authorized officer with requisite rank.",
        "legal_reference": "Police Manual Reg 104 / Role Matrix"
    },
    {
        "id": "RULE_APPROV_01",
        "name": "Approval Outside Hierarchy",
        "description": "Approval request granted by an officer outside the chain of command.",
        "category": RuleCategory.APPROVAL.value,
        "severity": SeverityLevel.CRITICAL.value,
        "remediation": "Escalate to District Commissioner for re-approval and invalidate unauthorized sign-off.",
        "legal_reference": "KSP Administrative Guidelines Sec 12"
    },
    {
        "id": "RULE_GOV_01",
        "name": "Missing Override Justification",
        "description": "Workload or assignment recommendation overridden without mandatory written rationale.",
        "category": RuleCategory.GOVERNANCE.value,
        "severity": SeverityLevel.MEDIUM.value,
        "remediation": "Mandate supervisor to record formal justification in override log.",
        "legal_reference": "Silo Buster Governance Standard 4.1"
    },
    {
        "id": "RULE_APPROV_02",
        "name": "Invalid Delegation",
        "description": "Delegated approval authority exceeds maximum permitted delegation duration or role level.",
        "category": RuleCategory.APPROVAL.value,
        "severity": SeverityLevel.HIGH.value,
        "remediation": "Cancel delegation and revert pending approvals to primary officer.",
        "legal_reference": "Delegation Policy Order 2025-A"
    },
    {
        "id": "RULE_APPROV_03",
        "name": "Expired Delegation Action",
        "description": "Approval granted using a delegation window that has already expired.",
        "category": RuleCategory.APPROVAL.value,
        "severity": SeverityLevel.HIGH.value,
        "remediation": "Flag approval as invalid and require fresh approval from active authority.",
        "legal_reference": "Delegation Policy Order 2025-B"
    },
    {
        "id": "RULE_ASSIGN_01",
        "name": "Officer Over Capacity",
        "description": "Task assigned to an officer whose active concurrent workload exceeds capacity limits.",
        "category": RuleCategory.ASSIGNMENT.value,
        "severity": SeverityLevel.MEDIUM.value,
        "remediation": "Rebalance active workload or reassign task to an available officer.",
        "legal_reference": "Workload Capacity Standard 2026"
    },
    {
        "id": "RULE_ASSIGN_02",
        "name": "Assignment Outside Jurisdiction",
        "description": "Officer assigned to investigation outside their assigned station or district boundaries without cross-boundary authorization.",
        "category": RuleCategory.ASSIGNMENT.value,
        "severity": SeverityLevel.HIGH.value,
        "remediation": "Attach cross-jurisdictional authorization order or reassign to local station officer.",
        "legal_reference": "Jurisdictional Boundary Protocol Sec 8"
    },
    {
        "id": "RULE_APPROV_04",
        "name": "Missing Mandatory Approval",
        "description": "Critical investigation task transitioned without required multi-tier approval sign-off.",
        "category": RuleCategory.APPROVAL.value,
        "severity": SeverityLevel.CRITICAL.value,
        "remediation": "Freeze task state and trigger high-priority approval workflow immediately.",
        "legal_reference": "Investigation Governance Directive 3"
    },
    {
        "id": "RULE_AUDIT_01",
        "name": "Missing Audit Trail",
        "description": "State transition performed without corresponding entry in the immutable audit ledger.",
        "category": RuleCategory.AUDIT.value,
        "severity": SeverityLevel.CRITICAL.value,
        "remediation": "Perform immediate integrity audit and append historical state entry.",
        "legal_reference": "Digital Evidence & Audit Standards Act"
    },
    {
        "id": "RULE_AUDIT_02",
        "name": "Broken Hash Chain",
        "description": "Cryptographic SHA-256 hash mismatch detected in audit ledger entry.",
        "category": RuleCategory.AUDIT.value,
        "severity": SeverityLevel.CRITICAL.value,
        "remediation": "Quarantine ledger sequence, notify System Administrator, and initiate forensic audit.",
        "legal_reference": "ISO 27001 Cryptographic Safeguards"
    },
    {
        "id": "RULE_NOTIF_01",
        "name": "Notification Delivery Failure",
        "description": "Critical operational escalation or approval alert failed all delivery channels.",
        "category": RuleCategory.NOTIFICATION.value,
        "severity": SeverityLevel.HIGH.value,
        "remediation": "Fallback to SMS/Push fallback gateway and alert Command Center dispatch.",
        "legal_reference": "Emergency Communication Standard 2"
    },
    {
        "id": "RULE_NOTIF_02",
        "name": "Excessive Reminder Retries",
        "description": "Escalating reminder retry threshold exceeded without response from officer.",
        "category": RuleCategory.NOTIFICATION.value,
        "severity": SeverityLevel.MEDIUM.value,
        "remediation": "Escalate unresponded task to supervisory command queue.",
        "legal_reference": "Operational SLA Policy 5.2"
    },
    {
        "id": "RULE_ESCAL_01",
        "name": "SLA Breach",
        "description": "Task or approval remained unacted beyond mandatory SLA time limits.",
        "category": RuleCategory.ESCALATION.value,
        "severity": SeverityLevel.HIGH.value,
        "remediation": "Trigger automated tier-2 escalation to Assistant Commissioner.",
        "legal_reference": "SLA & Escalation Rulebook"
    },
    {
        "id": "RULE_EVID_01",
        "name": "Unauthorized Evidence View",
        "description": "Classified evidence media or suspect profile accessed by officer not attached to investigation.",
        "category": RuleCategory.EVIDENCE.value,
        "severity": SeverityLevel.CRITICAL.value,
        "remediation": "Lock evidence access log and mandate security clearance review.",
        "legal_reference": "Evidence Secrecy Act Reg 4"
    },
    {
        "id": "RULE_EVID_02",
        "name": "Unauthorized Evidence Export",
        "description": "Case file or evidence export attempted without supervisory export clearance.",
        "category": RuleCategory.EVIDENCE.value,
        "severity": SeverityLevel.CRITICAL.value,
        "remediation": "Block export payload and alert Inspector General Audit Team.",
        "legal_reference": "Evidence Secrecy Act Reg 9"
    },
    {
        "id": "RULE_AUTH_02",
        "name": "Multiple Failed Logins",
        "description": "Excessive invalid authentication attempts detected for officer account.",
        "category": RuleCategory.AUTHENTICATION.value,
        "severity": SeverityLevel.HIGH.value,
        "remediation": "Temporarily suspend user token and mandate multi-factor re-authentication.",
        "legal_reference": "KSP Cyber Security Policy 1.1"
    },
    {
        "id": "RULE_AUTH_03",
        "name": "Privilege Escalation Attempt",
        "description": "User requested REST endpoint exceeding JWT role claims.",
        "category": RuleCategory.AUTHORIZATION.value,
        "severity": SeverityLevel.CRITICAL.value,
        "remediation": "Revoke active token session and trigger security incident report.",
        "legal_reference": "RBAC Security Enforcement Spec"
    },
    {
        "id": "RULE_APPROV_05",
        "name": "Concurrent Conflicting Approvals",
        "description": "Simultaneous conflicting approval states recorded for the same entity version.",
        "category": RuleCategory.APPROVAL.value,
        "severity": SeverityLevel.HIGH.value,
        "remediation": "Lock approval state and route to Senior Commissioner for resolution.",
        "legal_reference": "Approval Workflow Engine Rules"
    },
    {
        "id": "RULE_GOV_02",
        "name": "Missing Supervisor Review",
        "description": "Investigation closed or archived without mandatory supervisor sign-off review.",
        "category": RuleCategory.INVESTIGATION.value,
        "severity": SeverityLevel.HIGH.value,
        "remediation": "Re-open investigation workspace and queue supervisor review task.",
        "legal_reference": "Case Closure Standard Operating Procedure"
    },
    {
        "id": "RULE_SYS_01",
        "name": "Policy Version Mismatch",
        "description": "Action evaluated against deprecated or non-current policy engine version.",
        "category": RuleCategory.OPERATIONAL.value,
        "severity": SeverityLevel.LOW.value,
        "remediation": "Re-evaluate action state against current active policy engine version.",
        "legal_reference": "Policy Engine System Config"
    }
]


class RuleRepository:
    @staticmethod
    def seed_default_rules(db: Session) -> None:
        """Seed default 20 compliance rules into DB if not present."""
        existing_count = db.query(ComplianceRuleRecord).count()
        if existing_count >= len(DEFAULT_COMPLIANCE_RULES):
            return

        for r_dict in DEFAULT_COMPLIANCE_RULES:
            rule = db.query(ComplianceRuleRecord).filter_by(id=r_dict["id"]).first()
            if not rule:
                rec = ComplianceRuleRecord(
                    id=r_dict["id"],
                    name=r_dict["name"],
                    description=r_dict["description"],
                    category=r_dict["category"],
                    severity=r_dict["severity"],
                    enabled=True,
                    version=1,
                    policy_version="1.0.0",
                    evaluation_scope="SYSTEM",
                    remediation=r_dict["remediation"],
                    legal_reference=r_dict["legal_reference"]
                )
                db.add(rec)
        db.commit()

    @staticmethod
    def get_all_rules(db: Session) -> List[ComplianceRuleRecord]:
        return db.query(ComplianceRuleRecord).all()

    @staticmethod
    def save_violation(
        db: Session,
        rule_id: str,
        rule_name: str,
        category: str,
        severity: str,
        explanation: str,
        evidence: Dict[str, Any],
        remediation: str,
        violated_entity_type: Optional[str] = None,
        violated_entity_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        district_id: Optional[str] = None,
        legal_reference: Optional[str] = None,
        timestamp: Optional[datetime.datetime] = None
    ) -> ComplianceViolationRecord:
        if timestamp is None:
            timestamp = datetime.datetime.utcnow()

        rec = ComplianceViolationRecord(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=severity,
            explanation=explanation,
            evidence=json.dumps(evidence),
            remediation=remediation,
            violated_entity_type=violated_entity_type,
            violated_entity_id=violated_entity_id,
            actor_id=actor_id,
            district_id=district_id or "BANGALORE_CENTRAL",
            legal_reference=legal_reference,
            resolved=False,
            timestamp=timestamp
        )
        db.add(rec)
        db.flush()
        return rec

    @staticmethod
    def get_active_violations(db: Session, filters: Optional[ComplianceFilterDTO] = None) -> Tuple[List[ComplianceViolationRecord], int]:
        query = db.query(ComplianceViolationRecord).filter(ComplianceViolationRecord.resolved == False)

        if filters:
            if filters.category:
                cat_val = filters.category.value if hasattr(filters.category, "value") else str(filters.category)
                query = query.filter(ComplianceViolationRecord.category == cat_val)
            if filters.severity:
                sev_val = filters.severity.value if hasattr(filters.severity, "value") else str(filters.severity)
                query = query.filter(ComplianceViolationRecord.severity == sev_val)
            if filters.entity_type:
                query = query.filter(ComplianceViolationRecord.violated_entity_type == filters.entity_type)
            if filters.entity_id:
                query = query.filter(ComplianceViolationRecord.violated_entity_id == filters.entity_id)
            if filters.actor_id:
                query = query.filter(ComplianceViolationRecord.actor_id == filters.actor_id)
            if filters.district_id:
                query = query.filter(ComplianceViolationRecord.district_id == filters.district_id)

        total = query.count()
        page = filters.page if filters else 1
        page_size = filters.page_size if filters else 50
        offset = (page - 1) * page_size
        records = query.order_by(desc(ComplianceViolationRecord.timestamp)).offset(offset).limit(page_size).all()
        return records, total

    @staticmethod
    def record_to_dto(rec: ComplianceViolationRecord) -> ComplianceViolationDTO:
        evidence_dict = {}
        if rec.evidence:
            try:
                evidence_dict = json.loads(rec.evidence)
            except Exception:
                evidence_dict = {"raw": rec.evidence}

        return ComplianceViolationDTO(
            id=rec.id,
            rule_id=rec.rule_id,
            rule_name=rec.rule_name,
            category=RuleCategory(rec.category) if rec.category in RuleCategory.__members__ else RuleCategory.OPERATIONAL,
            severity=SeverityLevel(rec.severity) if rec.severity in SeverityLevel.__members__ else SeverityLevel.MEDIUM,
            violated_entity_type=rec.violated_entity_type,
            violated_entity_id=rec.violated_entity_id,
            actor_id=rec.actor_id,
            district_id=rec.district_id,
            explanation=rec.explanation,
            evidence=evidence_dict,
            remediation=rec.remediation,
            legal_reference=rec.legal_reference,
            resolved=rec.resolved,
            resolved_at=rec.resolved_at,
            resolved_by=rec.resolved_by,
            timestamp=rec.timestamp
        )
