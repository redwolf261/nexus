# Real-Time Dashboard Synchronization (Phase 8.3 Milestone 1)

## Overview

The Supervisor Command Console updates incrementally over WebSockets without requiring full page refreshes.

## Event Subscriptions

- `ASSIGNMENT_CREATED` / `ASSIGNMENT_REASSIGNED`: Updates active investigations and analyst workload cards.
- `TASK_COMPLETED` / `TASK_BLOCKED`: Updates task progress and SLA risk categorizations.
- `ASSIGNMENT_ESCALATED` / `ASSIGNMENT_APPROVED`: Refreshes approval queue cards.
- `INTELLIGENCE_DISCOVERED`: Appends new analytical intelligence feeds with explainability card links.
- `ASSIGNMENT_POLICY_WARNING`: Triggers operational alert banners.
