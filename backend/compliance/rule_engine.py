import json
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.compliance.rule_repository import RuleRepository, DEFAULT_COMPLIANCE_RULES
from backend.compliance.compliance_contracts import (
    ComplianceViolationDTO, RuleCategory, SeverityLevel
)


class RuleEngine:
    """
    100% Deterministic Policy Evaluation Engine. Zero AI/ML.
    """

    @classmethod
    def evaluate_audit_entry(cls, entry: Any, db: Session) -> List[Dict[str, Any]]:
        """
        Evaluates a single Audit Ledger Record against all 20 policy rules deterministically.
        Returns a list of violation dictionaries to be persisted if rules fail.
        """
        violations = []
        event_type = getattr(entry, "event_type", "")
        payload = getattr(entry, "payload", {})
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}

        actor_id = getattr(entry, "actor_id", None) or payload.get("user_id")
        entity_type = getattr(entry, "entity_type", None) or payload.get("entity_type")
        entity_id = getattr(entry, "entity_id", None) or payload.get("entity_id")
        district_id = payload.get("district_id") or "BANGALORE_CENTRAL"

        # 1. RULE_AUTH_01: Assignment Without Authority
        if event_type in ["ASSIGNMENT_CREATED", "TASK_ASSIGNED", "TASK_CREATED"]:
            officer_rank = payload.get("officer_rank", "CONSTABLE").upper()
            required_rank = payload.get("required_rank", "INSPECTOR").upper()
            if payload.get("unauthorized") is True or (payload.get("by_pass_auth") is True):
                violations.append(cls._build_violation_dict(
                    "RULE_AUTH_01",
                    f"Assignment of {entity_id} to officer {actor_id} performed without required authority.",
                    {"officer_rank": officer_rank, "required_rank": required_rank, "payload": payload},
                    entity_type, entity_id, actor_id, district_id
                ))

        # 2. RULE_APPROV_01: Approval Outside Hierarchy
        if event_type in ["APPROVAL_APPROVED", "APPROVAL_SUBMITTED"]:
            if payload.get("outside_hierarchy") is True or payload.get("chain_of_command_valid") is False:
                violations.append(cls._build_violation_dict(
                    "RULE_APPROV_01",
                    f"Approval granted for {entity_id} by approver {actor_id} outside proper chain of command hierarchy.",
                    {"approver_id": actor_id, "entity_id": entity_id},
                    entity_type, entity_id, actor_id, district_id
                ))

        # 3. RULE_GOV_01: Missing Override Justification
        if event_type in ["ASSIGNMENT_OVERRIDDEN", "RECOMMENDATION_OVERRIDDEN"]:
            rationale = str(payload.get("rationale") or payload.get("override_justification") or "")
            if len(rationale.strip()) < 10 or payload.get("missing_justification") is True:
                violations.append(cls._build_violation_dict(
                    "RULE_GOV_01",
                    f"Assignment override for {entity_id} recorded without mandatory written justification.",
                    {"rationale_length": len(rationale), "rationale": rationale},
                    entity_type, entity_id, actor_id, district_id
                ))

        # 4. RULE_APPROV_02: Invalid Delegation
        if event_type in ["DELEGATION_CREATED", "APPROVAL_DELEGATED"]:
            duration_days = payload.get("duration_days", 0)
            if duration_days > 30 or payload.get("exceeds_max_delegation") is True:
                violations.append(cls._build_violation_dict(
                    "RULE_APPROV_02",
                    f"Delegation for user {actor_id} created with invalid duration of {duration_days} days (max 30 days).",
                    {"duration_days": duration_days, "max_permitted": 30},
                    entity_type, entity_id, actor_id, district_id
                ))

        # 5. RULE_APPROV_03: Expired Delegation Action
        if event_type in ["APPROVAL_APPROVED", "APPROVAL_ACTION"]:
            if payload.get("using_expired_delegation") is True or payload.get("delegation_expired") is True:
                violations.append(cls._build_violation_dict(
                    "RULE_APPROV_03",
                    f"Approval action executed by {actor_id} using an expired delegation window.",
                    {"delegation_id": payload.get("delegation_id")},
                    entity_type, entity_id, actor_id, district_id
                ))

        # 6. RULE_ASSIGN_01: Officer Over Capacity
        if event_type in ["ASSIGNMENT_CREATED", "TASK_ASSIGNED", "TASK_CREATED"]:
            active_workload = payload.get("active_workload", 0)
            capacity_limit = payload.get("capacity_limit", 10)
            if active_workload > capacity_limit or payload.get("over_capacity") is True:
                violations.append(cls._build_violation_dict(
                    "RULE_ASSIGN_01",
                    f"Task assigned to officer {actor_id} exceeding workload capacity limit ({active_workload}/{capacity_limit}).",
                    {"active_workload": active_workload, "capacity_limit": capacity_limit},
                    entity_type, entity_id, actor_id, district_id
                ))

        # 7. RULE_ASSIGN_02: Assignment Outside Jurisdiction
        if event_type in ["ASSIGNMENT_CREATED", "TASK_ASSIGNED", "TASK_CREATED"]:
            officer_district = payload.get("officer_district")
            case_district = payload.get("case_district")
            if officer_district and case_district and officer_district != case_district and not payload.get("cross_jurisdiction_authorized"):
                violations.append(cls._build_violation_dict(
                    "RULE_ASSIGN_02",
                    f"Officer from {officer_district} assigned to case in {case_district} without cross-boundary clearance.",
                    {"officer_district": officer_district, "case_district": case_district},
                    entity_type, entity_id, actor_id, district_id
                ))

        # 8. RULE_APPROV_04: Missing Mandatory Approval
        if event_type in ["TASK_COMPLETED", "CASE_CLOSED"]:
            if payload.get("requires_approval") is True and payload.get("approval_granted") is not True:
                violations.append(cls._build_violation_dict(
                    "RULE_APPROV_04",
                    f"Task or Investigation {entity_id} transitioned to complete without required mandatory approval.",
                    {"requires_approval": True, "approval_granted": False},
                    entity_type, entity_id, actor_id, district_id
                ))

        # 9. RULE_AUDIT_01: Missing Audit Trail
        if payload.get("missing_audit_trail") is True:
            violations.append(cls._build_violation_dict(
                "RULE_AUDIT_01",
                f"State transition on {entity_id} detected without corresponding entry in audit ledger.",
                {"entity_id": entity_id},
                entity_type, entity_id, actor_id, district_id
            ))

        # 10. RULE_AUDIT_02: Broken Hash Chain
        if event_type in ["HASH_CHAIN_CORRUPTED", "INTEGRITY_CHECK_FAILED"] or payload.get("broken_hash_chain") is True:
            violations.append(cls._build_violation_dict(
                "RULE_AUDIT_02",
                f"Cryptographic hash chain breakage detected at audit entry sequence {payload.get('sequence', 'N/A')}.",
                {"sequence": payload.get("sequence"), "expected_hash": payload.get("expected_hash")},
                entity_type, entity_id, actor_id, district_id
            ))

        # 11. RULE_NOTIF_01: Notification Delivery Failure
        if event_type in ["NOTIFICATION_FAILED", "ALERT_FAILED"] or payload.get("delivery_status") == "FAILED":
            violations.append(cls._build_violation_dict(
                "RULE_NOTIF_01",
                f"Critical operational alert {entity_id} failed delivery across all notification channels.",
                {"notification_id": entity_id, "channels": payload.get("channels")},
                entity_type, entity_id, actor_id, district_id
            ))

        # 12. RULE_NOTIF_02: Excessive Reminder Retries
        if payload.get("reminder_retries", 0) > 5 or payload.get("excessive_retries") is True:
            violations.append(cls._build_violation_dict(
                "RULE_NOTIF_02",
                f"Reminder for {entity_id} exceeded maximum retry bounds without officer response.",
                {"retries": payload.get("reminder_retries", 6)},
                entity_type, entity_id, actor_id, district_id
            ))

        # 13. RULE_ESCAL_01: SLA Breach
        if event_type in ["TASK_SLA_BREACHED", "APPROVAL_EXPIRED"] or payload.get("sla_breached") is True:
            violations.append(cls._build_violation_dict(
                "RULE_ESCAL_01",
                f"Operational SLA deadline breached for {entity_type} {entity_id}.",
                {"overdue_hours": payload.get("overdue_hours", 24)},
                entity_type, entity_id, actor_id, district_id
            ))

        # 14. RULE_EVID_01: Unauthorized Evidence View
        if event_type in ["EVIDENCE_VIEWED", "MEDIA_ACCESSED"]:
            if payload.get("unauthorized_access") is True or payload.get("case_assigned") is False:
                violations.append(cls._build_violation_dict(
                    "RULE_EVID_01",
                    f"Classified evidence {entity_id} accessed by unassigned officer {actor_id}.",
                    {"evidence_id": entity_id, "actor_id": actor_id},
                    entity_type, entity_id, actor_id, district_id
                ))

        # 15. RULE_EVID_02: Unauthorized Evidence Export
        if event_type in ["EVIDENCE_EXPORTED", "CASE_EXPORTED"]:
            user_role = str(payload.get("user_role") or "ANALYST").upper()
            if user_role not in ["ADMIN", "SUPERVISOR", "ACP", "DCP"] or payload.get("unauthorized_export") is True:
                violations.append(cls._build_violation_dict(
                    "RULE_EVID_02",
                    f"Evidence payload export attempted by officer {actor_id} lacking export authorization clearance.",
                    {"user_role": user_role, "export_format": payload.get("format")},
                    entity_type, entity_id, actor_id, district_id
                ))

        # 16. RULE_AUTH_02: Multiple Failed Logins
        if event_type in ["LOGIN_FAILED", "AUTH_FAILURE"]:
            failed_count = payload.get("failed_attempts", 1)
            if failed_count >= 3 or payload.get("multiple_failed_logins") is True:
                violations.append(cls._build_violation_dict(
                    "RULE_AUTH_02",
                    f"Multiple failed login attempts ({failed_count}) detected for account {actor_id}.",
                    {"failed_attempts": failed_count, "ip": payload.get("ip_address")},
                    "User", actor_id, actor_id, district_id
                ))

        # 17. RULE_AUTH_03: Privilege Escalation Attempt
        if event_type in ["PERMISSION_DENIED", "PRIVILEGE_ESCALATION_ATTEMPT"] or payload.get("privilege_escalation") is True:
            violations.append(cls._build_violation_dict(
                "RULE_AUTH_03",
                f"Privilege escalation attempt detected: user {actor_id} requested endpoint {payload.get('endpoint')} exceeding claims.",
                {"endpoint": payload.get("endpoint"), "user_role": payload.get("role")},
                "User", actor_id, actor_id, district_id
            ))

        # 18. RULE_APPROV_05: Concurrent Conflicting Approvals
        if payload.get("concurrent_conflict") is True:
            violations.append(cls._build_violation_dict(
                "RULE_APPROV_05",
                f"Concurrent conflicting approval states recorded for entity {entity_id}.",
                {"conflicting_approvers": payload.get("approvers")},
                entity_type, entity_id, actor_id, district_id
            ))

        # 19. RULE_GOV_02: Missing Supervisor Review
        if event_type in ["CASE_CLOSED", "INVESTIGATION_ARCHIVED"]:
            if payload.get("supervisor_reviewed") is not True:
                violations.append(cls._build_violation_dict(
                    "RULE_GOV_02",
                    f"Investigation workspace {entity_id} closed without mandatory supervisor review sign-off.",
                    {"supervisor_reviewed": False},
                    entity_type, entity_id, actor_id, district_id
                ))

        # 20. RULE_SYS_01: Policy Version Mismatch
        if payload.get("policy_version") and payload.get("policy_version") != "1.0.0":
            violations.append(cls._build_violation_dict(
                "RULE_SYS_01",
                f"Action on {entity_id} evaluated against non-current policy engine version {payload.get('policy_version')}.",
                {"event_policy_version": payload.get("policy_version"), "system_version": "1.0.0"},
                entity_type, entity_id, actor_id, district_id
            ))

        return violations

    @staticmethod
    def _build_violation_dict(
        rule_id: str,
        explanation: str,
        evidence: Dict[str, Any],
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        district_id: Optional[str] = None
    ) -> Dict[str, Any]:
        # Find rule metadata from defaults
        rule_meta = next((r for r in DEFAULT_COMPLIANCE_RULES if r["id"] == rule_id), None)
        return {
            "rule_id": rule_id,
            "rule_name": rule_meta["name"] if rule_meta else rule_id,
            "category": rule_meta["category"] if rule_meta else RuleCategory.OPERATIONAL.value,
            "severity": rule_meta["severity"] if rule_meta else SeverityLevel.MEDIUM.value,
            "explanation": explanation,
            "evidence": evidence,
            "remediation": rule_meta["remediation"] if rule_meta else "Review compliance policy guidelines.",
            "legal_reference": rule_meta.get("legal_reference") if rule_meta else None,
            "violated_entity_type": entity_type,
            "violated_entity_id": entity_id,
            "actor_id": actor_id,
            "district_id": district_id or "BANGALORE_CENTRAL"
        }
