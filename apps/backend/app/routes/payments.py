"""
Rutas API para pagos y suscripciones con Wompi
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.subscription import Subscription, Payment, PaymentMethod, Coupon, CouponUsage
from ..services.wompi_service import wompi_service
from ..schemas.payment import (
    PaymentLinkRequest,
    PaymentLinkResponse,
    SubscriptionRequest,
    SubscriptionResponse,
    PaymentMethodRequest,
    PaymentMethodResponse,
    WebhookPayload,
    PlanResponse,
    InvoiceResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/payments",
    tags=["payments"]
)

@router.get("/plans", response_model=List[PlanResponse])
async def get_subscription_plans():
    """
    Obtener planes de suscripción disponibles
    """
    plans = []
    for plan_id, plan_data in wompi_service.subscription_plans.items():
        plans.append({
            "id": plan_id,
            "name": plan_data["name"],
            "price": plan_data["price_cop"],
            "currency": "COP",
            "features": plan_data["features"],
            "duration_days": plan_data["duration_days"],
            "xp_bonus": plan_data["xp_bonus"],
            "orbs_monthly": plan_data["orbs_monthly"],
            "popular": plan_id == "premium",  # Marcar plan premium como popular
            "savings": "20%" if plan_id == "elite" else None
        })
    
    return plans

@router.post("/create-payment-link", response_model=PaymentLinkResponse)
async def create_payment_link(
    request: PaymentLinkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear link de pago con Wompi
    """
    # Verificar si el usuario ya tiene una suscripción activa
    existing_subscription = db.query(Subscription).filter(
        Subscription.user_id == str(current_user.id),
        Subscription.status == "active"
    ).first()
    
    if existing_subscription and request.plan_id != "elite":
        raise HTTPException(
            status_code=400,
            detail="Ya tienes una suscripción activa"
        )
    
    # Aplicar cupón si se proporciona
    discount_amount = 0
    if request.coupon_code:
        coupon = db.query(Coupon).filter(
            Coupon.code == request.coupon_code,
            Coupon.is_active == True
        ).first()
        
        if not coupon:
            raise HTTPException(
                status_code=400,
                detail="Cupón inválido"
            )
        
        # Verificar si el cupón es válido
        now = datetime.utcnow()
        if coupon.valid_until and coupon.valid_until < now:
            raise HTTPException(
                status_code=400,
                detail="Cupón expirado"
            )
        
        # Verificar límite de uso
        if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
            raise HTTPException(
                status_code=400,
                detail="Cupón agotado"
            )
        
        # Verificar uso previo por el usuario
        previous_usage = db.query(CouponUsage).filter(
            CouponUsage.coupon_id == coupon.id,
            CouponUsage.user_id == str(current_user.id)
        ).count()
        
        if previous_usage >= (coupon.usage_limit_per_user or 1):
            raise HTTPException(
                status_code=400,
                detail="Ya has usado este cupón"
            )
        
        # Calcular descuento
        plan = wompi_service.subscription_plans[request.plan_id]
        if coupon.discount_type == "percentage":
            discount_amount = plan["price_cop"] * (coupon.discount_value / 100)
        else:
            discount_amount = float(coupon.discount_value)
    
    # Crear link de pago
    result = await wompi_service.create_payment_link(
        user=current_user,
        plan_id=request.plan_id,
        redirect_url=request.redirect_url
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Error creando link de pago")
        )
    
    # Guardar referencia del pago pendiente
    payment = Payment(
        user_id=str(current_user.id),
        amount=wompi_service.subscription_plans[request.plan_id]["price_cop"] - discount_amount,
        currency="COP",
        status="pending",
        reference=result["reference"],
        wompi_payment_link_id=result["link_id"],
        description=f"Suscripción {wompi_service.subscription_plans[request.plan_id]['name']}"
    )
    db.add(payment)
    
    # Si hay cupón, registrar su uso pendiente
    if request.coupon_code and discount_amount > 0:
        coupon_usage = CouponUsage(
            coupon_id=coupon.id,
            user_id=str(current_user.id),
            payment_id=payment.id,
            discount_amount=discount_amount
        )
        db.add(coupon_usage)
    
    db.commit()
    
    return {
        "payment_url": result["payment_url"],
        "reference": result["reference"],
        "expires_at": result["expires_at"],
        "amount": wompi_service.subscription_plans[request.plan_id]["price_cop"] - discount_amount,
        "discount_applied": discount_amount > 0,
        "discount_amount": discount_amount
    }

