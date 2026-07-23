"""Presence & Collaborative Awareness Service (Phase 8.3 Milestone 2).

Tracks active supervisor presence and current operational activities (e.g. reviewing cases,
approving overrides). Purely informational read-only awareness; zero locks.
"""

from __future__ import annotations

import time
from typing import List, Dict, Optional, Any

from backend.command_center.contracts import PresenceStatusDTO
from backend.command_center.subscription_manager import SubscriptionRegistry, SupervisorSession
from backend.core.logging import logger


class PresenceService:
    """Service managing live supervisor presence and activity tracking."""

    @staticmethod
    def get_presence_list(district_id: Optional[str] = None) -> List[PresenceStatusDTO]:
        """Fetch list of all active supervisor presence DTOs."""
        active_sessions = SubscriptionRegistry.get_active_sessions(district_id=district_id)
        return [s.to_presence_dto() for s in active_sessions]

    @staticmethod
    def update_activity(session_id: str, activity: str) -> Optional[PresenceStatusDTO]:
        """Update current activity string for a supervisor session."""
        success = SubscriptionRegistry.heartbeat(session_id, activity=activity)
        if success:
            sess = SubscriptionRegistry.get_session(session_id)
            if sess:
                logger.debug(f"Updated presence activity for '{sess.username}': {activity}")
                return sess.to_presence_dto()
        return None
