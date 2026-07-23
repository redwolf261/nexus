# Escalation Engine Architecture

## Overview
The `EscalationEngine` (`backend/approval/escalation.py` & `escalation_service.py`) provides operational continuity for the NEXUS platform, ensuring that approval requests never silently stall or expire unnoticed.

## Authority Tiers & Escalation Chains
The system implements a 4-tier command authority hierarchy:
1. **Supervisor**: Field / Precinct Operational Leader
2. **ACP** (Assistant Commissioner of Police): District / Division Leader
3. **DCP** (Deputy Commissioner of Police): Regional Executive
4. **Commissioner**: Highest Operational Authority

## Escalation Triggers & Reasons
- `SLA_TIMEOUT`: Triggered automatically when SLA ratio exceeds 85% without resolution.
- `OFFICER_UNAVAILABLE`: Triggered when assigned officer is marked unavailable.
- `SUPERVISOR_UNAVAILABLE`: Triggered when supervisor is absent without active delegation.
- `MANUAL_ESCALATION`: Manually requested by analyst or supervisor.
- `EMERGENCY`: Emergency bypass routing directly to ACP/DCP.
- `JURISDICTION_CONFLICT`: Cross-district boundary conflict.
- `POLICY_VIOLATION`: Security or governance rule violation.

## Performance Benchmarks
- Escalation evaluation latency: $<10 \text{ ms}$
- Pending escalations lookup: $<30 \text{ ms}$
- Escalation history query: $<20 \text{ ms}$
