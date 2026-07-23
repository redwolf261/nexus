# Burnout Model — Phase 8.2 Milestone 3

## Overview

The burnout model produces a deterministic **0–100 score** and a named
**risk band** for each officer. It is not an ML model. It is not a black box.
Every point in the score has a traceable cause: a factor, a coefficient, and
a denominator — all in `WorkloadPolicy`.

---

## Six-Factor Model

| Factor | Max Points | Formula | Denominator |
|--------|:----------:|---------|-------------|
| Workload ratio | 40 | `min(capacity_used, 1.0) × 40` | — (capped at 1.0) |
| Overdue tasks | 15 | `min(count / 5, 1.0) × 15` | 5 tasks saturates |
| Overdue investigations | 15 | `min(count / 3, 1.0) × 15` | 3 invs saturates |
| Consecutive active days | 10 | `min(days / 14, 1.0) × 10` | 14 days saturates |
| After-hours ratio | 10 | `min(ratio, 1.0) × 10` | 1.0 = 100% after-hours |
| Critical case ratio | 10 | `(critical_invs / active_invs) × 10` | ratio ∈ [0,1] |

**Total = sum of all factor points, clamped to 100.**

All six weights sum to 100. This is enforced at `WorkloadPolicy` construction
time — invalid weights raise `ValueError`.

---

## Risk Bands

| Band | Score Range | Meaning |
|------|:-----------:|---------|
| `HEALTHY` | 0–29 | Normal load |
| `MODERATE` | 30–59 | Elevated — monitor |
| `HIGH` | 60–79 | At risk — intervention recommended |
| `CRITICAL` | 80–100 | Immediate action required |

Thresholds are configurable in `WorkloadPolicy` (`burnout_moderate_threshold`,
`burnout_high_threshold`, `burnout_critical_threshold`). Default values: 30 / 60 / 80.

---

## Example: HIGH Risk

**Officer: Sub-Inspector Priya**
- Capacity used: 90% → workload factor = 0.9 × 40 = **36.0**
- Overdue tasks: 4 → overdue_task factor = min(4/5, 1.0) × 15 = **12.0**
- Overdue investigations: 0 → **0.0**
- Consecutive days: 7 → min(7/14, 1.0) × 10 = **5.0**
- After-hours ratio: 0 → **0.0**
- Critical investigations: 1 of 3 → (1/3) × 10 ≈ **3.3**

```
Total = 36.0 + 12.0 + 0.0 + 5.0 + 0.0 + 3.3 = 56.3 → MODERATE
```

Explanation lines produced:
- "High workload (90% of capacity)"
- "4 overdue tasks"
- "7 consecutive active days"
- "1 critical investigation"

---

## Explainability

`BurnoutAssessment.explanation` contains one line per **non-zero factor**.
Zero-contributing factors are omitted to avoid noise.

`BurnoutAssessment.factor_scores` contains the **raw points** from each factor
for audit and UI display:

```json
{
  "workload": 36.0,
  "overdue_tasks": 12.0,
  "overdue_invs": 0.0,
  "consecutive_days": 5.0,
  "after_hours": 0.0,
  "critical_ratio": 3.33
}
```

---

## Placeholder Metrics

`consecutive_active_days` and `after_hours_ratio` are placeholder inputs
accepted by the engine. Callers that don't have these data sources pass 0 —
the engine produces a valid, slightly conservative burnout score from the
remaining four factors.

When duty-roster and shift data are available (M4/M5), these can be wired in
without any change to the engine or DTO contracts.

---

## Determinism Guarantee

The same six inputs + the same `WorkloadPolicy` **always** produce the same
burnout score. There is no randomness, no time-based state, and no
model weights that drift. This is enforced by the 20-run determinism test.
