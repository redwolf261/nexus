"""Phase 8.2 (Milestone 1) schema migration — Officer Capability Foundation.

The NEXUS platform manages schema via SQLAlchemy `Base.metadata.create_all()`
plus idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements at app
startup (see backend/main.py). This script performs the same migration
standalone so it can be run explicitly against any environment:

    python -m backend.db.migrate_phase_8_2

It is idempotent: safe to run repeatedly. New tables are created via
create_all(); new columns on the pre-existing `officers` table are added via
additive ALTERs. Works on both PostgreSQL (production) and SQLite (tests/dev).

Note: PostgreSQL supports `ADD COLUMN IF NOT EXISTS`; SQLite (< 3.35) does not,
so on SQLite we detect existing columns via PRAGMA and skip present ones.
"""

from __future__ import annotations

import logging
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


# (column_name, DDL type + default) for additive migration on `officers`.
OFFICER_COLUMNS = [
    ("subdivision", "VARCHAR"),
    ("years_experience", "INTEGER"),
    ("maximum_capacity", "INTEGER DEFAULT 10"),
    ("availability_status", "VARCHAR DEFAULT 'ON_DUTY'"),
    ("current_case_count", "INTEGER DEFAULT 0"),
    ("current_task_count", "INTEGER DEFAULT 0"),
    ("leave_ends_on", "DATE"),
    ("capability_version", "INTEGER DEFAULT 1"),
]

BACKFILLS = [
    "UPDATE officers SET availability_status = 'ON_DUTY' WHERE availability_status IS NULL;",
    "UPDATE officers SET maximum_capacity = 10 WHERE maximum_capacity IS NULL;",
    "UPDATE officers SET current_case_count = 0 WHERE current_case_count IS NULL;",
    "UPDATE officers SET current_task_count = 0 WHERE current_task_count IS NULL;",
    "UPDATE officers SET years_experience = tenure_years "
    "WHERE years_experience IS NULL AND tenure_years IS NOT NULL;",
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_officers_availability ON officers(availability_status);",
    "CREATE INDEX IF NOT EXISTS idx_officers_subdivision ON officers(subdivision);",
]


def _existing_officer_columns(engine: Engine) -> set:
    insp = inspect(engine)
    if "officers" not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns("officers")}


def migrate(engine: Engine) -> dict:
    """Run the Phase 8.2 M1 migration. Returns a summary report."""
    from backend.db.schema import Base  # local import to avoid cycles

    dialect = engine.dialect.name
    report = {"dialect": dialect, "columns_added": [], "tables_created": [], "skipped": []}

    # 1. Create all new tables (officer_skills, officer_certifications, etc.)
    before = set(inspect(engine).get_table_names())
    Base.metadata.create_all(bind=engine)
    after = set(inspect(engine).get_table_names())
    report["tables_created"] = sorted(after - before)

    # 2. Additive columns on the existing `officers` table.
    existing = _existing_officer_columns(engine)
    with engine.begin() as conn:
        for name, ddl in OFFICER_COLUMNS:
            if name in existing:
                report["skipped"].append(name)
                continue
            if dialect == "postgresql":
                stmt = f"ALTER TABLE officers ADD COLUMN IF NOT EXISTS {name} {ddl};"
            else:
                # SQLite: no IF NOT EXISTS on ADD COLUMN; we already checked presence.
                stmt = f"ALTER TABLE officers ADD COLUMN {name} {ddl};"
            try:
                conn.execute(text(stmt))
                report["columns_added"].append(name)
            except Exception as e:  # pragma: no cover - defensive
                logger.warning("Column %s add failed: %s", name, e)
                report["skipped"].append(name)

        # 3. Indexes + backfills (idempotent)
        for stmt in INDEXES:
            try:
                conn.execute(text(stmt))
            except Exception as e:  # pragma: no cover
                logger.warning("Index step failed: %s", e)
        for stmt in BACKFILLS:
            try:
                conn.execute(text(stmt))
            except Exception as e:  # pragma: no cover
                logger.warning("Backfill step failed: %s", e)

    return report


def main() -> None:  # pragma: no cover - CLI entrypoint
    logging.basicConfig(level=logging.INFO)
    from backend.database import engine
    report = migrate(engine)
    logger.info("Phase 8.2 M1 migration complete: %s", report)
    print(report)


if __name__ == "__main__":  # pragma: no cover
    main()
