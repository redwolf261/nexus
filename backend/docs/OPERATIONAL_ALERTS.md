# Operational Alert Engine Specification (Phase 8.3 Milestone 1)

## Overview

The `OperationalAlertEngine` evaluates 6 strict deterministic operational rules across officers, investigations, tasks, and approval queues:

1. `ANALYST_OVERLOAD`: Triggered when officer capacity used >= 1.0 (Warning/Critical).
2. `BURNOUT_THRESHOLD_EXCEEDED`: Triggered when officer burnout score >= 75.0.
3. `CRITICAL_CASE_UNASSIGNED`: Triggered when a CRITICAL priority investigation remains unassigned.
4. `APPROVAL_STALE`: Triggered when an escalation approval remains pending in queue > 4 hours.
5. `OFFICER_OFF_DUTY_WITH_CASES`: Triggered when an officer status is `OFF_DUTY`, `LEAVE`, or `SUSPENDED` while holding active cases.
6. `SLA_RED_ALERT`: Triggered when a case/task enters RED or CRITICAL SLA state.
