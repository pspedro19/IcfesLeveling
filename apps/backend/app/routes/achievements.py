from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.achievement_service import AchievementService
from ..schemas.achievement import (
    AchievementResponse, UserAchievementResponse, UserAchievementSummary,
    AchievementShowcase, AchievementProgressUpdate, AchievementUnlockRequest
)
from ..middleware.rate_limit import rate_limit

router = APIRouter(prefix="/api/v1/achievements", tags=["achievements"])

@router.get("/", response_model=List[AchievementResponse])
@rate_limit(limit=100, window=60)
async def get_all_achievements(
    include_secret: bool = Query(False, description="Include secret achievements"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all available achievements"""
    try:
        achievement_service = AchievementService(db)
        achievements = achievement_service.get_all_achievements(include_secret=include_secret)
        return achievements
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving achievements: {str(e)}")

@router.get("/user", response_model=List[UserAchievementResponse])
@rate_limit(limit=100, window=60)
async def get_user_achievements(
    include_secret: bool = Query(True, description="Include secret achievements"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's achievements"""
    try:
        achievement_service = AchievementService(db)
        user_achievements = achievement_service.get_user_achievements(str(current_user.id), include_secret=include_secret)
        return user_achievements
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user achievements: {str(e)}")

@router.get("/summary", response_model=UserAchievementSummary)
@rate_limit(limit=100, window=60)
async def get_achievement_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get achievement summary for current user"""
    try:
        achievement_service = AchievementService(db)
        summary = achievement_service.get_user_achievement_summary(str(current_user.id))
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving achievement summary: {str(e)}")

@router.get("/showcase/{user_id}", response_model=AchievementShowcase)
@rate_limit(limit=100, window=60)
async def get_achievement_showcase(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get achievement showcase for a specific user"""
    try:
        achievement_service = AchievementService(db)
        showcase = achievement_service.get_achievement_showcase(user_id)
        return showcase
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving achievement showcase: {str(e)}")

@router.post("/unlock")
@rate_limit(limit=20, window=60) # Lower limit for POST requests
async def unlock_achievement(
    request: AchievementUnlockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually unlock an achievement (for testing)"""
    try:
        achievement_service = AchievementService(db)
        user_achievement = achievement_service.update_achievement_progress(
            str(current_user.id),
            request.achievement_id,
            request.progress_increment
        )
        return {
            "message": "Achievement progress updated",
            "achievement": user_achievement,
            "unlocked": user_achievement.is_unlocked
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating achievement: {str(e)}")

@router.post("/check-unit-completion")
@rate_limit(limit=50, window=60)
async def check_unit_completion_achievements(
    unit_number: int,
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check and update unit completion achievements"""
    try:
        achievement_service = AchievementService(db)
        unlocked_achievements = achievement_service.check_unit_completion_achievements(
            str(current_user.id),
            unit_number,
            subject_id
        )
        return {
            "message": f"Checked unit completion achievements",
            "unlocked_count": len(unlocked_achievements),
            "unlocked_achievements": unlocked_achievements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking unit completion achievements: {str(e)}")

@router.post("/check-score-improvement")
@rate_limit(limit=50, window=60)
async def check_score_improvement_achievements(
    new_score: float,
    previous_score: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check and update score improvement achievements"""
    try:
        achievement_service = AchievementService(db)
        unlocked_achievements = achievement_service.check_score_improvement_achievements(
            str(current_user.id),
            new_score,
            previous_score
        )
        return {
            "message": f"Checked score improvement achievements",
            "unlocked_count": len(unlocked_achievements),
            "unlocked_achievements": unlocked_achievements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking score improvement achievements: {str(e)}")

@router.post("/check-study-streak")
@rate_limit(limit=50, window=60)
async def check_study_streak_achievements(
    streak_days: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check and update study streak achievements"""
    try:
        achievement_service = AchievementService(db)
        unlocked_achievements = achievement_service.check_study_streak_achievements(
            str(current_user.id),
            streak_days
        )
        return {
            "message": f"Checked study streak achievements",
            "unlocked_count": len(unlocked_achievements),
            "unlocked_achievements": unlocked_achievements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking study streak achievements: {str(e)}")

@router.post("/check-secret")
@rate_limit(limit=50, window=60)
async def check_secret_achievements(
    action_type: str,
    action_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check and update secret achievements based on user actions"""
    try:
        achievement_service = AchievementService(db)
        unlocked_achievements = achievement_service.check_secret_achievements(
            str(current_user.id),
            action_type,
            action_data
        )
        return {
            "message": f"Checked secret achievements",
            "unlocked_count": len(unlocked_achievements),
            "unlocked_achievements": unlocked_achievements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking secret achievements: {str(e)}")

@router.get("/progress/{achievement_id}")
@rate_limit(limit=100, window=60)
async def get_achievement_progress(
    achievement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get progress for a specific achievement"""
    try:
        achievement_service = AchievementService(db)
        user_achievement = achievement_service.get_user_achievement(str(current_user.id), achievement_id)
        
        if not user_achievement:
            raise HTTPException(status_code=404, detail="Achievement not found for user")
        
        return {
            "achievement_id": achievement_id,
            "progress": user_achievement.progress,
            "is_unlocked": user_achievement.is_unlocked,
            "progress_percentage": user_achievement.get_progress_percentage(),
            "unlocked_at": user_achievement.unlocked_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving achievement progress: {str(e)}")

@router.get("/categories")
@rate_limit(limit=100, window=60)
async def get_achievement_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get achievement categories with counts"""
    try:
        achievement_service = AchievementService(db)
        user_achievements = achievement_service.get_user_achievements(str(current_user.id))
        
        categories = {}
        for ua in user_achievements:
            category = ua.achievement.category
            if category not in categories:
                categories[category] = {
                    "total": 0,
                    "unlocked": 0,
                    "points": 0
                }
            categories[category]["total"] += 1
            if ua.is_unlocked:
                categories[category]["unlocked"] += 1
                categories[category]["points"] += ua.achievement.points
        
        return {
            "categories": categories,
            "total_achievements": len(user_achievements),
            "total_unlocked": sum(1 for ua in user_achievements if ua.is_unlocked)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving achievement categories: {str(e)}")

@router.get("/recent")
@rate_limit(limit=100, window=60)
async def get_recent_achievements(
    limit: int = Query(5, description="Number of recent achievements to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent unlocked achievements"""
    try:
        achievement_service = AchievementService(db)
        user_achievements = achievement_service.get_user_achievements(str(current_user.id))
        
        recent_achievements = sorted(
            [ua for ua in user_achievements if ua.is_unlocked and ua.unlocked_at],
            key=lambda x: x.unlocked_at,
            reverse=True
        )[:limit]
        
        return {
            "recent_achievements": recent_achievements,
            "count": len(recent_achievements)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving recent achievements: {str(e)}")
 