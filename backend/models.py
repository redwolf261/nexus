"""
Backward-compatibility shim.

The full data-layer schema now lives in `backend/db/schema.py`. The API and
repository layers import Person / Vehicle / FIR from here, so this module
re-exports them unchanged. All three retain their original table names and
columns (extended, never broken).
"""
from backend.db.schema import Person, Vehicle, FIR  # noqa: F401

__all__ = ["Person", "Vehicle", "FIR"]
