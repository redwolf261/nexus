# Phase 8.2 — Milestone 1: Officer Capability Foundation

**Status:** ✅ Complete — 73/73 M1 tests passing, 0 regressions (98/98 with M0)
**Date:** 2026-07-21
**Verification standard:** every claim below is backed by executed `pytest` / interpreter output.

---

## What was built

Milestone 1 establishes the data + policy foundation the rest of Phase 8.2 builds
on: the officer capability model, the immutable scoring contract, and the
capacity/availability/reconciliation services. **No auto-assignment logic yet**
(that is M2+); this milestone is deliberately about *modeling* and *rules*.

### 1. Schema extensions (`backend/db/schema.py`)

**Officer table — 8 new columns** (all nullable/defaulted → dataset CSV loader
stays backward-compatible):
`subdivision`, `years_experience`, `maximum_capacity` (default 10),
`availability_status` (default `ON_DUTY`), `current_case_count`,
`current_task_count`, `leave_ends_on`, `capability_version`.

**6 new tables:**
| Table | Purpose |
|-------|---------|
| `officer_skills` | Officer ↔ SkillCode (fixed catalog) + proficiency |
| `officer_specializations` | Officer ↔ Specialization + primary flag |
| `officer_certifications` | Certs with issued/expiry/authority/status |
| `officer_availability_logs` | Audit of every availability transition |
| `officer_workload_reconciliation` | Record of cache-vs-truth corrections |
| `assignment_records` | Immutable assignment + AssignmentScore + override audit |

**6 new enums:** `AvailabilityStatus` (7 states), `OfficerRank` (9),
`SkillCode` (21 — fixed catalog), `Specialization` (8), `CertificationStatus` (4),
`BurnoutRisk` (4).

### 2. AssignmentScore contract (`backend/assignment/contracts.py`)

The immutable interface M2/M4/M5/Phase-10 all build against — defined **now**, in
M1, so the contract is stable before any scoring code exists.

- Frozen dataclass. `SCORE_WEIGHTS` are the canonical Phase 8.2 weights
  (0.30/0.25/0.15/0.10/0.10/0.05/0.05) and **sum to exactly 1.0** (tested).
- `AssignmentScore.build(...)` computes the weighted `overall_score` in one place;
  all component inputs are clamped to [0,1]; NaN-safe.
- Deterministic: identical inputs → identical `overall_score` (tested — e.g. the
  worked example resolves to exactly `0.61`).
- `to_dict()` / `component_scores()` give JSON for API/audit/UI.
- Companion contracts: `CapacityDetails`, `CapacityViolation`, `RejectionReason`,
  `WorkloadSummary` — all with `to_dict()`.

### 3. OfficerRepository (`backend/assignment/officer_repository.py`)

Pure data access: skills/specializations/certifications CRUD (idempotent adds),
valid-cert filtering (`ACTIVE` + not past expiry), `mark_expired_certifications()`,
denormalized counter maintenance (`update_workload_counters` with zero-clamp,
`set_workload_counters`), and the **DB-derived truth counts**
(`count_open_cases_from_source`, `count_active_tasks_from_source`) that
reconciliation uses. `list_available_officers()` returns only `ON_DUTY` + `FIELD`.

### 4. AvailabilityStateManager (`backend/assignment/availability.py`)

Strict state machine matching the spec, with `ON_DUTY` as the hub:
```
ON_DUTY <-> BREAK | FIELD | LEAVE | TRAINING | OFF_DUTY
ON_DUTY  -> SUSPENDED
SUSPENDED -> ON_DUTY   (Admin/Supervisor only)
```
- Illegal transitions rejected with an explainable error.
- `SUSPENDED` cannot self-lift; requires `Role.Admin`/`Role.Supervisor`.
- No-op (same-state) transitions rejected.
- **Every** accepted transition writes an `OfficerAvailabilityLog` (who/when/why).
- `schedule_leave()` + `auto_expire_leave()` (returns officers from LEAVE on/after
  `leave_ends_on`, audited as actor `SYSTEM`).

### 5. OfficerCapacityService (`backend/assignment/capacity_service.py`)

Read-only capacity policy producing **explainable** results. `get_capacity_details()`
returns `assignable` + a list of `RejectionReason`s; rejection codes:
`UNAVAILABLE`, `FIELD_CRITICAL_ONLY`, `CAPACITY_EXCEEDED`, `MISSING_SKILL`,
`MISSING_CERTIFICATION`. Multiple rejections accumulate. Also
`get_workload_summary()` (utilization + burnout: LOW/MEDIUM/HIGH/CRITICAL at
0.6/0.85/1.0) and `list_capacity_violations()` (single-query, fleet-wide).

