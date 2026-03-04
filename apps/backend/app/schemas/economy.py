"""
Economy System Schemas
Gold Economy system for ICFES Leveling

This module defines the Pydantic models for the economy endpoints:
- GET /economy/balance - Return gold and gems
- GET /economy/shop - Return available items with prices
- POST /economy/purchase - Buy item with gold or gems
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class CurrencyType(str, Enum):
    """Currency types available in the game"""
    GOLD = "gold"
    GEMS = "gems"


class ItemCategory(str, Enum):
    """Shop item categories"""
    STREAK = "streak"
    HEARTS = "hearts"
    COSMETIC = "cosmetic"
    BOOST = "boost"
    AVATAR = "avatar"
    TITLE = "title"
    THEME = "theme"
    BUNDLE = "bundle"
    SPECIAL = "special"


class BalanceResponse(BaseModel):
    """Response model for GET /economy/balance"""
    gold: int = Field(..., description="Current gold balance (orbs)")
    gems: int = Field(..., description="Current gems balance (crystals)")

    class Config:
        json_schema_extra = {
            "example": {
                "gold": 1500,
                "gems": 25
            }
        }


class ShopItem(BaseModel):
    """Individual shop item model"""
    id: str = Field(..., description="Unique item identifier")
    name: str = Field(..., description="Display name of the item")
    description: str = Field(..., description="Item description")
    price_gold: int = Field(..., description="Price in gold (orbs)")
    price_gems: Optional[int] = Field(None, description="Price in gems (crystals), if available")
    category: ItemCategory = Field(..., description="Item category")
    icon: Optional[str] = Field(None, description="Icon identifier or URL")
    effect: Optional[str] = Field(None, description="Effect description")
    max_quantity: Optional[int] = Field(None, description="Maximum quantity per purchase")
    is_available: bool = Field(True, description="Whether item is currently available")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "streak_freeze",
                "name": "Streak Freeze",
                "description": "Protects your streak for one day if you miss practice",
                "price_gold": 200,
                "price_gems": None,
                "category": "streak",
                "icon": "ice_shield",
                "effect": "Prevents streak loss for 1 day",
                "max_quantity": 3,
                "is_available": True
            }
        }


class ShopResponse(BaseModel):
    """Response model for GET /economy/shop"""
    items: List[ShopItem] = Field(..., description="List of available shop items")
    prices: dict = Field(..., description="Quick reference price map for common items")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "streak_freeze",
                        "name": "Streak Freeze",
                        "description": "Protects your streak for one day",
                        "price_gold": 200,
                        "price_gems": None,
                        "category": "streak"
                    }
                ],
                "prices": {
                    "streak_freeze": 200,
                    "streak_repair": 300,
                    "hint": 50,
                    "mana_potion": 150
                }
            }
        }


class PurchaseRequest(BaseModel):
    """Request model for POST /economy/purchase"""
    item_id: str = Field(..., description="ID of the item to purchase")
    currency: CurrencyType = Field(CurrencyType.GOLD, description="Currency to use for purchase")
    quantity: int = Field(1, ge=1, le=10, description="Quantity to purchase")

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "streak_freeze",
                "currency": "gold",
                "quantity": 1
            }
        }


class PurchaseResponse(BaseModel):
    """Response model for POST /economy/purchase"""
    purchased: bool = Field(..., description="Whether purchase was successful")
    item_id: str = Field(..., description="ID of the purchased item")
    quantity: int = Field(..., description="Quantity purchased")
    gold_remaining: int = Field(..., description="Gold balance after purchase")
    gems_remaining: int = Field(..., description="Gems balance after purchase")
    message: str = Field(..., description="Success or error message")
    effect_applied: Optional[str] = Field(None, description="Description of effect applied, if any")

    class Config:
        json_schema_extra = {
            "example": {
                "purchased": True,
                "item_id": "streak_freeze",
                "quantity": 1,
                "gold_remaining": 1300,
                "gems_remaining": 25,
                "message": "Successfully purchased Streak Freeze",
                "effect_applied": "Streak protection activated for 1 day"
            }
        }


class PurchaseError(BaseModel):
    """Error response for failed purchases"""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "INSUFFICIENT_FUNDS",
                "message": "Not enough gold to complete this purchase",
                "details": {
                    "required": 200,
                    "available": 150
                }
            }
        }


# Item effect tracking models for inventory management

class UserInventoryItem(BaseModel):
    """Represents an item in user's inventory"""
    item_id: str = Field(..., description="Item identifier")
    name: str = Field(..., description="Item name")
    quantity: int = Field(..., description="Quantity owned")
    category: ItemCategory = Field(..., description="Item category")
    expires_at: Optional[datetime] = Field(None, description="Expiration time, if applicable")
    is_active: bool = Field(False, description="Whether effect is currently active")


