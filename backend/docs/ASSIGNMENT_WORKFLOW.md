# Assignment Operational Workflow — Phase 8.2 Milestone 4

## End-to-End Sequence Diagram

```
Investigation Created / Pending Staffing
        │
        ▼
GET /api/assignment/recommend/{investigation_id}
        │
        ├──► Scoring Engine (M2) — computes overall_score & breakdown
        └──► Workload Engine (M3) — computes capacity_used & burnout risk
        │
        ▼
Ranked Recommendation List Returned
        │
        ▼
POST /api/assignment/validate
        │
        ├──► Verify Officer ON_DUTY
        ├──► Verify Capacity Available
        ├──► Verify Jurisdiction & Required Skills
        └──► Verify Optimistic Lock Version
        │
        ▼
Supervisor Decision in Command Centre UI
        │
        ├──► Standard Assignment (Validation Passed)
        └──► Manual Override (Validation Warnings / Failures Override + Reason)
        │
        ▼
POST /api/assignment/assign  OR  POST /api/assignment/reassign
        │
        ├──► Update Investigation (assigned_officer, version++, last_sequence++)
        ├──► Update Officer case counters (prev--, new++)
        ├──► Append to AssignmentHistory (immutable audit)
        ├──► Log AuditLog entry (ASSIGNMENT_CREATED / ASSIGNMENT_REASSIGNED)
        └──► Dispatch WebSocket Event (ASSIGNMENT_CREATED / ASSIGNMENT_REASSIGNED)
```

---

## Validation Gate Rules

1. **`investigation_open`**: Status must not be `CLOSED`, `CANCELLED`, or `ARCHIVED`.
2. **`officer_on_duty`**: Officer `availability_status` must equal `ON_DUTY`.
3. **`capacity_available`**: Officer weighted `capacity_used` must be `< 1.0` (headroom for case).
4. **`jurisdiction_match`**: Case district must match officer district (unless cross-jurisdiction allowed).
5. **`version_match`**: `investigation.version` must match `expected_version` (prevents races).
