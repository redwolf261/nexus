# Deterministic Heatmap Engine Specification (Phase 8.3 Milestone 4)

## Overview

`HeatmapEngine` generates district matrix heatmaps for operational monitoring.

## Heatmap Categories

1. `RISK`: Overall operational risk index per district.
2. `BACKLOG`: Case and task backlog density.
3. `APPROVAL_DELAY`: Supervisor override and escalation approval delays.
4. `BURNOUT`: Investigator workload and fatigue risk.
5. `SLA`: SLA breach probability and time remaining.

## Risk Band Classification

- `LOW`: Score 0.0 – 24.9
- `MEDIUM`: Score 25.0 – 49.9
- `HIGH`: Score 50.0 – 74.9
- `CRITICAL`: Score 75.0 – 100.0
