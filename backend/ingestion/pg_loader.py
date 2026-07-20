"""
NEXUS PostgreSQL Loader.

Loads every catalogued CSV into Postgres in topological order using:
  - generic type coercion driven by each column's SQLAlchemy type
  - batched INSERT ... ON CONFLICT (pk) DO UPDATE (idempotent upsert)
  - per-batch transactions (a bad batch rolls back alone, load continues)
  - junction-table expansion from pipe-delimited columns
  - circular-FK backfill (criminals.gang_id set after gangs load)
  - checkpoint-based resume

Run via: python -m backend.ingestion.run_ingest pg
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Date, Float, Integer, Numeric, inspect as sa_inspect
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.database import engine, Base
from backend.db import schema  # noqa: F401 — registers all tables on Base.metadata
from backend.ingestion import catalog
from backend.ingestion.framework import (
    Checkpoint, Progress, batched, count_rows, logger, stream_rows, with_retry,
)

BATCH_SIZE = 2000

_TRUE = {"true", "1", "yes", "y", "t"}
_FALSE = {"false", "0", "no", "n", "f"}


# ── Type coercion ───────────────────────────────────────────────────────────
def _coerce(value: Optional[str], py_type: type) -> Any:
    if value is None:
        return None
    v = value.strip()
    if v == "":
        return None
    try:
        if py_type is bool:
            low = v.lower()
            if low in _TRUE:
                return True
            if low in _FALSE:
                return False
            return None
        if py_type is int:
            return int(float(v))  # handles "3.0"
        if py_type is float:
            return float(v)
        if py_type is dt.date:
            return _parse_date(v)
    except (ValueError, TypeError):
        return None
    return v  # str / text / numeric-as-str


def _parse_date(v: str) -> Optional[dt.date]:
    # Take the date part of an ISO datetime if present.
    head = v.split("T")[0].split(" ")[0]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return dt.datetime.strptime(head, fmt).date()
        except ValueError:
            continue
    return None


def _column_py_types(table) -> Dict[str, type]:
    """Map column name -> python type used for coercion."""
    out: Dict[str, type] = {}
    for col in table.columns:
        t = col.type
        if isinstance(t, Boolean):
            out[col.name] = bool
        elif isinstance(t, Integer):
            out[col.name] = int
        elif isinstance(t, Float):
            out[col.name] = float
        elif isinstance(t, Date):
            out[col.name] = dt.date
        elif isinstance(t, Numeric):
            out[col.name] = str  # keep precision; Postgres casts str->numeric
        else:
            out[col.name] = str
    return out


# ── CSV column -> table column mapping ──────────────────────────────────────
# A few CSVs use column names that differ from the model attribute. Only real
# divergences need entries; everything else maps by identical name.
COLUMN_ALIASES: Dict[str, Dict[str, str]] = {
    "campaigns": {},   # ground_truth_campaigns headers already match model
    "masterminds": {},
}


def _row_to_record(row: Dict[str, Optional[str]], table, py_types: Dict[str, type],
                   aliases: Dict[str, str]) -> Dict[str, Any]:
    valid_cols = set(py_types.keys())
    rec: Dict[str, Any] = {}
    for csv_key, raw in row.items():
        col = aliases.get(csv_key, csv_key)
        if col in valid_cols:
            rec[col] = _coerce(raw, py_types[col])
    return rec


# ── Upsert ──────────────────────────────────────────────────────────────────
def _upsert_batch(conn, table, records: List[Dict[str, Any]]) -> None:
    if not records:
        return
    pk_cols = [c.name for c in table.primary_key.columns]
    stmt = pg_insert(table).values(records)
    # Autoincrement synthetic PKs (social_network, entity_resolution): plain insert.
    autoincrement = (len(pk_cols) == 1 and isinstance(table.c[pk_cols[0]].type, Integer)
                     and pk_cols[0] not in records[0])
    if autoincrement:
        conn.execute(table.insert().values(records))
        return
    update_cols = {c.name: stmt.excluded[c.name]
                   for c in table.columns if c.name not in pk_cols}
    if update_cols:
        stmt = stmt.on_conflict_do_update(index_elements=pk_cols, set_=update_cols)
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=pk_cols)
    conn.execute(stmt)


def _load_one(ds: catalog.Dataset) -> int:
    table = Base.metadata.tables[ds.table]
    py_types = _column_py_types(table)
    aliases = COLUMN_ALIASES.get(ds.table, {})
    total = count_rows(ds.csv)
    prog = Progress(ds.table, total)
    loaded = 0

    for chunk in batched(stream_rows(ds.csv), BATCH_SIZE):
        records = [_row_to_record(r, table, py_types, aliases) for r in chunk]
        records = [r for r in records if r]  # drop empties
        if not records:
            prog.advance(len(chunk))
            continue

        # Deduplicate within-batch on PK (last wins) to avoid ON CONFLICT
        # "row affected twice" errors when a CSV repeats a key.
        pk_cols = [c.name for c in table.primary_key.columns]
        if pk_cols and not (len(pk_cols) == 1 and pk_cols[0] not in records[0]):
            seen: Dict[tuple, Dict[str, Any]] = {}
            for r in records:
                key = tuple(r.get(pc) for pc in pk_cols)
                seen[key] = r
            records = list(seen.values())

        def _txn():
            with engine.begin() as conn:
                _upsert_batch(conn, table, records)

        with_retry(_txn, what=f"{ds.table} batch")
        loaded += len(records)
        prog.advance(len(chunk))

    return loaded


# ── Junction expansion ──────────────────────────────────────────────────────
def _load_junction(j: catalog.Junction) -> int:
    table = Base.metadata.tables[j.table]
    pairs: List[Dict[str, str]] = []
    seen = set()
    for row in stream_rows(j.source_csv):
        parent = row.get(j.parent_key)
        raw_list = row.get(j.list_column)
        if not parent or not raw_list:
            continue
        for token in raw_list.split("|"):
            child = token.strip()
            if not child:
                continue
            key = (parent, child)
            if key in seen:
                continue
            seen.add(key)
            pairs.append({j.left_col: parent, j.right_col: child})

    loaded = 0
    for chunk in batched(iter(pairs), BATCH_SIZE):
        def _txn():
            with engine.begin() as conn:
                stmt = pg_insert(table).values(chunk).on_conflict_do_nothing()
                conn.execute(stmt)
        with_retry(_txn, what=f"{j.table} batch")
        loaded += len(chunk)
    logger.info(f"    {j.table}: {loaded:,} edges")
    return loaded


# ── Circular FK backfill ────────────────────────────────────────────────────
def _backfill_criminal_gang() -> int:
    """
    criminals.gang_id was loaded from the CSV, but if criminals loaded before
    gangs existed the value is still valid (it's just a string FK with use_alter).
    Re-affirm it from the gang_members junction so membership and the scalar FK
    agree even if the CSV column was blank. Only sets rows where gang_id is NULL.
    """
    from sqlalchemy import text
    sql = text("""
        UPDATE criminals c
        SET gang_id = gm.gang_id
        FROM gang_members gm
        WHERE gm.criminal_id = c.criminal_id
          AND c.gang_id IS NULL
    """)
    with engine.begin() as conn:
        result = conn.execute(sql)
        return result.rowcount or 0


# ── Public entrypoints ──────────────────────────────────────────────────────
def create_schema(drop: bool = False) -> None:
    if drop:
        logger.info("Dropping all tables (CASCADE) ...")
        # CASCADE clears any leftover constraints/objects from prior runs that
        # would otherwise block an ordered drop_all.
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
    logger.info("Creating schema (create_all) ...")
    Base.metadata.create_all(bind=engine)
    insp = sa_inspect(engine)
    logger.info(f"Schema ready — {len(insp.get_table_names())} tables present.")


def load_all(resume: bool = True, drop: bool = False) -> Dict[str, int]:
    create_schema(drop=drop)
    cp = Checkpoint(namespace="postgres")
    if not resume or drop:
        cp.reset()

    summary: Dict[str, int] = {}
    logger.info("=" * 60)
    logger.info("POSTGRES INGESTION")
    logger.info("=" * 60)

    for ds in catalog.datasets_in_load_order():
        if cp.is_done(ds.table):
            logger.info(f"  [skip] {ds.table} (checkpoint)")
            continue
        logger.info(f"  Loading {ds.table}  <- {ds.csv}")
        n = _load_one(ds)
        summary[ds.table] = n
        cp.mark_done(ds.table, rows=n)

    # Junctions after their parents
    logger.info("  Expanding junction tables ...")
    for j in catalog.JUNCTIONS:
        if cp.is_done(f"junction:{j.table}"):
            logger.info(f"  [skip] {j.table} (checkpoint)")
            continue
        n = _load_junction(j)
        summary[j.table] = n
        cp.mark_done(f"junction:{j.table}", rows=n)

    # Circular FK backfill
    if not cp.is_done("backfill:criminal_gang"):
        n = _backfill_criminal_gang()
        logger.info(f"  Backfilled criminals.gang_id: {n:,} rows")
        cp.mark_done("backfill:criminal_gang", rows=n)

    logger.info("-" * 60)
    logger.info(f"Postgres load complete — {sum(summary.values()):,} rows across "
                f"{len(summary)} tables.")
    return summary
