# Central Escalation Rules Reference (Phase 8.2 Milestone 5)

## Escalation Triggers

| Rule Name | Trigger Condition | Escalation Target | Hard Block? |
|-----------|-------------------|-------------------|-------------|
| `CRITICAL_CAPACITY` | Candidate `capacity_used >= 1.5` | ACP | No |
| `LEAVE_ASSIGNMENT` | Candidate `availability_status == "LEAVE"` | ACP | No |
| `UNAVAILABLE_ASSIGNMENT` | Candidate status in (`OFF_DUTY`, `TRAINING`) | ACP | No |
| `HIGH_RISK_CASE` | Investigation priority `CRITICAL` | ACP | No |
| `INTERSTATE_ASSIGNMENT` | Multi-state investigation | DCP | No |
| `SUSPENDED_OFFICER` | Candidate `availability_status == "SUSPENDED"` | DCP | Yes (Requires DCP) |

## API Endpoints for Escalations

- `GET /api/assignment/escalations` — Pending queue lookup (ACP/DCP/Admin)
- `POST /api/assignment/escalations/{id}/approve` — Approve escalation request
