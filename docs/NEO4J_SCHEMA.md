# NEXUS Graph Schema (Neo4j)

This document outlines the complete Neo4j graph schema for the NEXUS platform, replacing the incomplete earlier version. It includes all required node labels and formally justifies every relationship type used for intelligence graph traversals.

## Node Labels

| Label | Description | Primary ID Property |
|---|---|---|
| `Person` | Any citizen, including suspects, victims, and masterminds. | `citizen_id` |
| `Vehicle` | Any registered or tracked vehicle. | `vehicle_id` |
| `Phone` | Any mobile device or burner phone. | `phone_id` |
| `FIR` | First Information Report (core event). | `fir_id` |
| `Officer` | Investigating officers and station personnel. | `officer_id` |
| `Campaign` | Organized crime sprees orchestrated by gangs. | `campaign_id` |
| `Gang` | Organized criminal syndicates. | `gang_id` |
| `District` | Geographical boundaries for jurisdiction. | `district_id` |
| `Evidence` | Physical or digital evidence linked to FIRs. | `evidence_id` |
| `CCTV` | Traffic and surveillance cameras. | `camera_id` |
| `CellTower` | Telecom infrastructure for CDR pings. | `tower_id` |

*Note: All nodes use a unified `id` property for fast MERGE operations during ingestion, mapped from the primary ID property listed above.*

---

## Relationship Types

Every relationship is directed and serves a specific analytical purpose. 

### 1. `INVOLVED_IN`
- **Pattern:** `(Person) -[:INVOLVED_IN {role: "accused"|"victim"|"witness"}]-> (FIR)`
- **Justification:** Crucial for building an individual's rap sheet. Distinct from `COMMITTED`, this allows polymorphic querying to see if a victim in one FIR is an accused in another, exposing retaliation loops.

### 2. `OWNS`
- **Pattern:** `(Person) -[:OWNS]-> (Vehicle | Phone)`
- **Justification:** Asset tracing. Enables graph queries to find the registered owner of a burner phone or getaway vehicle spotted near a crime scene.

### 3. `USES`
- **Pattern:** `(Person) -[:USES]-> (Vehicle | Phone)`
- **Justification:** Differentiates between *registered ownership* and *actual usage*. A gang member might `USE` a vehicle that someone else `OWNS` (e.g., stolen or borrowed), which is vital for exposing proxies.

### 4. `LOCATED_AT`
- **Pattern:** `(FIR | CCTV | CellTower | Person | Gang) -[:LOCATED_AT]-> (District)`
- **Justification:** Spatial aggregation. Allows the graph to rapidly restrict any complex traversal (e.g., find all gangs operating in a specific area) without relying purely on GIS bounding boxes.

### 5. `CONTACTED`
- **Pattern:** `(Phone) -[:CONTACTED {timestamp: datetime, duration: int}]-> (Phone)`
- **Justification:** Call Detail Record (CDR) analysis. Essential for community detection algorithms to find hidden hierarchies and burn-phone networks.

### 6. `INVESTIGATED_BY`
- **Pattern:** `(FIR) -[:INVESTIGATED_BY]-> (Officer)`
- **Justification:** Identifies officer caseloads, detects potential conflict-of-interest (e.g., same officer investigating rival gangs), and measures resolution efficiency.

### 7. `BELONGS_TO`
- **Pattern:** `(Person) -[:BELONGS_TO {role: "leader"|"member"}]-> (Gang)`
- **Justification:** Organizational hierarchy. Maps the internal structure of syndicates and allows propagation of threat scores from gangs to individuals.

### 8. `ASSOCIATED_WITH`
- **Pattern:** `(Person) -[:ASSOCIATED_WITH {strength: float}]-> (Person)`
- **Justification:** Social network ties. Derived from shared addresses, family links, or historical accomplices. Used to predict who a suspect might hide with or recruit next.

### 9. `LINKED_TO`
- **Pattern:** `(FIR) -[:LINKED_TO {confidence: float, method: string}]-> (FIR)`
- **Justification:** The core of the "Silo Buster" feature. Connects seemingly disparate crimes through shared MO, weapons, or entities. Pre-computed linkages enable real-time UI rendering.

### 10. `CONNECTED_TO`
- **Pattern:** `(Evidence | Vehicle | Phone) -[:CONNECTED_TO]-> (FIR)`
- **Justification:** Connects physical and digital artifacts to crime events. A gun (Evidence) found at one FIR and a bullet casing found at another can bridge two separate investigations.
