"""Notification Prioritization & Deduplication Pipeline (Phase 8.3 Milestone 2).

Prioritizes alerts (CRITICAL, HIGH, MEDIUM, LOW) and collapses repeated alerts
(e.g., '5 investigations approaching SLA') to prevent notification fatigue.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

from backend.command_center.contracts import OperationalAlertItem, NotificationDigestDTO
from backend.core.logging import logger


class NotificationPipeline:
    """Processes, prioritizes, and deduplicates operational notifications."""

    PRIORITY_LEVELS = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

    @classmethod
    def process_alerts(cls, alerts: List[OperationalAlertItem]) -> List[NotificationDigestDTO]:
        """Group and collapse alerts into prioritized notification digests."""
        if not alerts:
            return []

        # Group by rule_code and severity
        grouped: Dict[str, List[OperationalAlertItem]] = {}
        for alt in alerts:
            key = f"{alt.severity}:{alt.rule_code}"
            grouped.setdefault(key, []).append(alt)

        digests: List[NotificationDigestDTO] = []
        for key, alt_group in grouped.items():
            severity, rule_code = key.split(":", 1)
            count = len(alt_group)

            if count == 1:
                summary = alt_group[0].message
            else:
                summary = f"{count} {rule_code.replace('_', ' ').lower()} alerts requiring attention."

            target_ids = [a.target_id for a in alt_group]
            digest_id = f"DIG-{uuid.uuid4().hex[:10].upper()}"

            digests.append(NotificationDigestDTO(
                digest_id=digest_id,
                priority=severity,
                collapsed_count=count,
                summary_message=summary,
                target_ids=target_ids,
                timestamp=datetime.utcnow().isoformat(),
            ))

        # Sort by priority (CRITICAL first) then timestamp
        digests.sort(key=lambda d: cls.PRIORITY_LEVELS.get(d.priority.upper(), 99))
        return digests
