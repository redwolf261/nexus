"""Executive Dashboard Aggregator (Phase 8.3 Milestone 4).

Aggregates KPIs, District Analytics, Multi-Period Trends, Operational Heatmaps,
and Command Center metrics into ExecutiveDashboardDTO with high-performance in-memory caching.
"""

from __future__ import annotations

import time
from threading import Lock
from datetime import datetime
from typing import List, Dict, Optional, Any

from sqlalchemy.orm import Session

from backend.command_center.executive_contracts import ExecutiveDashboardDTO
from backend.command_center.kpi_engine import KPIEngine
from backend.command_center.district_analytics import DistrictAnalyticsEngine
from backend.command_center.trend_engine import TrendAnalysisEngine
from backend.command_center.heatmap_engine import HeatmapEngine
from backend.core.logging import logger


class ExecutiveCacheEntry:
    def __init__(self, dto: ExecutiveDashboardDTO, ttl_seconds: float = 30.0):
        self.dto = dto
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds

    def is_valid(self) -> bool:
        return (time.time() - self.created_at) < self.ttl_seconds


class ExecutiveDashboardAggregator:
    """Thread-safe high-performance aggregator for Executive Command Center metrics."""

    _cache: Dict[str, ExecutiveCacheEntry] = {}
    _lock: Lock = Lock()

    def __init__(self, session: Session):
        self.session = session
        self.kpi_engine = KPIEngine(session)
        self.district_engine = DistrictAnalyticsEngine(session)
        self.trend_engine = TrendAnalysisEngine(session)
        self.heatmap_engine = HeatmapEngine(session)

    @classmethod
    def invalidate_cache(cls, key: Optional[str] = None):
        """Invalidate in-memory cache entries."""
        with cls._lock:
            if key and key in cls._cache:
                del cls._cache[key]
                logger.info(f"Invalidated executive cache entry for '{key}'")
            else:
                cls._cache.clear()
                logger.info("Cleared all executive command center cache entries")

    def get_dashboard(
        self,
        scope_role: str = "DCP",
        district_id: Optional[str] = None,
        force_refresh: bool = False
    ) -> ExecutiveDashboardDTO:
        """Fetch full aggregated ExecutiveDashboardDTO with caching."""
        cache_key = f"{scope_role.upper()}:{district_id or 'ALL'}"

        if not force_refresh:
            with self._lock:
                entry = self._cache.get(cache_key)
                if entry and entry.is_valid():
                    logger.debug(f"Serving executive dashboard DTO from cache for '{cache_key}'")
                    return entry.dto

        t0 = time.time()
        now_iso = datetime.utcnow().isoformat()

        # Generate components
        kpis = self.kpi_engine.calculate_all_kpis(district_id=district_id)
        districts = self.district_engine.get_district_analytics(caller_role=scope_role, user_district_id=district_id)
        trends = self.trend_engine.calculate_trends(district_id=district_id)
        heatmaps = self.heatmap_engine.generate_all_heatmaps(district_id=district_id)

        summary = {
            "total_active_cases": sum(d.active_cases for d in districts),
            "total_closed_cases": sum(d.closed_cases for d in districts),
            "avg_statewide_sla_pct": round(sum(d.sla_compliance_pct for d in districts) / len(districts), 1) if districts else 100.0,
            "overall_district_count": len(districts),
            "critical_cases_total": sum(d.critical_cases_count for d in districts),
            "cache_ttl_seconds": 30.0,
        }

        dto = ExecutiveDashboardDTO(
            scope_role=scope_role,
            district_id=district_id,
            kpis=kpis,
            district_analytics=districts,
            trends=trends,
            heatmaps=heatmaps,
            summary_metrics=summary,
            generated_at=now_iso,
        )

        with self._lock:
            self._cache[cache_key] = ExecutiveCacheEntry(dto, ttl_seconds=30.0)

        elapsed_ms = (time.time() - t0) * 1000.0
        logger.info(f"Aggregated ExecutiveDashboardDTO for '{cache_key}' in {elapsed_ms:.2f}ms")
        return dto
