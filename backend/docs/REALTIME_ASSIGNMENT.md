# Realtime Assignment WebSockets — Phase 8.2 Milestone 4

## Overview

Realtime assignment updates are broadcast via `EventDispatcher` over WebSocket channels (`/ws/case_{id}` and `/ws/global_feed`).

Every event contains a monotonic `sequence` number tied to the investigation's `last_sequence`, guaranteeing ordered event delivery and replay capabilities.

---

## Event Types Published

| Event Type | Trigger | Payload Contents |
|------------|---------|------------------|
| `ASSIGNMENT_RECOMMENDED` | `recommend()` called | `investigation_id`, `policy_version`, `top_recommendations` |
| `ASSIGNMENT_VALIDATED` | `validate()` called | `investigation_id`, `officer_id`, `is_valid`, `errors` |
| `ASSIGNMENT_CREATED` | `assign()` executed | `assignment_id`, `investigation_id`, `officer_id`, `assigned_by`, `sequence` |
| `ASSIGNMENT_REASSIGNED` | `reassign()` executed | `assignment_id`, `investigation_id`, `officer_id`, `previous_officer`, `reassign_type` |
| `ASSIGNMENT_FAILED` | `assign()` blocked | `investigation_id`, `officer_id`, `reasons` |

---

## Example WebSocket Payload

```json
{
  "event_id": "EVT-8F3A2B11",
  "event_type": "ASSIGNMENT_CREATED",
  "timestamp": "2026-07-23T10:09:42Z",
  "case_id": "INV-2026-002",
  "sequence": 2,
  "user_id": "supervisor_john",
  "payload": {
    "assignment_id": "ASG-8A91F2C3",
    "investigation_id": "INV-2026-002",
    "officer_id": "OFF-102",
    "previous_officer": null,
    "assigned_by": "supervisor_john",
    "timestamp": "2026-07-23T10:09:42Z",
    "policy_version": "1.0.0"
  }
}
```