class InventoryResponse(BaseModel):
    """Response model for user inventory"""
    items: List[UserInventoryItem] = Field(default_factory=list, description="List of owned items")
    active_effects: List[str] = Field(default_factory=list, description="Currently active item effects")


class TransactionRecord(BaseModel):
    """Record of an economy transaction"""
    id: str = Field(..., description="Transaction ID")
    user_id: str = Field(..., description="User who made the transaction")
    item_id: str = Field(..., description="Item purchased")
    quantity: int = Field(..., description="Quantity purchased")
    currency_type: CurrencyType = Field(..., description="Currency used")
    amount: int = Field(..., description="Amount spent")
    timestamp: datetime = Field(..., description="When the transaction occurred")

    class Config:
        from_attributes = True


# ============================================
# ECONOMY STATUS RESPONSE
# ============================================

class EconomyStatusResponse(BaseModel):
    """
    Comprehensive economy status for a user.

    Response for GET /economy/status
    """
    gold: int = Field(..., description="Current gold balance")
    total_xp: int = Field(..., description="Total XP earned")
    level: int = Field(..., description="Current player level")
    rank: str = Field(..., description="Current rank/tier name")
    xp_to_next_level: int = Field(..., description="XP needed to reach next level")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "gold": 1500,
                "total_xp": 12500,
                "level": 15,
                "rank": "Explorador",
                "xp_to_next_level": 500
            }
        }


# ============================================
# GOLD TRANSACTION RESPONSE
# ============================================

class TransactionType(str, Enum):
    """Types of gold transactions"""
    EARNED = "earned"
    SPENT = "spent"
    REWARD = "reward"
    PURCHASE = "purchase"
    REFUND = "refund"
    BONUS = "bonus"


class GoldTransactionResponse(BaseModel):
    """
    Response for a gold transaction.

    Used for tracking gold earned or spent.
    """
    id: str = Field(..., description="Transaction ID")
    amount: int = Field(..., description="Amount of gold in the transaction (positive or negative)")
    transaction_type: str = Field(..., description="Type of transaction")
    description: Optional[str] = Field(None, description="Human-readable description")
    balance_after: int = Field(..., description="Gold balance after this transaction")
    created_at: datetime = Field(..., description="When the transaction occurred")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "amount": 50,
                "transaction_type": "quest_reward",
                "description": "Completed daily challenge",
                "balance_after": 1550,
                "created_at": "2024-01-15T14:30:00Z"
            }
        }


class GoldTransactionListResponse(BaseModel):
    """Response for GET /economy/transactions/gold"""
    transactions: List[GoldTransactionResponse] = Field(..., description="List of gold transactions")
    total: int = Field(..., description="Total number of transactions")
    limit: int = Field(..., description="Number of transactions returned")
    offset: int = Field(..., description="Offset for pagination")

    class Config:
        json_schema_extra = {
            "example": {
                "transactions": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "amount": 50,
                        "transaction_type": "quest_reward",
                        "description": "Completed daily challenge",
                        "balance_after": 1550,
                        "created_at": "2024-01-15T14:30:00Z"
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
        }


# ============================================
# XP TRANSACTION RESPONSE
# ============================================

class XPTransactionResponse(BaseModel):
    """
    Response for an XP transaction.

    Used for tracking XP earned and level-ups.
    """
    id: str = Field(..., description="Transaction ID")
    amount: int = Field(..., description="XP gained")
    total_xp_after: int = Field(..., description="Total XP after this transaction")
    level_before: int = Field(..., description="Level before this transaction")
    level_after: int = Field(..., description="Level after this transaction")
    leveled_up: int = Field(..., description="Number of levels gained")
    source: str = Field(..., description="Source of XP (e.g., question_correct, quest_complete)")
    multiplier: float = Field(1.0, description="XP multiplier applied")
    created_at: datetime = Field(..., description="When the transaction occurred")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "amount": 100,
                "total_xp_after": 12600,
                "level_before": 15,
                "level_after": 16,
                "leveled_up": 1,
                "source": "quest_complete",
                "multiplier": 2.0,
                "created_at": "2024-01-15T14:30:00Z"
            }
        }


