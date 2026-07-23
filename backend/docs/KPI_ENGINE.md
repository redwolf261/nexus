# Deterministic KPI Engine Specification (Phase 8.3 Milestone 4)

## Overview

`KPIEngine` computes deterministic Key Performance Indicators across 5 core operational domains:

1. **Investigation KPIs**: Active count, closed count, avg duration, median duration, SLA compliance %, SLA breach count, backlog.
2. **Task KPIs**: Tasks created, tasks completed, completion rate %, blocked tasks, avg completion time.
3. **Assignment KPIs**: Avg workload, Workload Gini Coefficient ($G = \frac{\sum_{i=1}^n \sum_{j=1}^n |x_i - x_j|}{2n^2 \bar{x}}$), capacity utilization %, turnaround.
4. **Approval KPIs**: Pending approvals, avg approval delay hours, escalation rate %.
5. **Evidence KPIs**: Outstanding evidence requests, avg response time, external SLA breaches.

## Workload Gini Coefficient Formula

The Workload Gini Coefficient quantifies workload balance equality:
- `0.0`: Perfect equality (all officers carry identical case counts).
- `1.0`: Maximum inequality.
- Target threshold: `< 0.3`.
