# Supervisor Command Center Architecture (Phase 8.3 Milestone 1)

## Overview

The **Supervisor Command Center Workspace** provides an operational command console for supervisors, Assistant Commissioners (ACP), and Deputy Commissioners (DCP) to monitor active investigations, analyst workloads, approval queues, SLA risk health, analytical intelligence feeds, and operational alerts in real time.

```
┌────────────────────────────────────────────────────────┐
│              Supervisor Command Console                │
└───────────────────────────┬────────────────────────────┘
                            │ (Single Aggregated API Request)
                            ▼
┌────────────────────────────────────────────────────────┐
│           DashboardAggregationService                  │
│  - 30-Second TTL In-Memory Cache                       │
│  - Real-Time Event Invalidation                        │
│  - District Jurisdiction RBAC Scoping                  │
└───────────────────────────┬────────────────────────────┘
                            │
      ┌─────────────────────┼─────────────────────┐
      ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Task Engine  │     │ Workload Eng │     │ Governance   │
└──────────────┘     └──────────────┘     └──────────────┘
```

## Architectural Principles

1. **Operational Command Console**: Focuses purely on operational decisions, workload redistribution, and approval sign-offs rather than static BI charts.
2. **Single Aggregated DTO**: Aggregates all 7 operational domains into `SupervisorDashboardDTO`, powering the UI with one request in <500ms.
3. **Event-Driven Cache Invalidation**: In-memory 30s TTL cache invalidates immediately on assignment, task, approval, or intelligence WebSocket events.
4. **Jurisdiction Scoping**: Enforces Supervisor (district-only), ACP (district-wide), DCP (state-wide), Admin.