@router.post("/subscribe", response_model=SubscriptionResponse)
async def create_subscription(
    request: SubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear suscripción recurrente
    """
    # Verificar método de pago
    if request.payment_method_id:
        payment_method = db.query(PaymentMethod).filter(
            PaymentMethod.id == request.payment_method_id,
            PaymentMethod.user_id == str(current_user.id)
        ).first()
        
        if not payment_method:
            raise HTTPException(
                status_code=404,
                detail="Método de pago no encontrado"
            )
        
        card_token = payment_method.token
    else:
        card_token = request.card_token
    
    # Crear suscripción con Wompi
    result = await wompi_service.create_subscription(
        user=current_user,
        plan_id=request.plan_id,
        payment_method=request.payment_method,
        card_token=card_token
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Error creando suscripción")
        )
    
    # Guardar suscripción en base de datos
    plan = wompi_service.subscription_plans[request.plan_id]
    subscription = Subscription(
        user_id=str(current_user.id),
        plan_id=request.plan_id,
        plan_name=plan["name"],
        status="processing",
        price=plan["price_cop"],
        currency="COP",
        wompi_subscription_id=result["subscription_id"],
        features=plan["features"],
        xp_multiplier=plan["xp_bonus"],
        monthly_orbs=plan["orbs_monthly"]
    )
    db.add(subscription)
    db.commit()
    
    return {
        "subscription_id": subscription.id,
        "status": subscription.status,
        "plan_name": subscription.plan_name,
        "next_billing_date": result.get("next_payment_date")
    }

@router.post("/webhook/wompi")
async def handle_wompi_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook para recibir notificaciones de Wompi
    """
    # Obtener datos del webhook
    try:
        data = await request.json()
        signature = request.headers.get("X-Wompi-Signature", "")
        event_type = data.get("event")
        
        # Procesar webhook en background
        background_tasks.add_task(
            wompi_service.process_webhook,
            event_type,
            data.get("data", {}),
            signature
        )
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Error procesando webhook"
        )

@router.get("/subscription/status")
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener estado de suscripción del usuario
    """
    subscription = db.query(Subscription).filter(
        Subscription.user_id == str(current_user.id),
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        return {
            "has_subscription": False,
            "plan": "free",
            "features": wompi_service.subscription_plans.get("free", {}).get("features", [])
        }
    
    return {
        "has_subscription": True,
        "plan": subscription.plan_id,
        "plan_name": subscription.plan_name,
        "status": subscription.status,
        "end_date": subscription.end_date,
        "auto_renew": subscription.auto_renew,
        "features": subscription.features,
        "xp_multiplier": subscription.xp_multiplier,
        "monthly_orbs": subscription.monthly_orbs,
        "days_remaining": (subscription.end_date - datetime.utcnow()).days if subscription.end_date else 0
    }

@router.post("/subscription/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancelar suscripción activa
    """
    subscription = db.query(Subscription).filter(
        Subscription.user_id == str(current_user.id),
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=404,
            detail="No tienes una suscripción activa"
        )
    
    # Cancelar en Wompi
    if subscription.wompi_subscription_id:
        success = await wompi_service.cancel_subscription(
            user_id=str(current_user.id),
            subscription_id=subscription.wompi_subscription_id
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Error cancelando suscripción"
            )
    
    # Actualizar en base de datos
    subscription.status = "cancelled"
    subscription.cancelled_at = datetime.utcnow()
    subscription.auto_renew = False
    
    db.commit()
    
    return {
        "message": "Suscripción cancelada exitosamente",
        "active_until": subscription.end_date
    }

