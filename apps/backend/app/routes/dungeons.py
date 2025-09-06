from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..services.dungeon_service import DungeonService
from ..routes.auth import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/v1/dungeons", tags=["dungeons"])

class EncounterAnswersRequest(BaseModel):
    answers: List[str] = Field(..., description="List of answers for encounter questions")
    shadows_used: Optional[List[str]] = Field(None, description="IDs of shadows used in encounter")

@router.get("/gates", response_model=List[Dict[str, Any]])
async def get_available_gates(
    gate_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available dungeon gates for user"""
    service = DungeonService(db)
    return service.get_available_gates(str(current_user.id), gate_type, difficulty)

@router.post("/gates/{gate_id}/enter", response_model=Dict[str, Any])
async def enter_gate(
    gate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enter a dungeon gate"""
    service = DungeonService(db)
    
    result = service.enter_gate(str(current_user.id), gate_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result

@router.get("/encounters/{encounter_id}/questions", response_model=List[Dict[str, Any]])
async def get_encounter_questions(
    encounter_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get questions for dungeon encounter"""
    service = DungeonService(db)
    questions = service.get_questions_for_encounter(encounter_id)
    
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions found for this encounter"
        )
    
    return questions

@router.post("/encounters/{encounter_id}/submit", response_model=Dict[str, Any])
async def submit_encounter_answers(
    encounter_id: str,
    request: EncounterAnswersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit answers for dungeon encounter"""
    service = DungeonService(db)
    
    result = service.submit_encounter_answers(
        encounter_id,
        str(current_user.id),
        request.answers,
        request.shadows_used
    )
    
    return result

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_dungeon_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's dungeon run history"""
    service = DungeonService(db)
    return service.get_user_dungeon_history(str(current_user.id), limit)

@router.get("/gates/{gate_id}/leaderboard", response_model=List[Dict[str, Any]])
async def get_gate_leaderboard(
    gate_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get leaderboard for specific gate"""
    service = DungeonService(db)
    return service.get_gate_leaderboards(gate_id, limit)

@router.get("/stats", response_model=Dict[str, Any])
async def get_dungeon_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's overall dungeon statistics"""
    service = DungeonService(db)
    history = service.get_user_dungeon_history(str(current_user.id), 100)  # Get more for stats
    
    total_runs = len(history)
    completed_runs = len([h for h in history if h["status"] == "completed"])
    success_rate = (completed_runs / total_runs * 100) if total_runs > 0 else 0
    
    total_experience = sum(h["rewards"]["experience"] for h in history)
    total_orbs = sum(h["rewards"]["orbs"] for h in history)
    total_crystals = sum(h["rewards"]["crystals"] for h in history)
    
    best_score = max((h["score"] for h in history if h["score"] > 0), default=0)
    
    perfect_clears = len([h for h in history if h["stats"]["perfect_clear"]])
    speed_clears = len([h for h in history if h["stats"]["speed_clear"]])
    
    return {
        "total_runs": total_runs,
        "completed_runs": completed_runs,
        "success_rate": round(success_rate, 1),
        "total_rewards": {
            "experience": total_experience,
            "orbs": total_orbs,
            "crystals": total_crystals
        },
        "best_score": best_score,
        "special_achievements": {
            "perfect_clears": perfect_clears,
            "speed_clears": speed_clears
        }
    }