# Multi-Period Trend Analysis Engine Specification (Phase 8.3 Milestone 4)

## Overview

`TrendAnalysisEngine` calculates deterministic historical moving averages and period-over-period statistics without machine learning.

## Metrics & Periods

- **7-Day Moving Average**: Active cases and task completion rates.
- **30-Day Moving Average**: SLA compliance and district health.
- **Week-over-Week (WoW)**: Workload variations and officer utilization.
- **Month-over-Month (MoM)**: Approval delays and pending escalations.

## Direction Classification

- `UP`: Growth > +1.0%
- `DOWN`: Decline < -1.0%
- `STABLE`: Change within [-1.0%, +1.0%]
