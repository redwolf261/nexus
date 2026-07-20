"""
NEXUS Ingestion — Post-load Validation Pipeline (Step 6).

Runs a battery of integrity checks against the loaded Postgres + Neo4j stores and
writes a human-readable report to docs/VALIDATION_REPORT.md. Hard failures
(orphans on declared FKs, duplicate PKs, row-count shortfalls) set report.ok=False
so the orchestrator can exit non-zero for CI.

Checks:
  1. Row parity      — each table count vs its source CSV unique-PK count
  2. FK integrity    — zero orphans on every hard FK declared in schema metadata
  3. Duplicate PKs   — none (DB enforces, but we assert for defense-in-depth)
  4. GPS sanity      — lat in [-90,90], lng in [-180,180], not (0,0)
  5. Timestamps      — declared date/datetime cols are non-blank where NOT NULL
  6. Campaign integ. — every firs.campaign_id resolves to a campaigns row
  7. Graph parity    — Neo4j node counts vs Postgres for shared ("both") entities
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from sqlalchemy import text

from backend.database import engine, Base
from backend.db import schema  # noqa: F401 — ensures all tables register on Base.metadata
from backend.ingestion import catalog
from backend.ingestion.framework import count_rows, stream_rows, logger, get_output_dir

REPORT_PATH = Path(__file__).resolve().parents[2] / "docs" / "VALIDATION_REPORT.md"


@dataclass
class Check:
    name: str
    category: str
    passed: bool
    hard: bool                 # hard failure flips report.ok
    detail: str = ""


@dataclass
class Report:
    checks: List[Check] = field(default_factory=list)

    def add(self, check: Check) -> None:
        self.checks.append(check)
        status = "PASS" if check.passed else ("FAIL" if check.hard else "WARN")
        logger.info(f"  [{status}] {check.category}: {check.name} — {check.detail}")

    @property
    def ok(self) -> bool:
        return all(c.passed or not c.hard for c in self.checks)

    @property
    def counts(self):
        p = sum(c.passed for c in self.checks)
        hard_fail = sum((not c.passed and c.hard) for c in self.checks)
        warn = sum((not c.passed and not c.hard) for c in self.checks)
        return p, hard_fail, warn
def _scalar(conn, sql: str, **params) -> int:
    return conn.execute(text(sql), params).scalar() or 0


# ── 1. Row parity ────────────────────────────────────────────────────────────
def check_row_parity(conn, report: Report) -> None:
    for ds in catalog.datasets_in_load_order():
        if not ds.table or ds.skip:
            continue
        db_count = _scalar(conn, f"SELECT count(*) FROM {ds.table}")
        # unique-PK count in the CSV (loader dedups within-batch on PK)
        if ds.pk:
            seen = set()
            for row in stream_rows(ds.csv):
                pk = row.get(ds.pk)
                if pk:
                    seen.add(pk)
            csv_count = len(seen)
        else:
            csv_count = count_rows(ds.csv)
        ok = db_count == csv_count
        report.add(Check(
            name=ds.table, category="row-parity", passed=ok, hard=ok is False and ds.pk is not None,
            detail=f"db={db_count:,} csv_unique={csv_count:,}"
                   + ("" if ok else f" (Δ={db_count - csv_count:+,})"),
        ))


# ── 2. FK integrity (hard FKs only, from schema metadata) ────────────────────
def check_fk_integrity(conn, report: Report) -> None:
    for table in Base.metadata.sorted_tables:
        for fk in table.foreign_keys:
            child_col = fk.parent.name
            parent_tbl = fk.column.table.name
            parent_col = fk.column.name
            # orphans: child value set but no matching parent
            orphans = _scalar(conn, f"""
                SELECT count(*) FROM {table.name} c
                WHERE c.{child_col} IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM {parent_tbl} p WHERE p.{parent_col} = c.{child_col}
                  )
            """)
            ok = orphans == 0
            report.add(Check(
                name=f"{table.name}.{child_col}→{parent_tbl}.{parent_col}",
                category="fk-integrity", passed=ok, hard=True,
                detail=f"{orphans:,} orphan(s)" if not ok else "0 orphans",
            ))


# ── 3. Duplicate PKs ─────────────────────────────────────────────────────────
def check_duplicate_pks(conn, report: Report) -> None:
    for table in Base.metadata.sorted_tables:
        pk_cols = [c.name for c in table.primary_key.columns]
        if not pk_cols:
            continue
        cols = ", ".join(pk_cols)
        dups = _scalar(conn, f"""
            SELECT count(*) FROM (
                SELECT {cols} FROM {table.name} GROUP BY {cols} HAVING count(*) > 1
            ) d
        """)
        ok = dups == 0
        report.add(Check(
            name=f"{table.name}({cols})", category="duplicate-pk",
            passed=ok, hard=True,
            detail=f"{dups:,} duplicate key group(s)" if not ok else "unique",
        ))
# ── 4. GPS sanity ────────────────────────────────────────────────────────────
def check_gps(conn, report: Report) -> None:
    for table in Base.metadata.sorted_tables:
        colnames = {c.name for c in table.columns}
        lat = next((c for c in ("lat", "latitude") if c in colnames), None)
        lng = next((c for c in ("lng", "lon", "longitude") if c in colnames), None)
        if not (lat and lng):
            continue
        bad = _scalar(conn, f"""
            SELECT count(*) FROM {table.name}
            WHERE {lat} IS NOT NULL AND {lng} IS NOT NULL AND (
                {lat} NOT BETWEEN -90 AND 90 OR
                {lng} NOT BETWEEN -180 AND 180 OR
                ({lat} = 0 AND {lng} = 0)
            )
        """)
        ok = bad == 0
        report.add(Check(
            name=f"{table.name}({lat},{lng})", category="gps-sanity",
            passed=ok, hard=False,
            detail=f"{bad:,} out-of-range/null-island row(s)" if not ok else "all valid",
        ))


# ── 5. Timestamp presence on NOT NULL date/datetime cols ─────────────────────
def check_timestamps(conn, report: Report) -> None:
    from sqlalchemy import Date, DateTime
    for table in Base.metadata.sorted_tables:
        for col in table.columns:
            if not isinstance(col.type, (Date, DateTime)) or col.nullable:
                continue
            blanks = _scalar(conn, f"SELECT count(*) FROM {table.name} WHERE {col.name} IS NULL")
            ok = blanks == 0
            report.add(Check(
                name=f"{table.name}.{col.name}", category="timestamp",
                passed=ok, hard=False,
                detail=f"{blanks:,} null in NOT NULL col" if not ok else "populated",
            ))


# ── 6. Campaign integrity ────────────────────────────────────────────────────
def check_campaign_integrity(conn, report: Report) -> None:
    cols = {c.name for c in Base.metadata.tables["firs"].columns}
    if "campaign_id" not in cols:
        return
    orphans = _scalar(conn, """
        SELECT count(*) FROM firs f
        WHERE f.campaign_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM campaigns c WHERE c.campaign_id = f.campaign_id)
    """)
    ok = orphans == 0
    report.add(Check(
        name="firs.campaign_id→campaigns", category="campaign-integrity",
        passed=ok, hard=True,
        detail=f"{orphans:,} FIR(s) reference missing campaign" if not ok else "all resolve",
    ))


# ── 7. Graph parity (Neo4j node counts vs Postgres for shared entities) ──────
GRAPH_LABEL_FOR_TABLE = {
    "persons": "Person", "vehicles": "Vehicle", "phones": "Phone", "firs": "FIR",
    "officers": "Officer", "gangs": "Gang", "districts": "District",
    "evidence": "Evidence", "stations": "Station", "campaigns": "Campaign",
}


def check_graph_parity(conn, report: Report) -> None:
    try:
        from backend.neo4j_client import neo4j_client
    except Exception as e:
        report.add(Check(name="neo4j-connection", category="graph-parity",
                         passed=False, hard=False, detail=f"skipped: {e}"))
        return
    for ds in catalog.datasets_in_load_order():
        if ds.store != "both" or not ds.table:
            continue
        label = GRAPH_LABEL_FOR_TABLE.get(ds.table)
        if not label:
            continue
        pg = _scalar(conn, f"SELECT count(*) FROM {ds.table}")
        try:
            rec = neo4j_client.query(f"MATCH (n:{label}) RETURN count(n) AS c")
            graph = rec[0]["c"] if rec else 0
        except Exception as e:
            report.add(Check(name=f"{label}", category="graph-parity",
                             passed=False, hard=False, detail=f"query failed: {e}"))
            continue
        # Person is a superset in graph (criminals are also :Person); allow graph >= pg.
        ok = graph == pg if label != "Person" else graph >= pg
        report.add(Check(
            name=f"(:{label}) vs {ds.table}", category="graph-parity",
            passed=ok, hard=False,
            detail=f"graph={graph:,} pg={pg:,}",
        ))
# ── Report writer ────────────────────────────────────────────────────────────
def write_report(report: Report) -> None:
    passed, hard_fail, warn = report.counts
    lines = [
        "# NEXUS Ingestion — Validation Report",
        "",
        f"**Status:** {'PASS' if report.ok else 'FAIL'}  ",
        f"**Checks:** {passed} passed · {hard_fail} hard-fail · {warn} warning",
        "",
        "> Generated by `python -m backend.ingestion.run_ingest validate`. "
        "Hard failures block CI; warnings are expected for soft-referenced telemetry "
        "and known simulator quirks (see notes).",
        "",
    ]
    by_cat: dict = {}
    for c in report.checks:
        by_cat.setdefault(c.category, []).append(c)

    for cat, checks in by_cat.items():
        lines.append(f"## {cat}")
        lines.append("")
        lines.append("| Check | Result | Detail |")
        lines.append("|---|---|---|")
        for c in checks:
            mark = "PASS" if c.passed else ("**FAIL**" if c.hard else "WARN")
            lines.append(f"| {c.name} | {mark} | {c.detail} |")
        lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Validation report written to {REPORT_PATH}")


def run_all() -> Report:
    report = Report()
    logger.info("Running validation checks...")
    with engine.connect() as conn:
        check_row_parity(conn, report)
        check_fk_integrity(conn, report)
        check_duplicate_pks(conn, report)
        check_gps(conn, report)
        check_timestamps(conn, report)
        check_campaign_integrity(conn, report)
        check_graph_parity(conn, report)
    write_report(report)
    passed, hard_fail, warn = report.counts
    logger.info(f"Validation complete: {passed} passed, {hard_fail} hard-fail, {warn} warn "
                f"→ {'OK' if report.ok else 'FAILURES PRESENT'}")
    return report



