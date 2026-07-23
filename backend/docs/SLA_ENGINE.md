# SLA Timer Engine Architecture

## Overview
The `SLAEngine` (`backend/approval/sla_engine.py`) evaluates approval deadlines, reminder thresholds, escalation deadlines, and expiration bounds deterministically without background scheduler assumptions.

## SLA Evaluation Formulas

Given creation timestamp $T_{created}$, reference evaluation timestamp $T_{ref}$, and SLA duration $H_{sla}$:

$$\text{Elapsed Seconds } (S_{elapsed}) = T_{ref} - T_{created}$$
$$\text{Total SLA Seconds } (S_{total}) = H_{sla} \times 3600$$
$$\text{Ratio } (R) = \frac{S_{elapsed}}{S_{total}}$$

### Deterministic Thresholds:
- **SLA Warning**: Triggered when $R \ge 0.70$ (`SLA_WARNING`)
- **Escalation Due**: Triggered when $R \ge 0.85$ (`TRIGGER_AUTOMATIC_ESCALATION`)
- **SLA Breached**: Triggered when $R \ge 1.00$ (`SLA_BREACHED`)
- **Expiry Due**: Triggered when $R \ge 1.20$ or past `expires_at` (`EXPIRE_REQUEST`)

## Performance Guarantees
- SLA evaluation latency: $<10 \text{ ms}$
