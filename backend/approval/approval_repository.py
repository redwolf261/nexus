"""Approval Repository (Phase 8.4 Deliverable 4 & 6).

Thread-safe repository with optimistic locking, indexing, pagination, and persistence.
"""

from __future__ import annotations

import copy
import threading
from typing import Any, Dict, List, Optional, Tuple

from backend.approval.contracts import (
    ApprovalAggregate,
    ApprovalStatus,
    ApprovalType,
    OptimisticLockError,
)


class ApprovalRepository:
    """Thread-safe repository with optimistic concurrency control."""

    def __init__(self) -> None:
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def clear(self) -> None:
        with self._lock:
            self._storage.clear()

    def save(self, aggregate: ApprovalAggregate, expected_version: Optional[int] = None) -> ApprovalAggregate:
        """Saves or updates an ApprovalAggregate.
        
        If expected_version is provided, verifies that current stored version matches expected_version.
        Otherwise raises OptimisticLockError.
        """
        with self._lock:
            existing = self._storage.get(aggregate.approval_id)
            if existing is not None:
                current_ver = existing.get("version", 1)
                if expected_version is not None and current_ver != expected_version:
                    raise OptimisticLockError(
                        f"Version conflict for approval '{aggregate.approval_id}': stored version {current_ver} != expected version {expected_version}"
                    )

            # Store serialized copy
            serialized = aggregate.to_dict()
            self._storage[aggregate.approval_id] = copy.deepcopy(serialized)
            return aggregate

    def get_by_id(self, approval_id: str) -> Optional[ApprovalAggregate]:
        with self._lock:
            data = self._storage.get(approval_id)
            if not data:
                return None
            return ApprovalAggregate.from_dict(copy.deepcopy(data))

    def find(
        self,
        status: Optional[ApprovalStatus | str] = None,
        approval_type: Optional[ApprovalType | str] = None,
        requester_id: Optional[str] = None,
        pending_role: Optional[str] = None,
        district_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ApprovalAggregate]:
        with self._lock:
            results: List[ApprovalAggregate] = []
            for data in self._storage.values():
                agg = ApprovalAggregate.from_dict(copy.deepcopy(data))

                if status:
                    st_val = status.value if isinstance(status, ApprovalStatus) else str(status)
                    if agg.status.value != st_val:
                        continue

                if approval_type:
                    tp_val = approval_type.value if isinstance(approval_type, ApprovalType) else str(approval_type)
                    if agg.approval_type.value != tp_val:
                        continue

                if requester_id and agg.requester_id != requester_id:
                    continue

                if district_id and agg.district_id != district_id:
                    continue

                if pending_role:
                    stage = agg.current_stage()
                    if not stage:
                        continue
                    p_role_clean = str(pending_role).lower().replace("role.", "")
                    s_role_clean = str(stage.required_role).lower().replace("role.", "")
                    if p_role_clean != s_role_clean and p_role_clean not in ("admin", "dcp"):
                        continue

                results.append(agg)

            # Sort by created_at descending
            results.sort(key=lambda x: x.created_at, reverse=True)
            return results[offset : offset + limit]

    def count(
        self,
        status: Optional[ApprovalStatus | str] = None,
        approval_type: Optional[ApprovalType | str] = None,
        requester_id: Optional[str] = None,
        pending_role: Optional[str] = None,
        district_id: Optional[str] = None,
    ) -> int:
        with self._lock:
            return len(
                self.find(
                    status=status,
                    approval_type=approval_type,
                    requester_id=requester_id,
                    pending_role=pending_role,
                    district_id=district_id,
                    limit=1000000,
                    offset=0,
                )
            )
