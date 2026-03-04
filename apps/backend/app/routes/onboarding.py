"""
Onboarding Routes - LOGICA_DE_NEGOCIO.md Steps 2-5
Handles saving and retrieving user onboarding preferences.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..core import security
from ..models.user import User
from ..middleware.rate_limit import rate_limit

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


# =============================================================================
# SCHEMAS
# =============================================================================

class OnboardingPreferencesRequest(BaseModel):
    """Request schema for onboarding preferences (Steps 2-5)"""
    goal: Optional[str] = Field(None, description="Study goal: mejorarIcfes, aprobarExamen, practicar")
    exam_date: Optional[str] = Field(None, description="ISO format exam date (for aprobarExamen goal)")
    current_level: Optional[str] = Field(None, description="Self-assessed level: basico, intermedio, avanzado")
    weak_subjects: List[str] = Field(default=[], description="1-3 subjects user wants to improve")
    daily_study_time: Optional[str] = Field(None, description="Time commitment: tenMinutes, twentyMinutes, thirtyPlusMinutes")
    is_complete: bool = Field(default=False, description="Whether onboarding is complete")


class OnboardingPreferencesResponse(BaseModel):
    """Response schema for onboarding preferences"""
    goal: Optional[str] = None
    exam_date: Optional[str] = None
    current_level: Optional[str] = None
    weak_subjects: List[str] = []
    daily_study_time: Optional[str] = None
    is_complete: bool = False
    initial_mastery: float = 0.2
    daily_xp_goal: int = 50

    class Config:
        from_attributes = True


# =============================================================================
# HELPERS
# =============================================================================

def get_initial_mastery(level: Optional[str]) -> float:
    """Calculate initial mastery based on self-assessed level (LOGICA_DE_NEGOCIO.md)"""
    mastery_map = {
        "basico": 0.2,
        "intermedio": 0.5,
        "avanzado": 0.75,
    }
    return mastery_map.get(level, 0.2)


def get_daily_xp_goal(study_time: Optional[str]) -> int:
    """Calculate daily XP goal based on study time commitment"""
    xp_map = {
        "tenMinutes": 50,
        "twentyMinutes": 100,
        "thirtyPlusMinutes": 200,
    }
    return xp_map.get(study_time, 50)


def validate_preferences(prefs: OnboardingPreferencesRequest) -> bool:
    """Validate all required onboarding fields are set"""
    valid_goals = ["mejorarIcfes", "aprobarExamen", "practicar"]
    valid_levels = ["basico", "intermedio", "avanzado"]
    valid_times = ["tenMinutes", "twentyMinutes", "thirtyPlusMinutes"]
    valid_subjects = ["matematicas", "lectura_critica", "ciencias_naturales", "sociales_ciudadanas", "ingles"]

    # Check goal is valid
    if prefs.goal not in valid_goals:
        return False

    # Check level is valid
    if prefs.current_level not in valid_levels:
        return False

    # Check study time is valid
    if prefs.daily_study_time not in valid_times:
        return False

    # Check weak subjects (1-3 valid subjects)
    if not prefs.weak_subjects or len(prefs.weak_subjects) > 3:
        return False

    for subject in prefs.weak_subjects:
        if subject not in valid_subjects:
            return False

    return True


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/preferences", response_model=OnboardingPreferencesResponse)
@rate_limit(limit=10, window=60)
async def save_onboarding_preferences(
    request: Request,
    preferences: OnboardingPreferencesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    """
    Save user onboarding preferences (Steps 2-5).

    This endpoint:
    1. Validates all required preferences are set
    2. Stores preferences in user profile
    3. Calculates initial mastery based on self-assessed level
    4. Sets daily XP goal based on study time commitment
    5. Marks onboarding as complete

    Per LOGICA_DE_NEGOCIO.md:
    - Step 2: Goal Setting (mejorarIcfes, aprobarExamen, practicar)
    - Step 3: Level Assessment (basico, intermedio, avanzado)
    - Step 4: Weak Subjects Selection (1-3 subjects)
    - Step 5: Study Time Commitment (10min, 20min, 30+min)
    """
    # Validate preferences if marking as complete
    if preferences.is_complete and not validate_preferences(preferences):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incomplete onboarding preferences. All fields are required."
        )

    # Calculate derived values
    initial_mastery = get_initial_mastery(preferences.current_level)
    daily_xp_goal = get_daily_xp_goal(preferences.daily_study_time)

    # Store preferences in user profile metadata
    # Using onboarding_preferences JSON field on user
    onboarding_data = {
        "goal": preferences.goal,
        "exam_date": preferences.exam_date,
        "current_level": preferences.current_level,
        "weak_subjects": preferences.weak_subjects,
        "daily_study_time": preferences.daily_study_time,
        "is_complete": preferences.is_complete,
        "initial_mastery": initial_mastery,
        "daily_xp_goal": daily_xp_goal,
        "completed_at": datetime.utcnow().isoformat() if preferences.is_complete else None,
    }

    # Update user's onboarding preferences
    current_user.onboarding_preferences = onboarding_data

    # If onboarding is complete, mark diagnostic as next step
    if preferences.is_complete:
        current_user.onboarding_completed = True

    db.commit()
    db.refresh(current_user)

    return OnboardingPreferencesResponse(
        goal=preferences.goal,
        exam_date=preferences.exam_date,
        current_level=preferences.current_level,
        weak_subjects=preferences.weak_subjects,
        daily_study_time=preferences.daily_study_time,
        is_complete=preferences.is_complete,
        initial_mastery=initial_mastery,
        daily_xp_goal=daily_xp_goal,
    )


@router.get("/preferences", response_model=OnboardingPreferencesResponse)
@rate_limit(limit=30, window=60)
async def get_onboarding_preferences(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    """
    Get current user's onboarding preferences.
    Returns empty defaults if not yet set.
    """
    prefs = current_user.onboarding_preferences or {}

    return OnboardingPreferencesResponse(
        goal=prefs.get("goal"),
        exam_date=prefs.get("exam_date"),
        current_level=prefs.get("current_level"),
        weak_subjects=prefs.get("weak_subjects", []),
        daily_study_time=prefs.get("daily_study_time"),
        is_complete=prefs.get("is_complete", False),
        initial_mastery=prefs.get("initial_mastery", 0.2),
        daily_xp_goal=prefs.get("daily_xp_goal", 50),
    )


@router.get("/status")
@rate_limit(limit=30, window=60)
async def get_onboarding_status(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    """
    Get onboarding completion status and next step.
    Useful for resuming onboarding after app restart.
    """
    prefs = current_user.onboarding_preferences or {}

    # Determine current step
    current_step = 1  # Start at value prop
    if prefs.get("goal"):
        current_step = 3  # Completed goal selection
    if prefs.get("current_level"):
        current_step = 4  # Completed level assessment
    if prefs.get("weak_subjects"):
        current_step = 5  # Completed subject selection
    if prefs.get("daily_study_time"):
        current_step = 6  # Completed study time (ready for diagnostic)
    if prefs.get("is_complete"):
        current_step = 0  # All complete

    return {
        "is_complete": prefs.get("is_complete", False),
        "current_step": current_step,
        "next_route": _get_next_route(current_step),
        "steps_completed": {
            "goal": prefs.get("goal") is not None,
            "level": prefs.get("current_level") is not None,
            "subjects": len(prefs.get("weak_subjects", [])) > 0,
            "study_time": prefs.get("daily_study_time") is not None,
        }
    }


def _get_next_route(step: int) -> str:
    """Get the next route based on current onboarding step"""
    routes = {
        0: "/home",           # Complete -> go home
        1: "/onboarding",     # Value prop
        2: "/onboarding/goal",
        3: "/onboarding/level",
        4: "/onboarding/subjects",
        5: "/onboarding/study-time",
        6: "/diagnostic",     # Ready for diagnostic
    }
    return routes.get(step, "/onboarding")
