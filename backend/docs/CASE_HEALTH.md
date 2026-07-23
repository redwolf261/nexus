# Operational Case Health Engine Specification (Phase 8.3 Milestone 3)

## Overview

`CaseHealthEngine` computes a 0–100 operational case health score based on 6 weighted factors:

1. **SLA Utilization** (25%)
2. **Evidence Completeness** (20%)
3. **Task Completion Ratio** (20%)
4. **Assignment Stability** (15%)
5. **Analytical Confidence** (10%)
6. **Approval Backlog Penalty** (10%)

## Categories

- `HEALTHY`: Score 80.0 – 100.0
- `MONITOR`: Score 60.0 – 79.9
- `ATTENTION`: Score 40.0 – 59.9
- `CRITICAL`: Score 0.0 – 39.9
