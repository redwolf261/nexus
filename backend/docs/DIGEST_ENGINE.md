# Digest Engine Specification

## Overview
The `DigestEngine` (`backend/notification/digest_engine.py`) produces deterministic, reproducible operational digests for officers, supervisors, ACPs, and DCPs.

## Supported Digest Types
- `MORNING_DIGEST`, `EVENING_DIGEST`, `SHIFT_DIGEST`
- `DAILY_SUMMARY`, `WEEKLY_SUMMARY`
- `SUPERVISOR_DIGEST`, `ACP_DIGEST`, `DCP_DIGEST`

## Performance SLA Benchmark
- Digest generation latency: $<50 \text{ ms}$
