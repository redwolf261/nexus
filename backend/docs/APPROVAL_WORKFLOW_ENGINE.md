# Approval Workflow Engine Architecture

## Overview
The `ApprovalWorkflowEngine` (`backend/approval/workflow_engine.py`) provides deterministic state machine management, sequential and parallel approval stage transitions, automatic timeout and expiration enforcement, and escalation processing for the NEXUS Approval & Governance System.

## Key Principles
1. **Deterministic State Machine**: Every state transition (`DRAFT -> SUBMITTED -> UNDER_REVIEW -> APPROVED / REJECTED / RETURNED / ESCALATED / EXPIRED / CANCELLED`) is explicitly validated against `ALLOWED_TRANSITIONS`. Unauthorized or out-of-order jumps are rejected with `InvalidApprovalStateError`.
2. **Stage Progression**: Workflows consist of 1 or more ordered `ApprovalStage` objects. A stage requires a minimum number of approver signatures (`min_approvers`) belonging to a specified role level before advancing to the next stage.
3. **No Skipped Stages**: Workflows must satisfy stage $N$ before stage $N+1$ becomes active (`IN_PROGRESS`).
4. **Timeouts & Auto-Expiry**: The workflow engine checks expiration bounds (`expires_at`) on every state transition and backgrounds job runs.

## Supported States
- `DRAFT`: Request created but not yet submitted for review.
- `SUBMITTED`: Request submitted by requester.
- `UNDER_REVIEW`: Active stage in progress awaiting approver decision.
- `APPROVED`: Terminal state when all stages satisfy minimum approver signatures.
- `REJECTED`: Terminal state when an approver rejects the request.
- `RETURNED`: Non-terminal state when returned for requester revision.
- `ESCALATED`: Non-terminal state when escalated to higher authority tier.
- `EXPIRED`: Terminal state when approval timeout bound is exceeded.
- `CANCELLED`: Terminal state when requester or administrator cancels request.

## Performance Guarantees
- Stage progression validation: $<10 \text{ ms}$
- Expiration check: $<5 \text{ ms}$
