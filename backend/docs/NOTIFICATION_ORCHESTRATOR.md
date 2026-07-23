# Notification Orchestrator Architecture

## Overview
The `NotificationOrchestrator` (`backend/notification/orchestrator.py`) handles event batching, deduplication windowing, replay safety, and multi-entity routing without random generators or background cron dependencies.

## Deduplication Strategy & Replay Safety

$$\text{Dedup Hash} = \text{SHA256}(\text{event\_type} \parallel \text{source\_entity\_type} \parallel \text{source\_entity\_id} \parallel \text{recipient\_id} \parallel \text{title})$$

- Sliding window: 60 seconds deduplication suppression.
- Replay safety: Processing identical event replay streams produces exact deterministic aggregate records without duplicate sends.
