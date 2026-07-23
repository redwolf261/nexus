# Approval Policy Engine Specification

## Overview
The `ApprovalPolicyEngine` (`backend/approval/policy_engine.py`) enforces governance policies, role capability hierarchies, segregation of duties, and operational constraints across all 10 approval request types in NEXUS.

## Core Governance Rules

### 1. Segregation of Duties
- The requester of an approval request **cannot** approve or reject their own request.
- Attempting self-approval returns `ApprovalPolicyViolationError`.

### 2. Role Tier Requirements
- **Search Warrant**: Requires `supervisor` role or higher.
- **Arrest Warrant**: Multi-stage approval requiring `supervisor` for initial review and `acp` for final sign-off.
- **Cross-District Investigation**: Requires `acp` role or higher and target district metadata.
- **Budget/Resource Request**: Requests $\le 500,000 \text{ INR}$ require `acp`; requests $> 500,000 \text{ INR}$ require `dcp` sign-off.
- **Emergency Operational Approval**: Requires `supervisor` or higher with mandatory emergency justification metadata. Automatically expires after 24 hours.

### 3. Policy Validation API
The policy engine exposes:
- `validate_request_creation(...)`: Evaluates metadata and requester role prior to request submission.
- `validate_action(...)`: Evaluates role capability and segregation of duties prior to decision execution.
- Returns `PolicyValidationResult(valid, violations, warnings)`.
