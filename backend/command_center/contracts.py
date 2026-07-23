"""Supervisor Command Center Contracts & DTOs (Phase 8.3 Milestone 1).

Immutable, serializable DTOs for the unified operational command dashboard.
Combines active investigations, analyst workloads, approval queue, SLA health,
analytical intelligence feeds, operational metrics, and rule-based alerts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass(frozen=True)
class ActiveInvestigationItem:
    """Operational item for active investigation monitoring."""
    id: str
    title: str
    priority: str
    assigned_officer_id: Optional[str]
    assigned_officer_name: Optional[str]
    status: str
    progress_pct: float
    remaining_sla_seconds: Optional[float]
    workload_weight: float
    assignment_age_hours: float
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "assigned_officer_id": self.assigned_officer_id,
            "assigned_officer_name": self.assigned_officer_name,
            "status": self.status,
            "progress_pct": round(self.progress_pct, 1),
            "remaining_sla_seconds": round(self.remaining_sla_seconds, 1) if self.remaining_sla_seconds is not None else None,
            "workload_weight": round(self.workload_weight, 2),
            "assignment_age_hours": round(self.assignment_age_hours, 1),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class AnalystWorkloadItem:
    """Operational item for analyst/officer workload and burnout monitoring."""
    officer_id: str
    name: str
    rank: str
    district_id: Optional[str]
    availability_status: str
    current_case_count: int
    current_task_count: int
    weighted_workload: float
    burnout_score: float
    burnout_risk_band: str
    capacity_used_pct: float
    skills: List[str]
    recommendation_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "officer_id": self.officer_id,
            "name": self.name,
            "rank": self.rank,
            "district_id": self.district_id,
            "availability_status": self.availability_status,
            "current_case_count": self.current_case_count,
            "current_task_count": self.current_task_count,
            "weighted_workload": round(self.weighted_workload, 2),
            "burnout_score": round(self.burnout_score, 1),
            "burnout_risk_band": self.burnout_risk_band,
            "capacity_used_pct": round(self.capacity_used_pct, 1),
            "skills": list(self.skills),
            "recommendation_score": round(self.recommendation_score, 3) if self.recommendation_score is not None else None,
        }


@dataclass(frozen=True)
class ApprovalQueueItem:
    """Operational item for supervisor and ACP/DCP approval queues."""
    approval_id: str
    investigation_id: str
    decision_type: str
    chosen_officer_id: Optional[str]
    supervisor_id: str
    required_role: str
    override_reason: Optional[str]
    justification: Optional[str]
    status: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "investigation_id": self.investigation_id,
            "decision_type": self.decision_type,
            "chosen_officer_id": self.chosen_officer_id,
            "supervisor_id": self.supervisor_id,
            "required_role": self.required_role,
            "override_reason": self.override_reason,
            "justification": self.justification,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class SLAAlertItem:
    """Operational item for SLA risk categorizations (GREEN, YELLOW, RED, CRITICAL)."""
    task_id: str
    investigation_id: str
    task_title: str
    assigned_officer_id: Optional[str]
    sla_category: str  # GREEN / YELLOW / RED / CRITICAL
    remaining_sla_seconds: float
    due_at: Optional[str]
    breach_age_hours: Optional[float]
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "investigation_id": self.investigation_id,
            "task_title": self.task_title,
            "assigned_officer_id": self.assigned_officer_id,
            "sla_category": self.sla_category,
            "remaining_sla_seconds": round(self.remaining_sla_seconds, 1),
            "due_at": self.due_at,
            "breach_age_hours": round(self.breach_age_hours, 1) if self.breach_age_hours is not None else None,
            "recommended_action": self.recommended_action,
        }


@dataclass(frozen=True)
class IntelligenceFeedItem:
    """Operational item for Phase 7 analytical intelligence feeds."""
    alert_id: str
    alert_type: str  # CRIME_SERIES / ENTITY_RESOLUTION / TEMPORAL / SPATIAL / GRAPH
    title: str
    summary: str
    confidence_score: float
    affected_entities: List[str]
    explainability_card_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "title": self.title,
            "summary": self.summary,
            "confidence_score": round(self.confidence_score, 2),
            "affected_entities": list(self.affected_entities),
            "explainability_card_id": self.explainability_card_id,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class OperationalAlertItem:
    """Rule-based operational alert item generated by OperationalAlertEngine."""
    alert_id: str
    severity: str  # INFO / WARNING / CRITICAL
    rule_code: str
    message: str
    target_id: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity,
            "rule_code": self.rule_code,
            "message": self.message,
            "target_id": self.target_id,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class CommandMetricsDTO:
    """Operational summary metrics for the command dashboard."""
    open_investigations: int
    avg_workload_weight: float
    avg_assignment_delay_hours: float
    approvals_pending: int
    critical_alerts_count: int
    analysts_online: int
    cases_nearing_sla: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "open_investigations": self.open_investigations,
            "avg_workload_weight": round(self.avg_workload_weight, 2),
            "avg_assignment_delay_hours": round(self.avg_assignment_delay_hours, 1),
            "approvals_pending": self.approvals_pending,
            "critical_alerts_count": self.critical_alerts_count,
            "analysts_online": self.analysts_online,
            "cases_nearing_sla": self.cases_nearing_sla,
        }


@dataclass(frozen=True)
class SupervisorDashboardDTO:
    """Aggregated root DTO powering the Supervisor Command Center workspace."""
    active_cases: List[ActiveInvestigationItem]
    analyst_workloads: List[AnalystWorkloadItem]
    approval_queue: List[ApprovalQueueItem]
    sla_alerts: List[SLAAlertItem]
    intelligence_feed: List[IntelligenceFeedItem]
    alerts: List[OperationalAlertItem]
    metrics: CommandMetricsDTO
    generated_at: str
    sequence: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_cases": [c.to_dict() for c in self.active_cases],
            "analyst_workloads": [a.to_dict() for a in self.analyst_workloads],
            "approval_queue": [q.to_dict() for q in self.approval_queue],
            "sla_alerts": [s.to_dict() for s in self.sla_alerts],
            "intelligence_feed": [i.to_dict() for i in self.intelligence_feed],
            "alerts": [alt.to_dict() for alt in self.alerts],
            "metrics": self.metrics.to_dict(),
            "generated_at": self.generated_at,
            "sequence": self.sequence,
        }


# ── Phase 8.3 Milestone 2 Real-Time DTOs ─────────────────────────────────────

@dataclass(frozen=True)
class DashboardPatchDTO:
    """Serializable incremental patch representing updates to specific dashboard sections."""
    patch_id: str
    target_sections: List[str]  # e.g., ["active_cases", "metrics", "workload"]
    delta_data: Dict[str, Any]
    timestamp: str
    sequence: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "target_sections": list(self.target_sections),
            "delta_data": dict(self.delta_data),
            "timestamp": self.timestamp,
            "sequence": self.sequence,
        }


@dataclass(frozen=True)
class PresenceStatusDTO:
    """Serializable snapshot of active supervisor presence and collaborative awareness."""
    session_id: str
    user_id: str
    username: str
    role: str
    district_id: Optional[str]
    current_activity: str  # e.g., "Reviewing Case INV-2026-001"
    last_heartbeat: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "district_id": self.district_id,
            "current_activity": self.current_activity,
            "last_heartbeat": self.last_heartbeat,
        }


@dataclass(frozen=True)
class NotificationDigestDTO:
    """Prioritized and deduplicated operational alert digest DTO."""
    digest_id: str
    priority: str  # CRITICAL / HIGH / MEDIUM / LOW
    collapsed_count: int
    summary_message: str
    target_ids: List[str]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "digest_id": self.digest_id,
            "priority": self.priority,
            "collapsed_count": self.collapsed_count,
            "summary_message": self.summary_message,
            "target_ids": list(self.target_ids),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class ReplayResponseDTO:
    """Response payload for WebSocket sequence reconnect replay."""
    client_last_sequence: int
    current_sequence: int
    missed_patches: List[DashboardPatchDTO]
    is_gap_detected: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_last_sequence": self.client_last_sequence,
            "current_sequence": self.current_sequence,
            "missed_patches": [p.to_dict() for p in self.missed_patches],
            "is_gap_detected": self.is_gap_detected,
        }

