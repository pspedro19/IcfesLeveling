from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.store_service import StoreService
from ..schemas.store import (
    StoreItemResponse, StoreTransactionResponse, UserPowerUpResponse,
    CurrencyEarningResponse, StorePurchaseRequest, StorePurchaseResponse,
    UserCurrencyResponse, StoreInventoryResponse, PowerUpActivationRequest,
    PowerUpActivationResponse, CurrencyEarningSummary
)

router = APIRouter()

@router.get("/store/items", response_model=List[StoreItemResponse])
async def get_store_items(
    item_type: Optional[str] = Query(None, description="Filter by item type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available store items"""
    try:
        store_service = StoreService(db)
        items = store_service.get_store_items(item_type)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/store/cosmetics", response_model=List[StoreItemResponse])
async def get_cosmetic_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cosmetic items available in store"""
    try:
        store_service = StoreService(db)
        items = store_service.get_cosmetic_items()
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/store/power-ups", response_model=List[StoreItemResponse])
async def get_power_up_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get power-up items available in store"""
    try:
        store_service = StoreService(db)
        items = store_service.get_power_up_items()
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/store/purchase", response_model=StorePurchaseResponse)
async def purchase_item(
    purchase_request: StorePurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Purchase an item from the store"""
    try:
        store_service = StoreService(db)
        result = store_service.purchase_item(str(current_user.id), purchase_request)
        
        return StorePurchaseResponse(
            success=True,
            message="Item purchased successfully",
            transaction=result["transaction"],
            remaining_orbs=result["remaining_orbs"],
            remaining_crystals=result["remaining_crystals"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/store/inventory", response_model=StoreInventoryResponse)
async def get_store_inventory(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get store inventory and user currency"""
    try:
        store_service = StoreService(db)
        
        cosmetic_items = store_service.get_cosmetic_items()
        power_up_items = store_service.get_power_up_items()
        currency_summary = store_service.get_user_currency_summary(str(current_user.id))
        
        return StoreInventoryResponse(
            cosmetic_items=cosmetic_items,
            power_up_items=power_up_items,
            user_currency=UserCurrencyResponse(**currency_summary)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/store/currency", response_model=UserCurrencyResponse)
async def get_user_currency(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's current currency"""
    try:
        store_service = StoreService(db)
        currency_summary = store_service.get_user_currency_summary(str(current_user.id))
        return UserCurrencyResponse(**currency_summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/store/transactions", response_model=List[StoreTransactionResponse])
async def get_user_transactions(
    limit: int = Query(20, description="Number of transactions to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's transaction history"""
    try:
        store_service = StoreService(db)
        transactions = store_service.get_user_transactions(str(current_user.id), limit)
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/store/power-ups/active", response_model=List[UserPowerUpResponse])
async def get_active_power_ups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's active power-ups"""
    try:
        store_service = StoreService(db)
        power_ups = store_service.get_user_power_ups(str(current_user.id))
        return power_ups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/store/power-ups/activate", response_model=PowerUpActivationResponse)
async def activate_power_up(
    activation_request: PowerUpActivationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate a power-up for use"""
    try:
        store_service = StoreService(db)
        result = store_service.activate_power_up(str(current_user.id), activation_request.power_up_id)
        
        return PowerUpActivationResponse(
            success=True,
            message="Power-up activated successfully",
            power_up=result["power_up"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/store/earnings", response_model=CurrencyEarningSummary)
async def get_currency_earnings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's currency earning summary"""
    try:
        store_service = StoreService(db)
        currency_summary = store_service.get_user_currency_summary(str(current_user.id))
        
        return CurrencyEarningSummary(
            total_orbs_earned=currency_summary["total_earned_orbs"],
            total_crystals_earned=currency_summary["total_earned_crystals"],
            earnings_by_source=currency_summary["earnings_by_source"],
            recent_earnings=currency_summary["recent_earnings"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/store/earn/unit-completion")
async def earn_orbs_for_unit_completion(
    unit_number: int,
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Earn orbs for completing a study unit"""
    try:
        store_service = StoreService(db)
        earning = store_service.earn_orbs_for_unit_completion(str(current_user.id), unit_number, subject_id)
        
        return {
            "success": True,
            "message": f"Earned {earning.amount} orbs for completing unit {unit_number}",
            "earning": earning
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/store/earn/achievement")
async def earn_crystals_for_achievement(
    achievement_id: str,
    achievement_rarity: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Earn crystals for unlocking an achievement"""
    try:
        store_service = StoreService(db)
        earning = store_service.earn_crystals_for_achievement(str(current_user.id), achievement_id, achievement_rarity)
        
        return {
            "success": True,
            "message": f"Earned {earning.amount} crystals for achievement",
            "earning": earning
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/store/power-ups/effects/{quiz_id}")
async def get_power_up_effects(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active power-up effects for a quiz"""
    try:
        store_service = StoreService(db)
        effects = store_service.check_power_up_effects(str(current_user.id), quiz_id)
        
        return {
            "quiz_id": quiz_id,
            "effects": effects
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 