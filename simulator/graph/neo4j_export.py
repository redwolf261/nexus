"""
NEXUS Simulator — Neo4j CSV Exporter
Exports the knowledge graph as Neo4j Admin Import-ready CSV files:
  - nodes_persons.csv
  - nodes_firs.csv
  - nodes_vehicles.csv
  - nodes_gangs.csv
  - nodes_evidence.csv
  - nodes_stations.csv
  - nodes_officers.csv
  - relationships.csv
"""
from __future__ import annotations
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any

from simulator.graph.builder import CrimeKnowledgeGraph

logger = logging.getLogger(__name__)


def export_neo4j_csvs(graph: CrimeKnowledgeGraph, output_dir: Path) -> None:
    """Export graph nodes and relationships as Neo4j Admin Import CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Nodes: partition by type ───────────────────────────────────────────
    nodes_by_type: Dict[str, List[Dict]] = {}
    for node_id, props in graph.nodes.items():
        ntype = props.get("type", "Unknown")
        nodes_by_type.setdefault(ntype, []).append(props)

    for node_type, nodes in nodes_by_type.items():
        safe_name = node_type.lower().replace(" ", "_")
        path = output_dir / f"nodes_{safe_name}.csv"
        _write_nodes_csv(nodes, path, node_type)
        logger.info(f"  Wrote {len(nodes):,} {node_type} nodes -> {path.name}")

    # ── Relationships ──────────────────────────────────────────────────────
    rel_path = output_dir / "relationships.csv"
    _write_relationships_csv(graph.edges, rel_path)
    logger.info(f"  Wrote {len(graph.edges):,} relationships -> {rel_path.name}")

    # ── Summary ───────────────────────────────────────────────────────────
    summary_path = output_dir / "import_summary.txt"
    stats = graph.stats()
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("NEXUS Knowledge Graph — Neo4j Import Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total Nodes:       {stats['num_nodes']:,}\n")
        f.write(f"Total Edges:       {stats['num_edges']:,}\n\n")
        f.write("Node Breakdown:\n")
        for ntype, count in sorted(stats["node_types"].items()):
            f.write(f"  {ntype:<20} {count:>8,}\n")
        f.write("\nNeo4j Import Command:\n")
        f.write("  neo4j-admin database import full \\\n")
        for ntype in nodes_by_type:
            safe = ntype.lower().replace(" ", "_")
            f.write(f"    --nodes={ntype}=nodes_{safe}.csv \\\n")
        f.write("    --relationships=relationships.csv \\\n")
        f.write("    --overwrite-destination=true nexus\n")
    logger.info(f"  Import summary -> {summary_path.name}")


def _write_nodes_csv(nodes: List[Dict], path: Path, node_type: str) -> None:
    """Write node CSV in Neo4j admin import format."""
    if not nodes:
        return

    # Collect all unique keys
    all_keys = set()
    for n in nodes:
        all_keys.update(n.keys())
    all_keys.discard("type")

    # Neo4j header: :ID, :LABEL, then properties
    headers = [":ID", ":LABEL"] + sorted(all_keys - {"id"})

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for node in nodes:
            row = {":ID": node.get("id", ""), ":LABEL": node_type}
            for key in sorted(all_keys - {"id"}):
                val = node.get(key, "")
                # Serialize lists/dicts
                if isinstance(val, (list, dict)):
                    val = str(val)
                row[key] = val
            writer.writerow(row)


def _write_relationships_csv(edges: List[Dict], path: Path) -> None:
    """Write relationships CSV in Neo4j admin import format."""
    if not edges:
        return

    all_keys = set()
    for e in edges:
        all_keys.update(e.keys())
    all_keys -= {"source", "target", "relation"}

    headers = [":START_ID", ":END_ID", ":TYPE"] + sorted(all_keys)

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for edge in edges:
            row = {
                ":START_ID": edge.get("source", ""),
                ":END_ID": edge.get("target", ""),
                ":TYPE": edge.get("relation", "RELATED_TO"),
            }
            for key in sorted(all_keys):
                val = edge.get(key, "")
                if isinstance(val, (list, dict)):
                    val = str(val)
                row[key] = val
            writer.writerow(row)
