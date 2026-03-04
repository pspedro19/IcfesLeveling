"""
Streak Routes - ICFES Leveling Mobile App
Streak management with timezone-aware daily resets

Endpoints:
- GET /streaks/status - Get current streak status with multiplier and repair info
- POST /streaks/check - Check and update streak based on XP earned
- POST /streaks/buy-freeze - Buy a streak freeze (200 gold, max 5)
- POST /streaks/repair - Repair lost streak within 24h window (300 gold)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Literal
from datetime import datetime, date, timedelta
from uuid import UUID
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user
from ..core.redis_cache import cache
from ..models import User, UserDailyActivity, StreakFreeze
from ..services.streak_service import StreakService
from ..utils.response import success_response


# ============================================
# PYDANTIC SCHEMAS
# ============================================

class StreakStatusResponse(BaseModel):
    """Response for GET /streak/status"""
    current: int
    longest: int
    today_xp: int
    daily_goal: int
    goal_met: bool
    last_activity_date: Optional[date] = None
    freezes_available: int
    at_risk: bool
    day_resets_at: str  # "04:00" - 4 AM local time
    timezone: str
    multiplier: float  # 1.0, 1.2, 1.5, 2.0 based on streak days
    can_repair: bool
    repair_window_ends_at: Optional[datetime] = None


class StreakExtendRequest(BaseModel):
    """Request for POST /streak/extend"""
    xp_earned: int
    activity_date: Optional[date] = None


class StreakUpdateInfo(BaseModel):
    """Streak update information"""
    current: int
    longest: int
    extended: bool
    multiplier: float


class DailyGoalInfo(BaseModel):
    """Daily goal information"""
    xp_earned: int
    target: int
    met: bool
    first_time_today: bool


class BonusInfo(BaseModel):
    """Bonus rewards for streak milestones"""
    gold_earned: int
    badge_earned: Optional[str] = None


class StreakExtendResponse(BaseModel):
    """Response for POST /streak/extend"""
    streak: StreakUpdateInfo
    daily_goal: DailyGoalInfo
    bonus: Optional[BonusInfo] = None


class StreakRepairRequest(BaseModel):
    """Request for POST /streak/repair"""
    method: Literal["gold", "ad"]


class StreakRepairResponse(BaseModel):
    """Response for POST /streak/repair"""
    streak_repaired: bool
    current_streak: int
    gold_remaining: Optional[int] = None


class StreakFreezeRequest(BaseModel):
    """Request for POST /streak/freeze"""
    method: Literal["gold", "item"] = "item"
    gold_cost: int = 200


class StreakFreezeResponse(BaseModel):
    """Response for POST /streak/freeze"""
    freezes_remaining: int
    freeze_date: date
    gold_remaining: Optional[int] = None


# ============================================
# ROUTER
# ============================================

router = APIRouter(prefix="/streaks", tags=["Streaks"])


async def get_current_user_id(
    current_user: User = Depends(get_current_user)
) -> UUID:
    """Extract user ID from JWT-authenticated user"""
    return current_user.id


# ============================================
# ENDPOINTS
# ============================================

@router.get("/status")
async def get_streak_status(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get current streak status.

    Returns comprehensive streak information including:
    - Current and longest streak
    - Today's XP and daily goal progress
    - Day reset time (4:00 AM local time)
    - XP multiplier based on streak length
    - Whether streak can be repaired (within 24h window)

    Streak Multipliers:
    - 1-6 days: 1.0x
    - 7-13 days: 1.2x
    - 14-29 days: 1.3x
    - 30-59 days: 1.5x
    - 60+ days: 1.8x
    """
    # Check Redis cache first (2 min TTL)
    cache_key = f"streak:status:{user_id}"
    cached = cache.get(cache_key)
    if cached:
        return success_response(cached)

    service = StreakService(db)

    try:
        status = service.get_streak_status(user_id)
        cache.set(cache_key, status, 120)  # Cache for 2 minutes
        return success_response(status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/extend")
async def extend_streak(
    request: StreakExtendRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Record XP earned and extend streak if daily goal met.

    The daily goal is 20 XP by default. When met for the first time
    in a day, the streak is extended.

    Streak milestones award bonus gold:
    - 7 days: 50 gold
    - 14 days: 100 gold
    - 30 days: 200 gold
    """
    service = StreakService(db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user timezone and current streak day
    user_timezone = getattr(user, 'timezone', 'America/Bogota') or 'America/Bogota'
    today = request.activity_date or service.get_current_streak_day(user_timezone)

    # Get or create daily activity
    activity = db.query(UserDailyActivity).filter(
        UserDailyActivity.user_id == user_id,
        UserDailyActivity.activity_date == today
    ).first()

    first_time = activity is None

    if not activity:
        activity = UserDailyActivity(
            user_id=user_id,
            activity_date=today,
            first_session_at=datetime.utcnow()
        )
        db.add(activity)
        db.flush()

    # Update activity
    old_xp = activity.xp_earned or 0
    activity.xp_earned = old_xp + request.xp_earned
    activity.last_session_at = datetime.utcnow()

    # Check daily goal
    daily_goal = getattr(user, 'daily_goal_xp', 20) or 20
    goal_met = activity.xp_earned >= daily_goal
    activity.daily_goal_met = goal_met

    # Track streak extension
    streak_extended = False
    current_streak = getattr(user, 'current_streak', 0) or 0
    longest_streak = getattr(user, 'longest_streak', 0) or 0
    bonus_data = None

    if goal_met and not activity.streak_extended:
        activity.streak_extended = True
        streak_extended = True

        # Check if streak continues or resets
        last_activity = getattr(user, 'last_activity_date', None)
        yesterday = today - timedelta(days=1)

        if last_activity == yesterday:
            # Consecutive day - extend streak
            current_streak = current_streak + 1
            user.current_streak = current_streak
        elif last_activity != today:
            # First activity or gap - start new streak
            current_streak = 1
            user.current_streak = current_streak

        # Update longest streak
        if current_streak > longest_streak:
            longest_streak = current_streak
            user.longest_streak = longest_streak

        user.last_activity_date = today

        # Check for milestone bonuses
        gold_reward = 0
        badge = None

        if current_streak == 7:
            gold_reward = 50
            badge = "week_warrior"
        elif current_streak == 14:
            gold_reward = 100
            badge = "fortnight_fighter"
        elif current_streak == 30:
            gold_reward = 200
            badge = "month_master"
        elif current_streak == 100:
            gold_reward = 500
            badge = "century_champion"

        if gold_reward > 0:
            current_gold = getattr(user, 'orbs', 0) or 0
            user.orbs = current_gold + gold_reward
            bonus_data = {
                "gold_earned": gold_reward,
                "badge_earned": badge
            }

    db.commit()

    # Get multiplier
    multiplier = service.get_streak_multiplier(current_streak)

    response_data = {
        "streak": {
            "current": current_streak,
            "longest": longest_streak,
            "extended": streak_extended,
            "multiplier": multiplier
        },
        "daily_goal": {
            "xp_earned": activity.xp_earned,
            "target": daily_goal,
            "met": goal_met,
            "first_time_today": first_time
        },
        "bonus": bonus_data
    }
    return success_response(response_data)


class StreakCheckRequest(BaseModel):
    """Request for POST /streaks/check"""
    xp_earned: int


class StreakCheckResponse(BaseModel):
    """Response for POST /streaks/check"""
    extended: bool
    current: int
    previous: Optional[int] = None
    lost: bool = False
    today_xp: int
    multiplier: float


@router.post("/check")
async def check_streak(
    request: StreakCheckRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Check and update streak based on XP earned.

    Requires minimum 20 XP (MIN_XP_FOR_STREAK) to count towards streak.

    Returns:
    - extended: Whether streak was extended today
    - current: Current streak count
    - previous: Previous streak (if lost)
    - lost: Whether streak was lost
    - today_xp: Total XP earned today
    - multiplier: Current XP multiplier based on streak
    """
    service = StreakService(db)

    # Check minimum XP requirement
    if request.xp_earned < service.MIN_XP_FOR_STREAK:
        # Still track XP but don't extend streak
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        current_streak = getattr(user, 'current_streak', 0) or 0
        return success_response({
            "extended": False,
            "current": current_streak,
            "lost": False,
            "today_xp": request.xp_earned,
            "multiplier": service.get_streak_multiplier(current_streak),
            "message": f"Need {service.MIN_XP_FOR_STREAK} XP to extend streak"
        })

    try:
        result = service.check_and_update_streak(user_id, request.xp_earned)
        result["multiplier"] = service.get_streak_multiplier(result.get("current", 0))
        return success_response(result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


class BuyFreezeResponse(BaseModel):
    """Response for POST /streaks/buy-freeze"""
    success: bool
    freezes_available: int
    gold_remaining: int


@router.post("/buy-freeze")
async def buy_streak_freeze(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Buy a streak freeze for 200 gold.

    Max 5 freezes can be held at once.

    Error codes:
    - NOT_ENOUGH_GOLD: Insufficient gold (need 200)
    - MAX_FREEZES_REACHED: Already have 5 freezes
    """
    service = StreakService(db)

    try:
        result = service.buy_streak_freeze(user_id)
        return success_response(result)

    except ValueError as e:
        error_code = str(e)

        if error_code == "NOT_ENOUGH_GOLD":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "NOT_ENOUGH_GOLD",
                    "message": "No tienes suficiente oro (necesitas 200)"
                }
            )
        elif error_code == "MAX_FREEZES_REACHED":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "MAX_FREEZES_REACHED",
                    "message": "Ya tienes el maximo de 5 streak freezes"
                }
            )
        else:
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/repair")
async def repair_streak(
    request: StreakRepairRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Repair a lost streak within 24h window.

    Available repair methods:
    - "gold": Costs 300 gold
    - "ad": Watch an ad (1 per day)

    The streak can only be repaired if:
    1. The streak was recently lost (within 24 hours)
    2. There was a previous streak to restore

    Error codes:
    - NO_STREAK_TO_REPAIR: No streak to repair
    - STREAK_REPAIR_EXPIRED: 24h repair window has passed
    - AD_REPAIR_USED: Already used ad repair today
    - NOT_ENOUGH_GOLD: Insufficient gold (need 300)
    """
    service = StreakService(db)

    try:
        result = service.repair_streak(user_id, request.method)
        return success_response(result)

    except ValueError as e:
        error_code = str(e)

        if error_code == "NO_STREAK_TO_REPAIR":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "NO_STREAK_TO_REPAIR",
                    "message": "No hay racha para reparar"
                }
            )
        elif error_code == "STREAK_REPAIR_EXPIRED":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "STREAK_REPAIR_EXPIRED",
                    "message": "Ventana de reparacion de 24h expirada"
                }
            )
        elif error_code == "AD_REPAIR_USED":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "AD_REPAIR_USED",
                    "message": "Ya usaste el anuncio para reparar hoy"
                }
            )
        elif error_code == "NOT_ENOUGH_GOLD":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "NOT_ENOUGH_GOLD",
                    "message": "No tienes suficiente oro (necesitas 300)"
                }
            )
        else:
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/freeze")
async def use_streak_freeze(
    request: StreakFreezeRequest = StreakFreezeRequest(),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Use a streak freeze to protect streak for one day.

    Available methods:
    - "item": Use an existing streak freeze item
    - "gold": Purchase a streak freeze for 200 gold

    Error codes:
    - NO_FREEZES: No streak freezes available
    - NOT_ENOUGH_GOLD: Insufficient gold (need 200)
    """
    from sqlalchemy import or_

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.method == "gold":
        # Check gold
        current_gold = getattr(user, 'orbs', 0) or 0
        if current_gold < request.gold_cost:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "NOT_ENOUGH_GOLD",
                    "message": f"No tienes suficiente oro (necesitas {request.gold_cost})"
                }
            )

        # Create a new freeze and use it immediately
        freeze = StreakFreeze(
            user_id=user_id,
            source="purchased",  # Matches DB schema
            is_used=True,
            used_at=datetime.utcnow(),
            used_for_date=date.today()
        )
        db.add(freeze)

        # Deduct gold
        user.orbs = current_gold - request.gold_cost
        gold_remaining = user.orbs

    else:
        # Use existing freeze
        freeze = db.query(StreakFreeze).filter(
            StreakFreeze.user_id == user_id,
            StreakFreeze.is_used == False,
            or_(
                StreakFreeze.expires_at == None,
                StreakFreeze.expires_at > datetime.utcnow()
            )
        ).first()

        if not freeze:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "NO_FREEZES",
                    "message": "No tienes streak freezes disponibles"
                }
            )

        freeze.is_used = True
        freeze.used_at = datetime.utcnow()
        freeze.used_for_date = date.today()
        gold_remaining = None

    # Count remaining freezes
    remaining = db.query(StreakFreeze).filter(
        StreakFreeze.user_id == user_id,
        StreakFreeze.is_used == False,
        or_(
            StreakFreeze.expires_at == None,
            StreakFreeze.expires_at > datetime.utcnow()
        )
    ).count()

    db.commit()

    response_data = {
        "freezes_remaining": remaining,
        "freeze_date": freeze.used_for_date.isoformat() if freeze.used_for_date else None,
        "gold_remaining": gold_remaining
    }
    return success_response(response_data)
