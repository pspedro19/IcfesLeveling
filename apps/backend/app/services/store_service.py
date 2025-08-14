from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from ..models.store import StoreTransaction, UserPowerUp, CurrencyEarning
from ..models.item import Item, UserItem
from ..models.user import User
from ..models.study_plan import PlanProgress
from ..models.achievement import UserAchievement
from ..schemas.store import StorePurchaseRequest, PowerUpActivationRequest, CurrencyEarningCreate

class StoreService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_store_items(self, item_type: Optional[str] = None) -> List[Item]:
        """Get available store items"""
        query = self.db.query(Item).filter(Item.is_available_in_store == True)
        
        if item_type:
            query = query.filter(Item.item_type == item_type)
        
        return query.all()
    
    def get_cosmetic_items(self) -> List[Item]:
        """Get cosmetic items available in store"""
        return self.db.query(Item).filter(
            and_(
                Item.is_available_in_store == True,
                Item.is_cosmetic == True
            )
        ).all()
    
    def get_power_up_items(self) -> List[Item]:
        """Get power-up items available in store"""
        return self.db.query(Item).filter(
            and_(
                Item.is_available_in_store == True,
                Item.is_power_up == True
            )
        ).all()
    
    def purchase_item(self, user_id: str, purchase_request: StorePurchaseRequest) -> Dict[str, Any]:
        """Purchase an item from the store"""
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Get item
        item = self.db.query(Item).filter(
            and_(
                Item.id == purchase_request.item_id,
                Item.is_available_in_store == True
            )
        ).first()
        
        if not item:
            raise ValueError("Item not available in store")
        
        # Calculate total cost
        if purchase_request.currency_type == "orbs":
            total_cost = item.store_price_orbs * purchase_request.quantity
            if user.orbs < total_cost:
                raise ValueError("Insufficient orbs")
            user.orbs -= total_cost
        else:  # crystals
            total_cost = item.store_price_crystals * purchase_request.quantity
            if user.crystals < total_cost:
                raise ValueError("Insufficient crystals")
            user.crystals -= total_cost
        
        # Create transaction record
        transaction = StoreTransaction(
            user_id=user_id,
            item_id=purchase_request.item_id,
            transaction_type="purchase",
            currency_type=purchase_request.currency_type,
            amount_spent=total_cost,
            quantity=purchase_request.quantity
        )
        self.db.add(transaction)
        
        # Add item to user inventory
        user_item = UserItem(
            user_id=user_id,
            item_id=purchase_request.item_id,
            quantity=purchase_request.quantity
        )
        self.db.add(user_item)
        
        # If it's a power-up, activate it
        if item.is_power_up:
            power_up = UserPowerUp(
                user_id=user_id,
                item_id=purchase_request.item_id,
                effect_data=item.power_up_effect
            )
            self.db.add(power_up)
        
        self.db.commit()
        
        return {
            "success": True,
            "transaction": transaction,
            "remaining_orbs": user.orbs,
            "remaining_crystals": user.crystals
        }
    
    def get_user_power_ups(self, user_id: str) -> List[UserPowerUp]:
        """Get user's active power-ups"""
        return self.db.query(UserPowerUp).filter(
            and_(
                UserPowerUp.user_id == user_id,
                UserPowerUp.is_active == True
            )
        ).all()
    
    def activate_power_up(self, user_id: str, power_up_id: str) -> Dict[str, Any]:
        """Activate a power-up for use"""
        power_up = self.db.query(UserPowerUp).filter(
            and_(
                UserPowerUp.id == power_up_id,
                UserPowerUp.user_id == user_id
            )
        ).first()
        
        if not power_up:
            raise ValueError("Power-up not found")
        
        if not power_up.can_use():
            raise ValueError("Power-up cannot be used")
        
        # Use the power-up
        if power_up.use():
            self.db.commit()
            return {
                "success": True,
                "power_up": power_up,
                "uses_remaining": power_up.uses_remaining
            }
        else:
            raise ValueError("Failed to use power-up")
    
    def earn_currency(self, user_id: str, currency_type: str, amount: int, source: str, source_id: Optional[str] = None, metadata: Dict[str, Any] = None) -> CurrencyEarning:
        """Earn currency for completing activities"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Add currency to user
        if currency_type == "orbs":
            user.orbs += amount
        elif currency_type == "crystals":
            user.crystals += amount
        
        # Create earning record
        earning = CurrencyEarning(
            user_id=user_id,
            currency_type=currency_type,
            amount=amount,
            source=source,
            source_id=source_id,
            metadata=metadata or {}
        )
        self.db.add(earning)
        self.db.commit()
        
        return earning
    
    def earn_orbs_for_unit_completion(self, user_id: str, unit_number: int, subject_id: str) -> CurrencyEarning:
        """Earn orbs for completing a study unit"""
        # Base orbs for unit completion
        base_orbs = 50
        
        # Bonus orbs for higher units
        bonus_orbs = (unit_number - 1) * 10
        
        total_orbs = base_orbs + bonus_orbs
        
        metadata = {
            "unit_number": unit_number,
            "subject_id": subject_id,
            "base_orbs": base_orbs,
            "bonus_orbs": bonus_orbs
        }
        
        return self.earn_currency(
            user_id=user_id,
            currency_type="orbs",
            amount=total_orbs,
            source="unit_completion",
            source_id=subject_id,
            metadata=metadata
        )
    
    def earn_crystals_for_achievement(self, user_id: str, achievement_id: str, achievement_rarity: str) -> CurrencyEarning:
        """Earn crystals for unlocking achievements"""
        # Crystals based on achievement rarity
        crystal_rewards = {
            "common": 5,
            "rare": 15,
            "epic": 30,
            "legendary": 75
        }
        
        crystals = crystal_rewards.get(achievement_rarity, 5)
        
        metadata = {
            "achievement_id": achievement_id,
            "achievement_rarity": achievement_rarity
        }
        
        return self.earn_currency(
            user_id=user_id,
            currency_type="crystals",
            amount=crystals,
            source="achievement",
            source_id=achievement_id,
            metadata=metadata
        )
    
    def get_user_currency_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user's currency summary"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Get total earnings
        orbs_earnings = self.db.query(func.sum(CurrencyEarning.amount)).filter(
            and_(
                CurrencyEarning.user_id == user_id,
                CurrencyEarning.currency_type == "orbs"
            )
        ).scalar() or 0
        
        crystals_earnings = self.db.query(func.sum(CurrencyEarning.amount)).filter(
            and_(
                CurrencyEarning.user_id == user_id,
                CurrencyEarning.currency_type == "crystals"
            )
        ).scalar() or 0
        
        # Get earnings by source
        earnings_by_source = {}
        source_stats = self.db.query(
            CurrencyEarning.source,
            func.sum(CurrencyEarning.amount)
        ).filter(CurrencyEarning.user_id == user_id).group_by(CurrencyEarning.source).all()
        
        for source, amount in source_stats:
            earnings_by_source[source] = amount
        
        # Get recent earnings
        recent_earnings = self.db.query(CurrencyEarning).filter(
            CurrencyEarning.user_id == user_id
        ).order_by(CurrencyEarning.earned_at.desc()).limit(10).all()
        
        return {
            "orbs": user.orbs,
            "crystals": user.crystals,
            "total_earned_orbs": orbs_earnings,
            "total_earned_crystals": crystals_earnings,
            "earnings_by_source": earnings_by_source,
            "recent_earnings": recent_earnings
        }
    
    def get_user_transactions(self, user_id: str, limit: int = 20) -> List[StoreTransaction]:
        """Get user's transaction history"""
        return self.db.query(StoreTransaction).filter(
            StoreTransaction.user_id == user_id
        ).order_by(StoreTransaction.transaction_date.desc()).limit(limit).all()
    
    def check_power_up_effects(self, user_id: str, quiz_id: str) -> Dict[str, Any]:
        """Check active power-up effects for a quiz"""
        active_power_ups = self.get_user_power_ups(user_id)
        
        effects = {
            "double_xp": False,
            "time_extension": 0,
            "hint_master": False,
            "perfect_score_boost": False,
            "shield": False,
            "critical_boost": 1.0
        }
        
        for power_up in active_power_ups:
            if not power_up.can_use():
                continue
            
            effect_data = power_up.effect_data
            effect_type = effect_data.get("effect")
            
            if effect_type == "double_xp":
                effects["double_xp"] = True
            elif effect_type == "time_extension":
                effects["time_extension"] += effect_data.get("seconds", 0)
            elif effect_type == "hint_master":
                effects["hint_master"] = True
            elif effect_type == "perfect_score_boost":
                effects["perfect_score_boost"] = True
            elif effect_type == "shield":
                effects["shield"] = True
            elif effect_type == "critical_boost":
                effects["critical_boost"] *= effect_data.get("multiplier", 1)
        
        return effects 