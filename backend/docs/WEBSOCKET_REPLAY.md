# WebSocket Sequence Reconnect Replay Specification (Phase 8.3 Milestone 2)

## Overview

`ReplayService` maintains a 1,000-element circular buffer per district (`ReplayWindow`) to allow clients to catch up after network dropouts without page reloads.

## Replay Execution

1. Client reconnects and provides `client_last_sequence`.
2. `ReplayService.compute_replay(client_last_sequence)` identifies missed patches where `patch.sequence > client_last_sequence`.
3. If client sequence is older than the circular buffer capacity, sets `is_gap_detected = True`, signaling the client to perform a clean refresh.
4. Otherwise, returns `ReplayResponseDTO` with ordered missed patches. Response computed in <200ms.
