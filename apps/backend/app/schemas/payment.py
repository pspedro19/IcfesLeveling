"""
Schemas para pagos y suscripciones
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

class PlanResponse(BaseModel):
    """Respuesta con información del plan"""
    id: str
    name: str
    price: float
    currency: str = "COP"
    features: List[str]
    duration_days: int
    xp_bonus: float
    orbs_monthly: int
    popular: bool = False
    savings: Optional[str] = None

class PaymentLinkRequest(BaseModel):
    """Solicitud para crear link de pago"""
    plan_id: str = Field(..., description="ID del plan a comprar")
    redirect_url: Optional[str] = Field(None, description="URL de redirección después del pago")
    coupon_code: Optional[str] = Field(None, description="Código de cupón de descuento")

class PaymentLinkResponse(BaseModel):
    """Respuesta con link de pago"""
    payment_url: str
    reference: str
    expires_at: str
    amount: float
    discount_applied: bool = False
    discount_amount: float = 0

class SubscriptionRequest(BaseModel):
    """Solicitud para crear suscripción"""
    plan_id: str
    payment_method: str = Field(..., description="CARD, NEQUI, PSE, etc")
    payment_method_id: Optional[str] = Field(None, description="ID del método de pago guardado")
    card_token: Optional[str] = Field(None, description="Token de tarjeta de Wompi")

class SubscriptionResponse(BaseModel):
    """Respuesta de suscripción"""
    subscription_id: str
    status: str
    plan_name: str
    next_billing_date: Optional[datetime] = None

class PaymentMethodRequest(BaseModel):
    """Solicitud para agregar método de pago"""
    type: str = Field(..., description="CARD, NEQUI, PSE")
    token: str = Field(..., description="Token de Wompi")
    last_four: Optional[str] = None
    card_brand: Optional[str] = None
    card_holder: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    set_as_default: bool = False

class PaymentMethodResponse(BaseModel):
    """Respuesta de método de pago"""
    id: str
    type: str
    last_four: Optional[str] = None
    card_brand: Optional[str] = None
    is_default: bool
    expiry: Optional[str] = None

class WebhookPayload(BaseModel):
    """Payload de webhook de Wompi"""
    event: str
    data: Dict[str, Any]
    timestamp: datetime
    signature: Optional[str] = None

class InvoiceResponse(BaseModel):
    """Respuesta de factura"""
    id: str
    invoice_number: str
    amount: float
    currency: str
    status: str
    date: datetime
    description: Optional[str] = None
    download_url: str

class PaymentStatusResponse(BaseModel):
    """Estado de pago"""
    id: str
    status: str
    amount: float
    currency: str
    payment_method: str
    created_at: datetime
    paid_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

class CouponValidationRequest(BaseModel):
    """Solicitud de validación de cupón"""
    code: str
    plan_id: str

class CouponValidationResponse(BaseModel):
    """Respuesta de validación de cupón"""
    valid: bool
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    final_price: Optional[float] = None
    message: Optional[str] = None

class SubscriptionStatusResponse(BaseModel):
    """Estado de suscripción del usuario"""
    has_subscription: bool
    plan: str
    plan_name: Optional[str] = None
    status: Optional[str] = None
    end_date: Optional[datetime] = None
    auto_renew: bool = False
    features: List[str] = []
    xp_multiplier: float = 1.0
    monthly_orbs: int = 0
    days_remaining: int = 0

class PaymentHistoryItem(BaseModel):
    """Item del historial de pagos"""
    id: str
    amount: float
    currency: str
    status: str
    payment_method: str
    description: Optional[str] = None
    date: datetime
    reference: str

class CheckoutSessionRequest(BaseModel):
    """Solicitud para crear sesión de checkout"""
    plan_id: str
    payment_method_preference: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    customer_document: Optional[str] = None

class CheckoutSessionResponse(BaseModel):
    """Respuesta de sesión de checkout"""
    session_id: str
    checkout_url: str
    public_key: str
    amount: float
    currency: str
    expires_at: datetime

class RefundRequest(BaseModel):
    """Solicitud de reembolso"""
    payment_id: str
    reason: str
    amount: Optional[float] = None  # None para reembolso completo

class RefundResponse(BaseModel):
    """Respuesta de reembolso"""
    refund_id: str
    status: str
    amount: float
    currency: str
    reason: str
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True