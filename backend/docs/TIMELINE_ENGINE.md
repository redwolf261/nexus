# Unified Investigation Timeline Engine (Phase 8.3 Milestone 3)

## Overview

`InvestigationTimelineService` merges events from Task Engine, Assignment Engine, Governance, Approvals, Evidence, Analytical discoveries, Investigation edits, Case notes, and Escalations into a single chronologically ordered timeline.

## Features

- **Deterministic Chronological Ordering**: Newest first for operational timelines.
- **Cursor Pagination**: Supports `cursor` and `limit` for high-performance timeline pagination (<50ms).
- **Category Filtering**: Filter timeline events by category (`TASK`, `ASSIGNMENT`, `ACTION`, `EVIDENCE`, `NOTE`).
