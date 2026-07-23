# Immutable Assignment History — Phase 8.2 Milestone 4

## Overview

The `AssignmentHistory` table (`assignment_histories`) provides an **immutable, append-only audit record** of every assignment and reassignment event.

History records are **never modified or deleted**. Reassignments always append a new entry to the timeline, preserving complete historical provenance.

---

## Database Schema

```sql
CREATE TABLE assignment_histories (
    id VARCHAR PRIMARY KEY,
    assignment_id VARCHAR INDEX,
    investigation_id VARCHAR REFERENCES investigations(id) INDEX,
    officer_id VARCHAR REFERENCES officers(officer_id) INDEX,
    assigned_by VARCHAR REFERENCES users(id) INDEX,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() INDEX,
    reason TEXT,
    recommendation_score FLOAT,
    policy_version VARCHAR,
    manual_override BOOLEAN DEFAULT FALSE,
    override_reason TEXT,
    previous_officer VARCHAR INDEX
);
```

---

## Reassignment Triggers Supported

1. **`RESIGNATION`** — Officer leaves service; open cases redistributed with previous_officer retained.
2. **`LEAVE`** — Scheduled or emergency leave; cases temporarily reassigned.
3. **`SUSPENSION`** — Disciplinary action; immediate reassignment with audit reason.
4. **`PROMOTION`** — Rank change / transfer to specialized unit.
5. **`MANUAL`** — Standard supervisor operational decision.
6. **`BULK`** — Station-wide workload rebalancing batch.

---

## Manual Overrides

When a supervisor overrides an operational gate failure (e.g. assigning an officer near capacity or during training), `manual_override = True` and a mandatory `override_reason` are recorded. This ensures total audit transparency for high-level commanders.
