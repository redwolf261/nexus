# Notification Preferences Specification

## Overview
The `PreferenceEngine` (`backend/notification/preference_engine.py`) manages user quiet hours, channel muting, minimum priority thresholds, and digest modes.

## Mandatory Emergency Bypass Rule
Notifications with `PriorityLevel.CRITICAL` MUST NEVER be suppressed or delayed by quiet hours, digest modes, or channel muting preferences. They immediately dispatch across all available channels.
