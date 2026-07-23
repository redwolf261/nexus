# Rebalancing Strategy — Phase 8.2 Milestone 3

## Overview

The rebalancing recommender identifies overloaded officers, finds movable
investigations, and suggests eligible destinations. It **never auto-assigns**.
Human approval via the supervisor UI (Milestone 5) is the only path to an
actual assignment change.

Every recommendation is deterministic and reproducible. Running the same
inputs twice produces the same recommendation list in the same order.

---

## Algorithm

### Step 1: Identify Overloaded Sources

An officer is considered overloaded when:

```
capacity_used > rebalance_destination_capacity_max   (default: 0.85)
```

This is the same threshold that prevents a destination officer from accepting
work. Sources are sorted by `officer_id` ascending for deterministic ordering.

### Step 2: Select Movable Investigations

For each overloaded source, candidate investigations are:
- **Active** — status not in the inactive set (not COMPLETED / CANCELLED / ARCHIVED / CLOSED)
- **Non-zero weight** — investigation has a recognizable priority

Candidates are sorted by **priority descending** (CRITICAL first), then by
`investigation_id` ascending for tie-breaking. The highest-burden cases are
recommended for transfer first.

### Step 3: Find Eligible Destinations

For each candidate investigation, a destination officer is eligible when all
of the following are true:

| Constraint | Rule |
|-----------|------|
| Not self | Destination ≠ Source |
| Capacity headroom | `capacity_used < 0.85` **and** after absorbing the case, still `< 0.85` |
| Jurisdiction | Same district as source, unless `allow_cross_jurisdiction=True` |

> **Note on skills**: The current implementation does not enforce skill
> matching as a hard gate (the assignment engine's skill gate is in M2
> `OfficerCapacityService`). Destination skills are recorded in
> `skills_matched` for supervisor transparency, but do not filter eligibility.
> A future iteration can add a required-skill gate here without contract changes.

### Step 4: Select Best Destination

Among eligible destinations, select the one with the **lowest `capacity_used`**
(most headroom). Ties broken by `officer_id` ascending.

### Step 5: Build Recommendation

For each (source, investigation, destination) triple, create a
`RebalanceRecommendation` containing:

- Current and expected workload for both officers
- Percentage reduction for the source
- Why the source is overloaded (human-readable)
- Why the destination qualifies (human-readable)
- Skills the destination holds
- Jurisdiction validity flag

---

## Constraints Summary

| Rule | Value |
|------|-------|
| Source threshold | capacity_used > 0.85 |
| Destination hard ceiling | capacity_used after move < 0.85 |
| Cross-jurisdiction | Blocked by default; enabled via `allow_cross_jurisdiction=True` |
| Auto-assignment | **Never** — recommendations only |
| Inactive investigations | Never recommended for transfer |

---

## Example Recommendation

```
Move Investigation KA-2026-001 (CRITICAL)
  Source:      Officer A    current=12.0  expected=7.0   reduction=41.7%
  Destination: Officer C    current=3.0   expected=8.0
  
  Source overloaded:    Officer A capacity at 120% (workload 12.0 / max 10)
  Destination qualifies: Officer C has capacity at 30% (7.0 weighted slots available)
  Skills matched: [CYBER_FORENSICS, OSINT]
  Jurisdiction: valid (same district)
```

---

## Ordering of Output

Recommendations are ordered:
1. **Primary**: `source_officer_id` ascending (alphabetical)
2. **Secondary**: `investigation_priority` descending (CRITICAL before LOW)
3. **Tertiary**: `investigation_id` ascending (stable tie-break)

This ordering is deterministic and reproducible.

---

## Performance

Target: < 2 seconds for 1,000 officers with 10 investigations each.

The algorithm is O(S × I × D) where:
- S = overloaded sources (typically a small fraction of the fleet)
- I = active investigations per source (bounded by max_capacity × weight ratio)
- D = eligible destinations

In practice, S × I is small (overloaded officers are the minority), making
the algorithm much faster than the worst case.

---

## What This Is Not

- **Not an assignment engine.** The rebalancing recommender does not write
  to `assignment_records` or modify any investigation's `assigned_officer`.
- **Not AI or ML.** Every decision has a traceable, deterministic rule.
- **Not final.** Recommendations are inputs to human judgment, not outputs
  of it. A supervisor may accept, reject, or modify any recommendation.
