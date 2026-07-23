# Compliance REST API Reference

| Endpoint | Method | Role | Description |
| :--- | :--- | :--- | :--- |
| `/api/compliance/dashboard` | `GET` | All Authenticated | Executive dashboard summary & metrics. |
| `/api/compliance/violations` | `GET` | All Authenticated | Paginated list of active policy violations. |
| `/api/compliance/entity/{id}` | `GET` | All Authenticated | Violations for a specific entity. |
| `/api/compliance/user/{id}` | `GET` | All Authenticated | Violations for a specific user/actor. |
| `/api/compliance/rules` | `GET` | All Authenticated | Catalog of 20 policy rules. |
| `/api/compliance/scan` | `POST` | All Authenticated | Trigger incremental or entity scan. |
| `/api/compliance/recalculate`| `POST` | All Authenticated | Recalculate operational risk score. |
| `/api/compliance/risk` | `GET` | All Authenticated | Risk score & subsystem breakdown. |
| `/api/compliance/history` | `GET` | All Authenticated | Historical compliance trend lines. |
| `/api/compliance/export` | `POST` | `ADMIN`, `SUPERVISOR`, `ACP`, `DCP` | RBAC protected report export. |
