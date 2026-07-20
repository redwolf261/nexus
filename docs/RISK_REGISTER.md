# NEXUS Risk Register

This document outlines known risks, quirks, and technical debt items identified during the Phase 1 reconstruction of the Data Layer.

## 1. Data Quirks from Simulator

| ID | Risk Description | Impact Level | Mitigation / Handling |
|---|---|---|---|
| **R01** | `evidence.csv` contains duplicate primary keys. Out of 2,318 rows, only 1,779 unique `evidence_id`s exist. | Medium | The ingestion pipeline's `pg_loader.py` actively deduplicates within the batch on primary key before insertion. The loss of 539 duplicate rows is intentional and prevents constraint violation crashes. |
| **R02** | `daily_context.csv` is completely corrupted in the source output. The CSV contains Python object representations (`<DayContext object at 0x...>`) instead of scalar values. | Low | The dataset is excluded from the ingestion pipeline. No features currently depend on this table. |
| **R03** | `firs_with_noise.csv` is an experimental variation of `firs.csv` and breaks primary key constraints if loaded concurrently. | Low | Excluded from the relational schema; `firs.csv` is the single source of truth for all crime events. |
| **R04** | Telemetry tables (e.g., `patrol_logs.csv` with 154,208 rows) are exceptionally large compared to the rest of the dataset. | Medium | Loaded at the end of the ingestion pipeline in large batches. In production, these should be moved to a time-series or columnar database. |

## 2. Graph Discrepancies

| ID | Risk Description | Impact Level | Mitigation / Handling |
|---|---|---|---|
| **R05** | Graph nodes don't perfectly match Postgres rows (e.g., only 2,534 Persons in Neo4j vs 5,000 in Postgres). | Low | This is standard for a knowledge graph; only entities connected to crimes, gangs, or investigations are pushed to Neo4j. Validation warns but doesn't hard-fail. |

## 3. Structural & Architectural Risks

| ID | Risk Description | Impact Level | Mitigation / Handling |
|---|---|---|---|
| **R06** | The `criminals` table and the `gangs` table form a reference cycle (`gang_id` and `leader_criminal_id`). | High | mode hard FK constraints impossible without deferred checks. The schema implements these as "soft references" (indexed without `ForeignKey` constraints). Integrity is validated post-load by the Python validation script. |
| **R07** | Polymorphic edges in `social_network.csv` (source and target IDs can refer to multiple different entity types like citizen or criminal). | Medium | Left as soft references. The API layer must handle polymorphic joins programmatically when traversing social networks in Postgres. (Neo4j handles this natively without issue). |
| **R08** | The sheer size of geographic boundaries (`boundaries.geojson`) currently loaded client-side. | Medium | While not an ingestion issue, future phases should consider serving map tiles dynamically from a GIS-enabled Postgres (PostGIS) extension rather than a static 5MB file. |
