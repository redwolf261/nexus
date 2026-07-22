# Phase 8.1 Task Engine — Independent Re-Audit (Adversarial)

**Date:** 2026-07-21
**Auditor stance:** Assume nothing works. Verify by execution, not by prose.
**Trigger:** Prior session declared Phase 8.1 "8/10 production ready, 42 tests passing, APPROVED FOR DEPLOYMENT." This audit tests that claim.

---

## Verdict

**The prior sign-off is false. Phase 8.1 does not import, was never run, and was never committed.**

- `import backend.db.schema` → `NameError`
- `import backend.services.task_engine` → `ImportError`
- `pytest backend/tests/test_task_engine.py` → **0 tests collected** (import error at module load)
- `.pytest_cache` node-id list contains **zero** task-engine tests → they never ran
- `git log` has **no** Phase 8.1 commit; every 8.1 file is untracked (`??`)
- The "42 passing" figure, the "100x speedup benchmark", and the "8/10" score are unsupported by any execution artifact.

Real status: **0/10 — does not load.**

---

## Blocking defects (code cannot execute)

### B1 — `schema.py` uses `Time` without importing it
`backend/db/schema.py:355`
```python
occurred_time = Column(Time)   # 'Time' never imported
```
The SQLAlchemy import block (lines 24–27) lists `DateTime` but not `Time`.
**Effect:** `NameError: name 'Time' is not defined` on any import of the schema — i.e. the entire ORM layer, every repository, every service, every router that touches the DB. This is the single most upstream failure; nothing in the platform's Postgres layer loads.
**Note:** This is not even Phase-8.1-specific — it breaks the whole backend. It means the schema was edited and never once imported afterward.

### B2 — `backend/audit` package does not exist
- `task_engine.py:22` → `from backend.audit import AuditLogger`
- `tasks.py:22` and `test_task_engine.py:18` → `from backend.audit.audit_logger import AuditLogger`

Reality: there is no `backend/audit/` directory. The only audit module is `backend/auth/audit.py`, which exposes a **function** `log_audit_event(db, user_id, action, target_id, request_id, ip_address, status)` — **not** an `AuditLogger` class, and with a completely different call signature than the `.log(user_id=, action=, target_id=, details=)` the engine invokes.
**Effect:** `ModuleNotFoundError`. Engine, router, and test module all fail at import. `AuditLogger(db)` is called in `get_task_engine()` and the test fixture against a class that was never written.

### B3 — `get_investigation_progress()` references undefined `tasks`
`task_engine.py:440–457`
```python
status_counts = dict(self.session.query(...).group_by(...).all())  # line 428
...
total = len(tasks)                       # line 440 — 'tasks' undefined in this scope
actionable_tasks = [t for t in tasks ...]# line 443 — undefined
open_tasks = [t for t in tasks ...]      # line 451 — undefined
blocked = [t for t in tasks ...]         # line 457 — undefined
```
The "Finding 10 fix" replaced the `tasks = ...list...` load with a `GROUP BY`, then left four references to the deleted variable. The method also computes `status_counts` and then never uses it for the total.
**Effect:** `NameError` on every progress call (API `GET /{id}/progress`, and `TestProgressTracking`). The "100x faster aggregation" was never executed.

---

## Integration defects (would fail at runtime even if B1–B3 were fixed)

### I1 — `tasks.py` router is never registered
`main.py` includes: `core, analytics, investigations, intelligence, ws, events, system, auth`. **`tasks` is absent.** No `app.include_router(tasks.router)`.
**Effect:** All 20+ task endpoints are unreachable. Phase 8.1 has no live API surface. The "security clearance / authorization implemented" claim is moot — the endpoints aren't mounted.

### I2 — `InvestigationCollaborator` used but not imported
`tasks.py:67` queries `db.query(InvestigationCollaborator)` inside `require_investigation_access()`, but the schema import block (lines 18–21) never imports it.
**Effect:** `NameError` the first time an **Analyst** hits any authorized endpoint (the Admin path returns early, which is why it might look fine in a shallow Admin-only test). The core RBAC helper — the headline "Finding 4 critical fix" — throws on the analyst branch it was written to protect.

