"""
NEXUS Ingestion — Neo4j Graph Loader

Loads the investigative subgraph over Bolt (driver-only; works against local
Docker Neo4j or a managed AuraDB). Supersedes load_neo4j_aura.py by adding:
  - framework integration (retry, checkpoint/resume, progress)
  - Campaign nodes synthesized from ground_truth_campaigns.csv (absent from export)
  - RAN_CAMPAIGN (Gang->Campaign) and BELONGS_TO (FIR->Campaign) edges
  - INVOLVES edges (FIR->Phone, FIR->Vehicle) so the API's cross-jurisdiction
    query MATCH (f1:FIR)-[:INVOLVES]->(e)-[:INVOLVES]->(f2:FIR) resolves

Every node is created with an `id` PROPERTY (not just the import :ID), because
the API queries by property: MATCH (f:FIR {id: $fir_id}).

Usage:
    python -m backend.ingestion.run_ingest graph
    (or set NEO4J_URI/USER/PASSWORD env vars to target AuraDB)
"""
from __future__ import annotations

import csv
import glob
import os
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from backend.neo4j_client import neo4j_client
from backend.ingestion.framework import (
    Checkpoint, Progress, batched, logger, stream_rows, with_retry,
)

NEO4J_DIR = Path(__file__).resolve().parents[2] / "output" / "neo4j"
META_COLS = {":ID", ":LABEL", ":START_ID", ":END_ID", ":TYPE"}
BATCH_SIZE = 500

# Labels that get a uniqueness constraint on `id`.
NODE_LABELS = ["Person", "FIR", "Gang", "Station", "District",
               "Officer", "Phone", "Vehicle", "Evidence", "Campaign"]


def _clean_key(key: str) -> str:
    return key.lstrip("﻿").strip()


