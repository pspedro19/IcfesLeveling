"""
Service for Hearts (Mana) and Grace Mode System
ICFES Leveling Backend
"""

import logging
from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Any

from sqlalchemy.orm import Session

from ..models import User, HeartTransaction
from ..services.mobile_service import MobileService

logger = logging.getLogger(__name__)

# Constants moved from router
MAX_HEARTS = 5
HEART_REGEN_HOURS = 4
MAX_ADS_PER_DAY = 3
REFILL_GOLD_COST = 150

class HeartsService:
    def __init__(self, db: Session):
        self.db = db

    # ============================================
    # SPEC-COMPLIANT METHODS (per API specification)
    # ============================================

    def get_user_hearts(self, user_id: UUID) -> dict:
        """
        Get user hearts with regeneration logic.
        Spec-compliant method signature: get_user_hearts(db, user_id)
        Returns hearts status including regeneration info.
        """
        return self.get_status(user_id)

    def lose_heart(self, user_id: UUID) -> dict:
        """
        Lose a heart (called on wrong answer).
        Spec-compliant method signature: lose_heart(db, user_id)
        Returns: hearts_remaining, is_grace_mode, next_regen_in_seconds
        """
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError("USER_NOT_FOUND")

        data, record = self._get_user_hearts_data(user)
        is_unlimited = bool(data["unlimited_hearts_until"] and data["unlimited_hearts_until"] > datetime.now(timezone.utc))

        if not is_unlimited:
            if data["hearts"] <= 0:
                raise ValueError("HEARTS_EMPTY")

            record.hearts -= 1
            if record.hearts == MAX_HEARTS - 1:
                regen_attr = 'last_heart_used_at' if hasattr(record, 'last_heart_used_at') else 'hearts_last_regeneration'
                setattr(record, regen_attr, datetime.now(timezone.utc))

        transaction = HeartTransaction(
            user_id=user_id, transaction_type="lost", amount=-1, hearts_after=record.hearts,
            source_type="wrong_answer", source_id=None
        )
        self.db.add(transaction)
        self.db.commit()

        # Calculate next_regen_in_seconds
        next_regen_at = self._calculate_next_regen(record.hearts, MAX_HEARTS, data["hearts_last_regeneration"])
        next_regen_in_seconds = None
        if next_regen_at:
            delta = next_regen_at - datetime.now(timezone.utc)
            next_regen_in_seconds = max(0, int(delta.total_seconds()))

        return {
            "hearts_remaining": record.hearts,
            "is_grace_mode": data["grace_mode_active"],
            "next_regen_in_seconds": next_regen_in_seconds
        }

    def restore_heart_with_ad(self, user_id: UUID) -> dict:
        """
        Restore one heart by watching an ad.
        Spec-compliant method signature: restore_heart_with_ad(db, user_id)
        Max 3 ads per day.
        """
        return self.refill_hearts(user_id, method="ad")

    def refill_hearts_with_gold(self, user_id: UUID) -> dict:
        """
        Refill all hearts using gold.
        Spec-compliant method signature: refill_hearts_with_gold(db, user_id)
        Cost: 150 gold.
        """
        return self.refill_hearts(user_id, method="gold")

    def _get_or_create_user_engagement(self, user_id: UUID) -> Tuple[Any, bool]:
        try:
            from ..models.diagnostic_two_phase import UserEngagement
            engagement = self.db.query(UserEngagement).filter_by(user_id=user_id).first()
            if not engagement:
                engagement = UserEngagement(user_id=user_id, hearts=MAX_HEARTS, max_hearts=MAX_HEARTS)
                self.db.add(engagement)
                self.db.flush()
            return engagement, True
        except Exception:
            return None, False

    def _get_user_hearts_data(self, user: User) -> Tuple[dict, Any]:
        engagement, using_engagement = self._get_or_create_user_engagement(user.id)
        if using_engagement and engagement:
            return {
                "hearts": engagement.hearts if engagement.hearts is not None else MAX_HEARTS,
                "max_hearts": engagement.max_hearts if engagement.max_hearts is not None else MAX_HEARTS,
                "grace_mode_active": engagement.grace_mode_active or False,
                "hearts_last_regeneration": engagement.last_heart_used_at,
                "unlimited_hearts_until": None,
                "ads_watched_today": engagement.ads_watched_today or 0,
            }, engagement
        
        return {
            "hearts": getattr(user, 'hearts', MAX_HEARTS),
            "max_hearts": getattr(user, 'max_hearts', MAX_HEARTS),
            "grace_mode_active": getattr(user, 'grace_mode_active', False),
            "hearts_last_regeneration": getattr(user, 'hearts_last_regeneration', None),
            "unlimited_hearts_until": getattr(user, 'unlimited_hearts_until', None),
            "ads_watched_today": getattr(user, 'ads_watched_today', 0),
        }, user

    def _calculate_next_regen(self, hearts: int, max_hearts: int, last_regen: Optional[datetime]) -> Optional[datetime]:
        if hearts >= max_hearts:
            return None
        if not last_regen:
            return datetime.now(timezone.utc) + timedelta(hours=HEART_REGEN_HOURS)
        return last_regen + timedelta(hours=HEART_REGEN_HOURS)

    def get_status(self, user_id: UUID) -> dict:
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user: raise ValueError("USER_NOT_FOUND")

        try:
            mobile_service = MobileService(self.db)
            mobile_service.regenerate_hearts(user_id)
        except Exception:
            pass
            
        data, record = self._get_user_hearts_data(user)
        is_unlimited = bool(data["unlimited_hearts_until"] and data["unlimited_hearts_until"] > datetime.now(timezone.utc))

        if data["grace_mode_active"] and data["hearts"] > 0:
            record.grace_mode_active = False
            self.db.commit()
            data["grace_mode_active"] = False

        return {
            "hearts": data["hearts"],
            "max_hearts": data["max_hearts"],
            "regen_hours": HEART_REGEN_HOURS,
            "next_regen_at": self._calculate_next_regen(data["hearts"], data["max_hearts"], data["hearts_last_regeneration"]),
            "unlimited_until": data["unlimited_hearts_until"],
            "is_unlimited": is_unlimited,
            "grace_mode_active": data["grace_mode_active"],
            "ads_watched_today": data["ads_watched_today"],
            "max_ads_per_day": MAX_ADS_PER_DAY,
        }

    def get_grace_status(self, user_id: UUID) -> dict:
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user: raise ValueError("USER_NOT_FOUND")
        data, _ = self._get_user_hearts_data(user)
        hearts = data["hearts"]
        grace_mode_active = data["grace_mode_active"]
        return {
            "hearts": hearts,
            "can_enter_grace_mode": (hearts == 0 and not grace_mode_active),
            "grace_mode_active": grace_mode_active,
            "practice_allowed": True,
            "xp_enabled": (hearts > 0 and not grace_mode_active),
        }

    def enter_grace_mode(self, user_id: UUID) -> dict:
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user: raise ValueError("USER_NOT_FOUND")
        data, record = self._get_user_hearts_data(user)
        if data["grace_mode_active"]:
            return {"grace_mode_active": True, "message": "Ya estas en modo entrenamiento."}
        if data["hearts"] > 0:
            raise ValueError("HEARTS_AVAILABLE")
        
        record.grace_mode_active = True
        if hasattr(record, 'grace_mode_started_at'):
             record.grace_mode_started_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"grace_mode_active": True, "message": "Modo entrenamiento activado. Practica sin XP."}

    def exit_grace_mode(self, user_id: UUID) -> dict:
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user: raise ValueError("USER_NOT_FOUND")
        _, record = self._get_user_hearts_data(user)
        record.grace_mode_active = False
        if hasattr(record, 'grace_mode_started_at'):
            record.grace_mode_started_at = None
        self.db.commit()
        return {"grace_mode_active": False}

    def use_heart(self, user_id: UUID, reason: str, source_id: Optional[UUID]) -> dict:
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user: raise ValueError("USER_NOT_FOUND")
        
        data, record = self._get_user_hearts_data(user)
        is_unlimited = bool(data["unlimited_hearts_until"] and data["unlimited_hearts_until"] > datetime.now(timezone.utc))

        if not is_unlimited:
            if data["hearts"] <= 0:
                raise ValueError("HEARTS_EMPTY")
            
            record.hearts -= 1
            if record.hearts == MAX_HEARTS - 1:
                regen_attr = 'last_heart_used_at' if hasattr(record, 'last_heart_used_at') else 'hearts_last_regeneration'
                setattr(record, regen_attr, datetime.now(timezone.utc))

        transaction = HeartTransaction(
            user_id=user_id, transaction_type="lost", amount=-1, hearts_after=record.hearts,
            source_type=reason, source_id=source_id
        )
        self.db.add(transaction)
        self.db.commit()

        return {
            "hearts_remaining": record.hearts,
            "next_regen_at": self._calculate_next_regen(record.hearts, MAX_HEARTS, data["hearts_last_regeneration"]),
            "can_enter_grace_mode": (record.hearts == 0)
        }

    def _reset_ads_if_new_day(self, user: User) -> None:
        """Reset ads_watched_today if it's a new day (per spec: max 3 ads/day)"""
        from datetime import date
        today = date.today()

        if user.ads_watched_date != today:
            user.ads_watched_today = 0
            user.ads_watched_date = today
            self.db.flush()

    def refill_hearts(self, user_id: UUID, method: str) -> dict:
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user: raise ValueError("USER_NOT_FOUND")

        data, record = self._get_user_hearts_data(user)
        initial_hearts = data["hearts"]

        if method == "gold":
            # Use gold field (primary currency per spec)
            user_gold = getattr(user, 'gold', 0) or getattr(user, 'orbs', 0)
            if user_gold < REFILL_GOLD_COST:
                raise ValueError("NOT_ENOUGH_GOLD")
            # Deduct from gold (primary) or orbs (fallback)
            if hasattr(user, 'gold') and user.gold is not None:
                user.gold -= REFILL_GOLD_COST
            else:
                user.orbs -= REFILL_GOLD_COST
            record.hearts = MAX_HEARTS
        elif method == "ad":
            # Reset ads counter if new day
            self._reset_ads_if_new_day(user)

            # Check User model fields first (per spec), then fallback to engagement
            ads_today = user.ads_watched_today or 0
            if ads_today >= MAX_ADS_PER_DAY:
                raise ValueError("AD_LIMIT_REACHED")

            # Increment on User model (per spec)
            user.ads_watched_today = ads_today + 1
            user.ads_watched_date = datetime.now(timezone.utc).date()

            # Also update engagement if using it
            if hasattr(record, 'ads_watched_today'):
                record.ads_watched_today = user.ads_watched_today

            record.hearts = min(initial_hearts + 1, MAX_HEARTS)
        elif method == "purchase":
            # In-app purchase heart refill — full refill to max
            record.hearts = MAX_HEARTS
        else:
            raise ValueError("Invalid refill method.")

        transaction = HeartTransaction(
            user_id=user_id, transaction_type="refilled", amount=record.hearts - initial_hearts,
            hearts_after=record.hearts, source_type=method
        )
        self.db.add(transaction)

        if record.hearts > 0 and data["grace_mode_active"]:
            record.grace_mode_active = False

        self.db.commit()

        # Return gold from primary field or fallback
        gold_remaining = getattr(user, 'gold', None)
        if gold_remaining is None:
            gold_remaining = getattr(user, 'orbs', None)

        return {
            "hearts": record.hearts,
            "max_hearts": MAX_HEARTS,
            "gold_remaining": gold_remaining,
            "ads_remaining_today": MAX_ADS_PER_DAY - (user.ads_watched_today or 0)
        }
