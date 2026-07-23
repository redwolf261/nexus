from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class RuleCategory(str, Enum):
    AUTHORIZATION = "AUTHORIZATION"
    ASSIGNMENT = "ASSIGNMENT"
    APPROVAL = "APPROVAL"
    GOVERNANCE = "GOVERNANCE"
    ESCALATION = "ESCALATION"
    NOTIFICATION = "NOTIFICATION"
    AUDIT = "AUDIT"
    EVIDENCE = "EVIDENCE"
    AUTHENTICATION = "AUTHENTICATION"
    INVESTIGATION = "INVESTIGATION"
    OPERATIONAL = "OPERATIONAL"


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskBand(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplianceRuleDTO(BaseModel):
    id: str
    name: str
    description: str
    category: RuleCategory
    severity: SeverityLevel
    enabled: bool = True
    version: int = 1
    policy_version: str = "1.0.0"
    evaluation_scope: str = "SYSTEM"  # SYSTEM, ENTITY, USER, DISTRICT
    remediation: str
    legal_reference: Optional[str] = None


class ComplianceViolationDTO(BaseModel):
    id: str
    rule_id: str
    rule_name: str
    category: RuleCategory
    severity: SeverityLevel
    violated_entity_type: Optional[str] = None
    violated_entity_id: Optional[str] = None
    actor_id: Optional[str] = None
    district_id: Optional[str] = None
    explanation: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    remediation: str
    legal_reference: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ComplianceRiskDTO(BaseModel):
    overall_score: float  # 0 - 100
    risk_band: RiskBand
    subsystem_breakdown: Dict[str, float] = Field(default_factory=dict)
    contributing_factors: List[Dict[str, Any]] = Field(default_factory=list)
    total_active_violations: int = 0
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class ComplianceDashboardDTO(BaseModel):
    compliance_score: float  # 100 - overall_score
    risk_summary: ComplianceRiskDTO
    active_violations: List[ComplianceViolationDTO]
    violations_by_severity: Dict[str, int]
    violations_by_district: Dict[str, int]
    violations_by_subsystem: Dict[str, int]
    trend_7d: List[Dict[str, Any]]
    trend_30d: List[Dict[str, Any]]
    top_recurring_rules: List[Dict[str, Any]]
    outstanding_remediation_count: int


class ComplianceFilterDTO(BaseModel):
    category: Optional[RuleCategory] = None
    severity: Optional[SeverityLevel] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    actor_id: Optional[str] = None
    district_id: Optional[str] = None
    resolved: Optional[bool] = False
    page: int = 1
    page_size: int = 50


class ScanRequestDTO(BaseModel):
    scan_scope: str = "INCREMENTAL"  # INCREMENTAL, FULL, ENTITY, USER, DISTRICT
    target_entity_type: Optional[str] = None
    target_entity_id: Optional[str] = None
    target_user_id: Optional[str] = None
    target_district_id: Optional[str] = None
