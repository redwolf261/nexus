# Confidence Calibration Report
**Phase 7.1 Analytical Intelligence**

## Objective
Verify that the `ConfidenceScore` engine provides a calibrated probability of correctness, avoiding opaque scores and preventing a single weak data point from generating high-confidence assertions.

---

## 1. Distribution & Thresholds
The `ConfidenceScore` uses a weighted geometric mean across 5 dimensions:
- Evidence Quality (weight: 0.25)
- Data Completeness (weight: 0.20)
- Algorithm Confidence (weight: 0.30)
- Source Reliability (weight: 0.15)
- Recency Weight (weight: 0.10)

### Sensitivity Analysis
- **All components = 1.0** -> Overall = 1.0 (100%)
- **One component = 0.5** (e.g. data 180 days old) -> Overall = ~0.93 (High)
- **One component = 0.1** (e.g. terrible data completeness) -> Overall = ~0.63 (Medium)
- **One component = 0.01** (e.g. no evidence quality) -> Overall = ~0.31 (Low)

Because we use a geometric mean, a single zero-confidence dimension pulls the entire score down heavily. This is the desired behavior for a law enforcement intelligence platform (conservative assertions).

### Recommended Action Thresholds
- **> 0.85 (High Confidence):** Render prominently in Investigation Workspace. Safe for automated alerts (e.g., Timeline insertions).
- **0.50 - 0.85 (Medium Confidence):** Render in Intelligence Panels as secondary insights. Requires manual investigator verification.
- **< 0.50 (Low Confidence):** Filter out or place in deep drill-down views. Do not push to top-level dashboards.

---

## 2. Temporal Decay (Recency Calibration)
Recency uses an exponential decay function: `Score = 0.5^(days_old / 180)`
- Day 0 = 1.0
- Day 90 = 0.707
- Day 180 = 0.50
- Day 365 = 0.24

This naturally lowers the confidence of intelligence derived from decades-old data, prompting the investigator to seek fresh corroborating evidence.

---

## 3. High Confidence False Positives (HCFP)
**Risk:** The algorithm is >90% confident, but wrong.
**Calibration adjustment:** In Entity Resolution, even if Jaro-Winkler name match is 1.0, the overall score is gated by `MATCH_THRESHOLD=0.40`. If only the name matches (and no geography/phone/Aadhaar/associates match), the weighted sum is `0.15` and the match is discarded entirely before confidence is even calculated.

## 4. Low Confidence True Positives (LCTP)
**Risk:** The algorithm is right, but confidence is <30%.
**Calibration adjustment:** Spatial and Temporal analytics are highly sensitive to data completeness. If FIRs lack exact timestamps or coordinates, confidence drops significantly. This correctly reflects the uncertainty of the data, even if the underlying analytical pattern is real.
