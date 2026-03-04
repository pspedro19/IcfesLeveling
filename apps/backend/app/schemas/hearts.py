"""
Schemas for Hearts (Mana) System - ICFES Leveling
Includes Grace Mode schemas for training without XP
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ============================================
# GRACE MODE SCHEMAS
# ============================================

class GraceStatusResponse(BaseModel):
    """
    Response for GET /hearts/grace-status

    Grace Mode allows users to practice without earning XP
    when they have 0 hearts remaining.
    """
    hearts: int
    can_enter_grace_mode: bool
    grace_mode_active: bool
    practice_allowed: bool  # Always True - users can always practice
    xp_enabled: bool  # False when in grace mode or hearts=0


class EnterGraceModeResponse(BaseModel):
    """
    Response for POST /hearts/enter-grace-mode

    Activates training mode without XP rewards.
    """
    grace_mode_active: bool
    message: str


class ExitGraceModeResponse(BaseModel):
    """
    Response for POST /hearts/exit-grace-mode

    Deactivates grace mode.
    """
    grace_mode_active: bool


# ============================================
# HEARTS STATUS SCHEMA (UPDATED)
# ============================================

class HeartsStatusResponse(BaseModel):
    """
    Response for GET /hearts/status

    Updated to include:
    - regen_hours: 4 (changed from 2)
    - grace_mode_active: boolean
    - ads_watched_today: number
    - max_ads_per_day: 3
    """
    hearts: int  # Current hearts (0-5)
    max_hearts: int  # Maximum hearts (5)
    regen_hours: int  # Hours per heart regeneration (4)
    next_regen_at: Optional[datetime] = None  # Next regeneration timestamp
    unlimited_until: Optional[datetime] = None  # Unlimited hearts expiration
    is_unlimited: bool  # True if unlimited hearts are active
    grace_mode_active: bool  # True if in training mode
    ads_watched_today: int  # Ads watched today for heart refill
    max_ads_per_day: int  # Maximum ads per day (3)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "hearts": 3,
                "max_hearts": 5,
                "regen_hours": 4,
                "next_regen_at": "2024-01-15T14:30:00Z",
                "unlimited_until": None,
                "is_unlimited": False,
                "grace_mode_active": False,
                "ads_watched_today": 1,
                "max_ads_per_day": 3
            }
        }


# ============================================
# HEARTS USE/REFILL SCHEMAS
# ============================================

class HeartsUseRequest(BaseModel):
    """Request to use a heart"""
    reason: str = "wrong_answer"  # 'wrong_answer' | 'skip_question'
    source_id: Optional[str] = None  # Question ID if applicable


class HeartsUseResponse(BaseModel):
    """Response after using a heart"""
    hearts_remaining: int
    next_regen_at: Optional[datetime] = None
    can_enter_grace_mode: bool = False  # True if hearts just hit 0


class HeartsRefillRequest(BaseModel):
    """Request to refill hearts"""
    method: str  # 'gold' | 'ad' | 'purchase'
    gold_spent: Optional[int] = None  # Cost: 150 gold


class HeartsRefillResponse(BaseModel):
    """Response after refilling hearts"""
    hearts: int  # Should be 5 after refill
    max_hearts: int
    gold_remaining: Optional[int] = None  # If method=gold
    ads_remaining_today: Optional[int] = None  # If method=ad


# ============================================
# ERROR RESPONSE SCHEMAS
# ============================================

class HeartsErrorData(BaseModel):
    """Data included in hearts error responses"""
    next_regen_at: Optional[datetime] = None
    can_watch_ad: bool = False
    can_enter_grace_mode: bool = False


class HeartsErrorResponse(BaseModel):
    """Error response for hearts-related errors"""
    code: str  # 'HEARTS_EMPTY' | 'HEARTS_AVAILABLE' | etc.
    message: str
    data: Optional[HeartsErrorData] = None


# ============================================
# HEART ACTION RESPONSE (UNIFIED)
# ============================================

class HeartActionResponse(BaseModel):
    """
    Unified response for heart-related actions.

    Used for:
    - POST /hearts/use
    - POST /hearts/refill
    - POST /hearts/watch-ad
    """
    hearts_remaining: int
    is_grace_mode: bool = False
    ads_remaining_today: int = 3
    gold_spent: Optional[int] = None
    message: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "hearts_remaining": 4,
                "is_grace_mode": False,
                "ads_remaining_today": 2,
                "gold_spent": None,
                "message": "Heart used for wrong answer"
            }
        }
