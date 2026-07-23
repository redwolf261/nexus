# Notification Engine Architecture

## Overview
The `NotificationService` and `NotificationAggregate` (`backend/notification/`) form the operational communication backbone of the NEXUS platform.

## Notification Lifecycle States
- `CREATED`: Initial creation and recipient resolution.
- `QUEUED`: Enqueued for dispatch processing.
- `DISPATCHED`: Sent across active channels.
- `DELIVERED`: Confirmed delivery at target channels.
- `ACKNOWLEDGED`: Explicitly acknowledged by recipient user.
- `FAILED`: Delivery attempt exhausted or failed.
- `EXPIRED`: Unacknowledged notification past SLA deadline.
- `CANCELLED`: Cancelled by system or supervisor.

## Performance SLA Benchmarks
- Creation latency: $<10 \text{ ms}$
- Routing latency: $<5 \text{ ms}$
- Dispatch latency: $<15 \text{ ms}$
- Acknowledgement latency: $<5 \text{ ms}$
- Unread query latency: $<20 \text{ ms}$
