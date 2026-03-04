"""
Hearts (Mana) System Routes - ICFES Leveling
Endpoints for hearts, mana, and Grace Mode.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from uuid import UUID

from ..core.database import get_db
from ..core.security import get_current_user
from ..models import User
from ..schemas.hearts import (
    HeartsStatusResponse,
    GraceStatusResponse,
    EnterGraceModeResponse,
    ExitGraceModeResponse,
    HeartsUseRequest,
    HeartsUseResponse,
    HeartsRefillRequest,
    HeartsRefillResponse,
)
from ..services.hearts_service import HeartsService
from ..utils.response import success_response

router = APIRouter(prefix="/hearts", tags=["Hearts"])

# ============================================
# ENDPOINTS
# ============================================

@router.get("/status")
async def get_hearts_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = HeartsService(db)
    try:
        status_data = service.get_status(current_user.id)
        return success_response(status_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while getting hearts status.")

@router.post("/use")
async def use_heart(
    request: HeartsUseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = HeartsService(db)
    try:
        result = service.use_heart(current_user.id, request.reason, UUID(request.source_id) if request.source_id else None)
        return success_response(result)
    except ValueError as e:
        if str(e) == "HEARTS_EMPTY":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "HEARTS_EMPTY", "message": "No tienes mana disponible"})
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while using a heart.")

@router.post("/refill")
async def refill_hearts(
    request: HeartsRefillRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = HeartsService(db)
    try:
        result = service.refill_hearts(current_user.id, request.method)
        return success_response(result)
    except ValueError as e:
        error_code = str(e)
        if error_code == "NOT_ENOUGH_GOLD":
            raise HTTPException(status_code=400, detail="Not enough gold")
        elif error_code == "AD_LIMIT_REACHED":
            raise HTTPException(status_code=400, detail="Ad limit reached for today")
        elif error_code == "Invalid refill method":
            raise HTTPException(status_code=400, detail="Invalid refill method")
        raise HTTPException(status_code=404, detail=error_code)
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="Purchase method not implemented.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred during refill.")

@router.get("/grace-status")
async def get_grace_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = HeartsService(db)
    try:
        status_data = service.get_grace_status(current_user.id)
        return success_response(status_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while getting grace status.")

@router.post("/enter-grace-mode")
async def enter_grace_mode(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = HeartsService(db)
    try:
        result = service.enter_grace_mode(current_user.id)
        return success_response(result)
    except ValueError as e:
        if str(e) == "HEARTS_AVAILABLE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "HEARTS_AVAILABLE", "message": "No puedes entrar a Grace Mode con mana disponible"}
            )
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/exit-grace-mode")
async def exit_grace_mode(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = HeartsService(db)
    try:
        result = service.exit_grace_mode(current_user.id)
        return success_response(result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# SPEC-COMPLIANT ENDPOINTS (per API specification)
# ============================================

@router.post("/restore-with-ad")
async def restore_heart_with_ad(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restore one heart by watching an ad.
    Max 3 ads per day.
    """
    service = HeartsService(db)
    try:
        result = service.restore_heart_with_ad(current_user.id)
        return success_response(result)
    except ValueError as e:
        error_code = str(e)
        if error_code == "AD_LIMIT_REACHED":
            raise HTTPException(status_code=400, detail="Ad limit reached for today (max 3 per day)")
        raise HTTPException(status_code=404, detail=error_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while restoring heart with ad.")


@router.post("/refill-with-gold")
async def refill_hearts_with_gold(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refill all hearts using gold.
    Cost: 150 gold.
    """
    service = HeartsService(db)
    try:
        result = service.refill_hearts_with_gold(current_user.id)
        return success_response(result)
    except ValueError as e:
        error_code = str(e)
        if error_code == "NOT_ENOUGH_GOLD":
            raise HTTPException(status_code=400, detail="Not enough gold (requires 150)")
        raise HTTPException(status_code=404, detail=error_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while refilling hearts with gold.")


@router.post("/grace-mode/enter")
async def enter_grace_mode_spec(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enter grace mode (training without XP).
    Spec-compliant endpoint path: POST /hearts/grace-mode/enter
    """
    service = HeartsService(db)
    try:
        result = service.enter_grace_mode(current_user.id)
        return success_response(result)
    except ValueError as e:
        if str(e) == "HEARTS_AVAILABLE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "HEARTS_AVAILABLE", "message": "Cannot enter Grace Mode with hearts available"}
            )
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/grace-mode/exit")
async def exit_grace_mode_spec(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exit grace mode.
    Spec-compliant endpoint path: POST /hearts/grace-mode/exit
    """
    service = HeartsService(db)
    try:
        result = service.exit_grace_mode(current_user.id)
        return success_response(result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# AD VERIFICATION ENDPOINTS
# ============================================

from pydantic import BaseModel
from typing import Optional


class AdVerificationRequest(BaseModel):
    """Request para verificar ad reward"""
    key_id: str
    signature: str
    reward_item: str = "heart"
    reward_amount: int = 1
    timestamp: int
    custom_data: Optional[str] = None


@router.post("/refill-verified")
async def refill_heart_with_verified_ad(
    verification: AdVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Refill de corazón con verificación server-side de ad.

    El cliente envía los parámetros de verificación de AdMob,
    el servidor verifica la legitimidad antes de otorgar el reward.
    """
    from ..services.admob_service import AdMobService

    admob_service = AdMobService()

    is_valid = await admob_service.verify_reward(
        key_id=verification.key_id,
        signature=verification.signature,
        user_id=str(current_user.id),
        reward_item=verification.reward_item,
        reward_amount=verification.reward_amount,
        timestamp=verification.timestamp,
        custom_data=verification.custom_data
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_AD_VERIFICATION", "message": "Verificación de anuncio fallida"}
        )

    # Verificación exitosa - otorgar reward
    hearts_service = HeartsService(db)
    result = hearts_service.refill_hearts(current_user.id, method="ad")
    return success_response(result)


@router.post("/callback/admob")
async def admob_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Callback endpoint para AdMob SSV.

    AdMob envía una request a este endpoint cuando un usuario
    completa un anuncio recompensado.
    """
    from ..services.admob_service import AdMobService

    callback_url = str(request.url)
    admob_service = AdMobService()

    result = await admob_service.verify_callback(callback_url)

    if not result.get("verified"):
        raise HTTPException(status_code=400, detail="Verification failed")

    # Procesar reward
    user_id = result.get("user_id")
    if user_id:
        try:
            hearts_service = HeartsService(db)
            hearts_service.refill_hearts(UUID(user_id), method="ad")
        except Exception as e:
            # Log pero no fallar - AdMob reintentará
            import logging
            logging.error(f"Failed to process AdMob callback for {user_id}: {e}")

    return {"status": "ok"}