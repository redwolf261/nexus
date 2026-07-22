# Investigator Workflow Report
**Phase 7.3 Intelligence Quality Audit**

## Objective
Evaluate the human factors of the Analytical Engine. Does the UI generate alert fatigue? Are explanations too technical for police officers?

## 1. Alert Fatigue Analysis
- **Crime Series (DBSCAN `min_samples=2`):** Generates immense alert fatigue. Analysts will learn to completely ignore the "Crime Series" tab if every pair of minor thefts in a district generates a high-priority alert.
- **Temporal Alerts (Seasonality):** Generates moderate alert fatigue. Analysts will dismiss alerts in October/November (Diwali season) as "the usual spike".
- **Graph Metrics (PageRank updates):** Low fatigue. Because these are passively rendered as numbers in the dashboard (rather than aggressive pop-up alerts), they serve as useful context rather than interruptions.

## 2. Explainability Sufficiency (The "Why")
- **Is the explanation too technical?**
  - *Bad:* "DBSCAN clustered these points in 10D space with eps 0.25." (An investigator cannot use this in court).
  - *Current Nexus Implementation:* "Cluster formed due to shared features: 02:00-04:00 AM, Window Entry, Ground Floor." (An investigator CAN use this in court). 
- **Verdict:** The `IntelligenceExplanation` schema successfully shields the analyst from the underlying math while exposing the tangible investigative features that triggered the math.

## 3. Automation Safety Audit

### Safe for Automation
- **Cross-Case Overlaps:** Automatically inserting a timeline event stating "Suspect attached to Case B" is 100% safe and highly useful.
- **Temporal Alerts:** Automatically flagging a district map red during a crime spike is safe and encourages proactive patrols.

### Requires Human Review (Never Automate)
- **Entity Resolution Merges:** The system should NEVER automatically merge two identities. It must propose the merge for manual approval.
- **Link Prediction Arrest Recommendations:** Predicting that A knows B is a lead, not probable cause. Generating an automated "Arrest B" recommendation based on Link Prediction is legally dangerous.

## 4. Confidence Displays
- **Misleading Display:** Rendering 63% confidence in the UI. To an investigator, a 63% grade is a "D" (Failure). In the Geometric Mean model, 63% is actually a strong indicator of a True Positive. 
- **Recommendation:** The UI should abstract numerical confidence into categorical bands: `[LOW, MEDIUM, HIGH, CRITICAL]` to avoid misinterpretation of the underlying math.
