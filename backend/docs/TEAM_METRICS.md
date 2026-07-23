# Team Metrics — Phase 8.2 Milestone 3

## Overview

`TeamMetrics` provides the fleet-wide distributional view of workload that a
superintendent or operations commander needs to spot systemic imbalance.

All values are deterministic. The same set of `OfficerWorkload` objects always
produces the same `TeamMetrics`.

---

## Statistical Measures

| Metric | Formula | Notes |
|--------|---------|-------|
| `mean_workload` | `Σ raw_workload / n` | Arithmetic mean |
| `median_workload` | Middle value | Population median (not sample) |
| `std_workload` | `√(Σ(xi − μ)² / n)` | **Population** standard deviation |
| `max_workload` | `max(raw_workloads)` | Highest individual burden |
| `min_workload` | `min(raw_workloads)` | Lowest individual burden |
| `average_capacity_used` | Mean of `capacity_used` ratios | Requires pre-computed CapacityMetrics |
| `gini_coefficient` | See below | Inequality measure ∈ [0, 1] |

**Note on std_workload**: uses **population** standard deviation (divide by n,
not n−1). This is correct when all officers being measured form the complete
group of interest (e.g., all officers in a station). It would need adjustment
if used as a sample estimate for a larger population.

---

## Gini Coefficient

The Gini coefficient is the primary inequality metric for workload distribution.

### Formula

```
G = ΣΣ|xi − xj| / (2 × n² × μ)
```

where `n` is the officer count and `μ` is the mean workload.

### Interpretation

| Gini | Meaning |
|:----:|---------|
| 0.0 | Perfect equality — all officers have identical workload |
| 0.5 | Significant inequality |
| 1.0 | Perfect inequality — one officer holds all work |

In practice, a healthy team should have Gini < 0.3. A Gini above 0.5 indicates
structural overload on a minority of officers.

### Edge Cases

| Condition | Return value |
|-----------|:------------:|
| 0 officers | 0.0 |
| 1 officer | 0.0 |
| All zero workloads | 0.0 |
| All equal workloads | 0.0 |

None of these divide by zero.

### Complexity

The exact Gini formula is **O(n²)**. For 1,000 officers this is 1,000,000
operations — measured at < 200 ms in production Python. For very large
populations (n > 10,000), a sorted O(n log n) equivalent should be substituted.
The current implementation is documented with this constraint.

---

## Burnout Distribution

The burnout distribution counts officers by risk band:

```json
{
  "HEALTHY": 45,
  "MODERATE": 12,
  "HIGH": 3,
  "CRITICAL": 1
}
```

This requires pre-computed `BurnoutAssessment` objects to be passed to
`calculate_team_metrics_full()`. When calling `calculate_team_metrics()` without
burnout data, the distribution is zero-valued.

---

## Capacity Histogram

The capacity histogram divides `capacity_used` into 5 buckets:

| Bucket | Range |
|--------|-------|
| `0–25%` | `[0.0, 0.25)` |
| `25–50%` | `[0.25, 0.50)` |
| `50–75%` | `[0.50, 0.75)` |
| `75–100%` | `[0.75, 1.00)` |
| `100%+` | `[1.00, ∞)` |

Each bucket contains a `count` (number of officers). An officer with
`capacity_used = 1.0` falls into the `100%+` bucket (the check is `>= 1.0`).

---

## Two-Method API

| Method | Use case |
|--------|---------|
| `calculate_team_metrics(workloads)` | Quick view — only workload stats + coarse histogram |
| `calculate_team_metrics_full(workloads, capacities, burnouts)` | Full view — all fields populated accurately |

Use `calculate_team_metrics_full()` in production. The lighter version is for
quick debugging or when capacity/burnout data is not available.

---

## Empty Team Handling

An empty officer list returns a fully valid `TeamMetrics` with all numeric fields
set to `0.0` and all distribution/histogram counts set to `0`. No exception is
raised.
