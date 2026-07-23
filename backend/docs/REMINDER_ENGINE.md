# Reminder Engine Specification

## Overview
The `ReminderEngine` (`backend/notification/reminder_engine.py`) evaluates escalating reminder intervals, maximum retry bounds, and mandatory suppression.

## Escalating Interval Formula

$$\text{Reminder Delay (Minutes)} = 2^{\text{reminder\_count}} \times \text{base\_interval}$$

## Suppression Rules
Reminders are automatically suppressed if:
1. Notification is in state `ACKNOWLEDGED`, `EXPIRED`, or `CANCELLED`.
2. Notification has explicit `acknowledged_at` or `dismissed_at` timestamps.
3. Maximum retry limit (`max_reminders`) is reached.
