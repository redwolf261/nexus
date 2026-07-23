# Workload Model — Phase 8.2 Milestone 3

## Overview

The workload model answers one question: **how operationally burdened is an
investigator right now?** The answer is a single dimensionless number
(`raw_workload`) produced by a deterministic, configurable formula.

It is **not** a simple case count. Two officers each holding ten investigations
are not equally loaded if one holds ten critical cases and the other holds ten
minor cases.

---

## Formula

```
raw_workload = Σ investigation_weight(priority, status)
             + Σ task_weight(status)
```

Both sums are computed over investigations and tasks **assigned to the officer**.
Inactive investigations and terminal tasks contribute **zero** — they are excluded
from the officer's burden.

---

## Investigation Priority Weights

| Priority   | Weight |
|------------|-------:|
| `CRITICAL` |    5.0 |
| `HIGH`     |    3.0 |
| `MEDIUM`   |    2.0 |
| `LOW`      |    1.0 |

An unrecognized priority falls back to the LOW weight (1.0) as a safe default.

### Inactive Investigation Statuses (weight = 0 regardless of priority)

| Status        | Variants handled          |
|---------------|--------------------------|
| `Completed`   | `COMPLETED`              |
| `Cancelled`   | `CANCELLED`              |
| `Archived`    | `ARCHIVED`               |
| `Closed`      | `CLOSED`                 |

Any investigation in one of these states contributes **exactly 0** to the
officer's workload. The check is case-aware — both `Completed` and `COMPLETED`
are handled.

---

## Task Status Weights

| Status        | Weight | Notes                          |
|---------------|-------:|-------------------------------|
| `CREATED`     |    1.0 | Equivalent to spec "OPEN"      |
| `ASSIGNED`    |    1.0 | Equivalent to spec "OPEN"      |
| `ACTIVE`      |    1.5 | Actively worked; highest effort|
| `BLOCKED`     |    0.5 | Waiting; still monitored       |
| `COMPLETED`   |    0.0 | Terminal — no burden           |
| `SKIPPED`     |    0.0 | Terminal — no burden           |
| `CANCELLED`   |    0.0 | Terminal — no burden           |

---

## Example Calculation

**Officer: Inspector Rajan**
- 1 × CRITICAL investigation (Open)   → weight 5.0
- 2 × HIGH investigation (Under Investigation) → weight 6.0
- 1 × MEDIUM investigation (Completed)   → weight 0.0 (inactive)
- 3 × ACTIVE tasks                     → weight 4.5
- 2 × BLOCKED tasks                    → weight 1.0

```
raw_workload = (5.0 + 6.0 + 0.0) + (4.5 + 1.0) = 16.5
```

With `maximum_capacity = 10`:
```
capacity_used = 16.5 / 10 = 1.65  (65% over capacity)
```

---

## Configuration: WorkloadPolicy

All weights live in `WorkloadPolicy` (`backend/assignment/workload_policy.py`).
The default is `DEFAULT_POLICY` (version `1.0.0`).

To recalibrate for a specific unit:

```python
from backend.assignment.workload_policy import WorkloadPolicy, DEFAULT_POLICY

ct_policy = WorkloadPolicy(
    version="1.1.0-counter-terrorism",
    task_weights={**DEFAULT_POLICY.task_weights, "ACTIVE": 2.0},
)
```

The `policy_version` string is stamped into every `OfficerWorkload` output,
so every historical workload figure can be traced back to the policy that
produced it.

---

## Implementation Notes

- `WorkloadEngine.calculate_workload()` is ORM-free and pure. It accepts
  plain `OfficerSnapshot`, `InvestigationSnapshot`, and `TaskSnapshot` objects.
- `WorkloadDataLoader.load_team_snapshots()` performs **4 queries** for any
  team size (bulk load). Do not call single-officer loads in a loop.
- `raw_workload` is always ≥ 0.0 and is not clamped at any upper bound.
  An officer with a 5× overload gets `raw_workload = 5 × maximum_capacity`.
