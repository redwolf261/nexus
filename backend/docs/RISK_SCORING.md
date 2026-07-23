# Deterministic Operational Risk Scoring Specification

## Mathematical Formula

Each subsystem category raw score is computed by accumulating severity point weights for active unresolved violations:
$$\text{RawScore}(C) = \sum_{v \in \text{Violations}(C)} \text{SeverityWeight}(v.\text{severity})$$

Where:
- $\text{SeverityWeight}(\text{CRITICAL}) = 25.0$
- $\text{SeverityWeight}(\text{HIGH}) = 15.0$
- $\text{SeverityWeight}(\text{MEDIUM}) = 8.0$
- $\text{SeverityWeight}(\text{LOW}) = 3.0$

Subsystem score capped at 100:
$$\text{SubsystemScore}(C) = \min(100.0, \text{RawScore}(C))$$

Overall Operational Risk Score:
$$\text{OverallRiskScore} = \sum_{C} w_C \times \text{SubsystemScore}(C)$$

Where subsystem weights $w_C$:
- `AUTHENTICATION`: 0.15
- `ASSIGNMENT`: 0.15
- `GOVERNANCE`: 0.15
- `APPROVAL`: 0.15
- `EVIDENCE`: 0.15
- `NOTIFICATIONS`: 0.10
- `AUDIT`: 0.10
- `OPERATIONAL`: 0.05

## Risk Bands
- **`LOW`**: $0 \le \text{Score} \le 25$
- **`MODERATE`**: $25 < \text{Score} \le 50$
- **`HIGH`**: $50 < \text{Score} \le 75$
- **`CRITICAL`**: $\text{Score} > 75$
