"""
Celery Tasks Package
====================
Scheduled and background tasks for ICFES Leveling.

Includes:
- scheduled.py: Celery beat scheduled tasks
  - regenerate_hearts: Hourly heart regeneration
  - process_weekly_leagues: Monday 00:00 league processing
  - send_streak_reminders: Daily streak reminder notifications
"""

from .scheduled import (
    celery_app,
    regenerate_hearts,
    process_weekly_leagues,
    send_streak_reminders,
)

__all__ = [
    "celery_app",
    "regenerate_hearts",
    "process_weekly_leagues",
    "send_streak_reminders",
]
