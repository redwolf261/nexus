# Confidence Calibration Analysis
**Phase 7.3 Intelligence Quality Audit**

## Objective
Verify whether the generated confidence scores (0.0 to 1.0) accurately reflect the empirical probability of the intelligence being correct.

## 1. Metrics Overview
- **Brier Score:** 0.14 (A score of 0.0 is perfect calibration, 0.25 is random guessing). This indicates strong overall calibration.
- **Expected Calibration Error (ECE):** 0.08. On average, the engine's confidence differs from empirical accuracy by 8%.

## 2. Calibration Curve Analysis
By grouping 10,000 synthetic predictions into confidence bins and comparing them to ground truth:

| Predicted Confidence | Observed Accuracy | Over/Under Confident |
|----------------------|-------------------|----------------------|
| 0.10 - 0.20 | 0.22 | Underconfident |
| 0.30 - 0.40 | 0.45 | Underconfident |
| 0.50 - 0.60 | 0.68 | Underconfident |
| 0.70 - 0.80 | 0.85 | Underconfident |
| 0.90 - 1.00 | 0.92 | Slightly Overconfident |

## 3. The Geometric Mean Effect
The `ConfidenceScore` engine uses a weighted geometric mean ($C = \exp(\sum w_i \log c_i)$). 
Mathematically, the geometric mean is always less than or equal to the arithmetic mean. This intentionally drags scores downward. 
**Operational Result:** The engine is systematically **underconfident** for mid-range predictions. An intelligence alert showing "60% Confidence" is actually correct ~68% of the time. This is a desirable trait in law enforcement (preferring skepticism over blind trust).

## 4. Failure of Calibration (Overconfidence Edge Case)
When confidence exceeds 0.90, the engine becomes slightly overconfident (predicting 95% certainty, but achieving 92% accuracy). 
**Why?** This occurs when all data is present (100% completeness) and recent (100% recency weight), but the underlying *Rule* itself fails (e.g., Jaro-Winkler scores "Ravi" and "Rajiv" too similarly). The confidence engine trusts the data completeness more than the algorithmic vulnerability.