class XPTransactionListResponse(BaseModel):
    """Response for XP transaction history"""
    transactions: List[XPTransactionResponse] = Field(..., description="List of XP transactions")
    total: int = Field(..., description="Total number of transactions")
    limit: int = Field(..., description="Number of transactions returned")
    offset: int = Field(..., description="Offset for pagination")


# ============================================
# USER ECONOMY MODEL (Spec Requirement)
# ============================================

class UserEconomy(BaseModel):
    """
    Complete economy status for a user.

    Combines all economy-related data including currencies, XP, level, and rank.
    """
    user_id: str = Field(..., description="User's UUID")
    gold: int = Field(..., description="Current gold balance (primary currency)")
    orbs: int = Field(0, description="Knowledge orbs (secondary currency)")
    crystals: int = Field(0, description="Premium currency (gems)")
    total_xp: int = Field(..., description="Total XP earned")
    level: int = Field(..., description="Current player level")
    rank: str = Field(..., description="Current rank (E/D/C/B/A/S)")
    xp_to_next_level: int = Field(..., description="XP needed to reach next level")
    level_progress_percent: float = Field(..., description="Progress percentage toward next level")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "gold": 1500,
                "orbs": 250,
                "crystals": 25,
                "total_xp": 12500,
                "level": 15,
                "rank": "B",
                "xp_to_next_level": 500,
                "level_progress_percent": 75.5
            }
        }


# ============================================
# ADD GOLD/XP REQUESTS
# ============================================

class AddGoldRequest(BaseModel):
    """Request to add gold to a user"""
    amount: int = Field(..., gt=0, description="Amount of gold to add")
    transaction_type: str = Field(..., description="Type of transaction")
    description: Optional[str] = Field(None, description="Transaction description")

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 100,
                "transaction_type": "quest_reward",
                "description": "Completed daily challenge"
            }
        }


class SpendGoldRequest(BaseModel):
    """Request to spend gold from a user"""
    amount: int = Field(..., gt=0, description="Amount of gold to spend")
    transaction_type: str = Field(..., description="Type of transaction")
    description: Optional[str] = Field(None, description="Transaction description")

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 200,
                "transaction_type": "purchase",
                "description": "Bought streak freeze"
            }
        }


class AddXPRequest(BaseModel):
    """Request to add XP to a user"""
    amount: int = Field(..., gt=0, description="Amount of XP to add")
    source: str = Field(..., description="Source of XP")
    multiplier: float = Field(1.0, ge=0.1, le=10.0, description="XP multiplier")

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 50,
                "source": "question_correct",
                "multiplier": 1.0
            }
        }


class AddXPResponse(BaseModel):
    """Response after adding XP"""
    success: bool = Field(..., description="Whether XP was added successfully")
    xp_gained: int = Field(..., description="Actual XP gained (after multiplier)")
    total_xp: int = Field(..., description="Total XP after addition")
    level: int = Field(..., description="Current level after addition")
    leveled_up: bool = Field(..., description="Whether user leveled up")
    levels_gained: int = Field(..., description="Number of levels gained")
    xp_to_next_level: int = Field(..., description="XP needed for next level")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "xp_gained": 100,
                "total_xp": 12600,
                "level": 16,
                "leveled_up": True,
                "levels_gained": 1,
                "xp_to_next_level": 400
            }
        }


class UpdateRankRequest(BaseModel):
    """Request to update user rank based on mastery"""
    mastery_percent: float = Field(..., ge=0, le=100, description="Mastery percentage (0-100)")

    class Config:
        json_schema_extra = {
            "example": {
                "mastery_percent": 75.5
            }
        }


class UpdateRankResponse(BaseModel):
    """Response after updating rank"""
    success: bool = Field(..., description="Whether rank was updated successfully")
    new_rank: str = Field(..., description="New rank after update")
    old_rank: Optional[str] = Field(None, description="Previous rank")
    rank_changed: bool = Field(..., description="Whether rank actually changed")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "new_rank": "A",
                "old_rank": "B",
                "rank_changed": True
            }
        }
