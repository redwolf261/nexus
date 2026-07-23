"""Dashboard Subscription Manager (Phase 8.3 Milestone 2).

Manages active supervisor WebSocket sessions, subscription registries,
district/role scoping, and session heartbeat expirations.
"""

from __future__ import annotations

import time
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Set

from backend.command_center.contracts import DashboardPatchDTO, PresenceStatusDTO
from backend.core.logging import logger


@dataclass
class SupervisorSession:
    """Represents an active supervisor WebSocket session."""
    session_id: str
    user_id: str
    username: str
    role: str
    district_id: Optional[str]
    current_activity: str = "Viewing Dashboard"
    last_heartbeat: float = field(default_factory=time.time)
    connected_at: float = field(default_factory=time.time)

    def to_presence_dto(self) -> PresenceStatusDTO:
        return PresenceStatusDTO(
            session_id=self.session_id,
            user_id=self.user_id,
            username=self.username,
            role=self.role,
            district_id=self.district_id,
            current_activity=self.current_activity,
            last_heartbeat=datetime.fromtimestamp(self.last_heartbeat).isoformat(),
        )


@dataclass
class DashboardSubscription:
    """Subscription parameters for a supervisor session."""
    subscription_id: str
    session_id: str
    district_id: Optional[str]
    subscribed_at: float = field(default_factory=time.time)


class SubscriptionRegistry:
    """Thread-safe registry for managing active supervisor sessions and subscriptions."""

    _sessions: Dict[str, SupervisorSession] = {}
    _subscriptions: Dict[str, DashboardSubscription] = {}
    _lock = threading.Lock()
    _SESSION_TIMEOUT_SECONDS = 60.0  # Expire sessions inactive for >60s

    @classmethod
    def subscribe(
        cls,
        user_id: str,
        username: str,
        role: str,
        district_id: Optional[str] = None
    ) -> Tuple[SupervisorSession, DashboardSubscription]:
        """Create a new supervisor session and dashboard subscription."""
        session_id = f"SESS-{uuid.uuid4().hex[:12].upper()}"
        sub_id = f"SUB-{uuid.uuid4().hex[:12].upper()}"
        now = time.time()

        session = SupervisorSession(
            session_id=session_id,
            user_id=user_id,
            username=username,
            role=role,
            district_id=district_id,
            last_heartbeat=now,
            connected_at=now,
        )

        sub = DashboardSubscription(
            subscription_id=sub_id,
            session_id=session_id,
            district_id=district_id,
            subscribed_at=now,
        )

        with cls._lock:
            cls._sessions[session_id] = session
            cls._subscriptions[sub_id] = sub

        logger.info(f"Supervisor '{username}' subscribed with session '{session_id}' (District: {district_id or 'ALL'})")
        return session, sub

    @classmethod
    def unsubscribe(cls, session_id: str):
        """Remove a supervisor session and associated subscriptions."""
        with cls._lock:
            cls._sessions.pop(session_id, None)
            subs_to_del = [k for k, v in cls._subscriptions.items() if v.session_id == session_id]
            for k in subs_to_del:
                cls._subscriptions.pop(k, None)
        logger.info(f"Supervisor session '{session_id}' unsubscribed.")

    @classmethod
    def heartbeat(cls, session_id: str, activity: Optional[str] = None) -> bool:
        """Update last heartbeat timestamp and current activity for a session."""
        with cls._lock:
            if session_id in cls._sessions:
                sess = cls._sessions[session_id]
                sess.last_heartbeat = time.time()
                if activity:
                    sess.current_activity = activity
                return True
        return False

    @classmethod
    def auto_expire_sessions(cls) -> List[str]:
        """Automatically drop sessions exceeding the 60-second inactivity timeout."""
        now = time.time()
        expired: List[str] = []
        with cls._lock:
            for session_id, sess in list(cls._sessions.items()):
                if (now - sess.last_heartbeat) > cls._SESSION_TIMEOUT_SECONDS:
                    expired.append(session_id)
                    cls._sessions.pop(session_id, None)

            for sub_id, sub in list(cls._subscriptions.items()):
                if sub.session_id in expired:
                    cls._subscriptions.pop(sub_id, None)

        if expired:
            logger.info(f"Auto-expired {len(expired)} inactive supervisor sessions: {expired}")
        return expired

    @classmethod
    def get_active_sessions(cls, district_id: Optional[str] = None) -> List[SupervisorSession]:
        """Get all active supervisor sessions (optionally filtered by district)."""
        cls.auto_expire_sessions()
        with cls._lock:
            sessions = list(cls._sessions.values())
            if district_id:
                return [s for s in sessions if s.district_id in (district_id, None)]
            return sessions

    @classmethod
    def get_session(cls, session_id: str) -> Optional[SupervisorSession]:
        with cls._lock:
            return cls._sessions.get(session_id)

    @classmethod
    def broadcast_patch(cls, patch: DashboardPatchDTO, district_id: Optional[str] = None) -> int:
        """Find matching subscribers and prepare broadcast count."""
        active = cls.get_active_sessions(district_id=district_id)
        logger.debug(f"Broadcast patch '{patch.patch_id}' prepared for {len(active)} active supervisor sessions.")
        return len(active)
