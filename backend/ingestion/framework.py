"""
NEXUS Ingestion — Shared Framework

Reusable primitives for both the Postgres and Neo4j loaders:
  - CSV streaming (chunked; never loads a 154K-row file fully into memory)
  - BOM-safe header cleaning and empty-string -> None normalization
  - retry with exponential backoff on transient errors
  - a JSON checkpoint store for resume-after-failure
  - structured logging + a lightweight progress reporter
"""
from __future__ import annotations

import csv
import json
import logging
import os
import time
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, TypeVar

logger = logging.getLogger("nexus.ingest")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%H:%M:%S"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)

# output/ dir (repo_root/output)
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"
CHECKPOINT_PATH = OUTPUT_DIR / ".ingest_state.json"

T = TypeVar("T")


# ── CSV streaming ───────────────────────────────────────────────────────────
def _clean_key(key: str) -> str:
    return key.lstrip("﻿").strip()


def count_rows(csv_name: str) -> int:
    """Fast data-row count (excludes header). Returns 0 if file missing."""
    path = OUTPUT_DIR / csv_name
    if not path.exists():
        return 0
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def stream_rows(csv_name: str) -> Iterator[Dict[str, Optional[str]]]:
    """
    Yield each CSV row as a dict with cleaned keys and "" -> None.
    Streams line by line — safe for very large files.
    """
    path = OUTPUT_DIR / csv_name
    if not path.exists():
        logger.warning(f"  CSV not found: {csv_name}")
        return
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        reader.fieldnames = [_clean_key(f) for f in (reader.fieldnames or [])]
        for raw in reader:
            yield {_clean_key(k): (v if v not in ("", None) else None) for k, v in raw.items()}


def batched(iterable: Iterator[T], size: int) -> Iterator[List[T]]:
    """Group an iterator into lists of at most `size`."""
    batch: List[T] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


# ── Retry ───────────────────────────────────────────────────────────────────
def with_retry(fn: Callable[[], T], *, attempts: int = 4, base_delay: float = 0.5,
               what: str = "operation") -> T:
    """
    Call fn(), retrying on any exception with exponential backoff.
    Raises the last exception if all attempts fail.
    """
    last: Optional[BaseException] = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - deliberately broad; DB/driver transient errors
            last = e
            if attempt == attempts:
                break
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(f"  {what} failed (attempt {attempt}/{attempts}): "
                           f"{type(e).__name__}: {str(e)[:120]} — retrying in {delay:.1f}s")
            time.sleep(delay)
    assert last is not None
    raise last


# ── Checkpoint store (resume) ───────────────────────────────────────────────
class Checkpoint:
    """
    Tiny JSON-backed progress store. Records which tables/steps have completed
    so a re-run can skip them. Because all writes are idempotent (upsert/MERGE),
    the checkpoint is an optimization, not a correctness requirement.
    """

    def __init__(self, path: Path = CHECKPOINT_PATH, namespace: str = "default"):
        self.path = path
        self.namespace = namespace
        self._state: Dict[str, Dict] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._state = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._state = {}
        self._state.setdefault(self.namespace, {})

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._state, indent=2), encoding="utf-8")

    def is_done(self, step: str) -> bool:
        return bool(self._state.get(self.namespace, {}).get(step, {}).get("done"))

    def mark_done(self, step: str, **meta) -> None:
        self._state.setdefault(self.namespace, {})[step] = {"done": True, **meta}
        self._save()

    def reset(self) -> None:
        self._state[self.namespace] = {}
        self._save()


# ── Progress reporter ───────────────────────────────────────────────────────
class Progress:
    """Logs incremental progress for a single dataset load."""

    def __init__(self, label: str, total: int):
        self.label = label
        self.total = total
        self.done = 0
        self._last_pct = -1

    def advance(self, n: int) -> None:
        self.done += n
        if self.total <= 0:
            return
        pct = int(self.done * 100 / self.total)
        # log every ~20% to keep output readable for big tables
        if pct >= self._last_pct + 20 or self.done >= self.total:
            logger.info(f"    {self.label}: {self.done:,}/{self.total:,} ({pct}%)")
            self._last_pct = pct


def get_output_dir() -> Path:
    return OUTPUT_DIR
