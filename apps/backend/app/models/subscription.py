"""
Modelos para sistema de suscripciones y pagos
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey, Enum, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from ..core.database import Base

class PlanType(enum.Enum):
    """Tipos de planes de suscripción"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ELITE = "elite"

class PaymentStatus(enum.Enum):
    """Estados de pago"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class Subscription(Base):
    """Modelo de suscripción de usuario"""
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan_id = Column(String, nullable=False)
    plan_name = Column(String, nullable=False)
    status = Column(String, default="inactive")  # active, inactive, cancelled, expired
    
    # Fechas
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    cancelled_at = Column(DateTime)
    trial_ends_at = Column(DateTime)
    
    # Precio y facturación
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="COP")
    billing_cycle = Column(String, default="monthly")  # monthly, quarterly, yearly
    next_billing_date = Column(DateTime)
    
    # Integración con Wompi
    wompi_subscription_id = Column(String)
    wompi_customer_id = Column(String)
    wompi_plan_id = Column(String)
    
    # Beneficios del plan
    features = Column(JSON)
    xp_multiplier = Column(Float, default=1.0)
    monthly_orbs = Column(Integer, default=0)
    shadow_slots = Column(Integer, default=3)
    daily_questions_limit = Column(Integer)
    
    # Configuración
    auto_renew = Column(Boolean, default=True)
    payment_method_id = Column(String, ForeignKey("payment_methods.id"))
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="subscription")
    payments = relationship("Payment", back_populates="subscription")
    payment_method = relationship("PaymentMethod", back_populates="subscriptions")

class Payment(Base):
    """Modelo de pagos realizados"""
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subscription_id = Column(String, ForeignKey("subscriptions.id"))
    
    # Información del pago
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="COP")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_method = Column(String)  # CARD, NEQUI, PSE, etc
    
    # Referencias de Wompi
    wompi_transaction_id = Column(String, unique=True)
    wompi_payment_link_id = Column(String)
    reference = Column(String, unique=True)
    authorization_code = Column(String)
    
    # Detalles de la transacción
    description = Column(Text)
    invoice_number = Column(String)
    tax_amount = Column(Numeric(10, 2), default=0)
    
    # Información del pagador
    payer_email = Column(String)
    payer_name = Column(String)
    payer_phone = Column(String)
    payer_document = Column(String)
    
    # Respuesta de la pasarela
    gateway_response = Column(JSON)
    failure_reason = Column(Text)
    failure_code = Column(String)
    
    # Fechas
    paid_at = Column(DateTime)
    failed_at = Column(DateTime)
    refunded_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")

class PaymentMethod(Base):
    """Métodos de pago guardados del usuario"""
    __tablename__ = "payment_methods"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Tipo de método de pago
    type = Column(String, nullable=False)  # CARD, NEQUI, PSE
    provider = Column(String, default="wompi")
    
    # Información tokenizada (segura)
    token = Column(String)  # Token de Wompi
    last_four = Column(String)  # Últimos 4 dígitos de tarjeta
    card_brand = Column(String)  # VISA, MASTERCARD, etc
    card_holder = Column(String)
    expiry_month = Column(Integer)
    expiry_year = Column(Integer)
    
    # Cuenta bancaria (para PSE/Nequi)
    bank_name = Column(String)
    account_type = Column(String)  # savings, checking
    
    # Estado
    is_default = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime)
    
    # Relaciones
    user = relationship("User", back_populates="payment_methods")
    subscriptions = relationship("Subscription", back_populates="payment_method")

class Invoice(Base):
    """Facturas generadas"""
    __tablename__ = "invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    payment_id = Column(String, ForeignKey("payments.id"))
    subscription_id = Column(String, ForeignKey("subscriptions.id"))
    
    # Información de factura
    invoice_number = Column(String, unique=True, nullable=False)
    invoice_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    
    # Montos
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="COP")
    
    # Estado
    status = Column(String, default="pending")  # pending, paid, overdue, cancelled
    paid_at = Column(DateTime)
    
    # Información fiscal
    customer_name = Column(String)
    customer_document = Column(String)
    customer_address = Column(Text)
    customer_city = Column(String)
    customer_email = Column(String)
    
    # Items de la factura
    items = Column(JSON)  # Lista de items con descripción, cantidad, precio
    
    # URLs
    pdf_url = Column(String)
    public_url = Column(String)
    
    # Metadata
    notes = Column(Text)
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="invoices")
    payment = relationship("Payment")

class Coupon(Base):
    """Cupones de descuento"""
    __tablename__ = "coupons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    description = Column(Text)
    
    # Tipo de descuento
    discount_type = Column(String, nullable=False)  # percentage, fixed
    discount_value = Column(Numeric(10, 2), nullable=False)
    
    # Aplicabilidad
    applicable_plans = Column(JSON)  # Lista de plan_ids donde aplica
    minimum_amount = Column(Numeric(10, 2))
    
    # Límites
    usage_limit = Column(Integer)  # Límite total de usos
    usage_count = Column(Integer, default=0)
    usage_limit_per_user = Column(Integer, default=1)
    
    # Validez
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_by = Column(String)
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CouponUsage(Base):
    """Registro de uso de cupones"""
    __tablename__ = "coupon_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coupon_id = Column(String, ForeignKey("coupons.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    payment_id = Column(String, ForeignKey("payments.id"))
    
    # Descuento aplicado
    discount_amount = Column(Numeric(10, 2), nullable=False)
    
    # Fecha de uso
    used_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    coupon = relationship("Coupon")
    user = relationship("User")
    payment = relationship("Payment")