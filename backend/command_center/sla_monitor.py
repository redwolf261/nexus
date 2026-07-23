"""SLA Monitor Service (Phase 8.3 Milestone 1).

Deterministic service that monitors task SLA statuses, categorizes risk into
GREEN, YELLOW, RED, and CRITICAL bands, and suggests operational recommendations.
Uses existing Task Engine and DB schemas without duplicating business logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Optional, Any

from sqlalchemy.orm import Session

from backend.db.schema import InvestigationTask, SLAState, TaskStatus
from backend.command_center.contracts import SLAAlertItem


class SLAMonitorService:
    """Service for monitoring SLA health across open tasks and investigations."""

    def __init__(self, session: Session):
        self.session = session

    def evaluate_task_sla(self, task: InvestigationTask) -> SLAAlertItem:
        """Evaluate SLA category, remaining time, and recommended action for a single task."""
        now = datetime.utcnow()
        due_at = task.due_at or (now + (task.sla_duration if hasattr(task, "sla_duration") and task.sla_duration else datetime.resolution))

        remaining_seconds = (due_at - now).total_seconds() if task.due_at else 86400.0
        breach_age_hours = None

        if remaining_seconds < 0:
            category = "CRITICAL"
            breach_age_hours = abs(remaining_seconds) / 3600.0
            rec_action = f"IMMEDIATE ESCALATION: Task breached by {breach_age_hours:.1f}h. Reassign or escalate to ACP."
        elif remaining_seconds < 7200.0:  # < 2 hours
            category = "RED"
            rec_action = "HIGH RISK: Less than 2 hours remaining. Prioritize immediately."
        elif remaining_seconds < 28800.0:  # < 8 hours
            category = "YELLOW"
            rec_action = "ELEVATED RISK: Approaching SLA limit within 8 hours. Monitor progress."
        else:
            category = "GREEN"
            rec_action = "ON SCHEDULE: Task progressing within normal SLA parameters."

        return SLAAlertItem(
            task_id=task.id,
            investigation_id=task.investigation_id,
            task_title=task.title or "Untitled Task",
            assigned_officer_id=task.assigned_officer_id,
            sla_category=category,
            remaining_sla_seconds=remaining_seconds,
            due_at=due_at.isoformat() if due_at else None,
            breach_age_hours=breach_age_hours,
            recommended_action=rec_action,
        )

    def get_active_sla_alerts(self, limit: int = 50) -> List[SLAAlertItem]:
        """Fetch open tasks ordered by SLA urgency."""
        tasks = self.session.query(InvestigationTask).filter(
            InvestigationTask.status.in_([TaskStatus.CREATED, TaskStatus.ASSIGNED, TaskStatus.ACTIVE, TaskStatus.BLOCKED])
        ).all()


        alerts = [self.evaluate_task_sla(t) for t in tasks]
        # Sort by urgency: CRITICAL first, then RED, YELLOW, GREEN, then by remaining_sla_seconds
        priority_map = {"CRITICAL": 0, "RED": 1, "YELLOW": 2, "GREEN": 3}
        alerts.sort(key=lambda x: (priority_map.get(x.sla_category, 99), x.remaining_sla_seconds))
        return alerts[:limit]
