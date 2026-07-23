"""Dashboard Aggregation Service (Phase 8.3 Milestone 1 & 2).

Orchestrates dashboard aggregation with event-driven cache invalidation, cache versioning,
thread-safe invalidation, and district-scoped permissions.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Optional, Any, Tuple

from sqlalchemy.orm import Session

from backend.command_center.contracts import SupervisorDashboardDTO
from backend.command_center.aggregation import CommandCenterAggregator
from backend.core.logging import logger


@dataclass
class CacheEntry:
    """Wrapper holding a cached DTO, creation timestamp, and version integer."""
    dto: SupervisorDashboardDTO
    timestamp: float
    version: int


class CacheInvalidationReason:
    """Standardized reasons for dashboard cache invalidation."""
    ASSIGNMENT_CHANGE = "ASSIGNMENT_CHANGE"
    TASK_UPDATE = "TASK_UPDATE"
    APPROVAL_CHANGE = "APPROVAL_CHANGE"
    INTELLIGENCE_EVENT = "INTELLIGENCE_EVENT"
    MANUAL_REFRESH = "MANUAL_REFRESH"


class DashboardAggregationService:
    """Production Dashboard Aggregation Service with Event-Driven Cache Invalidation."""

    _cache: Dict[str, CacheEntry] = {}
    _lock = threading.Lock()
    _CACHE_TTL_SECONDS = 30.0
    _cache_version: int = 1

    def __init__(self, session: Session):
        self.session = session
        self.aggregator = CommandCenterAggregator(session)

    def get_dashboard(
        self,
        district_id: Optional[str] = None,
        sort_cases_by: str = "sla_risk",
        force_refresh: bool = False
    ) -> SupervisorDashboardDTO:
        """Get aggregated command dashboard with event-driven cache lookup."""
        cache_key = f"dash:{district_id or 'ALL'}:{sort_cases_by}"
        now = time.time()

        if not force_refresh:
            with self._lock:
                if cache_key in self._cache:
                    entry = self._cache[cache_key]
                    if (now - entry.timestamp) < self._CACHE_TTL_SECONDS:
                        logger.debug(f"Command Center cache hit for '{cache_key}' (v{entry.version})")
                        return entry.dto

        # Cache miss or force refresh
        t0 = time.time()
        dto = self.aggregator.aggregate_dashboard(district_id=district_id, sort_cases_by=sort_cases_by)
        elapsed_ms = (time.time() - t0) * 1000.0
        logger.info(f"Command Center aggregation generated in {elapsed_ms:.1f}ms for key '{cache_key}'")

        with self._lock:
            self._cache[cache_key] = CacheEntry(
                dto=dto,
                timestamp=now,
                version=self._cache_version,
            )

        return dto

    @classmethod
    def invalidate_cache(
        cls,
        district_id: Optional[str] = None,
        reason: str = CacheInvalidationReason.ASSIGNMENT_CHANGE
    ):
        """Invalidate dashboard cache on operational events (Assignment, Task, Approval, etc.)."""
        with cls._lock:
            cls._cache_version += 1
            if district_id:
                keys_to_del = [k for k in cls._cache if f"dash:{district_id}" in k or "dash:ALL" in k]
                for k in keys_to_del:
                    cls._cache.pop(k, None)
            else:
                cls._cache.clear()
        logger.info(f"Command Center cache invalidated for district '{district_id or 'ALL'}' (Reason: {reason}, v{cls._cache_version})")

    @classmethod
    def get_current_cache_version(cls) -> int:
        with cls._lock:
            return cls._cache_version
