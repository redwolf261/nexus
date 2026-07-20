# NEXUS Import Architecture

This document details the data ingestion architecture used to populate PostgreSQL and Neo4j from the raw simulator outputs. The entire pipeline has been rewritten to be fully Pythonic, robust, and idempotent.

## 1. Orchestration Layer (`run_ingest.py`)

The pipeline is orchestrated by a unified CLI, `backend/ingestion/run_ingest.py`. 
It provides commands to run the PostgreSQL loader, the Neo4j graph loader, and the Validation pipeline either individually or all together.

**Usage:**
```bash
python -m backend.ingestion.run_ingest pg         # load PostgreSQL
python -m backend.ingestion.run_ingest graph      # load Neo4j
python -m backend.ingestion.run_ingest validate   # run validation report
python -m backend.ingestion.run_ingest all        # pg -> graph -> validate
```

## 2. PostgreSQL Ingestion Pipeline (`pg_loader.py`)

The Postgres loader reads the CSV datasets, maps them to the updated 32-table relational schema (`backend/db/schema.py`), and executes bulk inserts.

### Key Features:
- **Bulk Inserts & Transactions:** Uses SQLAlchemy batch inserts enclosed in transactions to maximize throughput and guarantee ACID compliance.
- **Idempotency & Resumption:** Tracks successful table loads in a local state file (`output/.ingest_state.json`). If the pipeline fails midway, restarting it will seamlessly resume from the last successful table. Use `--no-resume` to override this behavior.
- **Conflict Handling & Duplicate Detection:** Deduplicates overlapping primary keys (e.g. in `evidence.csv`) within the ingestion batch before hitting the database, preventing constraint violation crashes.
- **Referential Integrity Validation:** The framework ingests reference/geography tables first, followed by dimension tables, and finally fact tables (e.g. `firs`), ensuring foreign key relationships are respected natively by the database.

## 3. Neo4j Graph Ingestion Pipeline (`load_neo4j_aura.py` / `graph_loader.py`)

The Neo4j importer eliminates the dependency on `neo4j-admin` and enables direct import into a managed AuraDB instance entirely via the Python Neo4j driver (Bolt protocol).

### Key Features:
- **No `neo4j-admin` Required:** Data is pushed directly via Cypher `UNWIND ... MERGE` statements, making it compatible with cloud-native AuraDB deployments without requiring direct filesystem access to the database server.
- **Batch Processing:** Both nodes and relationships are processed in batches (default: 500 rows) to keep transaction sizes manageable and prevent out-of-memory errors on the Neo4j server.
- **Idempotency:** Nodes are created using `MERGE` on the universal `id` property. Relationships are similarly created using `MERGE`. Re-running the pipeline on a populated database will simply update properties rather than creating duplicates.
- **Schema Initialization:** Automatically creates `IS UNIQUE` constraints on the `id` property for all Node Labels prior to data ingestion, ensuring rapid node lookup during relationship creation.

## 4. Progress Reporting and Logging (`framework.py`)

A centralized logging and framework utility orchestrates the ingestion context. 
It emits structured, color-coded logging to `stdout`, displaying the current ingestion phase, row-level progress, execution times, and comprehensive post-run summaries.
