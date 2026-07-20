"""
NEXUS Ingestion Orchestrator (CLI).

Usage:
    python -m backend.ingestion.run_ingest pg         # load PostgreSQL
    python -m backend.ingestion.run_ingest graph      # load Neo4j
    python -m backend.ingestion.run_ingest validate   # run validation report
    python -m backend.ingestion.run_ingest all        # pg -> graph -> validate

Flags:
    --drop        drop & recreate all Postgres tables before loading (pg/all)
    --no-resume   ignore checkpoints, reload everything
    --fresh-graph wipe the Neo4j graph before loading (graph/all)
"""
from __future__ import annotations

import argparse
import sys

from backend.ingestion.framework import logger


def _run_pg(args) -> int:
    from backend.ingestion import pg_loader
    summary = pg_loader.load_all(resume=not args.no_resume, drop=args.drop)
    logger.info("Postgres summary:")
    for table, n in summary.items():
        logger.info(f"  {table:28} {n:>8,}")
    return 0


def _run_graph(args) -> int:
    from backend.ingestion import graph_loader
    summary = graph_loader.load_all(resume=not args.no_resume, fresh=args.fresh_graph)
    logger.info("Graph summary:")
    for label, n in summary.items():
        logger.info(f"  {label:28} {n:>8,}")
    return 0


def _run_validate(args) -> int:
    from backend.ingestion import validate
    report = validate.run_all()
    return 0 if report.ok else 2


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="run_ingest", description="NEXUS ingestion pipeline")
    p.add_argument("command", choices=["pg", "graph", "validate", "all"])
    p.add_argument("--drop", action="store_true", help="drop & recreate Postgres tables")
    p.add_argument("--no-resume", action="store_true", help="ignore checkpoints")
    p.add_argument("--fresh-graph", action="store_true", help="wipe Neo4j before load")
    args = p.parse_args(argv)

    if args.command == "pg":
        return _run_pg(args)
    if args.command == "graph":
        return _run_graph(args)
    if args.command == "validate":
        return _run_validate(args)
    if args.command == "all":
        rc = _run_pg(args)
        if rc:
            return rc
        rc = _run_graph(args)
        if rc:
            return rc
        return _run_validate(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
