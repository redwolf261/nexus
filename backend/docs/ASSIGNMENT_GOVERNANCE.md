# Assignment Governance Architecture (Phase 8.2 Milestone 5)

## Overview

The Assignment Governance framework implements the human decision layer governing investigation assignment.
While analytical engines (M1–M4) measure officer capacity, rank candidates, and compute workload, the **Assignment Governance Service** enforces human authorization, justification tracking, deterministic override validation, multi-level escalation sign-offs, and legal reproducibility.

```
┌────────────────────────────────────────────────────────┐
│               Supervisor / ACP / DCP                   │
└───────────────────────────┬────────────────────────────┘
                            │ (ACCEPT / OVERRIDE / REJECT / DEFER)
                            ▼
┌────────────────────────────────────────────────────────┐
│             Assignment Governance Service              │
│  - Enforces mandatory 50+ char override justification  │
│  - Executes deterministic policy validation            │
│  - Manages multi-level escalation queue (ACP/DCP)     │
└─────────────┬──────────────────────────┬───────────────┘
              │                          │
              ▼                          ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│  Recommendation Snapshot │   │ Decision Audit History   │
│  (100% Reproducibility)  │   │  (Append-Only Log)       │
└──────────────────────────┘   └──────────────────────────┘
```

## Guiding Principles

1. **Zero AI / ML / Randomness**: All decision workflows, policy gates, and escalation tiers are 100% deterministic.
2. **Supervisor Authority**: No automatic assignment. Human authorization is mandatory.
3. **Mandatory Audit Justification**: Overrides require standardized reason selection and a minimum of 50 characters of detailed free-text justification.
4. **Persisted Recommendation Snapshots**: Every decision captures the byte-exact candidate rankings, scores, and policy context for legal audit and Phase 10 explainability.
5. **Optimistic Locking**: Prevents concurrent supervisor race conditions.
