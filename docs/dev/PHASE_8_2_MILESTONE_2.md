# Phase 8.2 — Milestone 2: Assignment Scoring Engine

**Status:** ✅ Complete — 54/54 M2 tests passing, 152/152 across M0+M1+M2 (0 regressions)
**Date:** 2026-07-21
**Verification standard:** every claim below is backed by executed `pytest` output.

---

## What was built

A **deterministic, fully-explainable** 7-factor scoring engine and a ranking
service that recommends officers for a case — **without ever auto-assigning**.
No ML, no LLM, no randomness: identical inputs always yield identical output
(guaranteed by tests, including a 20-run determinism check).

### The 7-factor model (`SCORE_WEIGHTS`, defined once in `contracts.py`)

| Component | Weight | Logic |
|-----------|:-----:|-------|
| `workload` | 0.30 | `1 − utilization` (cases/max_capacity), clamped to [0,1] |
| `skill_match` | 0.25 | fraction of preferred skills held + required-specialization bonus |
| `district_match` | 0.15 | 1.0 same jurisdiction, 0.0 different, 0.5 unknown |
| `priority_alignment` | 0.10 | urgent cases reward experience; calm cases neutral |
| `experience` | 0.10 | normalized years (0 at 0y, 1.0 at 25y ceiling) |
| `recent_case_similarity` | 0.05 | holds skills/spec implied by the case type |
| `supervisor_preference` | 0.05 | supervisor's explicit preference list (rank-decayed) |

Weights sum to exactly **1.0** (tested). The weighting lives only in
`AssignmentScore.build()` — the engine's `_score_*` methods each return a
`(score∈[0,1], explanation_or_None)` tuple and never touch weights.

### Explainability

Every non-neutral component contributes a human-readable line. A strong
candidate produces output like:

```
Officer B — overall 0.71
  • 62% workload (8/13 cases)
  • 2/2 preferred skills (CYBER_FORENSICS, OSINT); CYBER_CRIME specialization
  • Same jurisdiction
  • High-priority case aligned with 12y experience
  • 12 years experience
  • Handled similar CYBER work
  • Supervisor-preferred officer
```

This is exactly the spec's "Recommended Officer B because…" narrative, generated
deterministically. It feeds supervisor UI (M5), audit (`assignment_records`), and
future LLM explanation (Phase 10) through the stable `AssignmentScore` contract.

### Case-type → capability mapping

A hand-curated, deterministic map (`_CASE_TYPE_SKILLS`, `_CASE_TYPE_SPECIALIZATION`)
translates a free-text `case_type` ("CYBER", "ATTEMPT_MURDER", …) into the skills
and specialization that make an officer a natural fit. Substring matching means
"MURDER" and "ATTEMPT_MURDER" both resolve to HOMICIDE. Unknown types contribute
a neutral 0.5 (no fabricated signal).

### Ranking & recommendation (`RecommendationService`)

Combines scoring with the **M1 capacity gate**. Ranking is deterministic:

1. Officers passing the capacity/availability gate rank **above** those failing it.
2. Within a group: `overall_score` descending.
3. Ties broken by `officer_id` ascending (stable across runs/machines).

A high-scoring but at-capacity officer is shown **ranked last with its rejection
reason** — never silently dropped, never assignable. This is the core guarantee:
*capacity cannot be bypassed by a good score.*

Surface (consumed by M4 API):
- `rank_officers(context)` → full `RankedRecommendation` list
- `recommend_officer(context)` → best **assignable** candidate (or None)
- `recommend_multiple(context, top_n, include_non_assignable=False)`

---

## Contracts added (Milestone 2)

- **`ScoringContext`** (frozen) — the immutable case description the caller (M4)
  assembles from Investigation + FIR data. Keeps the engine decoupled from
  persistence. Optional fields degrade gracefully to neutral scores.
- **`RankedRecommendation`** (frozen) — an `AssignmentScore` + rank + assignable
  flag + rejection summary. `to_dict()` merges the score for a flat API payload.

---

## Test evidence

```
$ python -m pytest backend/tests/test_assignment_scoring.py -q -p no:warnings
54 passed in 4.35s

$ python -m pytest backend/tests/test_assignment_scoring.py \
                   backend/tests/test_officer_capability.py \
                   backend/tests/test_task_engine.py -q -p no:warnings
152 passed in 8.98s        # 54 M2 + 73 M1 + 25 M0, no regressions
```

**Coverage by area (54 tests):** determinism (3), workload (5), skill match (7),
district (3), priority alignment (4), experience (4), recent similarity (3),
supervisor preference (4), explainability (3), case-type mapping (4), ranking (12),
certification-in-ranking (1), scale/1000-officers (1).

Scale: ranking **1,000 officers** completes in < 5s, output verified sorted +
deterministic.

---

## Acceptance criteria (M2 subset)

| Criterion | Status |
|-----------|--------|
| Deterministic scoring (no ML/LLM/random) | ✅ 20-run identical-output test |
| Reproducible rankings | ✅ tie-break by officer_id, tested |
| Every recommendation explainable | ✅ per-component reasons, tested |
| Component score breakdown returned | ✅ `component_scores()` |
| Capacity cannot be bypassed by score | ✅ gated officer ranked last, non-assignable |
| No auto-assignment | ✅ service only recommends; returns candidates |
| No Phase 8.1 / M1 regression | ✅ 152/152 combined |

**Exit criterion — "Recommendation engine produces reproducible rankings" — MET.**

---

## Design notes for M3 / M4

- **M3 (workload engine):** `recent_case_similarity` currently uses capability as
  a similarity proxy (no case-history table yet). M3 may replace it with real
  completed-case history *behind the same contract* — no consumer changes needed.
- **M4 (API):** assemble `ScoringContext` from the Investigation + its FIR
  (case_type ← FIR.crime_category, district_id ← FIR/Investigation, priority ←
  Investigation.priority). Persist approved/overridden picks into
  `assignment_records` (modeled in M1). `recommend_officer()` gives the default;
  always return the ranked list so the supervisor sees alternatives.
- **Preferred vs required certs:** a *required* skill/cert gates (capacity layer);
  a *preferred* cert is a scoring concern (M2 wires the hook; a scoring penalty
  for expired-preferred can be layered in without contract change).

---

## Files added / changed

**Added:**
- `backend/assignment/scoring_engine.py` — `AssignmentScoringEngine`
- `backend/assignment/recommendation_service.py` — `RecommendationService`
- `backend/tests/test_assignment_scoring.py` — 54 tests

**Changed:**
- `backend/assignment/contracts.py` — `ScoringContext`, `RankedRecommendation`
- `backend/assignment/__init__.py` — exports

Ready for **Milestone 3 — Workload Engine** (weighted case load, burnout metrics,
rebalancing recommendations, Gini coefficient).
