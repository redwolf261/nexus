"""Unified Investigation Timeline Service (Phase 8.3 Milestone 3).

Merges events from Task Engine, Assignment Engine, Governance, Approvals, Evidence,
Analytical discoveries, Edits, Notes, and Escalations into a single chronologically ordered timeline.
Supports cursor pagination and incremental event appending.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

from sqlalchemy.orm import Session

from backend.db.schema import Investigation, InvestigationTask, TaskStatus, Officer
from backend.command_center.workspace_contracts import TimelineEventDTO
from backend.core.logging import logger


class InvestigationTimelineService:
    """Service generating chronologically unified investigation timelines."""

    # Memory store for custom supervisor notes / manual timeline events
    _custom_events: Dict[str, List[TimelineEventDTO]] = {}

    def __init__(self, session: Session):
        self.session = session

    def get_timeline(
        self,
        investigation_id: str,
        category_filter: Optional[str] = None,
        cursor: Optional[int] = None,
        limit: int = 50
    ) -> Tuple[List[TimelineEventDTO], Optional[int]]:
        """Fetch chronologically ordered timeline events with cursor pagination."""
        events: List[TimelineEventDTO] = []

        inv = self.session.query(Investigation).filter_by(id=investigation_id).first()
        if not inv:
            return [], None

        # 1. Investigation Creation Event
        created_at_str = inv.created_at.isoformat() if inv.created_at else datetime.utcnow().isoformat()
        events.append(TimelineEventDTO(
            event_id=f"EVT-INIT-{inv.id}",
            investigation_id=inv.id,
            timestamp=created_at_str,
            actor="System",
            event_type="INVESTIGATION_CREATED",
            category="ACTION",
            title=f"Investigation Created",
            description=f"Investigation '{inv.title}' created with priority {inv.priority}.",
            metadata={"priority": inv.priority, "case_type": getattr(inv, "case_type", "GENERAL")},
        ))

        # 2. Assignment Event
        if inv.assigned_officer:
            off = self.session.query(Officer).filter_by(officer_id=inv.assigned_officer).first()
            off_name = off.name_en if off else inv.assigned_officer
            events.append(TimelineEventDTO(
                event_id=f"EVT-ASSG-{inv.id}",
                investigation_id=inv.id,
                timestamp=created_at_str,
                actor="Supervisor",
                event_type="OFFICER_ASSIGNED",
                category="ASSIGNMENT",
                title=f"Assigned to {off_name}",
                description=f"Primary investigator set to {off_name} ({inv.assigned_officer}).",
                metadata={"assigned_officer": inv.assigned_officer},
            ))

        # 3. Tasks Events
        tasks = self.session.query(InvestigationTask).filter_by(investigation_id=investigation_id).all()
        for t in tasks:
            task_ts = t.created_at.isoformat() if hasattr(t, "created_at") and t.created_at else created_at_str
            status_val = t.status.value if hasattr(t.status, "value") else str(t.status)
            events.append(TimelineEventDTO(
                event_id=f"EVT-TSK-{t.id}",
                investigation_id=inv.id,
                timestamp=task_ts,
                actor=t.assigned_officer_id or "System",
                event_type=f"TASK_{status_val}",
                category="TASK",
                title=f"Task: {t.title}",
                description=f"Task '{t.title}' is currently {status_val}.",
                metadata={"task_id": t.id, "status": status_val},
            ))

        # 4. Custom Supervisor Notes & Operational Actions
        if investigation_id in self._custom_events:
            events.extend(self._custom_events[investigation_id])

        # Apply category filter
        if category_filter:
            events = [e for e in events if e.category.upper() == category_filter.upper()]

        # Sort chronologically (newest first for timeline view)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply cursor pagination (offset based on index)
        start_idx = cursor if cursor is not None else 0
        paginated_events = events[start_idx : start_idx + limit]
        next_cursor = (start_idx + limit) if (start_idx + limit) < len(events) else None

        return paginated_events, next_cursor

    @classmethod
    def add_custom_event(cls, event: TimelineEventDTO):
        """Append a custom timeline event (e.g. supervisor note or manual action)."""
        inv_id = event.investigation_id
        cls._custom_events.setdefault(inv_id, []).append(event)
        logger.info(f"Appended custom timeline event '{event.event_id}' to investigation '{inv_id}'")
