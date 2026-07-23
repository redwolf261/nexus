"""Investigation Workspace Router (Phase 8.3 Milestone 3).

Exposes REST API endpoints for the Supervisor Operational Investigation Workspace:
aggregated workspace DTO, unified timeline, case health scores, decision recommendations,
supervisor operational actions, and activity feeds.
"""

from __future__ import annotations

from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db, get_current_user, require_role
from backend.db.schema import User, Role
from backend.command_center.workspace_contracts import SupervisorActionPayload
from backend.command_center.workspace_aggregator import InvestigationWorkspaceAggregator
from backend.command_center.timeline_service import InvestigationTimelineService
from backend.command_center.case_health_engine import CaseHealthEngine
from backend.command_center.decision_support_engine import DecisionSupportEngine
from backend.command_center.supervisor_action_engine import SupervisorActionEngine


router = APIRouter(prefix="/workspace", tags=["Investigation Workspace"])


@router.get("/{investigation_id}")
def get_workspace(
    investigation_id: str,
    force_refresh: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /workspace/{id} — Fetch single aggregated investigation workspace DTO."""
    aggregator = InvestigationWorkspaceAggregator(db)
    try:
        dto = aggregator.get_workspace(investigation_id, force_refresh=force_refresh)
        return dto.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{investigation_id}/timeline")
def get_timeline(
    investigation_id: str,
    category: Optional[str] = Query(None),
    cursor: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /workspace/{id}/timeline — Fetch unified investigation timeline with cursor pagination."""
    service = InvestigationTimelineService(db)
    events, next_cursor = service.get_timeline(investigation_id, category_filter=category, cursor=cursor, limit=limit)
    return {
        "investigation_id": investigation_id,
        "events": [e.to_dict() for e in events],
        "next_cursor": next_cursor,
        "total_returned": len(events),
    }


@router.get("/{investigation_id}/health")
def get_case_health(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /workspace/{id}/health — Fetch operational case health score and category."""
    engine = CaseHealthEngine(db)
    health = engine.calculate_health(investigation_id)
    return health.to_dict()


@router.get("/{investigation_id}/recommendations")
def get_recommendations(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /workspace/{id}/recommendations — Fetch decision support supervisor recommendations."""
    engine = DecisionSupportEngine(db)
    recs = engine.generate_recommendations(investigation_id)
    return [r.to_dict() for r in recs]


@router.post("/{investigation_id}/actions")
def execute_supervisor_action(
    investigation_id: str,
    payload: SupervisorActionPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """POST /workspace/{id}/actions — Execute supervisor operational action with workflow governance."""
    engine = SupervisorActionEngine(db)
    supervisor_id = current_user.id if hasattr(current_user, "id") else current_user.username
    try:
        res = engine.execute_action(investigation_id, supervisor_id=supervisor_id, payload=payload)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{investigation_id}/refresh")
def refresh_workspace(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """POST /workspace/{id}/refresh — Force refresh of workspace in-memory cache."""
    InvestigationWorkspaceAggregator.invalidate_workspace_cache(investigation_id)
    aggregator = InvestigationWorkspaceAggregator(db)
    dto = aggregator.get_workspace(investigation_id, force_refresh=True)
    return {"message": f"Workspace '{investigation_id}' refreshed.", "workspace": dto.to_dict()}


@router.get("/{investigation_id}/activity")
def get_recent_activity(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /workspace/{id}/activity — Fetch recent operational activity stream."""
    service = InvestigationTimelineService(db)
    events, _ = service.get_timeline(investigation_id, limit=10)
    return [e.to_dict() for e in events]


@router.get("/{investigation_id}/summary")
def get_summary(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /workspace/{id}/summary — Fetch compact workspace summary DTO."""
    aggregator = InvestigationWorkspaceAggregator(db)
    try:
        dto = aggregator.get_workspace(investigation_id)
        return {
            "investigation_id": dto.investigation_id,
            "summary": dto.summary,
            "assigned_analyst": dto.assigned_analyst,
            "case_age_hours": dto.case_age_hours,
            "sla_utilization_pct": dto.sla_utilization_pct,
            "health_score": dto.health.score,
            "health_category": dto.health.category,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
