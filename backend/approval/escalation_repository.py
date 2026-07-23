"""Escalation Repository (Phase 8.4 Milestone 2 Deliverable 5).

Thread-safe storage with optimistic locking for EscalationAggregates.
"""

from __future__ import annotations

import copy
import threading
from typing import Any, Dict, List, Optional

from backend.approval.contracts import OptimisticLockError
from backend.approval.escalation import EscalationAggregate, EscalationReason, EscalationStatus


class EscalationRepository:
    """Thread-safe repository for EscalationAggregates with optimistic concurrency control."""

    def __init__(self) -> None:
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def clear(self) -> None:
        with self._lock:
            self._storage.clear()

    def save(self, aggregate: EscalationAggregate, expected_version: Optional[int] = None) -> EscalationAggregate:
        with self._lock:
            existing = self._storage.get(aggregate.escalation_id)
            if existing is not None:
                current_ver = existing.get("version", 1)
                if expected_version is not None and current_ver != expected_version:
                    raise OptimisticLockError(
                        f"Version conflict for escalation '{aggregate.escalation_id}': stored version {current_ver} != expected version {expected_version}"
                    )

            serialized = aggregate.to_dict()
            self._storage[aggregate.escalation_id] = copy.deepcopy(serialized)
            return aggregate

    def get_by_id(self, escalation_id: str) -> Optional[EscalationAggregate]:
        with self._lock:
            data = self._storage.get(escalation_id)
            if not data:
                return None
            return EscalationAggregate.from_dict(copy.deepcopy(data))

    def get_by_approval_id(self, approval_id: str) -> Optional[EscalationAggregate]:
        with self._lock:
            for data in self._storage.values():
                if data.get("approval_id") == approval_id:
                    return EscalationAggregate.from_dict(copy.deepcopy(data))
            return None

    def find(
        self,
        status: Optional[EscalationStatus | str] = None,
        reason: Optional[EscalationReason | str] = None,
        assigned_role: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EscalationAggregate]:
        with self._lock:
            results: List[EscalationAggregate] = []
            for data in self._storage.values():
                agg = EscalationAggregate.from_dict(copy.deepcopy(data))

                if status:
                    st_val = status.value if isinstance(status, EscalationStatus) else str(status)
                    if agg.status.value != st_val:
                        continue

                if reason:
                    rs_val = reason.value if isinstance(reason, EscalationReason) else str(reason)
                    if agg.reason.value != rs_val:
                        continue

                if assigned_role:
                    role_clean = str(assigned_role).lower().replace("role.", "")
                    assigned_clean = str(agg.assigned_to_role).lower().replace("role.", "")
                    if role_clean != assigned_clean and role_clean not in ("admin", "dcp"):
                        continue

                results.append(agg)

            results.sort(key=lambda x: x.created_at, reverse=True)
            return results[offset : offset + limit]

    def count(self, status: Optional[EscalationStatus | str] = None) -> int:
        with self._lock:
            return len(self.find(status=status, limit=1000000))
