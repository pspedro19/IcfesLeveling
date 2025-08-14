from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..services.recommendation_service import RecommendationService
from ..models.user import User

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
logger = logging.getLogger(__name__)

@router.get("/adaptive")
async def get_adaptive_recommendations(
    days: int = Query(30, description="Days of data to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get adaptive recommendations based on user performance"""
    try:
        recommendation_service = RecommendationService()
        recommendations = recommendation_service.get_adaptive_recommendations(
            str(current_user.id), db, days
        )
        return recommendations
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Error getting recommendations")

@router.get("/data-sufficiency")
async def check_data_sufficiency(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if user has sufficient data for reliable recommendations"""
    try:
        recommendation_service = RecommendationService()
        user_data = recommendation_service._gather_user_data(str(current_user.id), db, 30)
        data_sufficiency = recommendation_service._check_data_sufficiency(user_data)
        
        return {
            "has_sufficient_data": data_sufficiency["has_sufficient_data"],
            "subjects_with_sufficient_data": data_sufficiency["subjects_with_sufficient_data"],
            "subjects_needing_more_data": data_sufficiency["subjects_needing_more_data"],
            "min_questions_per_subject": data_sufficiency["min_questions_per_subject"],
            "recommendation_quality": data_sufficiency["recommendation_quality"]
        }
    except Exception as e:
        logger.error(f"Error checking data sufficiency: {e}")
        raise HTTPException(status_code=500, detail="Error checking data sufficiency")

@router.get("/rank-progression")
async def get_rank_progression(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get rank progression information"""
    try:
        recommendation_service = RecommendationService()
        user_data = recommendation_service._gather_user_data(str(current_user.id), db, 30)
        performance_analysis = recommendation_service._analyze_performance(user_data)
        rank_progression = recommendation_service._calculate_rank_progression(performance_analysis, user_data)
        
        return rank_progression
    except Exception as e:
        logger.error(f"Error getting rank progression: {e}")
        raise HTTPException(status_code=500, detail="Error getting rank progression")

@router.get("/study-schedule")
async def get_study_schedule(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized study schedule"""
    try:
        recommendation_service = RecommendationService()
        user_data = recommendation_service._gather_user_data(str(current_user.id), db, 30)
        performance_analysis = recommendation_service._analyze_performance(user_data)
        study_schedule = recommendation_service._generate_study_schedule(performance_analysis, user_data)
        
        return study_schedule
    except Exception as e:
        logger.error(f"Error getting study schedule: {e}")
        raise HTTPException(status_code=500, detail="Error getting study schedule")

@router.get("/next-topics")
async def get_next_topics(
    limit: int = Query(5, description="Number of topics to recommend"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recommended next topics to study"""
    try:
        recommendation_service = RecommendationService()
        user_data = recommendation_service._gather_user_data(str(current_user.id), db, 30)
        performance_analysis = recommendation_service._analyze_performance(user_data)
        next_topics = recommendation_service._recommend_next_topics(performance_analysis, user_data)
        
        return {"topics": next_topics[:limit]}
    except Exception as e:
        logger.error(f"Error getting next topics: {e}")
        raise HTTPException(status_code=500, detail="Error getting next topics")