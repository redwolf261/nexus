# Approval Service Architecture

## Overview
The `ApprovalService` (`backend/approval/approval_service.py`) is the primary domain orchestrator for the NEXUS Approval & Governance System.

## Architecture & Components
- **Repository Integration**: Interacts with `ApprovalRepository` supporting optimistic concurrency locking via an integer `version` field.
- **Workflow & Policy Engines**: Delegates state transition checks to `ApprovalWorkflowEngine` and governance rules to `ApprovalPolicyEngine`.
- **WebSocket Event Dispatching**: Emits real-time WebSocket events (`APPROVAL_SUBMITTED`, `APPROVAL_APPROVED`, `APPROVAL_REJECTED`, etc.) via `EventDispatcher`.
- **Immutable Audit Logging**: Records an immutable audit log entry in `ApprovalHistory` for every lifecycle event.

## Core Operations & SLA Benchmarks
- `submit_request()`: Latency $<40 \text{ ms}$
- `approve()`, `reject()`, `return_for_revision()`, `escalate()`, `cancel()`: Latency $<25 \text{ ms}$
- `history()`: Latency $<20 \text{ ms}$
- `validate()`: Latency $<10 \text{ ms}$
- `get_pending()`, `get_my_actions()`: Latency $<50 \text{ ms}$
