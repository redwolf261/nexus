# Assignment Service Architecture — Phase 8.2 Milestone 4

## Overview

`AssignmentService` (`backend/assignment/assignment_service.py`) is the operational coordinator connecting:
- **Officer Capability Model (M1)**
- **Assignment Scoring Engine (M2)**
- **Workload Engine (M3)**
- **Task Engine (Phase 8.1)**
- **Audit Framework**
- **WebSocket Dispatcher**
- **JWT / RBAC Access Control**

---

## Core Rule

> **The Assignment Service NEVER auto-assigns.**
> It computes explainable recommendations and validates operational constraints.
> **Only human supervisors perform assignments.**

---

## DDD Assignment Aggregate

To prevent state fragmentation across investigations, officers, and audit logs, operations center on the `AssignmentAggregate` (`backend/assignment/aggregate.py`).

```python
@dataclass
class AssignmentAggregate:
    investigation_id: str
    current_officer_id: Optional[str]
    investigation_status: str
    investigation_priority: str
    version: int
    policy_version: str
    history: List[AssignmentHistoryRecord]
    validation: Optional[AssignmentValidationResult]
    top_recommendation: Optional[RankedRecommendation]
    officer_workload: Optional[OfficerWorkload]
```

This aggregate provides a single, coherent domain object for M5 Supervisor Command Centre, Phase 8.4 Approval Workflows, and Phase 10 LLM Explanation feeds.

---

## Core Methods

| Method | Access Role | Description |
|--------|:-----------:|-------------|
| `recommend(investigation_id, limit)` | Analyst / Supervisor | Calculates ranked officer recommendations using M2 scoring + M3 workload. |
| `validate(investigation_id, officer_id)` | Analyst / Supervisor | Checks ON_DUTY status, capacity headroom, jurisdiction, and open status. |
| `assign(investigation_id, officer_id, assigned_by, ...)` | Supervisor / Admin | Validates, checks optimistic lock, updates case & officer state, logs audit & WebSocket. |
| `reassign(investigation_id, new_officer_id, ...)` | Supervisor / Admin | Handles resignation, leave, suspension, promotion, manual/bulk transfers with append-only history. |
| `bulk_reassign(reassignments, assigned_by)` | Supervisor / Admin | Executes batch reassignments atomically in a single transaction. |
| `recommend_many(investigation_ids, limit)` | Analyst / Supervisor | Bulk loading recommendation computation (<3s for 100 cases). |
| `estimate_completion(investigation_id)` | Authenticated | Deterministic heuristic estimating earliest, expected, and latest completion duration. |

---

## Optimistic Concurrency Control

Every investigation carries an integer `version`. Operations verify `inv.version == expected_version` before committing changes. Concurrency conflicts raise a `409 Conflict` (or `ValueError` in Python), preventing race conditions during simultaneous supervisor actions.
