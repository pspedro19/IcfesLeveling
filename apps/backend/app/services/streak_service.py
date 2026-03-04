"""
Streak Service - Timezone-aware streak management
ICFES Leveling Mobile App

Features:
- 4 AM local time cutoff for day transitions
- Streak multipliers based on days
- Streak repair within 24h window
- Daily XP tracking
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Tuple
from uuid import UUID
import logging

from ..models import User, UserDailyActivity, StreakFreeze

logger = logging.getLogger(__name__)


class StreakService:
    """Service for timezone-aware streak management"""

    # Daily cutoff time (4:00 AM local time)
    DAILY_CUTOFF = time(4, 0, 0)

    # Default timezone
    DEFAULT_TIMEZONE = "America/Bogota"

    # Minimum XP required to count towards streak
    MIN_XP_FOR_STREAK = 20

    # XP multipliers based on streak days (aligned with GameEngineService source of truth)
    # 7 days: 1.2x, 14 days: 1.5x, 30+ days: 2.0x
    STREAK_MULTIPLIERS = {
        (1, 6): 1.0,
        (7, 13): 1.2,
        (14, 29): 1.5,
        (30, float('inf')): 2.0
    }

    # Streak freeze costs
    FREEZE_GOLD_COST = 200
    MAX_FREEZES = 5

    # Streak repair costs
    REPAIR_GOLD_COST = 300
    MAX_AD_REPAIRS_PER_DAY = 1

    # Repair window in hours
    REPAIR_WINDOW_HOURS = 24

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def get_current_streak_day(user_timezone: str = None) -> date:
        """
        Get the current day for streaks.
        Day changes at 4:00 AM local time.
        This protects night owls who study late.

        Args:
            user_timezone: User's timezone string (e.g., "America/Bogota")

        Returns:
            date: The current streak day
        """
        timezone = user_timezone or StreakService.DEFAULT_TIMEZONE
        try:
            tz = ZoneInfo(timezone)
        except Exception:
            logger.warning(f"Invalid timezone: {timezone}, using default")
            tz = ZoneInfo(StreakService.DEFAULT_TIMEZONE)

        now = datetime.now(tz)

        if now.time() < StreakService.DAILY_CUTOFF:
            # Before 4 AM, still counts as yesterday
            return (now - timedelta(days=1)).date()
        return now.date()

    @staticmethod
    def get_day_reset_time(user_timezone: str = None) -> str:
        """Get the daily reset time string"""
        return "04:00"

    def get_streak_multiplier(self, streak_days: int) -> float:
        """
        Get XP multiplier based on streak days.

        Multipliers (aligned with GameEngineService source of truth):
        - 1-6 days: 1.0x
        - 7-13 days: 1.2x
        - 14-29 days: 1.5x
        - 30+ days: 2.0x

        Args:
            streak_days: Current streak length

        Returns:
            float: XP multiplier
        """
        for (min_days, max_days), multiplier in self.STREAK_MULTIPLIERS.items():
            if min_days <= streak_days <= max_days:
                return multiplier
        return 1.0

    def check_and_update_streak(
        self,
        user_id: UUID,
        xp_earned: int
    ) -> dict:
        """
        Check and update user's streak based on activity.

        Args:
            user_id: User's UUID
            xp_earned: XP earned from activity

        Returns:
            dict with:
            - extended: bool
            - current: int (current streak)
            - previous: int (previous streak if lost)
            - lost: bool
            - today_xp: int
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Get user's timezone
        user_timezone = getattr(user, 'timezone', self.DEFAULT_TIMEZONE) or self.DEFAULT_TIMEZONE
        current_day = self.get_current_streak_day(user_timezone)

        # Get last activity date
        last_activity_day = getattr(user, 'last_activity_date', None)

        # Get or create daily activity
        activity = self.db.query(UserDailyActivity).filter(
            UserDailyActivity.user_id == user_id,
            UserDailyActivity.activity_date == current_day
        ).first()

        if not activity:
            activity = UserDailyActivity(
                user_id=user_id,
                activity_date=current_day,
                first_session_at=datetime.utcnow()
            )
            self.db.add(activity)
            self.db.flush()

        # If already practiced today, just accumulate XP
        if last_activity_day == current_day:
            activity.xp_earned = (activity.xp_earned or 0) + xp_earned
            activity.last_session_at = datetime.utcnow()
            self.db.commit()

            return {
                "extended": False,
                "current": getattr(user, 'current_streak', 0) or 0,
                "today_xp": activity.xp_earned
            }

        # Calculate days difference
        days_diff = (current_day - last_activity_day).days if last_activity_day else 999

        extended = False
        lost = False
        previous_streak = 0

        if days_diff == 1:
            # Consecutive day - extend streak
            current_streak = (getattr(user, 'current_streak', 0) or 0) + 1
            user.current_streak = current_streak
            user.longest_streak = max(
                getattr(user, 'longest_streak', 0) or 0,
                current_streak
            )
            extended = True
        elif days_diff > 1:
            # Lost the streak
            previous_streak = getattr(user, 'current_streak', 0) or 0

            # Store previous streak for potential repair
            if not hasattr(user, 'previous_streak'):
                # Field might not exist, just track in activity
                pass
            else:
                user.previous_streak = previous_streak

            # Mark when streak was lost
            if not hasattr(user, 'streak_lost_at'):
                pass
            else:
                user.streak_lost_at = datetime.utcnow()

            user.current_streak = 1
            lost = True
        else:
            # Same day or first activity
            if getattr(user, 'current_streak', 0) == 0:
                user.current_streak = 1

        # Update last activity date
        user.last_activity_date = current_day

        # Update daily activity
        activity.xp_earned = xp_earned
        activity.last_session_at = datetime.utcnow()

        if extended:
            activity.streak_extended = True

        self.db.commit()

        return {
            "extended": extended,
            "current": getattr(user, 'current_streak', 1),
            "previous": previous_streak,
            "lost": lost,
            "today_xp": activity.xp_earned
        }

    def get_streak_status(self, user_id: UUID) -> dict:
        """
        Get comprehensive streak status for user.

        Returns dict with:
        - current: int
        - longest: int
        - today_xp: int
        - daily_goal: int
        - goal_met: bool
        - last_activity_date: date | None
        - freezes_available: int
        - at_risk: bool
        - day_resets_at: str (e.g., "04:00")
        - timezone: str
        - multiplier: float (1.0, 1.2, 1.5, 2.0)
        - can_repair: bool
        - repair_window_ends_at: datetime | None
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        user_timezone = getattr(user, 'timezone', self.DEFAULT_TIMEZONE) or self.DEFAULT_TIMEZONE
        current_day = self.get_current_streak_day(user_timezone)

        # Get today's activity
        today_activity = self.db.query(UserDailyActivity).filter(
            UserDailyActivity.user_id == user_id,
            UserDailyActivity.activity_date == current_day
        ).first()

        # Count available freezes (check User.streak_freeze_count first, then StreakFreeze table)
        user_freeze_count = getattr(user, 'streak_freeze_count', 0) or 0
        if user_freeze_count > 0:
            freezes = user_freeze_count
        else:
            # Fallback to StreakFreeze table for legacy support
            freezes = self.db.query(StreakFreeze).filter(
                StreakFreeze.user_id == user_id,
                StreakFreeze.is_used == False,
                or_(
                    StreakFreeze.expires_at == None,
                    StreakFreeze.expires_at > datetime.utcnow()
                )
            ).count()

        current_streak = getattr(user, 'current_streak', 0) or 0
        last_activity = getattr(user, 'last_activity_date', None)
        daily_goal = getattr(user, 'daily_goal_xp', 20) or 20

        # Check if at risk (hasn't practiced today and has streak)
        at_risk = current_streak > 0 and last_activity != current_day

        # Get multiplier
        multiplier = self.get_streak_multiplier(current_streak)

        # Check if can repair streak
        can_repair = False
        repair_window_ends_at = None
        streak_lost_at = getattr(user, 'streak_lost_at', None)

        if streak_lost_at:
            hours_since_lost = (datetime.utcnow() - streak_lost_at).total_seconds() / 3600
            if hours_since_lost <= self.REPAIR_WINDOW_HOURS:
                can_repair = True
                repair_window_ends_at = streak_lost_at + timedelta(hours=self.REPAIR_WINDOW_HOURS)

        return {
            "current": current_streak,
            "longest": getattr(user, 'longest_streak', 0) or 0,
            "today_xp": today_activity.xp_earned if today_activity else 0,
            "daily_goal": daily_goal,
            "goal_met": today_activity.daily_goal_met if today_activity else False,
            "last_activity_date": last_activity,
            "freezes_available": freezes,
            "at_risk": at_risk,
            "day_resets_at": self.get_day_reset_time(user_timezone),
            "timezone": user_timezone,
            "multiplier": multiplier,
            "can_repair": can_repair,
            "repair_window_ends_at": repair_window_ends_at
        }

    def repair_streak(
        self,
        user_id: UUID,
        method: str  # "gold" or "ad"
    ) -> dict:
        """
        Repair a lost streak within 24h window.

        Args:
            user_id: User's UUID
            method: "gold" (costs 300) or "ad" (1 per day)

        Returns:
            dict with:
            - streak_repaired: bool
            - current_streak: int
            - gold_remaining: int | None (if method=gold)

        Raises:
            ValueError with codes:
            - NO_STREAK_TO_REPAIR
            - STREAK_REPAIR_EXPIRED
            - AD_REPAIR_USED
            - NOT_ENOUGH_GOLD
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Check if there's a streak to repair
        streak_lost_at = getattr(user, 'streak_lost_at', None)
        previous_streak = getattr(user, 'previous_streak', 0) or 0

        if not streak_lost_at or previous_streak == 0:
            raise ValueError("NO_STREAK_TO_REPAIR")

        # Check if within 24h window
        hours_since_lost = (datetime.utcnow() - streak_lost_at).total_seconds() / 3600
        if hours_since_lost > self.REPAIR_WINDOW_HOURS:
            raise ValueError("STREAK_REPAIR_EXPIRED")

        # Handle payment method
        gold_remaining = None

        if method == "gold":
            # Use gold field (primary currency per spec), fallback to orbs
            current_gold = getattr(user, 'gold', None)
            if current_gold is None:
                current_gold = getattr(user, 'orbs', 0) or 0

            if current_gold < self.REPAIR_GOLD_COST:
                raise ValueError("NOT_ENOUGH_GOLD")

            # Deduct from gold (primary) or orbs (fallback)
            if hasattr(user, 'gold') and user.gold is not None:
                user.gold = current_gold - self.REPAIR_GOLD_COST
                gold_remaining = user.gold
            else:
                user.orbs = current_gold - self.REPAIR_GOLD_COST
                gold_remaining = user.orbs

        elif method == "ad":
            # Check if ad repair already used today
            ad_repairs_today = getattr(user, 'ad_repairs_today', 0) or 0
            if ad_repairs_today >= self.MAX_AD_REPAIRS_PER_DAY:
                raise ValueError("AD_REPAIR_USED")

            # Increment ad repairs used today
            user.ad_repairs_today = ad_repairs_today + 1
        else:
            raise ValueError("Invalid repair method")

        # Restore streak
        user.current_streak = previous_streak
        user.streak_lost_at = None
        user.previous_streak = 0

        self.db.commit()

        return {
            "streak_repaired": True,
            "current_streak": user.current_streak,
            "gold_remaining": gold_remaining
        }

    def buy_streak_freeze(self, user_id: UUID) -> dict:
        """
        Buy a streak freeze for 200 gold.

        Max 5 freezes can be held at once.

        Args:
            user_id: User's UUID

        Returns:
            dict with:
            - success: bool
            - freezes_available: int
            - gold_remaining: int

        Raises:
            ValueError with codes:
            - NOT_ENOUGH_GOLD
            - MAX_FREEZES_REACHED
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Count current freezes
        current_freezes = self.db.query(StreakFreeze).filter(
            StreakFreeze.user_id == user_id,
            StreakFreeze.is_used == False,
            or_(
                StreakFreeze.expires_at == None,
                StreakFreeze.expires_at > datetime.utcnow()
            )
        ).count()

        # Also check user's freeze_count field if available
        user_freeze_count = getattr(user, 'streak_freeze_count', 0) or 0
        total_freezes = max(current_freezes, user_freeze_count)

        if total_freezes >= self.MAX_FREEZES:
            raise ValueError("MAX_FREEZES_REACHED")

        # Check gold (use gold field, fallback to orbs)
        current_gold = getattr(user, 'gold', None)
        if current_gold is None:
            current_gold = getattr(user, 'orbs', 0) or 0

        if current_gold < self.FREEZE_GOLD_COST:
            raise ValueError("NOT_ENOUGH_GOLD")

        # Deduct gold
        if hasattr(user, 'gold') and user.gold is not None:
            user.gold = current_gold - self.FREEZE_GOLD_COST
            gold_remaining = user.gold
        else:
            user.orbs = current_gold - self.FREEZE_GOLD_COST
            gold_remaining = user.orbs

        # Create new freeze
        freeze = StreakFreeze(
            user_id=user_id,
            source="purchased",
            is_used=False,
            expires_at=None  # Purchased freezes don't expire
        )
        self.db.add(freeze)

        # Update user's freeze count if field exists
        if hasattr(user, 'streak_freeze_count'):
            user.streak_freeze_count = total_freezes + 1

        self.db.commit()

        return {
            "success": True,
            "freezes_available": total_freezes + 1,
            "gold_remaining": gold_remaining
        }

    def calculate_xp_with_multiplier(
        self,
        base_xp: int,
        streak_days: int
    ) -> int:
        """
        Calculate XP with streak multiplier applied.

        Args:
            base_xp: Base XP amount
            streak_days: Current streak length

        Returns:
            int: XP with multiplier applied
        """
        multiplier = self.get_streak_multiplier(streak_days)
        return int(base_xp * multiplier)


# Convenience functions for standalone usage
def get_streak_service(db: Session) -> StreakService:
    """Factory function to get StreakService instance"""
    return StreakService(db)


def get_user_streak(db: Session, user_id: UUID) -> dict:
    """
    Standalone function to get user streak status.

    Args:
        db: Database session
        user_id: User's UUID

    Returns:
        dict with streak status information
    """
    service = StreakService(db)
    return service.get_streak_status(user_id)


def check_and_update_streak(db: Session, user_id: UUID, xp_earned: int) -> dict:
    """
    Standalone function to check and update streak.

    Args:
        db: Database session
        user_id: User's UUID
        xp_earned: XP earned from activity

    Returns:
        dict with streak update information
    """
    service = StreakService(db)
    return service.check_and_update_streak(user_id, xp_earned)


def buy_streak_freeze(db: Session, user_id: UUID) -> dict:
    """
    Standalone function to buy a streak freeze.

    Args:
        db: Database session
        user_id: User's UUID

    Returns:
        dict with purchase result
    """
    service = StreakService(db)
    return service.buy_streak_freeze(user_id)


def repair_streak(db: Session, user_id: UUID, method: str = "gold") -> dict:
    """
    Standalone function to repair a lost streak.

    Args:
        db: Database session
        user_id: User's UUID
        method: "gold" (300 gold) or "ad" (1 per day)

    Returns:
        dict with repair result
    """
    service = StreakService(db)
    return service.repair_streak(user_id, method)
