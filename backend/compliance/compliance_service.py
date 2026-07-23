import json
import csv
import io
import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.compliance.schema import ComplianceViolationRecord, ComplianceRuleRecord
from backend.compliance.rule_repository import RuleRepository
from backend.compliance.risk_engine import RiskEngine
from backend.compliance.monitor import ComplianceMonitor
from backend.compliance.compliance_contracts import (
    ComplianceDashboardDTO, ComplianceRiskDTO, ComplianceViolationDTO,
    ComplianceFilterDTO, ComplianceRuleDTO, RuleCategory, SeverityLevel
)


class ComplianceService:
    @classmethod
    def get_dashboard(cls, db: Session) -> ComplianceDashboardDTO:
        RuleRepository.seed_default_rules(db)
        
        # Calculate live risk summary
        risk_summary = RiskEngine.calculate_risk(db)
        compliance_score = round(max(0.0, 100.0 - risk_summary.overall_score), 2)

        # Fetch active violations
        active_recs, _ = RuleRepository.get_active_violations(db, filters=ComplianceFilterDTO(page=1, page_size=100))
        active_dtos = [RuleRepository.record_to_dto(r) for r in active_recs]

        # Breakdowns
        violations_by_severity = {
            SeverityLevel.CRITICAL.value: 0,
            SeverityLevel.HIGH.value: 0,
            SeverityLevel.MEDIUM.value: 0,
            SeverityLevel.LOW.value: 0
        }
        violations_by_district: Dict[str, int] = {}
        violations_by_subsystem: Dict[str, int] = {}
        rule_counts: Dict[str, int] = {}

        all_active = db.query(ComplianceViolationRecord).filter_by(resolved=False).all()
        for v in all_active:
            sev = v.severity.upper()
            if sev in violations_by_severity:
                violations_by_severity[sev] += 1

            dist = v.district_id or "BANGALORE_CENTRAL"
            violations_by_district[dist] = violations_by_district.get(dist, 0) + 1

            sub = v.category.upper()
            violations_by_subsystem[sub] = violations_by_subsystem.get(sub, 0) + 1

            rule_counts[v.rule_name] = rule_counts.get(v.rule_name, 0) + 1

        # Top recurring rules
        sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_recurring = [{"rule_name": r[0], "count": r[1]} for r in sorted_rules]

        # 7d and 30d synthetic trend samples
        today = datetime.date.today()
        trend_7d = [
            {"date": (today - datetime.timedelta(days=i)).isoformat(), "score": max(50.0, compliance_score - i * 0.5)}
            for i in range(6, -1, -1)
        ]
        trend_30d = [
            {"date": (today - datetime.timedelta(days=i * 5)).isoformat(), "score": max(50.0, compliance_score - i * 0.2)}
            for i in range(5, -1, -1)
        ]

        return ComplianceDashboardDTO(
            compliance_score=compliance_score,
            risk_summary=risk_summary,
            active_violations=active_dtos[:20],
            violations_by_severity=violations_by_severity,
            violations_by_district=violations_by_district,
            violations_by_subsystem=violations_by_subsystem,
            trend_7d=trend_7d,
            trend_30d=trend_30d,
            top_recurring_rules=top_recurring,
            outstanding_remediation_count=len(all_active)
        )

    @classmethod
    def get_violations(cls, db: Session, filters: ComplianceFilterDTO) -> Tuple[List[ComplianceViolationDTO], int]:
        records, total = RuleRepository.get_active_violations(db, filters)
        return [RuleRepository.record_to_dto(r) for r in records], total

    @classmethod
    def get_rules(cls, db: Session) -> List[ComplianceRuleDTO]:
        RuleRepository.seed_default_rules(db)
        recs = RuleRepository.get_all_rules(db)
        return [
            ComplianceRuleDTO(
                id=r.id,
                name=r.name,
                description=r.description,
                category=RuleCategory(r.category) if r.category in RuleCategory.__members__ else RuleCategory.OPERATIONAL,
                severity=SeverityLevel(r.severity) if r.severity in SeverityLevel.__members__ else SeverityLevel.MEDIUM,
                enabled=r.enabled,
                version=r.version,
                policy_version=r.policy_version,
                evaluation_scope=r.evaluation_scope,
                remediation=r.remediation,
                legal_reference=r.legal_reference
            ) for r in recs
        ]

    @classmethod
    def export_report(cls, db: Session, filters: ComplianceFilterDTO, export_format: str = "json") -> str:
        records, _ = RuleRepository.get_active_violations(db, filters)
        dtos = [RuleRepository.record_to_dto(r) for r in records]

        if export_format.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "id", "timestamp", "rule_id", "rule_name", "category", "severity",
                "entity_type", "entity_id", "actor_id", "district_id", "explanation", "remediation"
            ])
            for d in dtos:
                writer.writerow([
                    d.id, d.timestamp.isoformat(), d.rule_id, d.rule_name,
                    d.category.value if hasattr(d.category, "value") else str(d.category),
                    d.severity.value if hasattr(d.severity, "value") else str(d.severity),
                    d.violated_entity_type or "", d.violated_entity_id or "",
                    d.actor_id or "", d.district_id or "", d.explanation, d.remediation
                ])
            return output.getvalue()

        elif export_format.lower() == "ndjson":
            lines = [d.model_dump_json() for d in dtos]
            return "\n".join(lines)

        else:
            return json.dumps([d.model_dump(mode="json") for d in dtos], indent=2, default=str)
