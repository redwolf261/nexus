# Operational Failure Mode Catalog
**Phase 7.3 Intelligence Quality Audit**

## Objective
Catalogue adversarial, operational, and edge-case inputs that cause the NEXUS Analytical Engine to fail, detailing the resulting output, confidence, explanation, and investigative risk.

---

## 1. The "Twins" Failure (Entity Resolution)
- **Scenario:** Identical twins share a surname, date of birth, home address, and occasionally share a phone.
- **Engine Output:** Entity Resolution heavily weights matching Phone (0.20), Address (0.07), and Geography (0.05). It merges the twins into a single criminal entity.
- **Confidence:** >90% (Extremely High).
- **Explanation:** "Exact phone match and high spatial proximity."
- **Risk:** CATASTROPHIC. Warrants may be executed against the innocent twin. This requires manual decoupling capabilities in the UI.

## 2. Phone Recycling
- **Scenario:** A telecom provider recycles a prepaid phone number from a known gang member to an innocent citizen.
- **Engine Output:** The innocent citizen is linked to the gang member's historical FIRs via `Phone.number`. Graph Centrality metrics spike for the innocent citizen.
- **Confidence:** >85% (High).
- **Explanation:** "Exact primary identifier match (Phone)."
- **Risk:** SEVERE. Relies on the investigator noticing that the dates of the FIRs predate the telecom issuance date. The engine currently lacks temporal constraint checking for phone ownership.

## 3. Common Surnames + Missing Aadhaar
- **Scenario:** Two distinct individuals named "Rahul Singh" commit crimes in the same district. Neither FIR includes an Aadhaar card or Phone number.
- **Engine Output:** Name match (Jaro-Winkler = 1.0) + Geography match (Same district). Score clears 0.40 threshold. Entities merged.
- **Confidence:** ~45% (Low).
- **Explanation:** "Jaro-winkler name match."
- **Risk:** MODERATE. The geometric mean correctly tanks the confidence due to `Data Completeness = 0.1` (Missing primary IDs), warning the investigator that this merge is highly speculative.

## 4. Lazy Data Entry (Default Police Station GPS)
- **Scenario:** Field officers skip GPS logging, defaulting the FIR location to the physical Police Station coordinates.
- **Engine Output:** Spatial Analytics detects a massive "Hotspot" directly over the precinct. Crime Series heavily weights these crimes together because distance = 0.
- **Confidence:** ~80% (High - data looks complete, just inaccurate).
- **Explanation:** "High density cluster (distance < 0.5km)."
- **Risk:** HIGH. Creates severe alert fatigue. Analysts will learn to ignore spatial clusters located near police stations.

## 5. Delayed FIR Registration
- **Scenario:** An incident from 2022 is finally registered in the digital system in 2026.
- **Engine Output:** Temporal CUSUM registers a massive spike in crime for "today" (the DB entry date) rather than the incident date.
- **Confidence:** 100% (The database definitively contains the record).
- **Risk:** LOW for individual cases, HIGH for executive dashboards. It creates artificial anomalies that trigger panic at the command level.
