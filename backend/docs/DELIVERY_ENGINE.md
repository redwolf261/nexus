# Notification Delivery Engine Specification

## Overview
The `DeliveryEngine` (`backend/notification/delivery_engine.py`) provides idempotent multi-channel dispatch, channel execution, exponential retries, offline queueing, and duplicate delivery suppression.

## Exponential Retry Policy

$$\text{Backoff Delay (Sec)} = 2^{(\text{attempt} - 1)} \times \text{base\_delay}$$

- Max retries: 3 attempts.
- Offline queue: Failed or offline channel dispatches are enqueued into an offline queue for deferred delivery.

## Strict Idempotency
Dispatches track `(notification_id, recipient_id, channel)` cache keys to guarantee zero duplicate sends.
