# Supervisor Action Center Engine Specification (Phase 8.3 Milestone 3)

## Overview

`SupervisorActionEngine` manages 14 operational supervisor actions:

- `ASSIGN`, `REASSIGN`, `APPROVE`, `REJECT`, `ESCALATE`, `RETURN_FOR_REVIEW`, `PAUSE`, `RESUME`, `MARK_BLOCKED`, `REQUEST_EVIDENCE`, `REQUEST_INTEL_REFRESH`, `CREATE_NOTE`, `CLOSE`, `REOPEN`.

## Governance Execution Flow

1. Validates RBAC permissions.
2. Validates workflow state transitions (e.g., cannot resume unpaused cases).
3. Writes immutable audit record to DB.
4. Appends action event to unified investigation timeline.
5. Invalidates workspace and command center caches.
6. Emits WebSocket event (`ASSIGNMENT_OVERRIDDEN`).
