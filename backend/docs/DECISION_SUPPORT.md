# Deterministic Decision Support Engine Specification (Phase 8.3 Milestone 3)

## Overview

`DecisionSupportEngine` evaluates 8 strict deterministic operational rules to generate explainable recommendations for supervisors without AI/ML.

## Evaluated Rules

1. `UNASSIGNED_CRITICAL`: CRITICAL priority investigation has no assigned officer.
2. `SLA_NEAR_BREACH`: Investigation age exceeds 80% of SLA limit.
3. `ANALYST_OVERLOAD`: Assigned investigator capacity utilization >= 100%.
4. `BLOCKED_TASK_DELAYS`: Active tasks blocked by uncompleted dependencies.
5. `EVIDENCE_MISSING`: High-priority investigation without physical/digital evidence.
6. `APPROVAL_BACKLOG`: Pending escalation approval > 4 hours.
7. `HIGH_RISK_SERIES`: Case linked to high-density spatial hotspot or crime series.
8. `FRESH_INTEL_DISCOVERY`: Unreviewed Phase 7 intelligence alert linked to case.
