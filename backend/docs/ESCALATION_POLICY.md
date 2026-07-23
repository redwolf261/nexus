# Escalation Policy Specification

## Overview
The `EscalationPolicyEngine` (`backend/approval/escalation_policy.py`) evaluates rules for escalation routing, authority tier transitions, and emergency overrides.

## Escalation Policy Rules

### 1. Authority Tier Progression Rule
Standard escalations progress linearly up the command chain:
$$\text{Supervisor} \longrightarrow \text{ACP} \longrightarrow \text{DCP} \longrightarrow \text{Commissioner}$$

### 2. Emergency Operational Bypass Rule
Emergency approval requests or escalations triggered with reason `EMERGENCY` bypass intermediate supervisor levels and route directly to the `ACP` or `DCP` tier.

### 3. Max Depth Limit Rule
Escalations reaching `Commissioner` (Tier 4) are marked with `MAX_ESCALATION_REACHED` to prevent out-of-bounds array overflows while maintaining active alert status.

### 4. Segregation of Duties & Authorization
Escalation actions (acknowledge, resolve, reassign) must be performed by a user holding the assigned role level or higher, or explicitly assigned user ID.
