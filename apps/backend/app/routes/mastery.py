"""
Mastery Routes - ICFES Leveling Mobile App

Endpoints for retrieving user mastery data, including topic mastery,
weak areas, and data for the mastery radar chart.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user
from ..models import User
from ..services.mastery_service import MasteryService

# ============================================
# ROUTER
# ============================================

router = APIRouter(prefix="/mastery", tags=["Mastery"])

async def get_current_user_id(current_user: User = Depends(get_current_user)) -> UUID:
    return current_user.id

# ============================================
# PYDANTIC SCHEMAS
# ============================================

class TopicMasteryInfo(BaseModel):
    id: UUID
    name: str
    subject_id: UUID
    subject_name: str
    mastery_score: float
    questions_seen: int
    questions_correct: int
    last_practiced_at: Optional[datetime]
    days_since_last: Optional[int]
    status: str
    next_review_in_days: int

class TopicsMasteryResponse(BaseModel):
    topics: List[TopicMasteryInfo]

class WeakAreaInfo(BaseModel):
    topic_id: UUID
    topic_name: str
    subject_id: UUID
    subject_name: str
    mastery_score: float
    priority: str
    suggested_practice: int

class WeakAreasResponse(BaseModel):
    weak_areas: List[WeakAreaInfo]

class RadarChartSubjectInfo(BaseModel):
    subject_id: UUID
    subject_name: str
    overall_mastery: float
    topics_mastered: int
    topics_total: int

class RadarChartResponse(BaseModel):
    subjects: List[RadarChartSubjectInfo]


# ============================================
# ENDPOINTS
# ============================================

@router.get("/topics", response_model=TopicsMasteryResponse)
async def get_topics_mastery(
    subject_id: Optional[UUID] = Query(None, description="Optional subject ID to filter topics"),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get the user's mastery level for all topics, optionally filtered by subject.
    """
    service = MasteryService(db)
    try:
        mastery_data = service.get_topics_mastery(user_id, subject_id)
        return TopicsMasteryResponse(**mastery_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@router.get("/weak-areas", response_model=WeakAreasResponse)
async def get_weak_areas(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get a prioritized list of the user's weakest areas to focus on.
    """
    service = MasteryService(db)
    try:
        weak_areas_data = service.get_weak_areas(user_id)
        return WeakAreasResponse(**weak_areas_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@router.get("/radar-chart", response_model=RadarChartResponse)
async def get_radar_chart_data(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get aggregated mastery data for each of the 5 main subjects,
    suitable for displaying in a radar chart.
    """
    service = MasteryService(db)
    try:
        radar_data = service.get_radar_chart_data(user_id)
        return RadarChartResponse(**radar_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
