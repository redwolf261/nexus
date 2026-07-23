"""Operational Event Router (Phase 8.3 Milestone 2).

Maps operational domain events to target dashboard patch sections, invalidates affected
cache entries, and broadcasts patches to subscribed supervisor sessions.
"""

from __future__ import annotations

import time
from typing import List, Dict, Optional, Any

from sqlalchemy.orm import Session

from backend.events.event_types import EventType
from backend.events.event_models import BaseEvent
from backend.command_center.contracts import DashboardPatchDTO
from backend.command_center.patch_engine import PatchBuilder, DeltaComputer
from backend.command_center.subscription_manager import SubscriptionRegistry
from backend.command_center.dashboard_service import DashboardAggregationService
from backend.core.logging import logger


class OperationalEventRouter:
    """Routes operational events to target dashboard section patches."""

    # Event mapping to affected dashboard sections
    EVENT_SECTION_MAPPING: Dict[str, List[str]] = {
        EventType.ASSIGNMENT_CREATED.value if hasattr(EventType.ASSIGNMENT_CREATED, "value") else "ASSIGNMENT_CREATED": ["active_cases", "analyst_workloads", "metrics"],
        EventType.ASSIGNMENT_REASSIGNED.value if hasattr(EventType.ASSIGNMENT_REASSIGNED, "value") else "ASSIGNMENT_REASSIGNED": ["active_cases", "analyst_workloads", "metrics"],
        EventType.ASSIGNMENT_ACCEPTED.value if hasattr(EventType.ASSIGNMENT_ACCEPTED, "value") else "ASSIGNMENT_ACCEPTED": ["active_cases", "approval_queue", "metrics"],
        EventType.ASSIGNMENT_OVERRIDDEN.value if hasattr(EventType.ASSIGNMENT_OVERRIDDEN, "value") else "ASSIGNMENT_OVERRIDDEN": ["active_cases", "approval_queue", "metrics"],
        EventType.ASSIGNMENT_ESCALATED.value if hasattr(EventType.ASSIGNMENT_ESCALATED, "value") else "ASSIGNMENT_ESCALATED": ["approval_queue", "metrics"],
        EventType.ASSIGNMENT_APPROVED.value if hasattr(EventType.ASSIGNMENT_APPROVED, "value") else "ASSIGNMENT_APPROVED": ["approval_queue", "active_cases", "metrics"],
        EventType.TASK_CREATED.value if hasattr(EventType.TASK_CREATED, "value") else "TASK_CREATED": ["active_cases", "sla_alerts", "metrics"],
        EventType.TASK_COMPLETED.value if hasattr(EventType.TASK_COMPLETED, "value") else "TASK_COMPLETED": ["active_cases", "sla_alerts", "metrics"],
        EventType.TASK_ASSIGNED.value if hasattr(EventType.TASK_ASSIGNED, "value") else "TASK_ASSIGNED": ["active_cases", "analyst_workloads", "sla_alerts"],
        EventType.INTELLIGENCE_DISCOVERED.value if hasattr(EventType.INTELLIGENCE_DISCOVERED, "value") else "INTELLIGENCE_DISCOVERED": ["intelligence_feed"],
        "SLA_ALERT": ["sla_alerts", "alerts", "metrics"],
        "OPERATIONAL_ALERT": ["alerts", "metrics"],
    }

    def __init__(self, session: Session):
        self.session = session
        self.dash_service = DashboardAggregationService(session)

    def route_event(self, event: BaseEvent) -> Optional[DashboardPatchDTO]:
        """Route an operational event, compute incremental patch, and invalidate cache."""
        event_str = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        target_sections = self.EVENT_SECTION_MAPPING.get(event_str, ["active_cases", "metrics"])

        # Invalidate cache for affected district
        district_id = event.payload.get("district_id") if isinstance(event.payload, dict) else None
        DashboardAggregationService.invalidate_cache(district_id=district_id)

        # Regenerate updated dashboard DTO
        dto = self.dash_service.get_dashboard(district_id=district_id, force_refresh=True)
        delta = DeltaComputer.compute_section_delta(old_dto=None, new_dto=dto, affected_sections=target_sections)

        seq = event.sequence or int(time.time() * 1000) % 1000000
        patch = PatchBuilder.build_patch(
            target_sections=delta.target_sections,
            delta_data=delta.delta_data,
            sequence=seq,
        )

        # Broadcast to active subscribers
        SubscriptionRegistry.broadcast_patch(patch, district_id=district_id)
        logger.info(f"Routed event '{event_str}' into patch '{patch.patch_id}' affecting sections {target_sections}")
        return patch