@router.post("/payment-method/add", response_model=PaymentMethodResponse)
async def add_payment_method(
    request: PaymentMethodRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Agregar método de pago
    """
    # Verificar si es el primer método de pago
    existing_methods = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == str(current_user.id)
    ).count()
    
    payment_method = PaymentMethod(
        user_id=str(current_user.id),
        type=request.type,
        token=request.token,
        last_four=request.last_four,
        card_brand=request.card_brand,
        card_holder=request.card_holder,
        expiry_month=request.expiry_month,
        expiry_year=request.expiry_year,
        is_default=existing_methods == 0 or request.set_as_default
    )
    
    # Si se marca como default, desmarcar otros
    if request.set_as_default:
        db.query(PaymentMethod).filter(
            PaymentMethod.user_id == str(current_user.id)
        ).update({"is_default": False})
    
    db.add(payment_method)
    db.commit()
    
    return {
        "id": payment_method.id,
        "type": payment_method.type,
        "last_four": payment_method.last_four,
        "card_brand": payment_method.card_brand,
        "is_default": payment_method.is_default
    }

@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener métodos de pago del usuario
    """
    methods = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == str(current_user.id)
    ).all()
    
    return [
        {
            "id": method.id,
            "type": method.type,
            "last_four": method.last_four,
            "card_brand": method.card_brand,
            "is_default": method.is_default,
            "expiry": f"{method.expiry_month}/{method.expiry_year}" if method.expiry_month else None
        }
        for method in methods
    ]

@router.delete("/payment-method/{method_id}")
async def delete_payment_method(
    method_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar método de pago
    """
    method = db.query(PaymentMethod).filter(
        PaymentMethod.id == method_id,
        PaymentMethod.user_id == str(current_user.id)
    ).first()
    
    if not method:
        raise HTTPException(
            status_code=404,
            detail="Método de pago no encontrado"
        )
    
    # Verificar si tiene suscripciones activas
    active_subscription = db.query(Subscription).filter(
        Subscription.user_id == str(current_user.id),
        Subscription.payment_method_id == method_id,
        Subscription.status == "active"
    ).first()
    
    if active_subscription:
        raise HTTPException(
            status_code=400,
            detail="No puedes eliminar un método de pago con suscripción activa"
        )
    
    db.delete(method)
    db.commit()
    
    return {"message": "Método de pago eliminado"}

@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener facturas del usuario
    """
    payments = db.query(Payment).filter(
        Payment.user_id == str(current_user.id),
        Payment.status == "completed"
    ).order_by(Payment.created_at.desc()).limit(20).all()
    
    invoices = []
    for payment in payments:
        invoices.append({
            "id": payment.id,
            "invoice_number": f"INV-{payment.created_at.strftime('%Y%m')}-{payment.id[:8].upper()}",
            "amount": float(payment.amount),
            "currency": payment.currency,
            "status": "paid",
            "date": payment.paid_at or payment.created_at,
            "description": payment.description,
            "download_url": f"/api/v1/payments/invoice/{payment.id}/download"
        })
    
    return invoices

@router.get("/payment-history")
async def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener historial de pagos
    """
    payments = db.query(Payment).filter(
        Payment.user_id == str(current_user.id)
    ).order_by(Payment.created_at.desc()).limit(50).all()
    
    return [
        {
            "id": payment.id,
            "amount": float(payment.amount),
            "currency": payment.currency,
            "status": payment.status.value if hasattr(payment.status, 'value') else payment.status,
            "payment_method": payment.payment_method,
            "description": payment.description,
            "date": payment.created_at,
            "reference": payment.reference
        }
        for payment in payments
    ]