### 6. ReconciliationService (`backend/assignment/reconciliation.py`)

`reconcile_officer_workload()` compares cached counters to source-of-truth counts,
corrects drift, and writes an audit row per mismatched field.
`reconcile_all_workloads()` returns an aggregate report. History via
`get_reconciliation_history()`. **The assignment engine never assumes the cache is
exact — this is the safety net.**

### 7. Migration (`backend/db/migrate_phase_8_2.py` + `backend/main.py` startup)

The platform manages schema via `create_all()` + idempotent `ALTER TABLE ... ADD
COLUMN IF NOT EXISTS` at startup (there is **no Alembic wiring** in this repo — the
prior Phase 8.1 alembic file was an orphan; see `PHASE_8_1_REAUDIT.md`). M1 follows
the real pattern:
- New tables via `create_all()`.
- 8 new `officers` columns via additive ALTERs (Postgres `IF NOT EXISTS`; SQLite
  via PRAGMA presence-check).
- Backfills: existing officers get `ON_DUTY`, capacity 10, zeroed counters, and
  `years_experience` seeded from `tenure_years`.
- Added to `main.py` startup **and** as a runnable script: `python -m backend.db.migrate_phase_8_2`.
- **Idempotent** — verified by running twice (2nd run adds 0 columns).

---

## Test evidence

```
$ python -m pytest backend/tests/test_officer_capability.py -q -p no:warnings
73 passed in 4.07s

$ python -m pytest backend/tests/test_officer_capability.py backend/tests/test_task_engine.py -q -p no:warnings
98 passed in 5.36s        # 73 M1 + 25 M0, no regressions
```

**Coverage by area:** AssignmentScore contract (9), OfficerRepository skills (4),
specializations (3), certifications (5), counters (5), availability filter (1),
availability state machine (13), leave (4), capacity service (18), reconciliation (6),
scale/1000-officers (2), migration (3). **73 total.**

Scale checks included: capacity-violation scan over **1,000 officers** completes in
< 0.5s; `reconcile_all` over 200 officers.

---

## Acceptance criteria (M1 subset)

| Criterion | Status |
|-----------|--------|
| Officer capability model complete & indexed | ✅ 8 columns + 6 tables + indexes |
| Fixed enumerated skill catalog | ✅ 21 `SkillCode` values |
| Certifications track expiry + status | ✅ mandatory-expired → reject |
| Availability strict state machine + audited | ✅ 13 tests, every transition logged |
| Workload counters reconcilable, DB = source of truth | ✅ ReconciliationService + audit |
| AssignmentScore contract defined (M1, not M2) | ✅ immutable, deterministic, weights=1.0 |
| Explainable rejections | ✅ `RejectionReason{code,message}` |
| No Phase 8.1 regression | ✅ 25/25 task-engine tests still green |
| Deterministic scoring | ✅ contract-level determinism tested |

---

## Integration notes for M2 (scoring engine)

- Consume `AssignmentScore.build(...)` — **do not** re-implement weighting.
- Use `OfficerCapacityService.can_assign_case()` as a hard pre-filter *before*
  scoring (capacity rules are gates, not score penalties — except preferred-cert,
  which M2 will model as a penalty per the spec).
- `OfficerRepository.list_available_officers()` is the candidate pool.
- Persist recommendations/overrides into `assignment_records` (already modeled).
- Counters are a cache; call reconciliation before trusting utilization in batch ops.

---

## Files added / changed

**Added:**
- `backend/assignment/__init__.py`
- `backend/assignment/contracts.py`
- `backend/assignment/officer_repository.py`
- `backend/assignment/availability.py`
- `backend/assignment/capacity_service.py`
- `backend/assignment/reconciliation.py`
- `backend/db/migrate_phase_8_2.py`
- `backend/tests/test_officer_capability.py`

**Changed:**
- `backend/db/schema.py` (Officer columns + 6 tables + 6 enums)
- `backend/main.py` (Phase 8.2 startup migrations)

---

## Milestone 1 exit criterion: **MET**

> "Officer capability model is complete and tested."

73/73 M1 tests green, migration verified idempotent on a simulated pre-8.2 DB, zero
regression to Phase 8.1. Ready for **Milestone 2 — Assignment Scoring Engine**.
