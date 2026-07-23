# Approval Workflow Templates Specification

## Overview
`ApprovalTemplates` (`backend/approval/approval_templates.py`) defines canonical workflow stage pipelines for all 10 approval request types in NEXUS.

## Workflow Templates Matrix

| Approval Type | Stage Count | Required Roles per Stage | Min Approvers | Default Expiry |
|---|---|---|---|---|
| `SEARCH_WARRANT` | 1 | Stage 1: Supervisor | 1 | 7 Days |
| `ARREST_WARRANT` | 2 | Stage 1: Supervisor, Stage 2: ACP | 1 | 7 Days |
| `EVIDENCE_COLLECTION` | 1 | Stage 1: Supervisor | 1 | 30 Days |
| `SURVEILLANCE_REQUEST` | 2 | Stage 1: Supervisor, Stage 2: ACP | 1 | 14 Days |
| `INVESTIGATION_CLOSURE` | 2 | Stage 1: Supervisor, Stage 2: ACP | 1 | 30 Days |
| `COLD_CASE_ARCHIVAL` | 1 | Stage 1: Supervisor | 1 | 30 Days |
| `CASE_REOPENING` | 1 | Stage 1: ACP | 1 | 30 Days |
| `CROSS_DISTRICT_INVESTIGATION` | 1 | Stage 1: ACP | 1 | 30 Days |
| `BUDGET_RESOURCE_REQUEST` | 1 or 2 | $\le 500k$: ACP; $> 500k$: Stage 1 ACP, Stage 2 DCP | 1 | 30 Days |
| `EMERGENCY_OPERATIONAL_APPROVAL` | 1 | Stage 1: Supervisor | 1 | 24 Hours |
