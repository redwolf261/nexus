# The NEXUS Analytical Intelligence Engine
**Phase 7.1 Architecture Guide**

## Core Philosophy
The Analytical Intelligence Engine shifts NEXUS from a passive data repository (CRUD) to a proactive intelligence platform. It is governed by three strict rules:
1. **No Black Boxes:** Every inference must be traceable to raw evidence via a standardized provenance chain.
2. **Determinism:** Algorithms must produce identical outputs given identical DB states. (No generative LLMs).
3. **Calibrated Confidence:** Every assertion carries a geometric-mean confidence score penalized by data age and incompleteness.

## The 6 Modules

### 1. Entity Resolution
**Goal:** Deduplicate records and discover aliases across jurisdictions.
**Engine:** Weighted multi-dimensional evidence aggregation.
**Key Features:** Jaro-Winkler transliteration-tolerant string matching, Haversine geospatial proximity, temporal career overlaps.

### 2. Crime Series Detection
**Goal:** Identify recurring criminal campaigns.
**Engine:** SciKit-Learn DBSCAN.
**Key Features:** Feature vectors encompassing crime type, hour of day, day of week, geography, and Modus Operandi. Generates an `emerging_trend_score` to prioritize active series.

### 3. Graph Analytics
**Goal:** Measure the structural importance of individuals within criminal networks.
**Engine:** Pure Cypher queries against Neo4j.
**Key Features:** PageRank (influence), Betweenness Centrality (brokers/middlemen), Community Detection (gang substructures), and Jaccard Link Prediction (discovering unknown associates).

### 4. Temporal Analytics
**Goal:** Detect statistically significant shifts in crime frequency.
**Engine:** Pandas + SciPy.
**Key Features:** CUSUM changepoint detection for crime spikes, and Coordinated Event burst detection (e.g. 5 FIRs in 12 hours). Offender schedule profiling (preferred days/months).

### 5. Spatial Analytics
**Goal:** Move beyond basic heatmaps into actionable geography.
**Engine:** DBSCAN (Haversine metric).
**Key Features:** Spatial hotspot clustering, travel corridor inference (linking sequential FIR locations to find escape routes), and inter-district transition matrices.

### 6. Explainability & Confidence Framework
**Goal:** Ensure Analyst Trust.
**Engine:** `ConfidenceScore` and `IntelligenceExplanation` models.
**Key Features:** Every API endpoint in the engine returns this schema. The frontend parses these explanations to render detailed, clickable provenance chains for every alert.

## Integration Architecture
Intelligence does not exist in a vacuum. It is injected directly into the analyst workflow:
1. **Live Workspace Hydration:** `InvestigationsService` automatically queries the Intelligence Engine when a workspace is loaded, attaching Series, Graph, and Temporal data to the payload.
2. **Event Bus:** As background workers run batch analytics, discoveries are published to the `INTELLIGENCE_DISCOVERED` event topic and pushed via WebSockets to live clients.
3. **Frontend Caching:** Redux / React-Query merges intelligence alerts seamlessly into the UI without full page reloads.
