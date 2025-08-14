from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CreateCheckoutSession(BaseModel):
    planId: str
    priceId: str
    userId: str

class PaymentIntentCreate(BaseModel):
    amount: int
    currency: str = "COP"

class PaymentIntentResponse(BaseModel):
    clientSecret: str
    amount: int
    currency: str

class SubscriptionResponse(BaseModel):
    is_premium: bool
    premium_plan: Optional[str]
    premium_expires_at: Optional[datetime]
    ai_requests_used: int
    ai_requests_limit: int
    simulacros_used: int
    simulacros_limit: int

class WebhookEvent(BaseModel):
    type: str
    data: dict