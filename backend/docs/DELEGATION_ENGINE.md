# Delegation Engine Architecture

## Overview
The `DelegationEngine` (`backend/approval/delegation_engine.py`) provides temporary command authority delegation for officers and supervisors during absences, leave, or emergency operations without modifying base role definitions.

## Delegation Types
- `TEMPORARY_ACTING`: Acting supervisor assignment during shift overlaps.
- `LEAVE_DELEGATION`: Delegated authority during official leave.
- `EMERGENCY_DELEGATION`: Emergency operational delegation.
- `VACATION_DELEGATION`: Delegated authority during scheduled vacation.

## Key Properties
- **No Role Mutation**: User base roles in DB (`User.role`) are untouched.
- **Time Bounds**: Every delegation requires explicit `start_time` and `end_time`.
- **Audit Traceability**: Actions taken under delegation log both the acting `delegatee_id` and the `delegator_id` for complete legal attribution.
- **Performance SLA**: Delegation lookup latency $<5 \text{ ms}$.
