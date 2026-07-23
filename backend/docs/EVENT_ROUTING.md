# Operational Event Router Specification (Phase 8.3 Milestone 2)

## Overview

`OperationalEventRouter` consumes Phase 7 and Phase 8 domain events and translates them into targeted dashboard patches.

## Event to Section Mapping

| Event Type | Target Dashboard Sections |
|------------|---------------------------|
| `ASSIGNMENT_CREATED` | `active_cases`, `analyst_workloads`, `metrics` |
| `ASSIGNMENT_REASSIGNED` | `active_cases`, `analyst_workloads`, `metrics` |
| `ASSIGNMENT_APPROVED` | `approval_queue`, `active_cases`, `metrics` |
| `TASK_COMPLETED` | `active_cases`, `sla_alerts`, `metrics` |
| `INTELLIGENCE_DISCOVERED` | `intelligence_feed` |
| `SLA_ALERT` | `sla_alerts`, `alerts`, `metrics` |
| `OPERATIONAL_ALERT` | `alerts`, `metrics` |
