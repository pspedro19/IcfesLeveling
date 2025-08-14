from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class TransactionType(str, Enum):
    PURCHASE = "purchase"
    REFUND = "refund"

class CurrencyType(str, Enum):
    ORBS = "orbs"
    CRYSTALS = "crystals"

class TransactionStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class StoreItemBase(BaseModel):
    name: str = Field(..., description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    item_type: str = Field(..., description="Item type")
    rarity: str = Field("common", description="Item rarity")
    icon_url: Optional[str] = Field(None, description="Icon URL")
    store_price_orbs: int = Field(0, description="Price in orbs")
    store_price_crystals: int = Field(0, description="Price in crystals")
    is_available_in_store: bool = Field(False, description="Available in store")
    is_cosmetic: bool = Field(False, description="Is cosmetic item")
    is_power_up: bool = Field(False, description="Is power-up item")
    power_up_effect: Dict[str, Any] = Field(default_factory=dict, description="Power-up effect data")

class StoreItemResponse(StoreItemBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class StoreTransactionBase(BaseModel):
    transaction_type: TransactionType = Field(..., description="Transaction type")
    currency_type: CurrencyType = Field(..., description="Currency used")
    amount_spent: int = Field(..., description="Amount spent")
    quantity: int = Field(1, description="Quantity purchased")
    status: TransactionStatus = Field(TransactionStatus.COMPLETED, description="Transaction status")
    notes: Optional[str] = Field(None, description="Transaction notes")

class StoreTransactionCreate(StoreTransactionBase):
    item_id: str = Field(..., description="Item ID to purchase")

class StoreTransactionResponse(StoreTransactionBase):
    id: str
    user_id: str
    item_id: str
    transaction_date: datetime
    item: StoreItemResponse
    
    class Config:
        from_attributes = True

class UserPowerUpBase(BaseModel):
    is_active: bool = Field(True, description="Is power-up active")
    activated_at: datetime = Field(..., description="When activated")
    expires_at: Optional[datetime] = Field(None, description="When expires")
    uses_remaining: int = Field(1, description="Uses remaining")
    effect_data: Dict[str, Any] = Field(default_factory=dict, description="Effect data")

class UserPowerUpCreate(UserPowerUpBase):
    item_id: str = Field(..., description="Power-up item ID")

class UserPowerUpResponse(UserPowerUpBase):
    id: str
    user_id: str
    item_id: str
    item: StoreItemResponse
    is_expired: bool = Field(False, description="Is power-up expired")
    can_use: bool = Field(True, description="Can use power-up")
    
    class Config:
        from_attributes = True

class CurrencyEarningBase(BaseModel):
    currency_type: CurrencyType = Field(..., description="Currency type")
    amount: int = Field(..., description="Amount earned")
    source: str = Field(..., description="Earning source")
    source_id: Optional[str] = Field(None, description="Source ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class CurrencyEarningCreate(CurrencyEarningBase):
    pass

class CurrencyEarningResponse(CurrencyEarningBase):
    id: str
    user_id: str
    earned_at: datetime
    
    class Config:
        from_attributes = True

class StorePurchaseRequest(BaseModel):
    item_id: str = Field(..., description="Item ID to purchase")
    quantity: int = Field(1, description="Quantity to purchase")
    currency_type: CurrencyType = Field(..., description="Currency to use")

class StorePurchaseResponse(BaseModel):
    success: bool = Field(..., description="Purchase success")
    message: str = Field(..., description="Response message")
    transaction: Optional[StoreTransactionResponse] = Field(None, description="Transaction details")
    remaining_orbs: int = Field(0, description="Remaining orbs")
    remaining_crystals: int = Field(0, description="Remaining crystals")

class UserCurrencyResponse(BaseModel):
    orbs: int = Field(0, description="Current orbs")
    crystals: int = Field(0, description="Current crystals")
    total_earned_orbs: int = Field(0, description="Total orbs earned")
    total_earned_crystals: int = Field(0, description="Total crystals earned")

class StoreInventoryResponse(BaseModel):
    cosmetic_items: List[StoreItemResponse] = Field(default_factory=list, description="Cosmetic items")
    power_up_items: List[StoreItemResponse] = Field(default_factory=list, description="Power-up items")
    user_currency: UserCurrencyResponse = Field(..., description="User currency")

class PowerUpActivationRequest(BaseModel):
    power_up_id: str = Field(..., description="Power-up ID to activate")

class PowerUpActivationResponse(BaseModel):
    success: bool = Field(..., description="Activation success")
    message: str = Field(..., description="Response message")
    power_up: Optional[UserPowerUpResponse] = Field(None, description="Activated power-up")

class CurrencyEarningSummary(BaseModel):
    total_orbs_earned: int = Field(0, description="Total orbs earned")
    total_crystals_earned: int = Field(0, description="Total crystals earned")
    earnings_by_source: Dict[str, int] = Field(default_factory=dict, description="Earnings by source")
    recent_earnings: List[CurrencyEarningResponse] = Field(default_factory=list, description="Recent earnings") 