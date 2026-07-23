# Operational Remediation Guide

This guide details mandatory corrective actions for compliance officers upon detection of policy violations.

## Remediation Workflow
1. Identify violation via `/api/compliance/violations` or the Compliance Dashboard.
2. Review explanation, violated entity, and evidence snapshot.
3. Execute required remediation steps specified by the rule:
   - **`RULE_AUTH_01`**: Reassign task to authorized officer with required rank.
   - **`RULE_APPROV_01`**: Invalidate signoff and route to District Commissioner.
   - **`RULE_GOV_01`**: Attach formal override rationale.
   - **`RULE_AUDIT_02`**: Quarantine sequence and initiate forensic audit.
4. Mark violation resolved via remediation panel or API endpoint.
