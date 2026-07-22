# Threshold Sensitivity Analysis
**Phase 7.3 Intelligence Quality Audit**

## Objective
Identify tipping points where minor threshold adjustments cause catastrophic failure (either infinite false positives or total silence) in the analytical modules.

## 1. Entity Resolution (MATCH_THRESHOLD)
- **Current Base:** `0.40`
- **Variations:**
  - `0.30`: Catastrophic Failure. The engine begins merging every person with the same surname in the same state, collapsing the criminal database into massive "super-entities". Precision drops to <10%.
  - `0.40`: Stable. Misses aliases unless supported by exact IDs or strong associates.
  - `0.60`: Overly Restrictive. Jaro-Winkler penalizes names too harshly. "Muhammad" vs "Mohammad" fails. Recall drops to <30%.
- **Verdict:** `0.40` is the mathematical sweet spot, but relies heavily on the Confidence Engine to warn the user when a 0.45 score is produced.

## 2. Crime Series (DBSCAN `eps` and `min_samples`)
- **Epsilon (`eps`):** (Current: `0.25`)
  - `0.10`: Total Silence. The feature space requires identical matches across time, location, and MO. Finds almost zero series.
  - `0.25`: Stable. Groups tight temporal/spatial bounds.
  - `0.40`: Catastrophic Failure. The radius is so large it groups all thefts in a district into a single "Mega-Series", rendering the intelligence useless.
- **Min Samples (`min_samples`):** (Current: `2`)
  - `2`: **High Risk.** Any two vaguely similar crimes form a series. Produces massive alert fatigue on the dashboard.
  - `3`: **Recommended.** Dramatically filters out coincidental noise.
  - `5`: Under-sensitive. Misses emerging serial offenders until it is too late.

## 3. Temporal Analytics (CUSUM `h` - Control Limit)
- **Current Base:** `4.0` (4 standard deviations from mean)
- **Variations:**
  - `2.0`: Catastrophic Alert Fatigue. Alerts trigger every weekend due to natural spikes in reporting.
  - `4.0`: Stable. Only flags extreme anomalies (e.g., riots, sudden gang wars, coordinated vehicle thefts).
  - `6.0`: Total Silence. Will miss everything short of a catastrophic event.
