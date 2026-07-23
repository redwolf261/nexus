# Override Policy Engine Specification (Phase 8.2 Milestone 5)

## Overview

The `OverridePolicyEngine` performs deterministic rule evaluation when a supervisor chooses to override candidate recommendations or assign an officer.

## Rules & Escalation Matrix

| Policy Rule | Condition | Policy Outcome | Required Escalation |
|-------------|-----------|----------------|---------------------|
| `CAPACITY_NORMAL` | `capacity_used < 1.0` | Passed | Supervisor |
| `CAPACITY_OVERLOAD` | `capacity_used >= 1.0` | Warning | Supervisor |
| `CRITICAL_CAPACITY` | `capacity_used >= 1.5` | Violation | **ACP Required** |
| `STATUS_ON_DUTY` | `availability_status == "ON_DUTY"` | Passed | Supervisor |
| `STATUS_LEAVE` | `availability_status == "LEAVE"` | Warning | **ACP Required** |
| `STATUS_UNAVAILABLE` | `availability_status` in (`OFF_DUTY`, `TRAINING`) | Warning | **ACP Required** |
| `STATUS_SUSPENDED` | `availability_status == "SUSPENDED"` | Violation | **DCP Required** |
| `INTERSTATE` | `is_interstate == True` | Violation | **DCP Required** |
| `CRITICAL_CASE_RISK` | `priority == "CRITICAL"` | Warning | **ACP Required** |

## Standardized Override Reasons

- `WORKLOAD_BALANCING`
- `LOCAL_KNOWLEDGE`
- `URGENT_OPERATION`
- `SPECIAL_EXPERTISE`
- `MANUAL_COMMAND`
- `RESOURCE_SHORTAGE`
- `TEMPORARY_ASSIGNMENT`
- `OTHER`
