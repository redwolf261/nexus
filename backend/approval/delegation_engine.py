"""Delegation Engine (Phase 8.4 Milestone 2 Deliverable 4).

Manages temporary acting supervisor assignments, leave/vacation delegations, and emergency fallback routing
without permanent role mutation, preserving full audit attribution.
"""

from __future__ import annotations

import copy
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DelegationType(str, Enum):
    TEMPORARY_ACTING = "TEMPORARY_ACTING"
    LEAVE_DELEGATION = "LEAVE_DELEGATION"
    EMERGENCY_DELEGATION = "EMERGENCY_DELEGATION"
    VACATION_DELEGATION = "VACATION_DELEGATION"


@dataclass
class DelegationRecord:
    delegation_id: str
    delegator_id: str
    delegatee_id: str
    delegator_role: str
    delegatee_role: str
    delegation_type: DelegationType
    start_time: str
    end_time: str
    is_active: bool = True
    reason: str = ""
    created_at: str = field(default_factory=_utc_now_iso)

    def is_valid_at(self, now_dt: Optional[datetime] = None) -> bool:
        if not self.is_active:
            return False
        ref_now = now_dt or datetime.now(timezone.utc)
        if ref_now.tzinfo is None:
            ref_now = ref_now.replace(tzinfo=timezone.utc)

        try:
            st = datetime.fromisoformat(self.start_time.replace("Z", "+00:00"))
            et = datetime.fromisoformat(self.end_time.replace("Z", "+00:00"))
            if st.tzinfo is None:
                st = st.replace(tzinfo=timezone.utc)
            if et.tzinfo is None:
                et = et.replace(tzinfo=timezone.utc)
            return st <= ref_now <= et
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delegation_id": self.delegation_id,
            "delegator_id": self.delegator_id,
            "delegatee_id": self.delegatee_id,
            "delegator_role": self.delegator_role,
            "delegatee_role": self.delegatee_role,
            "delegation_type": self.delegation_type.value if isinstance(self.delegation_type, Enum) else str(self.delegation_type),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "is_active": self.is_active,
            "reason": self.reason,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DelegationRecord:
        return cls(
            delegation_id=data["delegation_id"],
            delegator_id=data["delegator_id"],
            delegatee_id=data["delegatee_id"],
            delegator_role=data["delegator_role"],
            delegatee_role=data["delegatee_role"],
            delegation_type=DelegationType(data["delegation_type"]),
            start_time=data["start_time"],
            end_time=data["end_time"],
            is_active=data.get("is_active", True),
            reason=data.get("reason", ""),
            created_at=data.get("created_at", _utc_now_iso()),
        )


class DelegationEngine:
    """Thread-safe engine for managing temporary authority delegations."""

    def __init__(self) -> None:
        self._delegations: Dict[str, DelegationRecord] = {}
        self._lock = threading.RLock()

    def clear(self) -> None:
        with self._lock:
            self._delegations.clear()

    def create_delegation(
        self,
        delegator_id: str,
        delegatee_id: str,
        delegator_role: str,
        delegatee_role: str,
        delegation_type: DelegationType | str = DelegationType.TEMPORARY_ACTING,
        duration_hours: float = 24.0,
        reason: str = "",
        start_time: Optional[str] = None,
    ) -> DelegationRecord:
        """Creates a temporary delegation record."""
        del_type = DelegationType(delegation_type) if isinstance(delegation_type, str) else delegation_type
        now = datetime.now(timezone.utc)
        st_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00")) if start_time else now
        et_dt = st_dt + timedelta(hours=duration_hours)

        record = DelegationRecord(
            delegation_id=f"del_{uuid.uuid4().hex[:12]}",
            delegator_id=delegator_id,
            delegatee_id=delegatee_id,
            delegator_role=delegator_role,
            delegatee_role=delegatee_role,
            delegation_type=del_type,
            start_time=st_dt.isoformat(),
            end_time=et_dt.isoformat(),
            is_active=True,
            reason=reason,
        )

        with self._lock:
            self._delegations[record.delegation_id] = record
            return copy.deepcopy(record)

    def revoke_delegation(self, delegation_id: str) -> Optional[DelegationRecord]:
        """Revokes an active delegation."""
        with self._lock:
            record = self._delegations.get(delegation_id)
            if not record:
                return None
            record.is_active = False
            return copy.deepcopy(record)

    def resolve_active_delegatee(self, delegator_id: str, now_dt: Optional[datetime] = None) -> Optional[str]:
        """Finds the active delegatee user_id for a given delegator_id if valid delegation exists."""
        with self._lock:
            for rec in self._delegations.values():
                if rec.delegator_id == delegator_id and rec.is_valid_at(now_dt):
                    return rec.delegatee_id
            return None

    def is_user_acting_for(self, delegatee_id: str, delegator_id: str, now_dt: Optional[datetime] = None) -> bool:
        """Checks if delegatee_id is currently acting for delegator_id under an active delegation."""
        with self._lock:
            for rec in self._delegations.values():
                if rec.delegator_id == delegator_id and rec.delegatee_id == delegatee_id and rec.is_valid_at(now_dt):
                    return True
            return False

    def get_active_delegations(self, now_dt: Optional[datetime] = None) -> List[DelegationRecord]:
        with self._lock:
            return [copy.deepcopy(rec) for rec in self._delegations.values() if rec.is_valid_at(now_dt)]

    def get_delegations_for_user(self, user_id: str) -> List[DelegationRecord]:
        with self._lock:
            return [
                copy.deepcopy(rec)
                for rec in self._delegations.values()
                if rec.delegator_id == user_id or rec.delegatee_id == user_id
            ]
