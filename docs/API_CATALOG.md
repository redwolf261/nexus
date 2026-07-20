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
