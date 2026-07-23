# SLA Health Monitoring Specification (Phase 8.3 Milestone 1)

## SLA Risk Categories

`SLAMonitorService` categorizes open investigation tasks into 4 risk bands:

1. **GREEN**: `remaining_sla_seconds >= 8 hours` (>50% SLA remaining). Task progressing normally.
2. **YELLOW**: `2 hours <= remaining_sla_seconds < 8 hours` (20%-50% SLA remaining). Elevated risk; monitor closely.
3. **RED**: `0 < remaining_sla_seconds < 2 hours` (<20% SLA remaining). High risk; prioritize immediately.
4. **CRITICAL**: `remaining_sla_seconds < 0` (Breached). Immediate escalation required to ACP.

## Recommended Action Generator

The service deterministically outputs human-readable operational advice for each SLA alert (e.g. "IMMEDIATE ESCALATION: Task breached by 3.2h. Reassign or escalate to ACP.").
