# Command Center Aggregation & Caching Architecture (Phase 8.3 Milestone 1)

## Aggregation Strategy

The `CommandCenterAggregator` unifies data from 7 independent domain services into a single payload without modifying underlying models:

1. **Active Investigations**: Computes workload weights, progress %, assignment age hours, and remaining SLA.
2. **Analyst Workloads**: Evaluates weighted workload, capacity %, burnout score (0–100), risk band, and skills.
3. **Approval Queue**: Extracts pending supervisor decisions and ACP/DCP escalations.
4. **SLA Alerts**: Evaluates GREEN, YELLOW, RED, and CRITICAL SLA categories with recommended actions.
5. **Intelligence Feed**: Consumes Phase 7 analytical outputs and links to `ExplainabilityCard`.
6. **Rule-Based Alerts**: Evaluates deterministic operational alert rules.
7. **Operational Metrics**: Aggregates fleet-wide counts, average workloads, and assignment delays.

## In-Memory Caching

`DashboardAggregationService` implements thread-safe caching:
- **TTL**: 30 seconds
- **Invalidation**: Cleared automatically on `ASSIGNMENT_CREATED`, `ASSIGNMENT_REASSIGNED`, `TASK_COMPLETED`, `ASSIGNMENT_ESCALATED`, `ASSIGNMENT_APPROVED`, or `INTELLIGENCE_DISCOVERED` events.
