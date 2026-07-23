"""Supervisor Command Center Router (Phase 8.3 Milestone 1).

REST API endpoints for single-aggregated dashboard payload, active investigations,
analyst workloads, approval queue, SLA health alerts, intelligence feeds, and cache management.

Protected by JWT & RBAC (Supervisor, ACP, DCP, Admin).
"""

from typing import List, Dict, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.db.schema import User, Role
from backend.auth.deps import get_current_user, require_role
from backend.command_center.dashboard_service import DashboardAggregationService

router = APIRouter(prefix="/command-center", tags=["Supervisor Command Center"])


@router.get("/dashboard")
def get_supervisor_dashboard(
    district_id: Optional[str] = None,
    sort_cases_by: str = Query("sla_risk", enum=["sla_risk", "priority", "assignment_date", "workload"]),
    force_refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /command-center/dashboard — Single aggregated API payload powering the entire command workspace."""
    service = DashboardAggregationService(db)

    # Determine district scope by role
    user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    scoped_district = district_id
    if user_role == "Supervisor":
        # Supervisors restricted to their assigned district
        scoped_district = district_id or getattr(current_user, "district_id", None)

    dto = service.get_dashboard(
        district_id=scoped_district,
        sort_cases_by=sort_cases_by,
        force_refresh=force_refresh,
    )
    return dto.to_dict()


@router.get("/active-cases")
def get_active_cases(
    district_id: Optional[str] = None,
    sort_by: str = Query("sla_risk", enum=["sla_risk", "priority", "assignment_date", "workload"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /command-center/active-cases — Filterable and sortable active investigations."""
    service = DashboardAggregationService(db)
    dto = service.get_dashboard(district_id=district_id, sort_cases_by=sort_by)
    return [c.to_dict() for c in dto.active_cases]


@router.get("/analysts")
def get_analyst_workloads(
    district_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /command-center/analysts — Analyst workload, capacity %, and burnout risk breakdown."""
    service = DashboardAggregationService(db)
    dto = service.get_dashboard(district_id=district_id)
    return [a.to_dict() for a in dto.analyst_workloads]


@router.get("/approvals")
def get_approval_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /command-center/approvals — Pending supervisor and ACP/DCP approval queue."""
    service = DashboardAggregationService(db)
    dto = service.get_dashboard()
    return [q.to_dict() for q in dto.approval_queue]


@router.get("/sla-alerts")
def get_sla_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /command-center/sla-alerts — Task SLA risk categorizations (GREEN, YELLOW, RED, CRITICAL)."""
    service = DashboardAggregationService(db)
    dto = service.get_dashboard()
    return [s.to_dict() for s in dto.sla_alerts]


@router.get("/intelligence")
def get_intelligence_feed(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /command-center/intelligence — Phase 7 analytical intelligence alerts and explainability cards."""
    service = DashboardAggregationService(db)
    dto = service.get_dashboard()
    return [i.to_dict() for i in dto.intelligence_feed]


@router.get("/alerts")
def get_operational_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /command-center/alerts — Deterministic rule-based operational alerts."""
    service = DashboardAggregationService(db)
    dto = service.get_dashboard()
    return [a.to_dict() for a in dto.alerts]


@router.post("/refresh-cache")
def refresh_command_center_cache(
    district_id: Optional[str] = None,
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    DashboardAggregationService.invalidate_cache(district_id=district_id)
    return {"message": "Command center cache invalidated successfully.", "district_id": district_id}


# ── Phase 8.3 Milestone 2 Real-Time Endpoints ─────────────────────────────────

@router.post("/subscribe")
def subscribe_session(
    district_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """POST /command-center/subscribe — Create real-time WebSocket subscription session."""
    session, sub = SubscriptionRegistry.subscribe(
        user_id=current_user.id if hasattr(current_user, "id") else current_user.username,
        username=current_user.username,
        role=str(current_user.role),
        district_id=district_id or getattr(current_user, "district_id", None),
    )
    return {"session": session.to_presence_dto().to_dict(), "subscription_id": sub.subscription_id}


@router.post("/heartbeat")
def session_heartbeat(
    session_id: str = Query(...),
    activity: Optional[str] = Query(None),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """POST /command-center/heartbeat — Send keep-alive heartbeat and update presence activity."""
    success = SubscriptionRegistry.heartbeat(session_id, activity=activity)
    if not success:
        raise HTTPException(status_code=404, detail="Session expired or not found.")
    return {"session_id": session_id, "status": "ACTIVE", "activity": activity}


@router.get("/presence")
def get_presence(
    district_id: Optional[str] = Query(None),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /command-center/presence — Fetch active supervisor presence list."""
    target_district = district_id or getattr(current_user, "district_id", None)
    presence_list = PresenceService.get_presence_list(district_id=target_district)
    return [p.to_dict() for p in presence_list]


@router.post("/presence/activity")
def update_activity(
    session_id: str = Query(...),
    activity: str = Query(...),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """POST /command-center/presence/activity — Update active activity string for presence banner."""
    updated = PresenceService.update_activity(session_id, activity)
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found.")
    return updated.to_dict()


@router.get("/replay")
def replay_events(
    client_last_sequence: int = Query(0),
    district_id: Optional[str] = Query(None),
    current_user: User = Depends(require_role(Role.Supervisor)),
):
    """GET /command-center/replay — Replay missed sequence patches upon WebSocket reconnect."""
    target_district = district_id or getattr(current_user, "district_id", None)
    replay = ReplayService.compute_replay(client_last_sequence=client_last_sequence, district_id=target_district)
    return replay.to_dict()

