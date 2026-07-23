# Multi-Level Approval Escalation Workflow (Phase 8.2 Milestone 5)

## Overview

When an override triggers policy thresholds (e.g. officer on leave, critical workload >=150%, interstate investigation, or suspended officer), the Assignment Governance Service automatically routes the decision to the **Command Center Escalation Queue**.

```
  Supervisor Submits Override
               │
               ▼
   [Policy Check Engine]
       │             │
       │ Normal      │ Policy Threshold Exceeded
       ▼             ▼
Auto-Approved   Create Escalation (PENDING_ACP / PENDING_DCP)
                     │
                     ▼
             Executive Sign-Off (ACP / DCP)
                     │
                     ▼
             Executed & Audited
```

## Approval Tiers & RBAC

- **Supervisor**: Can accept, override standard cases, reject, or defer.
- **ACP (Assistant Commissioner of Police)**: Can approve ACP-tier escalations (critical capacity, officers on leave/off-duty, critical priority cases).
- **DCP (Deputy Commissioner of Police)**: Can approve DCP-tier escalations (interstate cases, suspended officers).
- **Admin**: Executive override authority for all escalation tiers.
