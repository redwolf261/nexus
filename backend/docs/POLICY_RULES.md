# Compliance Policy Rules Reference Catalog

## Rule Catalog (20 Mandatory Rules)

| Rule ID | Category | Severity | Name | Description |
| :--- | :--- | :--- | :--- | :--- |
| `RULE_AUTH_01` | ASSIGNMENT | HIGH | Assignment Without Authority | Task assigned to officer lacking requisite rank or role. |
| `RULE_APPROV_01` | APPROVAL | CRITICAL | Approval Outside Hierarchy | Approval granted by officer outside chain of command. |
| `RULE_GOV_01` | GOVERNANCE | MEDIUM | Missing Override Justification | Assignment override without mandatory written rationale. |
| `RULE_APPROV_02` | APPROVAL | HIGH | Invalid Delegation | Delegation duration exceeds 30-day limit. |
| `RULE_APPROV_03` | APPROVAL | HIGH | Expired Delegation Action | Action executed using expired delegation window. |
| `RULE_ASSIGN_01` | ASSIGNMENT | MEDIUM | Officer Over Capacity | Task assigned to officer exceeding active capacity limit. |
| `RULE_ASSIGN_02` | ASSIGNMENT | HIGH | Assignment Outside Jurisdiction | Officer assigned outside jurisdiction without clearance. |
| `RULE_APPROV_04` | APPROVAL | CRITICAL | Missing Mandatory Approval | Task completed without required approval signoff. |
| `RULE_AUDIT_01` | AUDIT | CRITICAL | Missing Audit Trail | State transition missing audit record entry. |
| `RULE_AUDIT_02` | AUDIT | CRITICAL | Broken Hash Chain | SHA-256 hash mismatch in audit ledger chain. |
| `RULE_NOTIF_01` | NOTIFICATION | HIGH | Notification Delivery Failure | Alert failed delivery across all notification gateways. |
| `RULE_NOTIF_02` | NOTIFICATION | MEDIUM | Excessive Reminder Retries | Escalating reminder retries exceeded threshold. |
| `RULE_ESCAL_01` | ESCALATION | HIGH | SLA Breach | Task or approval remained unacted past SLA limit. |
| `RULE_EVID_01` | EVIDENCE | CRITICAL | Unauthorized Evidence View | Classified evidence accessed by unassigned officer. |
| `RULE_EVID_02` | EVIDENCE | CRITICAL | Unauthorized Evidence Export | Case payload exported without authorization clearance. |
| `RULE_AUTH_02` | AUTHENTICATION| HIGH | Multiple Failed Logins | Excessive invalid login attempts for officer account. |
| `RULE_AUTH_03` | AUTHORIZATION | CRITICAL | Privilege Escalation Attempt| REST endpoint requested exceeding JWT role claims. |
| `RULE_APPROV_05` | APPROVAL | HIGH | Concurrent Conflicting Approvals| Simultaneous conflicting approval states recorded. |
| `RULE_GOV_02` | INVESTIGATION | HIGH | Missing Supervisor Review | Case closed without supervisor review sign-off. |
| `RULE_SYS_01` | OPERATIONAL | LOW | Policy Version Mismatch | Action evaluated against non-current policy version. |
