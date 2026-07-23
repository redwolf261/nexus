# Threading Engine Specification

## Overview
The `ThreadEngine` (`backend/notification/thread_engine.py`) groups related operational notifications by entity context (`INVESTIGATION`, `APPROVAL`, `ASSIGNMENT`, `ESCALATION`, `TASK`).

## Key Features
- Chronological ordering (oldest to newest).
- Cursor-based pagination.
- Unread count per thread.
- Performance SLA: Thread generation $<20 \text{ ms}$.
