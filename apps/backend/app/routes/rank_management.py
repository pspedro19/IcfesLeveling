"""
Rank Management API Routes

Provides endpoints for managing user ranks based on performance data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.performance_rank_service import PerformanceRankService
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

class RankUpdateResponse(BaseModel):
    user_id: str
    username: str
    current_rank: str
    new_rank: str
    current_level: int
    new_level: int
    rank_changed: bool
    level_changed: bool
    total_xp: int
    updates_made: list
    metrics: dict

class BulkRankUpdateResponse(BaseModel):
    total_users_processed: int
    users_updated: int
    rank_changes: int
    level_changes: int
    processing_results: list
    errors: list

@router.get("/user/{user_id}/rank-calculation", response_model=RankUpdateResponse)
async def calculate_user_rank(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate rank for a specific user based on diagnostic test performance.
    
    This endpoint calculates (but doesn't update) the user's rank based on:
    - Average theta scores from diagnostic tests
    - Test completion consistency
    - XP earned from actual test performance
    - Cross-subject performance stability
    """
    try:
        rank_service = PerformanceRankService(db)
        calculation_result = rank_service.calculate_user_rank(user_id)
        
        if "error" in calculation_result:
            raise HTTPException(status_code=404, detail=calculation_result["error"])
        
        # Get user info for response
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return RankUpdateResponse(
            user_id=user_id,
            username=user.username,
            current_rank=calculation_result.get("current_rank", "E"),
            new_rank=calculation_result.get("new_rank", "E"),
            current_level=calculation_result.get("current_level", 1),
            new_level=calculation_result.get("new_level", 1),
            rank_changed=calculation_result.get("rank_changed", False),
            level_changed=calculation_result.get("level_changed", False),
            total_xp=calculation_result.get("metrics", {}).get("total_xp_earned", 0),
            updates_made=[],
            metrics=calculation_result.get("metrics", {})
        )
        
    except Exception as e:
        logger.error(f"Error calculating rank for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rank calculation error: {str(e)}")

@router.post("/user/{user_id}/update-rank", response_model=RankUpdateResponse)
async def update_user_rank(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a user's rank and level in the database based on diagnostic test performance.
    
    This endpoint:
    1. Calculates the user's performance metrics from diagnostic tests
    2. Determines appropriate rank (E-SSS) based on theta scores and consistency
    3. Updates the user's level based on total XP earned
    4. Saves changes to the database
    """
    try:
        rank_service = PerformanceRankService(db)
        update_result = rank_service.update_user_rank_and_level(user_id)
        
        if "error" in update_result:
            raise HTTPException(status_code=404, detail=update_result["error"])
        
        # Get user info for response
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return RankUpdateResponse(
            user_id=user_id,
            username=user.username,
            current_rank=update_result.get("current_rank", "E"),
            new_rank=update_result.get("new_rank", "E"),
            current_level=update_result.get("current_level", 1),
            new_level=update_result.get("new_level", 1),
            rank_changed=update_result.get("rank_changed", False),
            level_changed=update_result.get("level_changed", False),
            total_xp=update_result.get("metrics", {}).get("total_xp_earned", 0),
            updates_made=update_result.get("updates_made", []),
            metrics=update_result.get("metrics", {})
        )
        
    except Exception as e:
        logger.error(f"Error updating rank for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rank update error: {str(e)}")

@router.post("/users/bulk-update-ranks", response_model=BulkRankUpdateResponse)
async def bulk_update_user_ranks(
    limit: Optional[int] = Query(None, description="Limit number of users to process"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update ranks for all users who have completed diagnostic tests.
    
    This is an admin endpoint for bulk rank recalculation based on performance data.
    Use this after:
    - Importing new diagnostic test data
    - Adjusting rank calculation algorithms
    - System maintenance requiring rank recalibration
    
    Args:
        limit: Optional limit on number of users to process (for testing or gradual rollout)
    """
    try:
        # Check if current user has admin privileges (you may want to add proper admin check)
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        rank_service = PerformanceRankService(db)
        bulk_result = rank_service.bulk_update_all_user_ranks(limit=limit)
        
        if "error" in bulk_result:
            raise HTTPException(status_code=500, detail=bulk_result["error"])
        
        return BulkRankUpdateResponse(**bulk_result)
        
    except Exception as e:
        logger.error(f"Error in bulk rank update: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk update error: {str(e)}")

@router.get("/rank-system/info")
async def get_rank_system_info():
    """
    Get information about the ranking system thresholds and criteria.
    
    Returns the current rank requirements and calculation methodology.
    """
    try:
        rank_service = PerformanceRankService(db=None)  # Just for accessing class constants
        
        return {
            "ranking_system": "Performance-based ranking using IRT theta scores",
            "rank_levels": ["E", "D", "C", "B", "A", "S", "SS", "SSS"],
            "criteria": {
                "theta_scores": "Average IRT ability estimation across subjects",
                "test_completion": "Number of completed diagnostic tests",
                "performance_stability": "Consistency of theta scores over time",
                "xp_per_test": "Average XP earned per diagnostic test"
            },
            "thresholds": rank_service.RANK_THRESHOLDS,
            "level_calculation": "Level = sqrt(total_xp / 50) + 1",
            "xp_sources": "Earned from diagnostic test questions based on Puntos_XP field"
        }
        
    except Exception as e:
        logger.error(f"Error getting rank system info: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve rank system information")

@router.get("/user/{user_id}/performance-metrics")
async def get_user_performance_metrics(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed performance metrics for a user.
    
    Returns raw performance data used in rank calculation:
    - Diagnostic test completion stats
    - Theta score evolution
    - Subject-specific performance
    - XP earning history
    """
    try:
        rank_service = PerformanceRankService(db)
        performance_data = rank_service._get_user_performance_data(user_id)
        
        # Get user info
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user_id,
            "username": user.username,
            "current_rank": user.rank,
            "current_level": user.level,
            "current_xp": user.experience,
            "performance_data": performance_data
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not retrieve performance metrics: {str(e)}")