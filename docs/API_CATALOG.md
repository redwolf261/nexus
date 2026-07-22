# NEXUS API Catalog

## Core Endpoints
### `GET /api/dashboard/executive`
Returns daily active cases, open campaigns, and top hotspots for the command center.

### `GET /api/district/{district_id}`
Returns district specific statistics.

### `GET /api/firs`
Queries the FIR catalog.
**Query Parameters:**
- `district_id` (optional)
- `crime_type` (optional)
- `crime_category` (optional)
- `status` (optional)
- `date_from` (optional)
- `date_to` (optional)

### `GET /api/fir/{fir_id}`
Detailed investigation dossier for a specific FIR, joining accused, victims, logs, and linked artifacts.

### `GET /api/person/{person_id}`
Profile dossier, joining criminal history, linked vehicles, and linked phones.

### `GET /api/vehicle/{vehicle_id}`
Vehicle profile joining ownership details and FIRs where the vehicle was present.

### `GET /api/criminal/{criminal_id}`
Criminal history and gang affiliations.

## Analytics Endpoints
### `GET /api/analytics/hotspots`
Clusters high-crime locations based on geographic FIR density.

### `GET /api/analytics/cross-jurisdiction`
Detects multi-FIR patterns linking across state borders using Neo4j cross-referencing.

### `GET /api/graph/person/{person_id}`
1-hop social graph traversal around a person of interest.

### `GET /api/campaign/{campaign_id}/timeline`
Time-series traversal of a crime campaign execution.

### `GET /api/search`
Unified elastic-style search over FIRs, Persons, and Vehicles.


## Investigations Endpoints
### GET /api/investigations
Returns a list of all investigation cases.

### POST /api/investigations
Creates a new investigation case.

### GET /api/investigations/{inv_id}/workspace
Returns the complete, unified case workspace (metadata, entities, timeline, notes).

### POST /api/investigations/{inv_id}/entities
Attaches an entity (FIR, Person, Vehicle) to a case.

### DELETE /api/investigations/{inv_id}/entities/{entity_id}
Removes an entity from a case.

### POST /api/investigations/{inv_id}/notes
Adds a markdown note to the case.

### PATCH /api/investigations/notes/{note_id}
Updates a markdown note.


## Intelligence Endpoints
### GET /api/intelligence/entity/{entity_id}
Returns the threat score, gang influence, and network centrality of a specific entity.

### GET /api/intelligence/recommendations/{case_id}
Generates contextual recommendations (CCTV footage, interviews) based on case evidence.

### GET /api/intelligence/links/{entity_id}
Discovers hidden links via entity resolution (e.g. same Aadhaar, identical phone).

### GET /api/intelligence/risk/{case_id}
Computes aggregated risk metrics (Threat, Network Complexity, Evidence Completeness) for a case.

### GET /api/intelligence/expand/{entity_id}?depth=2
Performs variable-depth Neo4j graph traversal originating from the entity.

### GET /api/intelligence/overlaps/{case_id}
Discovers other active cases that share entities with the target case.
