from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.subscription import Subscription

router = APIRouter(prefix="/premium", tags=["premium"])

@router.get("/plans")
async def get_premium_plans(db: Session = Depends(get_db)):
    """Obtener los planes premium disponibles"""
    try:
        # Define standard premium plans based on PlanType enum
        plans = [
            {
                "id": "basic",
                "name": "Plan Básico", 
                "price": 9.99,
                "currency": "COP",
                "billing_cycle": "monthly",
                "features": [
                    "Acceso completo a todo el contenido",
                    "Batallas ilimitadas", 
                    "AI explicaciones personalizadas",
                    "Soporte por email"
                ],
                "xp_multiplier": 1.2,
                "monthly_orbs": 100,
                "shadow_slots": 5
            },
            {
                "id": "premium", 
                "name": "Plan Premium",
                "price": 19.99,
                "currency": "COP",
                "billing_cycle": "monthly", 
                "features": [
                    "Todo lo del Plan Básico",
                    "Acceso a guilds premium",
                    "Eventos especiales",
                    "Mentores AI avanzados",
                    "Soporte prioritario"
                ],
                "xp_multiplier": 1.5,
                "monthly_orbs": 200,
                "shadow_slots": 10
            },
            {
                "id": "elite",
                "name": "Plan Elite", 
                "price": 29.99,
                "currency": "COP",
                "billing_cycle": "monthly",
                "features": [
                    "Todo lo del Plan Premium",
                    "Análisis avanzado de rendimiento",
                    "Tutorías personalizadas", 
                    "Contenido exclusivo",
                    "Soporte 24/7"
                ],
                "xp_multiplier": 2.0,
                "monthly_orbs": 300,
                "shadow_slots": 15
            }
        ]
        
        return {"plans": plans}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener planes: {str(e)}"
        )

@router.post("/create-checkout-session")
async def create_checkout_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear una sesión de checkout (simulada para desarrollo)"""
    return {
        "checkout_url": "https://example.com/checkout",
        "session_id": "mock_session_123",
        "success": True,
        "message": "Checkout session created successfully (mock)"
    }

@router.get("/status")
async def get_premium_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener el estado premium del usuario"""
    try:
        # Get user's active subscription from database
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.status == "active"
        ).first()
        
        if subscription:
            # User has active subscription
            is_premium = True
            plan_id = subscription.plan_id
            expires_at = subscription.end_date
            
            # Get features based on plan
            features_enabled = []
            if subscription.features:
                features_enabled = subscription.features.get("features", [])
            else:
                # Default features based on plan
                if plan_id == "basic":
                    features_enabled = ["unlimited_battles", "ai_explanations"]
                elif plan_id == "premium":
                    features_enabled = ["unlimited_battles", "ai_explanations", "premium_guilds", "advanced_mentors"]
                elif plan_id == "elite":
                    features_enabled = ["unlimited_battles", "ai_explanations", "premium_guilds", "advanced_mentors", "advanced_analytics", "personal_tutoring"]
                else:
                    features_enabled = ["unlimited_battles"]
        else:
            # Check if user has premium_plan in their user record (legacy)
            if hasattr(current_user, 'premium_plan') and current_user.premium_plan and current_user.premium_plan != "free":
                is_premium = True
                plan_id = current_user.premium_plan
                expires_at = datetime.now() + timedelta(days=365)  # Default expiry
                features_enabled = ["unlimited_battles", "ai_explanations"]
            else:
                # Free user
                is_premium = False
                plan_id = "free" 
                expires_at = None
                features_enabled = []
        
        return {
            "is_premium": is_premium,
            "plan": plan_id,
            "expires_at": expires_at,
            "features_enabled": features_enabled,
            "xp_multiplier": subscription.xp_multiplier if subscription else 1.0,
            "monthly_orbs": subscription.monthly_orbs if subscription else 0,
            "shadow_slots": subscription.shadow_slots if subscription else 3
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estado premium: {str(e)}"
        )

@router.post("/activate")
async def activate_premium(
    plan_id: str = "basic",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activar premium para un usuario"""
    try:
        # Check if user already has an active subscription
        existing_subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.status == "active"
        ).first()
        
        if existing_subscription:
            return {
                "success": False,
                "message": "Usuario ya tiene una suscripción activa",
                "current_plan": existing_subscription.plan_id
            }
        
        # Create new subscription
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)  # 30 days subscription
        
        # Set plan details based on plan_id
        plan_details = {
            "basic": {"price": 9.99, "xp_multiplier": 1.2, "monthly_orbs": 100, "shadow_slots": 5},
            "premium": {"price": 19.99, "xp_multiplier": 1.5, "monthly_orbs": 200, "shadow_slots": 10},
            "elite": {"price": 29.99, "xp_multiplier": 2.0, "monthly_orbs": 300, "shadow_slots": 15}
        }
        
        plan_info = plan_details.get(plan_id, plan_details["basic"])
        
        new_subscription = Subscription(
            user_id=current_user.id,
            plan_id=plan_id,
            plan_name=f"Plan {plan_id.capitalize()}",
            status="active",
            start_date=start_date,
            end_date=end_date,
            price=plan_info["price"],
            currency="COP",
            billing_cycle="monthly",
            xp_multiplier=plan_info["xp_multiplier"],
            monthly_orbs=plan_info["monthly_orbs"],
            shadow_slots=plan_info["shadow_slots"],
            features={
                "features": [
                    "unlimited_battles",
                    "ai_explanations"
                ] + (["premium_guilds", "advanced_mentors"] if plan_id != "basic" else [])
            }
        )
        
        db.add(new_subscription)
        
        # Also update user's premium_plan field for compatibility
        current_user.premium_plan = plan_id
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Plan {plan_id} activado exitosamente",
            "plan": plan_id,
            "expires_at": end_date,
            "features": new_subscription.features
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al activar premium: {str(e)}"
        )