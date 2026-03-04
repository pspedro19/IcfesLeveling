"""
Offline Features Models - DEPRECATED
=====================================
This module is DEPRECATED. All models have been consolidated into mobile_offline.py
which provides a more complete implementation with additional features:

- StreakFreeze
- UserLeagueHistory
- DailyChallenge / UserDailyChallenge
- NotificationHistory
- color field on LeagueDivision

Please import from mobile_offline instead:
    from ..models.mobile_offline import (
        UserQuestionHistory,
        UserTopicMastery,
        PendingAnswerSync,
        HeartTransaction,
        UserDailyActivity,
        LeagueDivision,
        LeagueWeek,
        LeagueGroup,
        UserLeague,
        UserDeviceToken,
        # Additional models not in this file:
        StreakFreeze,
        UserLeagueHistory,
        DailyChallenge,
        UserDailyChallenge,
        NotificationHistory,
    )

This file will be removed in a future version.
"""

import warnings

warnings.warn(
    "offline_features module is deprecated. Import from mobile_offline instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from mobile_offline for backwards compatibility
from .mobile_offline import (
    UserQuestionHistory,
    UserTopicMastery,
    PendingAnswerSync,
    HeartTransaction,
    UserDailyActivity,
    LeagueDivision,
    LeagueWeek,
    LeagueGroup,
    UserLeague,
    UserDeviceToken,
)

__all__ = [
    "UserQuestionHistory",
    "UserTopicMastery",
    "PendingAnswerSync",
    "HeartTransaction",
    "UserDailyActivity",
    "LeagueDivision",
    "LeagueWeek",
    "LeagueGroup",
    "UserLeague",
    "UserDeviceToken",
]
