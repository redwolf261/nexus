# NEXUS Performance Recommendations

This document outlines the performance optimizations, estimated storage, and indexing strategies for the newly designed PostgreSQL data layer, ensuring it can handle the scale required by the NEXUS platform.

## 1. Estimated Storage

Based on the row counts and column types in the simulator output, the initial storage footprint is highly manageable:
- **Reference & Dimensional Data:** `districts`, `stations`, `gangs`, `campaigns` (< 1MB)
- **Entities:** `persons` (5,000 rows), `officers` (3,801 rows), `vehicles` (1,606 rows), `phones` (4,168 rows) (~10MB)
- **Fact Tables:** `firs` (1,000 rows) along with `evidence`, `victims`, `accused` (~5MB)
- **Telemetry Data:** `patrol_logs` (154,208 rows), `cdrs` (14,336 rows), `vehicle_gps` (10,225 rows) (~30-50MB)
**Total Estimated Storage (PostgreSQL):** ~65 MB.
*Note: As this scales to millions of real-world FIRs and billions of telemetry points, the strategy below must be implemented.*

## 2. Recommended Indexes

The `backend/db/schema.py` automatically generates the required indexes, but here is the rationale for production scaling:

### A. Foreign Key Indexes
In PostgreSQL, foreign keys are not automatically indexed. Every foreign key (e.g., `firs.district_id`, `firs.station_id`, `evidence.fir_id`) has been explicitly indexed (`index=True` or via `__table_args__`).
- *Why:* Speeds up cascading deletes and joins (e.g., finding all evidence for an FIR).

### B. High-Cardinality Lookups
- `persons.name_en`, `persons.phone_primary`
- `vehicles.license_plate`
- `phones.phone_number`
- *Why:* Supports the global `/api/search` endpoint. Consider creating `pg_trgm` (trigram) indexes on `name_en` and `license_plate` for fast partial text search.

### C. Temporal and Spatial Indexes
- `firs.occurred_date`, `patrol_logs.patrol_date`, `cctv_events.event_timestamp`
- *Why:* Range queries (e.g., "crimes in the last 30 days") are frequent.
- *GIS Note:* `latitude` and `longitude` are currently stored as floats. For production, migrate these to `PostGIS` `geometry(Point, 4326)` columns and apply a `GIST` index for rapid spatial queries (e.g., bounding box searches).

## 3. Query Complexity Estimates

### A. Graph Traversal vs SQL Joins
- **Neo4j (O(1) per hop):** Finding a mastermind linked to a gang, linked to an FIR, linked to a vehicle is highly efficient. The "Silo Buster" and cross-jurisdiction endpoints must run exclusively on Neo4j.
- **PostgreSQL (O(N log N)):** Deeply joining `firs` -> `accused` -> `criminals` -> `persons` is acceptable for a single case report but will degrade if aggregating across the entire state.

### B. Analytical Aggregations
- Queries like `count(firs)` grouped by `district_name` and `crime_type` will scan the `firs` table. With the recommended indexes, this will be fast. For Executive Dashboards, consider Materialized Views that refresh hourly.

## 4. Partitioning Recommendations

As NEXUS absorbs live telemetry, partitioning is required to manage table bloat:

### A. Telemetry Data (Time-Based Partitioning)
- **Tables:** `patrol_logs`, `cdrs`, `vehicle_gps`, `cctv_events`, `cctv_logs`, `anpr_logs`
- **Strategy:** `PARTITION BY RANGE (timestamp)`
- **Granularity:** Monthly partitions (e.g., `cdrs_2021_01`).
- **Benefit:** Allows fast dropping of old telemetry data without expensive `DELETE` operations and keeps the active index sizes small.

### B. Fact Data (Time or Geographic Partitioning)
- **Table:** `firs`
- **Strategy:** If the table exceeds 10 million rows, `PARTITION BY LIST (district_id)` or `PARTITION BY RANGE (occurred_date)` depending on whether queries usually filter by jurisdiction or time.
