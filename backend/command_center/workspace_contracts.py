"""Investigation Workspace DTO Contracts (Phase 8.3 Milestone 3).

Defines aggregated DTO models for the Supervisor Operational Investigation Workspace,
including timeline events, case health score breakdowns, decision support recommendations,
and supervisor action payloads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any


@dataclass(frozen=True)
class TimelineEventDTO:
    """Represents a single chronological event on the investigation timeline."""
    event_id: str
    investigation_id: str
    timestamp: str
    actor: str  # e.g., "Supervisor John", "System", "Officer Smith"
    event_type: str  # TASK_CREATED, ASSIGNMENT_OVERRIDDEN, EVIDENCE_ATTACHED, etc.
    category: str  # TASK, ASSIGNMENT, GOVERNANCE, EVIDENCE, ANALYTICAL, NOTE, ACTION
    title: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "investigation_id": self.investigation_id,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "event_type": self.event_type,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CaseHealthDTO:
    """Deterministic operational case health score breakdown (0–100)."""
    investigation_id: str
    score: float  # 0.0 - 100.0
    category: str  # HEALTHY (80-100), MONITOR (60-79), ATTENTION (40-59), CRITICAL (0-39)
    factor_scores: Dict[str, float]  # Component breakdowns
    explanations: List[str]  # Human-readable reasons
    calculated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "score": round(self.score, 1),
            "category": self.category,
            "factor_scores": {k: round(v, 1) for k, v in self.factor_scores.items()},
            "explanations": list(self.explanations),
            "calculated_at": self.calculated_at,
        }


@dataclass(frozen=True)
class DecisionRecommendationDTO:
    """Deterministic supervisor decision support recommendation item."""
    recommendation_id: str
    investigation_id: str
    rule_code: str
    reason: str
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    recommended_action: str
    supporting_evidence: List[str]
    confidence_score: float  # Deterministic score (0.0 - 1.0)
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "investigation_id": self.investigation_id,
            "rule_code": self.rule_code,
            "reason": self.reason,
            "priority": self.priority,
            "recommended_action": self.recommended_action,
            "supporting_evidence": list(self.supporting_evidence),
            "confidence_score": round(self.confidence_score, 2),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class SupervisorActionPayload:
    """Request payload for executing a supervisor operational action."""
    action_type: str  # ASSIGN, REASSIGN, APPROVE, REJECT, ESCALATE, PAUSE, RESUME, CLOSE, etc.
    target_officer_id: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InvestigationWorkspaceDTO:
    """Single aggregated DTO for the Supervisor Operational Investigation Workspace."""
    investigation_id: str
    summary: Dict[str, Any]  # ID, Title, Priority, Status, Case Type, District
    assigned_analyst: Optional[Dict[str, Any]]
    supervisor: Optional[Dict[str, Any]]
    case_age_hours: float
    sla_utilization_pct: float
    evidence_summary: Dict[str, Any]
    task_progress: Dict[str, Any]  # Total, Completed, Active, Blocked, Progress %
    intelligence_summary: Dict[str, Any]  # Discoveries, Confidence
    linked_entities: List[Dict[str, Any]]
    crime_series_participation: List[Dict[str, Any]]
    spatial_hotspot_membership: List[Dict[str, Any]]
    graph_metrics_summary: Dict[str, Any]
    health: CaseHealthDTO
    recommendations: List[DecisionRecommendationDTO]
    timeline_summary: List[TimelineEventDTO]
    recent_activity: List[TimelineEventDTO]
    approval_status: Dict[str, Any]
    escalation_status: Dict[str, Any]
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "summary": dict(self.summary),
            "assigned_analyst": dict(self.assigned_analyst) if self.assigned_analyst else None,
            "supervisor": dict(self.supervisor) if self.supervisor else None,
            "case_age_hours": round(self.case_age_hours, 1),
            "sla_utilization_pct": round(self.sla_utilization_pct, 1),
            "evidence_summary": dict(self.evidence_summary),
            "task_progress": dict(self.task_progress),
            "intelligence_summary": dict(self.intelligence_summary),
            "linked_entities": list(self.linked_entities),
            "crime_series_participation": list(self.crime_series_participation),
            "spatial_hotspot_membership": list(self.spatial_hotspot_membership),
            "graph_metrics_summary": dict(self.graph_metrics_summary),
            "health": self.health.to_dict(),
            "recommendations": [r.to_dict() for r in self.recommendations],
            "timeline_summary": [t.to_dict() for t in self.timeline_summary],
            "recent_activity": [a.to_dict() for a in self.recent_activity],
            "approval_status": dict(self.approval_status),
            "escalation_status": dict(self.escalation_status),
            "generated_at": self.generated_at,
        }
