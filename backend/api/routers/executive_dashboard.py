"""Executive Dashboard Router (Phase 8.3 Milestone 4).

Exposes REST API endpoints for the Executive Analytics & Command Oversight Layer:
dashboard aggregation, KPIs, trends, heatmaps, district rankings, and executive summaries.
"""

from __future__ import annotations

from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db, get_current_user, require_role
from backend.db.schema import User, Role
from backend.command_center.executive_dashboard import ExecutiveDashboardAggregator
from backend.command_center.kpi_engine import KPIEngine
from backend.command_center.district_analytics import DistrictAnalyticsEngine
from backend.command_center.trend_engine import TrendAnalysisEngine
from backend.command_center.heatmap_engine import HeatmapEngine


router = APIRouter(prefix="/executive", tags=["Executive Dashboard"])


@router.get("/dashboard")
def get_executive_dashboard(
    district_id: Optional[str] = Query(None),
    force_refresh: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([Role.Supervisor, Role.ACP, Role.DCP, Role.Admin])),
):
    """GET /executive/dashboard — Fetch root aggregated executive dashboard DTO."""
    user_role = str(getattr(current_user, "role", Role.DCP))
    aggregator = ExecutiveDashboardAggregator(db)
    dto = aggregator.get_dashboard(scope_role=user_role, district_id=district_id, force_refresh=force_refresh)
    return dto.to_dict()


@router.get("/kpis")
def get_kpis(
    district_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([Role.Supervisor, Role.ACP, Role.DCP, Role.Admin])),
):
    """GET /executive/kpis — Fetch deterministic Key Performance Indicators."""
    engine = KPIEngine(db)
    kpis = engine.calculate_all_kpis(district_id=district_id)
    if category:
        kpis = [k for k in kpis if k.category.upper() == category.upper()]
    return [k.to_dict() for k in kpis]


@router.get("/trends")
def get_trends(
    district_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([Role.Supervisor, Role.ACP, Role.DCP, Role.Admin])),
):
    """GET /executive/trends — Fetch multi-period trend statistics."""
    engine = TrendAnalysisEngine(db)
    trends = engine.calculate_trends(district_id=district_id)
    return [t.to_dict() for t in trends]


@router.get("/heatmaps")
def get_heatmaps(
    heatmap_type: Optional[str] = Query(None),
    district_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([Role.Supervisor, Role.ACP, Role.DCP, Role.Admin])),
):
    """GET /executive/heatmaps — Fetch operational district risk and backlog heatmaps."""
    engine = HeatmapEngine(db)
    if heatmap_type:
        hm = engine.generate_heatmap(heatmap_type=heatmap_type, district_id=district_id)
        return [hm.to_dict()]
    else:
        hms = engine.generate_all_heatmaps(district_id=district_id)
        return [h.to_dict() for h in hms]


@router.get("/districts")
def get_districts(
    district_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([Role.Supervisor, Role.ACP, Role.DCP, Role.Admin])),
):
    """GET /executive/districts — Fetch district operational rankings and analytics."""
    user_role = str(getattr(current_user, "role", Role.DCP))
    engine = DistrictAnalyticsEngine(db)
    districts = engine.get_district_analytics(caller_role=user_role, user_district_id=district_id)
    return [d.to_dict() for d in districts]


@router.get("/summary")
def get_executive_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([Role.Supervisor, Role.ACP, Role.DCP, Role.Admin])),
):
    """GET /executive/summary — Fetch compact executive summary metrics."""
    aggregator = ExecutiveDashboardAggregator(db)
    user_role = str(getattr(current_user, "role", Role.DCP))
    dto = aggregator.get_dashboard(scope_role=user_role)
    return dto.summary_metrics