def _neo4j_rows(path: Path) -> Iterator[Dict[str, Optional[str]]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        reader.fieldnames = [_clean_key(f) for f in (reader.fieldnames or [])]
        for raw in reader:
            yield {_clean_key(k): (v if v not in ("", None) else None)
                   for k, v in raw.items()}


# ── Constraints ──────────────────────────────────────────────────────────────
def create_constraints() -> None:
    for label in NODE_LABELS:
        with_retry(
            lambda label=label: neo4j_client.query(
                f"CREATE CONSTRAINT IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
            ),
            what=f"constraint {label}",
        )
    logger.info(f"  Ensured uniqueness constraints on {len(NODE_LABELS)} labels.")


# ── Nodes ────────────────────────────────────────────────────────────────────
def _flush_nodes(label: str, batch: List[dict]) -> None:
    query = (
        "UNWIND $rows AS row "
        f"MERGE (n:{label} {{id: row.id}}) "
        "SET n += row"
    )
    with_retry(lambda: neo4j_client.query(query, parameters={"rows": batch}),
               what=f"nodes {label}")


def load_nodes(ckpt: Checkpoint) -> None:
    files = sorted(glob.glob(str(NEO4J_DIR / "nodes_*.csv")))
    if not files:
        logger.warning(f"  No node files in {NEO4J_DIR}")
        return
    for path in files:
        name = os.path.basename(path)
        step = f"nodes:{name}"
        if ckpt.is_done(step):
            logger.info(f"  {name}: already loaded (checkpoint) — skipping")
            continue

        def _rows_for(p=Path(path)):
            for row in _neo4j_rows(p):
                node_id = row.pop(":ID", None)
                label = row.pop(":LABEL", None)
                if node_id is None:
                    continue
                props = {k: v for k, v in row.items() if k not in META_COLS}
                props["id"] = node_id
                yield label, props

        label = None
        total = 0
        pending: List[dict] = []
        for lbl, props in _rows_for():
            label = label or lbl
            pending.append(props)
            if len(pending) >= BATCH_SIZE:
                _flush_nodes(label, pending)
                total += len(pending)
                pending = []
        if pending and label:
            _flush_nodes(label, pending)
            total += len(pending)
        logger.info(f"  {name}: loaded {total:,} :{label} nodes")
        ckpt.mark_done(step, rows=total)


# ── Base relationships (from export relationships.csv) ───────────────────────
def _flush_edges(rtype: str, batch: List[dict]) -> None:
    query = (
        "UNWIND $rows AS row "
        "MATCH (a {id: row.start}) "
        "MATCH (b {id: row.end}) "
        f"MERGE (a)-[r:{rtype}]->(b) "
        "SET r += row.props"
    )
    with_retry(lambda: neo4j_client.query(query, parameters={"rows": batch}),
               what=f"edges {rtype}")


def load_relationships(ckpt: Checkpoint) -> None:
    path = NEO4J_DIR / "relationships.csv"
    if not path.exists():
        logger.warning("  No relationships.csv found.")
        return
    step = "relationships.csv"
    if ckpt.is_done(step):
        logger.info("  relationships.csv: already loaded (checkpoint) — skipping")
        return

    by_type: Dict[str, List[dict]] = {}
    for row in _neo4j_rows(path):
        rtype = row.pop(":TYPE", None)
        start = row.pop(":START_ID", None)
        end = row.pop(":END_ID", None)
        if not (rtype and start and end):
            continue
        props = {k: v for k, v in row.items()
                 if k not in META_COLS and v is not None}
        by_type.setdefault(rtype, []).append(
            {"start": start, "end": end, "props": props})

    total = 0
    for rtype, rows in by_type.items():
        for batch in batched(iter(rows), BATCH_SIZE):
            _flush_edges(rtype, batch)
        total += len(rows)
        logger.info(f"  {rtype}: loaded {len(rows):,} relationships")
    logger.info(f"  Base relationships total: {total:,}")
    ckpt.mark_done(step, rows=total)


# ── INVOLVES (synthesized) ───────────────────────────────────────────────────
# The API's cross-jurisdiction query walks FIR-[:INVOLVES]->(entity)-[:INVOLVES]->FIR,
# so a FIR and its shared Phone/Vehicle need INVOLVES edges in BOTH directions.
# Derive from the export's entity->FIR edges (PHONE_LINKED_TO, USED_VEHICLE_IN).
def load_involves(ckpt: Checkpoint) -> None:
    path = NEO4J_DIR / "relationships.csv"
    if not path.exists():
        return
    step = "synth:INVOLVES"
    if ckpt.is_done(step):
        logger.info("  INVOLVES: already synthesized (checkpoint) — skipping")
        return

    pairs: List[dict] = []
    for row in _neo4j_rows(path):
        rtype = row.get(":TYPE")
        if rtype not in ("PHONE_LINKED_TO", "USED_VEHICLE_IN"):
            continue
        entity, fir = row.get(":START_ID"), row.get(":END_ID")
        if entity and fir:
            pairs.append({"fir": fir, "entity": entity})

    for batch in batched(iter(pairs), BATCH_SIZE):
        query = (
            "UNWIND $rows AS row "
            "MATCH (f:FIR {id: row.fir}) "
            "MATCH (e {id: row.entity}) "
            "MERGE (f)-[:INVOLVES]->(e) "
            "MERGE (e)-[:INVOLVES]->(f)"
        )
        with_retry(lambda b=batch: neo4j_client.query(query, parameters={"rows": b}),
                   what="INVOLVES")
    logger.info(f"  INVOLVES: synthesized {len(pairs):,} FIR<->entity links "
                f"({len(pairs) * 2:,} directed edges)")
    ckpt.mark_done(step, rows=len(pairs))


# ── Campaign nodes + edges (synthesized from CSVs) ───────────────────────────
def load_campaigns(ckpt: Checkpoint) -> None:
    step = "synth:Campaign"
    if ckpt.is_done(step):
        logger.info("  Campaign: already synthesized (checkpoint) — skipping")
        return

    # 1) Campaign nodes + RAN_CAMPAIGN (Gang)-[:RAN_CAMPAIGN]->(Campaign)
    campaigns: List[dict] = []
    for row in stream_rows("ground_truth_campaigns.csv"):
        cid = row.get("campaign_id")
        if not cid:
            continue
        campaigns.append({
            "id": cid,
            "gang_id": row.get("gang_id"),
            "props": {k: v for k, v in row.items() if v is not None},
        })

    for batch in batched(iter(campaigns), BATCH_SIZE):
        node_q = (
            "UNWIND $rows AS row "
            "MERGE (c:Campaign {id: row.id}) "
            "SET c += row.props"
        )
        with_retry(lambda b=batch: neo4j_client.query(node_q, parameters={"rows": b}),
                   what="Campaign nodes")
        edge_q = (
            "UNWIND $rows AS row "
            "WITH row WHERE row.gang_id IS NOT NULL "
            "MATCH (g:Gang {id: row.gang_id}) "
            "MATCH (c:Campaign {id: row.id}) "
            "MERGE (g)-[:RAN_CAMPAIGN]->(c)"
        )
        with_retry(lambda b=batch: neo4j_client.query(edge_q, parameters={"rows": b}),
                   what="RAN_CAMPAIGN")
    logger.info(f"  Campaign: created {len(campaigns):,} nodes + RAN_CAMPAIGN edges")

    # 2) BELONGS_TO (FIR)-[:BELONGS_TO]->(Campaign) from firs.campaign_id
    links: List[dict] = []
    for row in stream_rows("firs.csv"):
        fir_id, camp = row.get("fir_id"), row.get("campaign_id")
        if fir_id and camp:
            links.append({"fir": fir_id, "campaign": camp})

    for batch in batched(iter(links), BATCH_SIZE):
        q = (
            "UNWIND $rows AS row "
            "MATCH (f:FIR {id: row.fir}) "
            "MATCH (c:Campaign {id: row.campaign}) "
            "MERGE (f)-[:BELONGS_TO]->(c)"
        )
        with_retry(lambda b=batch: neo4j_client.query(q, parameters={"rows": b}),
                   what="BELONGS_TO")
    logger.info(f"  BELONGS_TO: linked {len(links):,} FIRs to campaigns")
    ckpt.mark_done(step, rows=len(campaigns))


# ── FIR date alias ───────────────────────────────────────────────────────────
# The API's get_campaign_timeline query orders BELONGS_TO members by e.date, but
# FIR nodes carry occurred_date. Mirror it into `date` so the existing query
# (which we must not modify) sorts correctly.
def alias_fir_date(ckpt: Checkpoint) -> None:
    step = "synth:fir_date_alias"
    if ckpt.is_done(step):
        logger.info("  FIR date alias: already applied (checkpoint) — skipping")
        return
    with_retry(
        lambda: neo4j_client.query(
            "MATCH (f:FIR) WHERE f.occurred_date IS NOT NULL AND f.date IS NULL "
            "SET f.date = f.occurred_date"
        ),
        what="FIR date alias",
    )
    logger.info("  FIR date alias: set date = occurred_date")
    ckpt.mark_done(step)


def wipe() -> None:
    logger.info("Wiping existing graph...")
    with_retry(lambda: neo4j_client.query("MATCH (n) DETACH DELETE n"), what="wipe")


def _graph_summary() -> Dict[str, int]:
    """Post-load counts per node label + a total edge count, for reporting."""
    summary: Dict[str, int] = {}
    for label in NODE_LABELS:
        rec = neo4j_client.query(f"MATCH (n:{label}) RETURN count(n) AS c")
        summary[f"(:{label})"] = rec[0]["c"] if rec else 0
    rec = neo4j_client.query("MATCH ()-[r]->() RETURN count(r) AS c")
    summary["[edges]"] = rec[0]["c"] if rec else 0
    return summary


def load_all(resume: bool = True, fresh: bool = False) -> Dict[str, int]:
    ckpt = Checkpoint(namespace="neo4j")
    if fresh:
        wipe()
        ckpt.reset()
    elif not resume:
        ckpt.reset()

    logger.info(f"Loading Neo4j graph from {NEO4J_DIR}")
    create_constraints()
    logger.info("Loading nodes...")
    load_nodes(ckpt)
    logger.info("Loading base relationships...")
    load_relationships(ckpt)
    logger.info("Synthesizing INVOLVES edges...")
    load_involves(ckpt)
    logger.info("Synthesizing Campaign nodes + edges...")
    load_campaigns(ckpt)
    logger.info("Aliasing FIR date property...")
    alias_fir_date(ckpt)
    logger.info("Neo4j graph load complete.")
    return _graph_summary()
