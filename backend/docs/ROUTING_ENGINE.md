# Notification Routing Engine Specification

## Overview
The `RoutingEngine` (`backend/notification/routing_engine.py`) determines recipient targets and active channels based on notification priority level and target parameters.

## Priority Level Channel Mappings

| Priority Level | Supported Channels |
|---|---|
| **CRITICAL** | In-app, WebSocket, Email, SMS, Push |
| **HIGH** | In-app, WebSocket, Email, Push |
| **MEDIUM** | In-app, WebSocket, Email |
| **LOW** | In-app, WebSocket |

## Recipient Resolution Hierarchy
1. **Individual Officer**: Direct username/user_id resolution.
2. **Role Groups**: Resolves roles to authority levels (`analyst`, `supervisor`, `acp`, `dcp`, `commissioner`).
3. **District Groups**: Resolves precincts or regional district groups.
