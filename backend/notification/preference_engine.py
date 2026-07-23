"""Notification Preference Engine (Phase 8.5 Milestone 1 Deliverable 4).

Evaluates user quiet hours, channel preferences, priority thresholds, digest modes, and role defaults.
Enforces MANDATORY EMERGENCY BYPASS for CRITICAL priority notifications (never suppressed).
"""

from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Dict, List, Optional, Tuple

from backend.notification.contracts import (
    ChannelType,
    DigestMode,
    NotificationPreference,
    PriorityLevel,
)


class PreferenceEngine:
    """Evaluates notification preferences, quiet hours, and emergency priority overrides."""

    def filter_channels_for_recipient(
        self,
        preference: NotificationPreference,
        priority: PriorityLevel,
        requested_channels: List[ChannelType],
        current_time_str: Optional[str] = None,
    ) -> List[ChannelType]:
        """Filters requested channels based on recipient preferences & emergency bypass rules."""
        # Rule 1: MANDATORY EMERGENCY BYPASS for CRITICAL priority
        if priority == PriorityLevel.CRITICAL:
            # CRITICAL priority bypasses quiet hours, digest mode, and channel muting!
            return list(set(requested_channels))

        # Rule 2: Minimum priority threshold filter
        priority_ranks = {
            PriorityLevel.LOW: 1,
            PriorityLevel.MEDIUM: 2,
            PriorityLevel.HIGH: 3,
            PriorityLevel.CRITICAL: 4,
        }
        if priority_ranks.get(priority, 1) < priority_ranks.get(preference.min_priority, 1):
            return []

        # Rule 3: Quiet Hours evaluation
        if preference.quiet_hours_enabled:
            if self.is_in_quiet_hours(
                preference.quiet_hours_start,
                preference.quiet_hours_end,
                current_time_str=current_time_str,
            ):
                # During quiet hours for non-CRITICAL notifications, restrict to IN_APP only
                return [ch for ch in requested_channels if ch == ChannelType.IN_APP]

        # Rule 4: User enabled channels filter
        enabled = set(preference.enabled_channels)
        filtered = [ch for ch in requested_channels if ch in enabled]

        # Always preserve IN_APP channel as base fallback
        if ChannelType.IN_APP not in filtered and ChannelType.IN_APP in requested_channels:
            filtered.append(ChannelType.IN_APP)

        return filtered

    def should_digest(
        self,
        preference: NotificationPreference,
        priority: PriorityLevel,
    ) -> bool:
        """Determines whether a notification should be buffered for digest delivery."""
        # CRITICAL notifications NEVER digest (immediate dispatch)
        if priority == PriorityLevel.CRITICAL:
            return False
        return preference.digest_mode != DigestMode.IMMEDIATE

    def is_in_quiet_hours(
        self,
        start_str: str = "22:00",
        end_str: str = "06:00",
        current_time_str: Optional[str] = None,
    ) -> bool:
        """Determines whether the current time falls inside quiet hours range."""
        try:
            if current_time_str:
                now_dt = datetime.fromisoformat(current_time_str)
            else:
                now_dt = datetime.now(timezone.utc)

            curr_t = now_dt.time()
            s_hour, s_min = map(int, start_str.split(":"))
            e_hour, e_min = map(int, end_str.split(":"))

            start_t = time(s_hour, s_min)
            end_t = time(e_hour, e_min)

            if start_t <= end_t:
                return start_t <= curr_t <= end_t
            else:
                # Overnight range (e.g., 22:00 to 06:00)
                return curr_t >= start_t or curr_t <= end_t
        except Exception:
            return False
