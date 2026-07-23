"""Notification Event Integration Pipeline (Phase 8.5 Milestone 1 Deliverable 8).

Subscribes to operational events across Task Engine, Assignment Engine, Approval Engine,
Escalation Engine, Case Engine, and Intelligence Engine to produce multi-channel notifications.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from backend.events.event_types import EventType
from backend.notification.contracts import PriorityLevel
from backend.notification.notification_service import NotificationService

logger = logging.getLogger("nexus.notification_event_handler")


class NotificationEventHandler:
    """Pipeline Handler routing operational platform events into the Notification Engine."""

    def __init__(self, service: Optional[NotificationService] = None):
        self.service = service or NotificationService()

    def handle_event(self, event_type: str, entity_id: str, details: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Handles inbound platform event and dispatches notification if applicable."""
        details = details or {}

        try:
            # 1. Task Assigned
            if event_type == EventType.TASK_ASSIGNED:
                assignee = details.get("assigned_to", "officer")
                title = details.get("title", f"Task {entity_id} Assigned")
                return self.service.create_and_send(
                    title=f"New Task Assigned: {title}",
                    body=f"Task {entity_id} has been assigned to you. Priority: {details.get('priority', 'MEDIUM')}",
                    event_type=event_type,
                    priority=PriorityLevel.MEDIUM,
                    source_entity_type="TASK",
                    source_entity_id=entity_id,
                    target_users=[assignee],
                )

            # 2. Task SLA Warning / Breach
            elif event_type in (EventType.TASK_SLA_WARNING, EventType.TASK_SLA_BREACHED):
                is_breach = event_type == EventType.TASK_SLA_BREACHED
                priority = PriorityLevel.CRITICAL if is_breach else PriorityLevel.HIGH
                return self.service.create_and_send(
                    title=f"Task SLA {'Breach' if is_breach else 'Warning'}: {entity_id}",
                    body=f"Task {entity_id} has {'breached' if is_breach else 'approached'} its SLA deadline.",
                    event_type=event_type,
                    priority=priority,
                    source_entity_type="TASK",
                    source_entity_id=entity_id,
                    target_roles=["supervisor"],
                )

            # 3. Approval Submitted
            elif event_type == EventType.APPROVAL_SUBMITTED:
                return self.service.create_and_send(
                    title=f"Approval Request Submitted: {entity_id}",
                    body=f"Approval request {entity_id} submitted by {details.get('requester_id', 'analyst')}.",
                    event_type=event_type,
                    priority=PriorityLevel.MEDIUM,
                    source_entity_type="APPROVAL",
                    source_entity_id=entity_id,
                    target_roles=["supervisor"],
                )

            # 4. Approval Approved / Rejected
            elif event_type in (EventType.APPROVAL_APPROVED, EventType.APPROVAL_REJECTED):
                is_app = event_type == EventType.APPROVAL_APPROVED
                requester = details.get("requester_id")
                return self.service.create_and_send(
                    title=f"Approval {'Approved' if is_app else 'Rejected'}: {entity_id}",
                    body=f"Your approval request {entity_id} was {'APPROVED' if is_app else 'REJECTED'}.",
                    event_type=event_type,
                    priority=PriorityLevel.HIGH,
                    source_entity_type="APPROVAL",
                    source_entity_id=entity_id,
                    target_users=[requester] if requester else None,
                    target_roles=["supervisor"] if not requester else None,
                )

            # 5. Escalation Created / SLA Breach
            elif event_type in (EventType.APPROVAL_ESCALATION_CREATED, EventType.SLA_BREACHED):
                return self.service.create_and_send(
                    title=f"CRITICAL ESCALATION ALERT: {entity_id}",
                    body=f"Emergency escalation created for {entity_id}. Reason: {details.get('reason', 'SLA_TIMEOUT')}",
                    event_type=event_type,
                    priority=PriorityLevel.CRITICAL,
                    source_entity_type="ESCALATION",
                    source_entity_id=entity_id,
                    target_roles=["acp", "dcp"],
                )

            # 6. SLA Warning
            elif event_type == EventType.SLA_WARNING:
                return self.service.create_and_send(
                    title=f"SLA Warning Threshold: {entity_id}",
                    body=f"SLA Warning threshold (70%) reached for approval request {entity_id}.",
                    event_type=event_type,
                    priority=PriorityLevel.HIGH,
                    source_entity_type="APPROVAL",
                    source_entity_id=entity_id,
                    target_roles=["supervisor"],
                )

            # 7. Intelligence Discovered
            elif event_type == EventType.INTELLIGENCE_DISCOVERED:
                return self.service.create_and_send(
                    title=f"Intelligence Pattern Discovered",
                    body=f"New intelligence inference generated for entity {entity_id}.",
                    event_type=event_type,
                    priority=PriorityLevel.HIGH,
                    source_entity_type="INTELLIGENCE",
                    source_entity_id=entity_id,
                    target_roles=["supervisor", "acp"],
                )

            # 8. New Case / Case Updated
            elif event_type in (EventType.NEW_CASE, EventType.CASE_UPDATED):
                return self.service.create_and_send(
                    title=f"Case Update: {entity_id}",
                    body=f"Investigation case {entity_id} was updated.",
                    event_type=event_type,
                    priority=PriorityLevel.MEDIUM,
                    source_entity_type="CASE",
                    source_entity_id=entity_id,
                    target_roles=["supervisor"],
                )

            # 9. Assignment Events
            elif event_type in (EventType.ASSIGNMENT_CREATED, EventType.ASSIGNMENT_REASSIGNED):
                target = details.get("assigned_to", "officer")
                return self.service.create_and_send(
                    title=f"Investigation Assignment: {entity_id}",
                    body=f"Case assignment updated for {entity_id}.",
                    event_type=event_type,
                    priority=PriorityLevel.MEDIUM,
                    source_entity_type="ASSIGNMENT",
                    source_entity_id=entity_id,
                    target_users=[target],
                )

            return None
        except Exception as e:
            logger.warning(f"Error handling event '{event_type}' for entity '{entity_id}': {e}")
            return None
