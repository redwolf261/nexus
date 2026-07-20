# NEXUS Data Catalogue

Master catalogue of every simulator output and how it maps into the data layer.
Source of truth in code: [`backend/ingestion/catalog.py`](../backend/ingestion/catalog.py).

## Legend

- **Store** — `both` = loaded into Postgres *and* represented in the Neo4j graph;
  `postgres` = relational only (telemetry / intelligence, not graph-eligible).
- **PK** — primary-key column in the CSV.
- **Rows** — unique-PK rows loaded (verified in [VALIDATION_REPORT.md](VALIDATION_REPORT.md)).

## Ingested datasets (35 tables)

| Dataset (CSV) | Table | PK | Store | Rows | Notes |
|---|---|---|---|---|---|
| districts.csv | districts | district_id | both | 31 | geography root |
| stations.csv | stations | station_id | both | 632 | FK district |
| officers.csv | officers | officer_id | both | 3,801 | FK station, district |
| pois.csv | pois | poi_id | postgres | 3,882 | points of interest |
| cctv_cameras.csv | cctv_cameras | camera_id | postgres | 12,336 | |
| anpr_cameras.csv | anpr_cameras | anpr_id | postgres | 1,250 | |
| cell_towers.csv | cell_towers | tower_id | postgres | 3,133 | |
| persons.csv | persons | citizen_id | both | 5,000 | population |
| vehicles.csv | vehicles | vehicle_id | both | 1,606 | FK owner→persons |
| phones.csv | phones | phone_id | both | 4,168 | FK owner→persons |
| criminals.csv | criminals | criminal_id | both | 245 | FK citizen; gang_id soft (cycle) |
| gangs.csv | gangs | gang_id | both | 5 | leader_criminal_id soft (cycle) |
| ground_truth_campaigns.csv | campaigns | campaign_id | both | 37 | FK gang, target_district |
| ground_truth_masterminds.csv | masterminds | mastermind_id | postgres | 5 | FK citizen |
| firs.csv | firs | fir_id | both | 1,000 | central fact; many FKs |
| victims.csv | victims | victim_id | both | 2,289 | FK fir |
| accused.csv | accused | accused_id | postgres | 1,081 | FK fir |
| evidence.csv | evidence | evidence_id | both | 1,779 | FK fir; source has dup PKs (see below) |
| investigation_logs.csv | investigation_logs | log_id | postgres | 5,074 | FK fir |
| modus_operandi.csv | modus_operandi | crime_event_id | postgres | 1,000 | FK fir |
| chargesheets.csv | chargesheets | chargesheet_id | postgres | 152 | FK fir |
| arrests.csv | arrests | arrest_id | postgres | 302 | FK fir |
| court_cases.csv | court_cases | case_id | postgres | 152 | FK fir |
| cctv_logs.csv | cctv_logs | log_id | postgres | 7,100 | telemetry, soft refs |
| cctv_events.csv | cctv_events | cctv_event_id | postgres | 718 | telemetry |
| anpr_logs.csv | anpr_logs | log_id | postgres | 813 | telemetry |
| cdrs.csv | cdrs | cdr_id | postgres | 14,336 | call detail records |
| cell_tower_pings.csv | cell_tower_pings | ping_id | postgres | 7,200 | telemetry |
| vehicle_gps.csv | vehicle_gps | gps_id | postgres | 10,225 | telemetry |
| patrol_logs.csv | patrol_logs | log_id | postgres | 154,208 | largest table |
| financial_transactions.csv | financial_transactions | transaction_id | postgres | 14 | intelligence |
| intelligence_tips.csv | intelligence_tips | tip_id | postgres | 12 | intelligence |
| informants.csv | informants | informant_id | postgres | 100 | intelligence |
| social_network.csv | social_network | tie_id | postgres | 983 | soft/polymorphic refs |
| entity_resolution.csv | entity_resolution | er_id | postgres | 603 | soft/polymorphic refs |

## Junction tables (expanded from pipe-delimited columns)

| Table | Source column | Left → Right |
|---|---|---|
| gang_members | gangs.member_criminal_ids | gang_id → criminal_id |
| criminal_associates | criminals.known_associates | criminal_id → associate_id |
| fir_accomplices | firs.accomplice_criminal_ids | fir_id → criminal_id |
| fir_vehicles | firs.vehicle_ids | fir_id → vehicle_id |
| fir_phones | firs.phone_ids | fir_id → phone_id |

## Intentionally NOT ingested

| File | Reason |
|---|---|
| daily_context.csv | Corrupt export — Python object reprs (`<DayContext object at 0x…>`), not tabular. |
| firs_with_noise.csv | Noise-augmented duplicate of firs.csv for ML robustness; not a distinct entity. |
| crime_statistics.json | Aggregate statistics, not relational. |
| gang_network.json | Denormalized aggregate of gangs.csv; relational form already loaded. |
| simulation_summary.json | Run metadata; used for row-count parity, not a table. |

## Known source-data quirks

- **evidence.csv** ships 2,318 rows but only **1,779 unique `evidence_id`s** — the simulator
  emits genuine duplicate PKs. The loader dedups within-batch on PK; the 539-row gap is a
  source quirk, not data loss. Flagged in the risk register.
- **criminals ↔ gangs** form a reference cycle (`criminals.gang_id` ↔ `gangs.leader_criminal_id`).
  Both directions are modelled as **soft indexed references** (no hard DB FK); the validation
  pipeline checks their integrity instead. See [MIGRATION_PLAN.md](MIGRATION_PLAN.md).
