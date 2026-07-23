"""Notification Orchestrator (Phase 8.5 Milestone 2 Deliverable 1).

Orchestrates event aggregation, batching, deduplication, routing decisions, reminder & digest scheduling,
and replay safety. Enforces deterministic ordering and idempotent execution without random generators.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.notification.contracts import (
    ChannelType,
    NotificationAggregate,
    NotificationRecipient,
    PriorityLevel,
)
from backend.notification.notification_service import NotificationService

logger = logging.getLogger("nexus.notification_orchestrator")


class NotificationOrchestrator:
    """Orchestrates event batching, deduplication, replay safety, and multi-entity notification routing."""

    def __init__(self, service: Optional[NotificationService] = None, window_seconds: float = 60.0):
        self.service = service or NotificationService()
        self.window_seconds = window_seconds
        # Deduplication cache key: hash(source_entity_type, source_entity_id, event_type, recipient_id) -> timestamp
        self._dedup_cache: Dict[str, float] = {}

    def compute_dedup_key(
        self,
        event_type: str,
        source_entity_type: str,
        source_entity_id: str,
        recipient_id: str,
        title: str = "",
    ) -> str:
        """Computes deterministic deduplication key for replay safety."""
        raw = f"{event_type}:{source_entity_type}:{source_entity_id}:{recipient_id}:{title}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def is_duplicate(
        self,
        event_type: str,
        source_entity_type: str,
        source_entity_id: str,
        recipient_id: str,
        title: str = "",
        now_ts: Optional[float] = None,
    ) -> bool:
        """Checks if identical notification was dispatched within deduplication window."""
        key = self.compute_dedup_key(event_type, source_entity_type, source_entity_id, recipient_id, title)
        curr = now_ts or time.time()
        last_ts = self._dedup_cache.get(key)
        if last_ts and (curr - last_ts) < self.window_seconds:
            return True
        return False

    def record_dispatch(
        self,
        event_type: str,
        source_entity_type: str,
        source_entity_id: str,
        recipient_id: str,
        title: str = "",
        now_ts: Optional[float] = None,
    ):
        """Records notification dispatch for deduplication tracking."""
        key = self.compute_dedup_key(event_type, source_entity_type, source_entity_id, recipient_id, title)
        self._dedup_cache[key] = now_ts or time.time()

    def process_event_batch(
        self,
        events: List[Dict[str, Any]],
        now_ts: Optional[float] = None,
    ) -> List[NotificationAggregate]:
        """Processes and deduplicates a batch of operational platform events deterministically."""
        dispatched_aggregates: List[NotificationAggregate] = []
        curr = now_ts or time.time()

        # Sort events by event_type and entity_id for stable deterministic ordering
        sorted_events = sorted(
            events,
            key=lambda e: (e.get("event_type", ""), str(e.get("source_entity_id", "")), e.get("title", "")),
        )

        for event in sorted_events:
            evt_type = event.get("event_type", "OPERATIONAL_EVENT")
            src_type = event.get("source_entity_type", "SYSTEM")
            src_id = str(event.get("source_entity_id", "0"))
            title = event.get("title", "Operational Update")
            body = event.get("body", "Notification content")
            priority = PriorityLevel(event.get("priority", PriorityLevel.MEDIUM.value))
            target_users = event.get("target_users", [])
            target_roles = event.get("target_roles", [])

            # Determine recipients
            recs, _ = self.service.routing_engine.route_notification(
                priority=priority,
                target_users=target_users,
                target_roles=target_roles,
            )

            # Filter duplicates per recipient
            filtered_recipients = []
            for r in recs:
                if not self.is_duplicate(evt_type, src_type, src_id, r.user_id, title, now_ts=curr):
                    filtered_recipients.append(r)
                    self.record_dispatch(evt_type, src_type, src_id, r.user_id, title, now_ts=curr)

            if filtered_recipients:
                agg = self.service.create_and_send(
                    title=title,
                    body=body,
                    event_type=evt_type,
                    priority=priority,
                    source_entity_type=src_type,
                    source_entity_id=src_id,
                    target_users=[r.user_id for r in filtered_recipients],
                )
                dispatched_aggregates.append(agg)

        return dispatched_aggregates

    def clear_cache(self):
        """Clears deduplication cache."""
        self._dedup_cache.clear()
