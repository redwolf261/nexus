"""Executive Analytics DTO Contracts (Phase 8.3 Milestone 4).

Defines aggregated DTO models for the Executive Analytics & Command Oversight Layer,
including deterministic KPIs, district analytics, multi-period trends, operational heatmaps,
and the root ExecutiveDashboardDTO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any


@dataclass(frozen=True)
class KPIDTO:
    """Individual deterministic Key Performance Indicator DTO."""
    kpi_id: str
    name: str
    category: str  # INVESTIGATION / TASK / ASSIGNMENT / APPROVAL / EVIDENCE
    value: float
    unit: str  # count / pct / hours / ratio
    formula: str
    explanation: str
    trend: str  # UP / DOWN / STABLE
    confidence_score: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kpi_id": self.kpi_id,
            "name": self.name,
            "category": self.category,
            "value": round(self.value, 2) if isinstance(self.value, float) else self.value,
            "unit": self.unit,
            "formula": self.formula,
            "explanation": self.explanation,
            "trend": self.trend,
            "confidence_score": round(self.confidence_score, 2),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class DistrictAnalyticsDTO:
    """District operational performance snapshot DTO."""
    district_id: str
    district_name: str
    rank: int
    active_cases: int
    closed_cases: int
    backlog_count: int
    sla_compliance_pct: float
    avg_approval_delay_hours: float
    officer_utilization_pct: float
    supervisor_utilization_pct: float
    burnout_risk_score: float
    critical_cases_count: int
    district_health_score: float
    calculated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "district_id": self.district_id,
            "district_name": self.district_name,
            "rank": self.rank,
            "active_cases": self.active_cases,
            "closed_cases": self.closed_cases,
            "backlog_count": self.backlog_count,
            "sla_compliance_pct": round(self.sla_compliance_pct, 1),
            "avg_approval_delay_hours": round(self.avg_approval_delay_hours, 1),
            "officer_utilization_pct": round(self.officer_utilization_pct, 1),
            "supervisor_utilization_pct": round(self.supervisor_utilization_pct, 1),
            "burnout_risk_score": round(self.burnout_risk_score, 1),
            "critical_cases_count": self.critical_cases_count,
            "district_health_score": round(self.district_health_score, 1),
            "calculated_at": self.calculated_at,
        }


@dataclass(frozen=True)
class TrendDTO:
    """Historical moving average and growth rate statistics DTO."""
    metric_name: str
    period: str  # 7d / 30d / WoW / MoM
    current_value: float
    previous_value: float
    change_pct: float
    moving_average: float
    direction: str  # UP / DOWN / STABLE
    calculated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "period": self.period,
            "current_value": round(self.current_value, 2),
            "previous_value": round(self.previous_value, 2),
            "change_pct": round(self.change_pct, 2),
            "moving_average": round(self.moving_average, 2),
            "direction": self.direction,
            "calculated_at": self.calculated_at,
        }


@dataclass(frozen=True)
class HeatmapDTO:
    """Matrix grid of district risk, backlog, approval, burnout, and SLA metrics."""
    heatmap_type: str  # RISK / BACKLOG / APPROVAL_DELAY / BURNOUT / SLA
    district_scores: Dict[str, float]  # district_id -> score
    district_categories: Dict[str, str]  # district_id -> LOW / MEDIUM / HIGH / CRITICAL
    matrix_data: List[Dict[str, Any]]
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "heatmap_type": self.heatmap_type,
            "district_scores": {k: round(v, 1) for k, v in self.district_scores.items()},
            "district_categories": dict(self.district_categories),
            "matrix_data": list(self.matrix_data),
            "generated_at": self.generated_at,
        }


@dataclass(frozen=True)
class ExecutiveDashboardDTO:
    """Root aggregated executive dashboard payload DTO."""
    scope_role: str  # Supervisor / ACP / DCP / Admin
    district_id: Optional[str]
    kpis: List[KPIDTO]
    district_analytics: List[DistrictAnalyticsDTO]
    trends: List[TrendDTO]
    heatmaps: List[HeatmapDTO]
    summary_metrics: Dict[str, Any]
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scope_role": self.scope_role,
            "district_id": self.district_id,
            "kpis": [k.to_dict() for k in self.kpis],
            "district_analytics": [d.to_dict() for d in self.district_analytics],
            "trends": [t.to_dict() for t in self.trends],
            "heatmaps": [h.to_dict() for h in self.heatmaps],
            "summary_metrics": dict(self.summary_metrics),
            "generated_at": self.generated_at,
        }
