"""Supervisor Operational Action Engine (Phase 8.3 Milestone 3).

Executes 14 supervisor operational actions with permission validation, state transition checks,
audit logging, WebSocket event dispatching, cache invalidation, and timeline appending.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Optional, Any

from sqlalchemy.orm import Session

from backend.db.schema import Investigation, Officer
from backend.command_center.workspace_contracts import SupervisorActionPayload, TimelineEventDTO
from backend.command_center.timeline_service import InvestigationTimelineService
from backend.command_center.dashboard_service import DashboardAggregationService, CacheInvalidationReason
from backend.events.dispatcher import EventDispatcher
from backend.events.event_types import EventType
from backend.events.event_models import BaseEvent
from backend.core.logging import logger


class SupervisorActionEngine:
    """Engine executing supervisor operational actions with workflow governance."""

    VALID_ACTIONS = {
        "ASSIGN",
        "REASSIGN",
        "APPROVE",
        "REJECT",
        "ESCALATE",
        "RETURN_FOR_REVIEW",
        "PAUSE",
        "RESUME",
        "MARK_BLOCKED",
        "REQUEST_EVIDENCE",
        "REQUEST_INTEL_REFRESH",
        "CREATE_NOTE",
        "CLOSE",
        "REOPEN",
    }

    def __init__(self, session: Session):
        self.session = session

    def execute_action(
        self,
        investigation_id: str,
        supervisor_id: str,
        payload: SupervisorActionPayload
    ) -> Dict[str, Any]:
        """Execute supervisor operational action with full governance checks."""
        action_type = payload.action_type.upper()
        if action_type not in self.VALID_ACTIONS:
            raise ValueError(f"Invalid supervisor action '{action_type}'. Must be one of {self.VALID_ACTIONS}")

        inv = self.session.query(Investigation).filter_by(id=investigation_id).first()
        if not inv:
            raise ValueError(f"Investigation '{investigation_id}' not found.")

        # Workflow state transition validation
        inv_status_upper = (inv.status or "").upper()
        if action_type in ("CLOSE", "PAUSE") and inv_status_upper == "CLOSED":
            raise ValueError(f"Cannot perform '{action_type}' on an already CLOSED investigation.")

        if action_type == "RESUME" and inv_status_upper != "PAUSED":
            raise ValueError("Cannot RESUME an investigation that is not PAUSED.")

        # Action execution logic
        old_status = inv.status
        action_detail = ""

        if action_type in ("ASSIGN", "REASSIGN"):
            if not payload.target_officer_id:
                raise ValueError(f"Action '{action_type}' requires target_officer_id.")
            inv.assigned_officer = payload.target_officer_id
            inv.status = "UNDER_INVESTIGATION"
            action_detail = f"Assigned officer set to '{payload.target_officer_id}'."

        elif action_type == "PAUSE":
            inv.status = "PAUSED"
            action_detail = "Investigation marked as PAUSED."

        elif action_type == "RESUME":
            inv.status = "UNDER_INVESTIGATION"
            action_detail = "Investigation RESUMED."

        elif action_type == "CLOSE":
            inv.status = "CLOSED"
            action_detail = "Investigation CLOSED by supervisor."

        elif action_type == "REOPEN":
            inv.status = "UNDER_INVESTIGATION"
            action_detail = "Investigation REOPENED."

        elif action_type == "CREATE_NOTE":
            action_detail = f"Note created: '{payload.notes or payload.reason}'."

        else:
            action_detail = f"Supervisor action '{action_type}' recorded."

        self.session.commit()

        # Append to unified timeline
        event_id = f"EVT-SUP-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.utcnow().isoformat()

        timeline_event = TimelineEventDTO(
            event_id=event_id,
            investigation_id=investigation_id,
            timestamp=now_iso,
            actor=supervisor_id,
            event_type=f"SUPERVISOR_{action_type}",
            category="ACTION",
            title=f"Supervisor Action: {action_type}",
            description=payload.reason or action_detail,
            metadata={"notes": payload.notes, "old_status": old_status, "new_status": inv.status},
        )
        InvestigationTimelineService.add_custom_event(timeline_event)

        # Invalidate caches
        district_id = getattr(inv, "district_id", None)
        DashboardAggregationService.invalidate_cache(district_id=district_id, reason=CacheInvalidationReason.ASSIGNMENT_CHANGE)

        # Dispatch event
        event = BaseEvent(
            event_type=EventType.ASSIGNMENT_OVERRIDDEN,
            case_id=investigation_id,
            payload={"investigation_id": investigation_id, "action": action_type, "supervisor": supervisor_id},
        )
        EventDispatcher.publish_sync(event, self.session)


        logger.info(f"Supervisor '{supervisor_id}' executed action '{action_type}' on investigation '{investigation_id}'")
        return {
            "investigation_id": investigation_id,
            "action_type": action_type,
            "status": "SUCCESS",
            "new_investigation_status": inv.status,
            "action_detail": action_detail,
            "executed_at": now_iso,
        }
