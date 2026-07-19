"""
Network loader for Neo4j AuraDB (cloud).

Reads the simulator's export from output/neo4j/*.csv and pushes nodes +
relationships over Bolt. Unlike `neo4j-admin database import` (which requires
filesystem access to the DB server), this works against a managed AuraDB
instance from anywhere.

IMPORTANT: The backend queries nodes by an `id` PROPERTY, e.g.
    MATCH (f:FIR {id: $fir_id})
so every node here is created with `id` set from the CSV `:ID` column.

Usage (run locally, pointing at your AuraDB):
    export NEO4J_URI="neo4j+s://<id>.databases.neo4j.io"
    export NEO4J_USER="neo4j"
    export NEO4J_PASSWORD="<your-aura-password>"
    python -m backend.ingestion.load_neo4j_aura

Add --wipe to clear the graph first.
"""

import os
import csv
import sys
import glob

from backend.neo4j_client import neo4j_client

DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../output/neo4j")
)

# Columns in the CSVs that are Neo4j metadata, not node properties.
META_COLS = {":ID", ":LABEL", ":START_ID", ":END_ID", ":TYPE"}

BATCH_SIZE = 500


def _clean_key(key: str) -> str:
    # Strip a UTF-8 BOM that Excel/exporters sometimes prepend to the first header.
    return key.lstrip("﻿").strip()


def _rows(path: str):
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            yield { _clean_key(k): (v if v != "" else None) for k, v in raw.items() }


def create_constraints():
    labels = ["Person", "FIR", "Gang", "Station", "District",
              "Officer", "Phone", "Vehicle", "Evidence"]
    for label in labels:
        neo4j_client.query(
            f"CREATE CONSTRAINT IF NOT EXISTS "
            f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
        )
    print(f"  Ensured uniqueness constraints on {len(labels)} labels.")


def load_nodes():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "nodes_*.csv")))
    if not files:
        print(f"  No node files found in {DATA_DIR}")
        return
    for path in files:
        name = os.path.basename(path)
        batch = []
        total = 0
        label = None
        for row in _rows(path):
            label = row.pop(":LABEL", None) or label
            node_id = row.pop(":ID", None)
            if node_id is None:
                continue
            props = {k: v for k, v in row.items() if k not in META_COLS}
            props["id"] = node_id
            batch.append(props)
            if len(batch) >= BATCH_SIZE:
                _flush_nodes(label, batch)
                total += len(batch)
                batch = []
        if batch:
            _flush_nodes(label, batch)
            total += len(batch)
        print(f"  {name}: loaded {total} :{label} nodes")


def _flush_nodes(label, batch):
    # MERGE on id so re-runs are idempotent; SET applies all properties.
    query = (
        f"UNWIND $rows AS row "
        f"MERGE (n:{label} {{id: row.id}}) "
        f"SET n += row"
    )
    neo4j_client.query(query, parameters={"rows": batch})


def load_relationships():
    path = os.path.join(DATA_DIR, "relationships.csv")
    if not os.path.exists(path):
        print("  No relationships.csv found.")
        return

    # Group by :TYPE because relationship type can't be parameterized in Cypher.
    by_type = {}
    for row in _rows(path):
        rtype = row.pop(":TYPE", None)
        start = row.pop(":START_ID", None)
        end = row.pop(":END_ID", None)
        if not (rtype and start and end):
            continue
        props = {k: v for k, v in row.items() if k not in META_COLS and v is not None}
        by_type.setdefault(rtype, []).append(
            {"start": start, "end": end, "props": props}
        )

    total = 0
    for rtype, rows in by_type.items():
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            query = (
                "UNWIND $rows AS row "
                "MATCH (a {id: row.start}) "
                "MATCH (b {id: row.end}) "
                f"MERGE (a)-[r:{rtype}]->(b) "
                "SET r += row.props"
            )
            neo4j_client.query(query, parameters={"rows": batch})
        total += len(rows)
        print(f"  {rtype}: loaded {len(rows)} relationships")
    print(f"  Total relationships: {total}")


def wipe():
    print("Wiping existing graph...")
    neo4j_client.query("MATCH (n) DETACH DELETE n")


def main():
    if "--wipe" in sys.argv:
        wipe()
    print(f"Loading Neo4j graph from {DATA_DIR}")
    print("Creating constraints...")
    create_constraints()
    print("Loading nodes...")
    load_nodes()
    print("Loading relationships...")
    load_relationships()
    neo4j_client.close()
    print("Done. Neo4j AuraDB graph is populated.")


if __name__ == "__main__":
    main()
