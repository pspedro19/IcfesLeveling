from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User

router = APIRouter(prefix="/premium", tags=["premium"])

# Mock data para desarrollo
MOCK_PLANS = [
    {
        "id": "basic",
        "name": "Plan Básico",
        "price": 9.99,
        "currency": "USD",
        "features": [
            "Acceso completo a todo el contenido",
            "Batallas ilimitadas",
            "AI explicaciones personalizadas",
            "Soporte por email"
        ]
    },
    {
        "id": "premium",
        "name": "Plan Premium",
        "price": 19.99,
        "currency": "USD",
        "features": [
            "Todo lo del Plan Básico",
            "Acceso a guilds premium",
            "Eventos especiales",
            "Mentores AI avanzados",
            "Soporte prioritario"
        ]
    }
]

@router.get("/plans")
async def get_premium_plans():
    """Obtener los planes premium disponibles"""
    return {"plans": MOCK_PLANS}

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
    # Por ahora, todos los usuarios tienen acceso premium en desarrollo
    return {
        "is_premium": True,
        "plan": "premium",
        "expires_at": datetime.now() + timedelta(days=365),
        "features_enabled": [
            "unlimited_battles",
            "ai_explanations",
            "premium_guilds",
            "advanced_mentors"
        ]
    }

@router.post("/activate")
async def activate_premium(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activar premium para un usuario (simulado para desarrollo)"""
    return {
        "success": True,
        "message": "Premium activated successfully (mock)",
        "expires_at": datetime.now() + timedelta(days=365)
    }