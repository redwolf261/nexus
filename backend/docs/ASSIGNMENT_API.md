# Assignment API & Access Control — Phase 8.2 Milestone 4

## REST API Specification

All endpoints are mounted under `/api/assignment` and require JWT authentication via `Authorization: Bearer <token>` or session cookies.

---

### Endpoint Reference

| Endpoint | Method | Required Role | Summary |
|----------|:------:|:-------------:|---------|
| `/api/assignment/recommend/{investigation_id}` | `GET` | Analyst+ | Get ranked officer recommendations. |
| `/api/assignment/validate` | `POST` | Analyst+ | Validate operational pre-conditions. |
| `/api/assignment/assign` | `POST` | Supervisor+ | Assign officer to investigation. |
| `/api/assignment/reassign` | `POST` | Supervisor+ | Reassign investigation to new officer. |
| `/api/assignment/bulk-reassign` | `POST` | Supervisor+ | Perform batch reassignments. |
| `/api/assignment/recommend-many` | `POST` | Analyst+ | Bulk recommendations for multiple cases. |
| `/api/assignment/history/{investigation_id}` | `GET` | ReadOnly+ | Get audit history for a case. |
| `/api/assignment/history/officer/{officer_id}` | `GET` | ReadOnly+ | Get assignment history for an officer. |
| `/api/assignment/estimate/{investigation_id}` | `GET` | ReadOnly+ | Deterministic completion duration estimate. |

---

## Role-Based Access Control (RBAC)

- **`Supervisor` / `Admin`**: Required for mutation operations (`assign`, `reassign`, `bulk-reassign`).
- **`Analyst`**: Authorized to generate recommendations and validate pre-conditions.
- **`ReadOnly`**: Authorized for history and estimation queries.
