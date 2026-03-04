"""
Advanced Stats Routes - ICFES Leveling Mobile App

Endpoints for:
- Activity Heatmap (GitHub-style)
- National Comparison for Radar Chart
- Historical Statistics
- Skill Tree with Visual Nodes
- Psychological Triggers
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, List

from ..core.database import get_db
from ..core.security import get_current_user
from ..models import User
from ..services.advanced_stats_service import AdvancedStatsService
from ..services.skill_tree_service import SkillTreeService
from ..services.psychological_triggers_service import PsychologicalTriggersService

# ============================================
# ROUTER
# ============================================

router = APIRouter(prefix="/stats", tags=["Advanced Stats"])


async def get_current_user_id(current_user: User = Depends(get_current_user)) -> UUID:
    return current_user.id


# ============================================
# RESPONSE SCHEMAS
# ============================================

class HeatmapResponse(BaseModel):
    heatmap: Dict[str, Dict[str, Any]]
    stats: Dict[str, Any]


class NationalComparisonResponse(BaseModel):
    subjects: List[Dict[str, Any]]
    overall: Dict[str, Any]


class HistoricalStatsResponse(BaseModel):
    questions_history: List[Dict[str, Any]]
    study_time_history: List[Dict[str, Any]]
    totals: Dict[str, Any]


class SkillTreeResponse(BaseModel):
    subjects: List[Dict[str, Any]]
    subject_stats: List[Dict[str, Any]]
    total_nodes: int
    total_mastered: int


class TriggersResponse(BaseModel):
    social_proof: Dict[str, Any]
    loss_aversion: Dict[str, Any]
    progress_illusion: Dict[str, Any]
    endowed_progress: Dict[str, Any]


# ============================================
# HEATMAP ENDPOINTS
# ============================================

@router.get("/heatmap", response_model=HeatmapResponse)
async def get_activity_heatmap(
    days: int = Query(365, ge=30, le=365, description="Number of days to include"),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get activity heatmap data (GitHub-style contribution calendar).
    Returns daily activity counts for the specified period.

    - **days**: Number of days to include (30-365)
    """
    service = AdvancedStatsService(db)
    try:
        data = service.get_activity_heatmap(user_id, days)
        return HeatmapResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching heatmap: {str(e)}")


# ============================================
# NATIONAL COMPARISON ENDPOINTS
# ============================================

@router.get("/national-comparison", response_model=NationalComparisonResponse)
async def get_national_comparison(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get user's mastery compared to national averages.
    Returns percentile ranking and comparison data for radar chart overlay.
    """
    service = AdvancedStatsService(db)
    try:
        data = service.get_national_comparison(user_id)
        return NationalComparisonResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching national comparison: {str(e)}")


# ============================================
# HISTORICAL STATS ENDPOINTS
# ============================================

@router.get("/historical", response_model=HistoricalStatsResponse)
async def get_historical_stats(
    days: int = Query(90, ge=7, le=365, description="Number of days to include"),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get historical statistics including questions answered and study time.

    - **days**: Number of days to include (7-365)
    """
    service = AdvancedStatsService(db)
    try:
        data = service.get_historical_stats(user_id, days)
        return HistoricalStatsResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical stats: {str(e)}")


# ============================================
# SKILL TREE ENDPOINTS
# ============================================

@router.get("/skill-tree", response_model=SkillTreeResponse)
async def get_skill_tree(
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get complete skill tree with nodes, connections, and mastery levels.
    Returns visual tree structure for rendering with progressive unlocking.

    - **subject_id**: Optional filter by subject
    """
    service = SkillTreeService(db)
    try:
        data = service.get_skill_tree(user_id, subject_id)
        return SkillTreeResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching skill tree: {str(e)}")


@router.get("/skill-tree/unlockable")
async def get_unlockable_nodes(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get nodes that are close to being unlocked or leveled up.
    Shows progress opportunities to motivate users.
    """
    service = SkillTreeService(db)
    try:
        unlockable = service.get_unlockable_nodes(user_id)
        return {"unlockable_nodes": unlockable}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching unlockable nodes: {str(e)}")


@router.post("/skill-tree/check-level-up")
async def check_level_up(
    topic_id: str,
    new_mastery: float,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Check if user leveled up in a topic after mastery update.
    Returns level-up data for animations if applicable.
    """
    service = SkillTreeService(db)
    try:
        result = service.check_level_up(user_id, topic_id, new_mastery)
        return {"level_up": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking level up: {str(e)}")


# ============================================
# PSYCHOLOGICAL TRIGGERS ENDPOINTS
# ============================================

@router.get("/triggers", response_model=TriggersResponse)
async def get_psychological_triggers(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get all psychological triggers for the user.
    Includes social proof, loss aversion, progress illusion, and endowed progress.
    """
    service = PsychologicalTriggersService(db)
    try:
        data = service.get_all_triggers(user_id)
        return TriggersResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching triggers: {str(e)}")


@router.get("/triggers/social-proof")
async def get_social_proof(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get social proof data (rankings, peer comparison)."""
    service = PsychologicalTriggersService(db)
    try:
        return service.get_social_proof_data(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/triggers/loss-aversion")
async def get_loss_aversion(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get loss aversion triggers (streak risk, demotion risk)."""
    service = PsychologicalTriggersService(db)
    try:
        return service.get_loss_aversion_triggers(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/triggers/progress")
async def get_optimized_progress(
    context: str = Query("general", description="Context for progress display"),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get optimized progress data with psychological enhancements."""
    service = PsychologicalTriggersService(db)
    try:
        return service.get_optimized_progress(user_id, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/triggers/variable-reward")
async def get_variable_reward(
    action_type: str = Query(..., description="Type of action: answer, lesson_complete, daily_login, streak"),
    base_reward: int = Query(..., ge=0, description="Base XP reward"),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Apply variable ratio reinforcement to a reward.
    May return bonus rewards based on psychological scheduling.
    """
    service = PsychologicalTriggersService(db)
    try:
        return service.get_variable_reward(user_id, action_type, base_reward)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# HEALTH CHECK
# ============================================

@router.get("/health")
async def health_check():
    """Advanced stats service health check."""
    return {
        "status": "healthy",
        "service": "advanced_stats",
        "timestamp": datetime.now().isoformat()
    }
