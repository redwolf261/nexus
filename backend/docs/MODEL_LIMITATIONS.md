# Model Limitations Report
**Phase 7.2 Independent Scientific Audit**

This document catalogues the known scientific limits of the Analytical Engine. Investigators must be trained on these limitations before using the system in court.

## 1. Graph Analytics
- **Unweighted Edges:** The Neo4j Cypher algorithms currently treat all relationships as unweighted. A phone call lasting 5 seconds is treated structurally identical to a shared arrest for murder.
- **Limitation:** Centrality metrics represent *structural* position, not *severity*. The most central node might simply be a low-level drug dealer who interacts with many distinct crews, rather than the cartel boss who maintains strict operational security (low degree).

## 2. Temporal Analytics
- **Granularity Limit:** The CUSUM engine operates on a Daily frequency.
- **Limitation:** It is impossible to detect intra-day anomalies (e.g. "Crime spiked sharply between 2 AM and 4 AM today"). The minimum detection window is 24 hours.
- **Seasonality Blindness:** The engine uses 30-day rolling averages. It has no concept of "Year-over-Year" seasonality (e.g., crime always spikes during Diwali). These predictable seasonal spikes will trigger false alarms.

## 3. Crime Series Detection
- **Curse of Dimensionality:** The DBSCAN engine attempts to cluster points in a 10-dimensional space using Euclidean distance.
- **Limitation:** In high-dimensional space, Euclidean distance loses meaning (all points appear roughly equidistant). Because categorical features (Day of Week, Crime Type) are One-Hot Encoded, they artificially expand the dimensionality, making dense numerical clusters harder to isolate.

## 4. Entity Resolution
- **Homophily Bias:** "Shared Associates" is used as a dimension to link two records.
- **Limitation:** If two distinct individuals share the exact same name and live in the exact same gang-controlled neighborhood, they likely share the same associates. The engine will merge them with high confidence, stripping the identity of the innocent party.

## Operational Recommendations for Investigators
1. **Never arrest based on Graph Centrality.** It is a lead generation tool, not evidentiary proof.
2. **Review merged entities carefully.** If a citizen complains their criminal record contains someone else's FIRs, an investigator must be able to manually decouple the entities.
3. **Ignore CUSUM alerts during known festivals.**
