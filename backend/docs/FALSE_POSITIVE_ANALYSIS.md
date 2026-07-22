# False Positive & Adversarial Analysis Report
**Phase 7.2 Independent Scientific Audit**

## Objective
Measure the robustness of the Analytical Engine against adversarial noise, poor data entry, and deliberate criminal obfuscation.

## 1. Entity Resolution (Alias Detection)
### Attack: Alias Injection / Typo Injection
- **Scenario:** A criminal alters their name ("Ravi Kumar" -> "Ravvi Cummarr") to avoid detection.
- **Engine Response:** Jaro-Winkler scores this highly (>0.85) because it prioritizes prefix matches and transpositions.
- **Verdict:** Highly robust against minor phonetic misspellings.
### Attack: Missing Primary Identifiers
- **Scenario:** The FIR omits the Aadhaar and Phone Number.
- **Engine Response:** The engine falls back to Name + Geography + Associates. If the name is generic ("John Doe") and no associates match, the confidence falls below the 0.40 threshold.
- **Verdict:** Fails closed (False Negative). It will miss the alias rather than falsely merge two innocent people. This is operationally correct.

## 2. Spatial Analytics (Coordinate Drift)
### Attack: GPS Drift
- **Scenario:** A police officer's mobile device records an FIR 500 meters away from the actual crime scene due to poor GPS signal indoors.
- **Engine Response:** DBSCAN uses a 500m epsilon by default. Drifts >500m will eject the FIR from the hotspot cluster, treating it as noise.
- **Verdict:** Highly sensitive to GPS accuracy. If accuracy > 500m, spatial clustering breaks down.

## 3. Crime Series Detection (Noise Injection)
### Attack: Random FIRs
- **Scenario:** A district has a steady baseline of 100 random, unrelated thefts per month.
- **Engine Response:** DBSCAN isolates these as `cluster_id = -1` (Noise). They do not form a series.
- **Verdict:** Robust. The engine excels at ignoring background noise.

## 4. Graph Analytics (Fake Gang Injection)
### Attack: Malicious FIR Linkage
- **Scenario:** An adversary creates 10 fake FIRs linking an innocent person to known gang members.
- **Engine Response:** The innocent person's PageRank will skyrocket, and Community Detection will absorb them into the gang's label.
- **Verdict:** **VULNERABLE.** Graph algorithms are purely structural; they assume all edges in Neo4j represent ground truth. If the relational data is compromised, the graph is compromised. This necessitates the "Source Reliability" weight in the Confidence Score to penalize unverified FIRs.
