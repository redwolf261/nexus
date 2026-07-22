# Cross-Module Consistency Matrix
**Phase 7.3 Intelligence Quality Audit**

## Objective
Verify that the output of one analytical module does not logically contradict the output of another when presented to the investigator on the same dashboard.

## Consistency Matrix

| Module A | Module B | Consistency Status | Description / Contradiction |
|----------|----------|--------------------|-----------------------------|
| Entity Resolution | Graph Analytics | **CONTRADICTS** | ER merges Person A and B. However, Graph Analytics computes PageRank based on raw Neo4j nodes (which still treat A and B as distinct). Result: The UI shows them as one person, but the Graph Metrics panel shows two different PageRanks for their distinct IDs. |
| Entity Resolution | Crime Series | **CONSISTENT** | ER merges identities. Crime Series clusters FIRs based on MO/Location, totally agnostic to the offender's identity. No conflict. |
| Temporal Analytics | Spatial Analytics | **CONSISTENT** | Temporal flags a time spike; Spatial flags a location cluster. If both overlap, it correctly reinforces a localized riot or gang war. |
| Graph Analytics | Link Prediction | **CONSISTENT** | Link prediction recommends connecting two disparate subgraphs. If accepted, it alters the Graph Analytics (PageRank shifts), which is an expected feedback loop. |
| Recommendation Engine | Entity Resolution | **CONTRADICTS** | The Recommendation Engine might suggest "Arrest Person B" based on a high Risk Score, even though Entity Resolution just flagged that "Person B is likely an alias of Person A (already in custody)". The engine lacks a mechanism to suppress recommendations for merged aliases. |

## Conclusion
The most severe inconsistencies stem from **Entity Resolution**. Because ER is probabilistic (generating an alert) rather than deterministic (actually executing a SQL `MERGE` on the database), the rest of the analytical engine continues to operate on the un-merged, dirty data. 

**Recommendation for Phase 8:** Entity Resolution alerts must feature an "Approve Merge" button that structurally mutates the PostgreSQL and Neo4j databases, forcing Graph and Recommendation modules to update their state.