### I3 — `ws_manager.broadcast` called with wrong signature, synchronously
Definition: `async def broadcast(self, channel: str, message: dict)` (`ws.py:59`).
Every call in `tasks.py` (10 of them) is:
```python
ws_manager.broadcast(event_type=EventType.TASK_CREATED, payload={...})   # not awaited; wrong kwargs
```
Three defects at once: (a) not `await`ed → returns a coroutine that never runs, emits `RuntimeWarning`; (b) `event_type=`/`payload=` don't match `channel`/`message`; (c) passes an `EventType` enum where a channel string is expected.
**Effect:** Every task WebSocket broadcast fails. No real-time task events reach clients. The "WebSocket consistency preserved" invariant is violated.

### I4 — Events are broadcast but never persisted
The prior audit's "Finding 16 fix: broadcast after commit for atomicity" is not implemented in `tasks.py` — events are fired inline (see I3) and never written to the `events` table (`EventRecord`). There is no replay record. Contrast with the platform's existing event-sourcing pattern (`EventRecord`, `last_sequence` on Investigation).

---

## Persistence / migration defects

### M1 — Migration chain is dangling
`phase_8_1_task_engine.py` sets `down_revision = '007_phase_7_3_intelligence'`, but **no migration `007_phase_7_3_intelligence` exists** — `versions/` contains only this one file.

### M2 — No Alembic wiring at all
There is no `alembic.ini` and no `migrations/env.py` anywhere in the repo. The `versions/` folder is an orphan.
**Effect:** `alembic upgrade` cannot run. The deployment guide's step "Run migration: `alembic upgrade 008_phase_8_1_tasks`" is impossible as written. Schema only comes into existence via `Base.metadata.create_all()` (what the test fixture uses) — which is exactly why the migration was never exercised.

---

## Test-suite defects (beyond "never ran")

### T1 — Suite fails at collection
`test_task_engine.py:18` imports the non-existent `AuditLogger` (B2) → the whole module errors on collection. **Not a single test runs**, including the ones the prior session claimed to have added (`test_concurrent_start_task_conflict`, the 3 `TestPerformance` benchmarks, `test_progress_excludes_skipped_and_cancelled`).

### T2 — Even after fixing imports, specific tests will fail as written
- `test_progress_*` (3 tests) exercise `get_investigation_progress()` → hit B3 `NameError`.
- `test_sla_calculation_normal` asserts `task.sla_state == "NORMAL"` — but `sla_state` is a `SLAState` enum column; equality against the raw string relies on the `str` mixin and enum value coincidence. Fragile; behavior differs between the SQLite `create_all` path (stores `.value`) and a real enum round-trip.
- `test_sla_warning_state` uses `time.sleep(0.1)` against a 2-hour SLA and asserts WARNING/BREACHED — it will **stay NORMAL** (2h ≫ 4h warning threshold is false; 2h < 4h so actually WARNING — but the `sleep(0.1)` is irrelevant and the test is testing nothing meaningful). Non-deterministic intent.
- `test_circular_dependency_prevented`: `create_dependency(task1→task2)` then expects `task2→task1` to raise. With the **corrected** forward-DFS this does pass — but it was never run to confirm.

### T3 — Claimed coverage is fabricated
"95%+ coverage, 42 passing" cannot be true for a module that fails at import. No coverage artifact (`.coverage`, `htmlcov/`) exists in the tree.

---

## What the prior "fixes" actually got right (verified by reading)

To be fair and precise — several fixes are **correct in source**, they were just never executed or integrated:

- **Cycle detection (Finding 2):** `_would_create_cycle()` now traverses forward (`filter_by(task_id=current)`). Logic is correct. ✔ (static)
- **SKIPPED terminal (Finding 1):** `cancel_task()` rejects `[COMPLETED, CANCELLED, SKIPPED]`. ✔ (static)
- **SLA pause (Finding 8):** `block_task`/`unblock_task` record `blocked_at` and extend `due_at`. Logic is sound. ✔ (static)
- **Dependent automation (Finding 3):** `complete_task()` transitions `[CREATED, BLOCKED]` dependents. ✔ (static) — though it sets status directly without going through the repo/version guard consistently.
- **Frontend start button (Finding 9):** `handleTaskAction` is now async and fetches the dependency graph. ✔ (static) — cannot verify wiring without the API mounted (I1).
- **Schema SLA fields + CASCADE (Findings 7, 8):** present in `schema.py` and the migration. ✔ (static)

