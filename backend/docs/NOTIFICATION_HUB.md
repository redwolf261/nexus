# Notification Hub API Specification

## Overview
The Notification Hub API (`backend/api/routers/notification_hub.py`) exposes REST endpoints for stateful operational inbox management, digests, threads, reminders, bulk actions, and analytics.

## Endpoints
- `GET /api/notification-hub/inbox`
- `GET /api/notification-hub/thread/{id}`
- `GET /api/notification-hub/digests`
- `POST /api/notification-hub/digest/generate`
- `POST /api/notification-hub/archive`
- `POST /api/notification-hub/pin`
- `POST /api/notification-hub/star`
- `POST /api/notification-hub/bulk`
- `GET /api/notification-hub/analytics`
- `GET /api/notification-hub/reminders`
- `POST /api/notification-hub/reminder`
- `GET /api/notification-hub/search`
