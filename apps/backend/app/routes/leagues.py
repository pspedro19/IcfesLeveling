"""
League Routes - ICFES Leveling Mobile App

Endpoints for managing user leagues, leaderboards, and history.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import date, datetime

from ..core.database import get_db
from ..core.security import get_current_user
from ..models import User
from ..services.leagues_service import LeagueService

# ============================================
# ROUTER
# ============================================

router = APIRouter(prefix="/leagues", tags=["Leagues"])

async def get_current_user_id(current_user: User = Depends(get_current_user)) -> UUID:
    return current_user.id

# ============================================
# PYDANTIC SCHEMAS
# ============================================

class DivisionInfo(BaseModel):
    id: UUID
    name: str
    tier: int
    color: Optional[str]

class LeagueStatusResponse(BaseModel):
    division: DivisionInfo
    group_id: UUID
    rank: int
    zone: str
    weekly_xp: int
    week_ends_at: datetime
    promotion_threshold: int
    relegation_threshold: int
    participants: int

class LeaderboardEntry(BaseModel):
    user_id: UUID
    name: str
    avatar_url: Optional[str] = None
    xp: int
    rank: int
    zone: str
    is_me: bool

class LeaderboardResponse(BaseModel):
    leaderboard: List[LeaderboardEntry]
    my_rank: int
    my_xp: int
    my_zone: str
    total_participants: int

class LeagueJoinResponse(BaseModel):
    group_id: UUID
    division: DivisionInfo
    position: int
    week_ends_at: datetime

class LeagueHistoryEntry(BaseModel):
    week_id: UUID
    week_start: Optional[str]
    week_end: Optional[str]
    division_name: str
    final_rank: int
    final_xp: int
    status: str
    gold_earned: int

class LeagueHistoryResponse(BaseModel):
    weeks: List[LeagueHistoryEntry]

# ============================================
# ENDPOINTS
# ============================================

@router.get("/current", response_model=LeagueStatusResponse)
async def get_current_league(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get the current league status for the authenticated user.
    If the user is not in a league, they will be automatically joined to one.
    """
    service = LeagueService(db)
    try:
        status = service.get_current_league_status(user_id)
        return LeagueStatusResponse(**status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_league_leaderboard(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get the leaderboard for the user's current league group.
    """
    service = LeagueService(db)
    try:
        leaderboard_data = service.get_leaderboard(user_id)
        return LeaderboardResponse(**leaderboard_data)
    except ValueError as e:
        if str(e) == "USER_NOT_IN_LEAGUE":
            raise HTTPException(status_code=404, detail="User is not in a league. Join one first.")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@router.post("/join", response_model=LeagueJoinResponse)
async def join_league(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Explicitly join a league. Users are typically auto-joined when they
    request their status, but this endpoint provides a clear entry point.
    """
    service = LeagueService(db)
    try:
        join_info = service.join_league(user_id)
        # The service returns the full status, we need to adapt it
        return LeagueJoinResponse(
            group_id=join_info["group_id"],
            division=join_info["division"],
            position=join_info["rank"],
            week_ends_at=join_info["week_ends_at"]
        )
    except ValueError as e:
        if str(e) == "USER_ALREADY_IN_LEAGUE":
            raise HTTPException(status_code=400, detail="User is already in a league for this week.")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@router.get("/history", response_model=LeagueHistoryResponse)
async def get_league_history(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get the user's league history for the past weeks.
    """
    service = LeagueService(db)
    try:
        history_data = service.get_league_history(user_id)
        return LeagueHistoryResponse(**history_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
