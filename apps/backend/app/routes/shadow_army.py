from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..services.shadow_army_service import ShadowArmyService
from ..routes.auth import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/v1/shadow-army", tags=["shadow-army"])

class ShadowExtractionRequest(BaseModel):
    enemy_name: str = Field(..., description="Name of defeated enemy")
    enemy_level: int = Field(..., ge=1, description="Level of defeated enemy")
    battle_id: str = Field(None, description="Associated battle ID")

class ShadowSummonRequest(BaseModel):
    shadow_id: str = Field(..., description="ID of shadow to summon")

class ShadowFormationRequest(BaseModel):
    name: str = Field(..., description="Formation name")
    formation_type: str = Field(..., description="Formation type: attack, defense, balanced, speed")
    shadow_positions: Dict[str, str] = Field(..., description="Position mapping for shadows")

@router.get("/stats", response_model=Dict[str, Any])
async def get_shadow_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's shadow monarch stats"""
    service = ShadowArmyService(db)
    stats = service.get_user_shadow_stats(str(current_user.id))
    
    if not stats:
        stats = service.initialize_user_shadow_system(str(current_user.id))
    
    return {
        "monarch_level": stats.monarch_level,
        "monarch_experience": stats.monarch_experience,
        "shadow_capacity": stats.shadow_capacity,
        "extraction_power": stats.extraction_power,
        "total_shadows_extracted": stats.total_shadows_extracted,
        "active_shadows": stats.active_shadows,
        "highest_rank_shadow": stats.highest_rank_shadow,
        "total_shadow_battles": stats.total_shadow_battles,
        "total_shadow_victories": stats.total_shadow_victories,
        "monarch_abilities": stats.monarch_abilities,
        "can_command_multiple": stats.can_command_multiple,
        "can_shadow_exchange": stats.can_shadow_exchange
    }

@router.get("/shadows", response_model=List[Dict[str, Any]])
async def get_user_shadows(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's shadow army"""
    service = ShadowArmyService(db)
    shadows = service.get_user_shadows(str(current_user.id), active_only)
    
    return [
        {
            "id": str(shadow.id),
            "name": shadow.name,
            "shadow_type": shadow.shadow_type,
            "rank": shadow.rank,
            "level": shadow.level,
            "experience": shadow.experience,
            "stats": {
                "attack_power": shadow.attack_power,
                "defense": shadow.defense,
                "magic_power": shadow.magic_power,
                "speed": shadow.speed,
                "health": shadow.health,
                "mana": shadow.mana,
                "combat_power": shadow.get_combat_power()
            },
            "loyalty": shadow.loyalty,
            "extraction_source": shadow.extraction_source,
            "special_abilities": shadow.special_abilities,
            "equipment": shadow.equipment,
            "is_summoned": shadow.is_summoned,
            "battles_won": shadow.battles_won,
            "battles_lost": shadow.battles_lost,
            "can_evolve": shadow.can_evolve(),
            "created_at": shadow.created_at
        }
        for shadow in shadows
    ]

@router.post("/extract", response_model=Dict[str, Any])
async def attempt_shadow_extraction(
    request: ShadowExtractionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Attempt to extract shadow from defeated enemy"""
    service = ShadowArmyService(db)
    
    result = service.attempt_shadow_extraction(
        str(current_user.id),
        request.enemy_name,
        request.enemy_level,
        request.battle_id
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result

@router.post("/summon", response_model=Dict[str, Any])
async def summon_shadow(
    request: ShadowSummonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Summon shadow for battle"""
    service = ShadowArmyService(db)
    
    result = service.summon_shadow(str(current_user.id), request.shadow_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result

@router.post("/dismiss/{shadow_id}", response_model=Dict[str, Any])
async def dismiss_shadow(
    shadow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dismiss a summoned shadow"""
    service = ShadowArmyService(db)
    
    result = service.dismiss_shadow(str(current_user.id), shadow_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result

@router.post("/evolve/{shadow_id}", response_model=Dict[str, Any])
async def evolve_shadow(
    shadow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Evolve shadow to next rank"""
    service = ShadowArmyService(db)
    
    result = service.evolve_shadow(str(current_user.id), shadow_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result

@router.post("/formations", response_model=Dict[str, Any])
async def create_formation(
    request: ShadowFormationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a shadow formation"""
    service = ShadowArmyService(db)
    
    result = service.create_formation(
        str(current_user.id),
        request.name,
        request.formation_type,
        request.shadow_positions
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result

@router.get("/battle-history", response_model=List[Dict[str, Any]])
async def get_shadow_battle_history(
    shadow_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get shadow battle history"""
    service = ShadowArmyService(db)
    return service.get_shadow_battle_history(str(current_user.id), shadow_id)

@router.get("/extraction-history", response_model=List[Dict[str, Any]])
async def get_extraction_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get shadow extraction history"""
    service = ShadowArmyService(db)
    return service.get_extraction_history(str(current_user.id), limit)

@router.post("/regenerate-power", response_model=Dict[str, Any])
async def regenerate_extraction_power(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate user's extraction power"""
    service = ShadowArmyService(db)
    return service.regenerate_extraction_power(str(current_user.id))