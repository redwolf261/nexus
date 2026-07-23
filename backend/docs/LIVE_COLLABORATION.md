# Live Collaboration & Presence Architecture (Phase 8.3 Milestone 2)

## Overview

`PresenceService` provides real-time awareness of active supervisors in the command workspace without pessimistic database locks.

## Principles

1. **Read-Only Awareness**: Supervisors can see who else is online and what cases/approvals they are inspecting.
2. **No Case Locking**: Investigations remain fully accessible and editable.
3. **Heartbeat Maintenance**: Active presence automatically expires if no heartbeat is received for 60 seconds.
