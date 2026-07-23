# Event-Driven Cache Coherence Specification (Phase 8.3 Milestone 2)

## Overview

`DashboardAggregationService` upgrades the 30-second TTL cache to an event-driven, version-tracked cache system.

## Invalidation Flow

1. Operational domain emits event (e.g. `ASSIGNMENT_CREATED`).
2. `OperationalEventRouter` handles event and calls `DashboardAggregationService.invalidate_cache(district_id, reason)`.
3. Invalidation increments global `_cache_version` integer and removes stale district keys.
4. Next read computes fresh state and stores new `CacheEntry(dto, timestamp, version)`.