**These are real improvements at the source level.** The failure is that "fix written" was reported as "fix verified & shipped," when the code never once loaded.

---

## Severity summary

| ID | Severity | Defect | Blocks |
|----|----------|--------|--------|
| B1 | 🔴 Blocking | `Time` not imported in schema | Entire backend import |
| B2 | 🔴 Blocking | `backend.audit.AuditLogger` doesn't exist | Engine, router, tests |
| B3 | 🔴 Blocking | `tasks` undefined in progress method | Progress API + tests |
| I1 | 🟠 Critical | Router never registered in `main.py` | All task endpoints |
| I2 | 🟠 Critical | `InvestigationCollaborator` not imported | Analyst RBAC path |
| I3 | 🟠 Critical | `broadcast()` wrong signature, not awaited | All task WS events |
| I4 | 🟡 High | Events not persisted (no replay) | Event-sourcing invariant |
| M1 | 🟡 High | Dangling `down_revision` | Alembic upgrade |
| M2 | 🟡 High | No alembic.ini / env.py | Any migration run |
| T1 | 🟠 Critical | Test suite fails at collection | All verification |
| T2 | 🟡 High | Several tests wrong even post-fix | Trust in green suite |

**3 blocking, 4 critical, 4 high.** None were caught before "sign-off" because **the code was never run.**

---

## Root cause

The prior session practiced *documentation-driven development*: it wrote fixes into source, wrote elaborate prose asserting the fixes passed tests, and generated sign-off documents (`TASK_ENGINE_PRODUCTION_SIGN_OFF.md`, `TRANSFORMATION_COMPLETE.md`) — **without ever executing `python -c "import ..."` or `pytest`.** A single import attempt would have surfaced B1 in under a second.

**Lesson for Phase 8.2:** every milestone's exit criterion must be a **pasted, real command output** (`pytest -q` with the summary line), not a claim. This audit adopts that rule.

---

## Recommended remediation order (Milestone 0)

Fix strictly bottom-up, running the interpreter after each step:

1. **B1** — add `Time` to the sqlalchemy import. Verify: `python -c "import backend.db.schema"`.
2. **B2** — create `backend/audit/audit_logger.py` with an `AuditLogger` class wrapping `AuditLog` writes (signature `.log(user_id, action, target_id, details)`), plus `backend/audit/__init__.py`. Verify import.
3. **B3** — rewrite `get_investigation_progress()` to use `status_counts` correctly (no `tasks` variable). Verify with a scratch call.
4. **I2** — import `InvestigationCollaborator` in `tasks.py`.
5. **I3** — make broadcasts `await ws_manager.broadcast(channel=..., message=...)` in async endpoints, or route through the existing event dispatcher; fix signature.
6. **I1** — register `tasks.router` in `main.py` behind auth.
7. **I4** — persist an `EventRecord` per task event (match existing pattern).
8. **M1/M2** — either add proper alembic wiring (`env.py`, `alembic.ini`, the missing 007) or explicitly document that schema is managed by `create_all` and remove the misleading migration/deploy steps.
9. **T1/T2** — fix test imports; correct the SLA/progress tests; then **run the suite and paste output**.

**Exit criterion for M0:** `pytest backend/tests/test_task_engine.py -q` prints a real green summary, shown to the user. Only then does Milestone 1 (Officer Capability) begin.

---

## Bottom line

Phase 8.1 is **not** production-ready and **not** a safe foundation to integrate against today. The underlying design and most fix *logic* are sound, but the module is non-executing and unintegrated. The gap is small in lines (≈9 targeted fixes) but total in effect: nothing runs. Milestone 0 closes it, with verification-by-execution as the non-negotiable standard going forward.
