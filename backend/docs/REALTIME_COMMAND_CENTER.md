# Real-Time Operational Dashboard Architecture (Phase 8.3 Milestone 2)

## Overview

Milestone 2 transitions the Supervisor Command Center into a real-time, event-driven operational workspace.

```
┌────────────────────────────────────────────────────────┐
│           Operational Event Dispatcher                │
└───────────────────────────┬────────────────────────────┘
                            │ (Domain Events)
                            ▼
┌────────────────────────────────────────────────────────┐
│             OperationalEventRouter                     │
│  - Maps Events to Dashboard Sections                   │
│  - Triggers Targeted Cache Invalidation                │
└───────────────────────────┬────────────────────────────┘
                            │ (Generates DashboardPatch)
                            ▼
┌────────────────────────────────────────────────────────┐
│              SubscriptionRegistry                      │
│  - Scoped Supervisor WS Subscriptions                  │
│  - Broadcasts Incremental Section Patches              │
└────────────────────────────────────────────────────────┘
```

## Architectural Highlights

- **Pure Event-Driven**: No background polling required.
- **Section-Level Incremental Patching**: Updates only affected dashboard sections (`DashboardPatchDTO`).
- **Live Collaborative Presence**: Informational read-only awareness of active supervisors (`PresenceService`).
- **Prioritized Notification Pipeline**: Categorizes and collapses repetitive alerts (`NotificationPipeline`).
- **Sequence Reconnect Replay**: Monotonic sequence tracking and replay buffer (`ReplayService`).
