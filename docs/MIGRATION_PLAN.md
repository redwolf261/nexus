# NEXUS Migration Plan & Execution Order

This document dictates the procedure for migrating the Nexus Data Layer from its previously non-functional state to the newly designed production schema, including the exact order of execution required to maintain referential integrity.

## Execution Order

Because the PostgreSQL schema now enforces 32 hard Foreign Key constraints, data must be loaded strictly in the following topological order. The Python ingestion framework (`run_ingest.py`) automatically enforces this sequence.

### Phase 1: Reference Data (Roots)
These entities have no outgoing foreign keys.
1. `districts`
2. `gangs`
3. `cctv_cameras`
4. `anpr_cameras`

### Phase 2: Dimensional Data (Level 1 Dependencies)
These entities depend only on Phase 1 roots.
5. `stations` (depends on `districts`)
6. `campaigns` (depends on `gangs`, `districts`)
7. `cell_towers` (depends on `stations`, `districts`)

### Phase 3: Dimensional Data (Level 2 Dependencies)
8. `officers` (depends on `stations`, `districts`)
9. `pois` (depends on `stations`, `districts`)
10. `persons` (depends on `districts`)

### Phase 4: Entity Extensions (Level 3 Dependencies)
11. `criminals` (depends on `persons`, `districts`, `stations`)
12. `vehicles` (depends on `persons`)
13. `phones` (depends on `persons`)
14. `masterminds` (depends on `persons`)
15. `informants` (depends on `persons`, `stations`)
16. `social_network`, `gang_members`, `criminal_associates`

### Phase 5: Fact Table (The Core Event)
17. `firs` (depends on `stations`, `districts`, `campaigns`, `officers`, `gangs`, `criminals`)

### Phase 6: Case Outcomes (Depend on FIRs)
18. `victims`, `accused`, `evidence`, `investigation_logs`, `modus_operandi`
19. `chargesheets`, `arrests`, `court_cases`
20. FIR Junctions (`fir_accomplices`, `fir_vehicles`, `fir_phones`)

### Phase 7: Telemetry & Intelligence (Leaves)
21. `cctv_events`, `cctv_logs`, `anpr_logs`
22. `cdrs`, `cell_tower_pings`, `vehicle_gps`, `patrol_logs`
23. `financial_transactions`, `intelligence_tips`, `entity_resolution`

---

## Migration Plan

### Step 1: Wipe Legacy State
Drop the existing legacy tables in Postgres and wipe the Neo4j graph.
```bash
python -m backend.ingestion.run_ingest pg --drop
python -m backend.ingestion.run_ingest graph --fresh-graph
```

### Step 2: Database Re-Initialization
The ingestion pipeline will automatically run SQLAlchemy's `Base.metadata.create_all(engine)` to create the new tables with the proper foreign key constraints before importing the data.

### Step 3: Run Validation Suite
Immediately following the data load, run the validation report to ensure row-parity and foreign-key integrity.
```bash
python -m backend.ingestion.run_ingest validate
```

### Step 4: Handle Soft References
- **`criminals` ↔ `gangs`:** This forms a mutual cyclic reference (`criminals.gang_id` and `gangs.leader_criminal_id`). This relationship is modeled as a "soft reference" (indexed but without a DB-enforced FK constraint). The validation script structurally verifies these references post-load.
- **Polymorphic references:** Tables like `social_network` and `entity_resolution` reference multiple target entity types depending on the row. These are intentionally kept as soft references and are verified by the validation pipeline.

### Step 5: Repoint API Layer
Once the data layer is populated and validated, Phase 2 of the project will update the FastAPI layer (`core_service.py` and `analytics_service.py`) to query the new DB schemas instead of generating hardcoded mock data.
