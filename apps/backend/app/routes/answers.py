"""
Answers API Routes - Anti-Gaming XP System
ICFES Leveling Mobile App

Implements POST /answers/submit with:
- Anti-gaming XP validation
- Topic mastery updates
- Grace mode support
- Streak multipliers
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import cast, Date as SQLDate
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime, date
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.question import Question
from ..models.mobile_offline import UserQuestionHistory, UserLeague, LeagueGroup, LeagueWeek
from ..services.game_engine_service import GameEngineService
from ..services.mastery_service import MasteryService
from ..services.hearts_service import HeartsService
from ..middleware.anti_gaming import get_anti_gaming
from ..middleware.rate_limit import rate_limit
from ..utils.response import success_response, paginated_response

router = APIRouter(prefix="/answers", tags=["answers"])
logger = logging.getLogger(__name__)


# ============================================
# REQUEST/RESPONSE SCHEMAS
# ============================================

class AnswerSubmitRequest(BaseModel):
    """Request body for submitting an answer"""
    question_id: UUID
    answer_id: str = Field(..., description="Selected option (a, b, c, or d)")
    time_spent_seconds: int = Field(ge=0, le=3600, description="Time spent on question")
    session_type: str = Field(default="practice", description="Type of session: practice, boss_raid, diagnostic")
    session_id: Optional[UUID] = Field(default=None, description="Optional session ID")


class MasteryUpdateResponse(BaseModel):
    """Topic mastery update details"""
    topic_id: str
    old_score: float
    new_score: float


class StreakUpdateResponse(BaseModel):
    """Streak update details"""
    current: int
    extended: bool
    daily_goal_met: bool


class AnswerSubmitResponse(BaseModel):
    """Response from submitting an answer"""
    correct: bool
    correct_answer_id: str
    explanation: Optional[str] = None
    attempt_type: str  # 'new', 'valid_review', 'invalid_repeat'
    xp_earned: int
    xp_multiplier: float
    hearts_remaining: Optional[int] = None
    in_grace_mode: bool
    mastery_update: Optional[MasteryUpdateResponse] = None
    streak_update: Optional[StreakUpdateResponse] = None


# ============================================
# HELPER FUNCTIONS
# ============================================

def _check_duplicate_submission(
    db: Session,
    user_id: UUID,
    question_id: UUID,
    session_id: Optional[UUID],
    session_type: str
) -> Optional[UserQuestionHistory]:
    """
    Check if a duplicate answer submission exists.
    """
    if session_id:
        return db.query(UserQuestionHistory).filter(
            UserQuestionHistory.user_id == user_id,
            UserQuestionHistory.question_id == question_id,
            UserQuestionHistory.session_id == session_id
        ).first()
    else:
        today = date.today()
        return db.query(UserQuestionHistory).filter(
            UserQuestionHistory.user_id == user_id,
            UserQuestionHistory.question_id == question_id,
            UserQuestionHistory.session_type == session_type,
            UserQuestionHistory.session_id.is_(None),
            cast(UserQuestionHistory.created_at, SQLDate) == today
        ).first()


# ============================================
# ENDPOINTS
# ============================================

@router.post("/submit")
@rate_limit(limit=60, window=60)
async def submit_answer(
    request: Request,
    payload: AnswerSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit an answer to a question with anti-gaming XP validation.
    """
    mastery_service = MasteryService(db)

    try:
        question = db.query(Question).filter(Question.id == payload.question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # ====== ANTI-GAMING VALIDATIONS ======
        anti_gaming = get_anti_gaming()

        # 1. Validate minimum answer time
        if payload.time_spent_seconds:
            time_ms = payload.time_spent_seconds * 1000
            is_valid_time, time_msg = anti_gaming.validate_answer_time(time_ms)
            if not is_valid_time:
                raise HTTPException(status_code=400, detail={"code": "TOO_FAST", "message": time_msg})

        existing_submission = _check_duplicate_submission(
            db=db, user_id=current_user.id, question_id=payload.question_id,
            session_id=payload.session_id, session_type=payload.session_type
        )
        if existing_submission:
            raise HTTPException(status_code=409, detail="DUPLICATE_SUBMISSION")

        is_correct = payload.answer_id.lower().strip() == (question.respuesta_correcta or "").lower()

        attempt_type = GameEngineService.determine_attempt_type(
            db=db, user_id=current_user.id, question_id=payload.question_id, topic_id=question.topic_id
        )

        streak_days = current_user.streak_days or 0

        # Obtener estado real de corazones
        hearts_service = HeartsService(db)
        hearts_status = hearts_service.get_status(current_user.id)
        in_grace_mode = hearts_status.get("grace_mode_active", False)
        hearts_remaining = hearts_status.get("hearts", 5)
        is_unlimited = hearts_status.get("is_unlimited", False)

        xp_earned = GameEngineService.calculate_xp_for_answer(
            attempt_type=attempt_type, is_correct=is_correct,
            streak_days=streak_days, in_grace_mode=in_grace_mode
        )
        xp_multiplier = GameEngineService.get_streak_multiplier(streak_days)

        attempt_record = UserQuestionHistory(
            user_id=current_user.id, question_id=payload.question_id, was_correct=is_correct,
            time_spent_seconds=payload.time_spent_seconds, session_type=payload.session_type,
            session_id=payload.session_id, client_timestamp=datetime.utcnow()
        )
        previous_attempts = db.query(UserQuestionHistory).filter_by(user_id=current_user.id, question_id=payload.question_id).count()
        attempt_record.attempt_number = previous_attempts + 1
        db.add(attempt_record)

        mastery_result = mastery_service.update_topic_mastery(
            db=db, user_id=current_user.id, topic_id=question.topic_id, is_correct=is_correct
        )

        rate_limited = False
        if not in_grace_mode and xp_earned > 0:
            # 2. Anti-Gaming: Check XP rate limit
            within_limit = await anti_gaming.check_xp_rate(str(current_user.id), xp_earned)
            if not within_limit:
                # Rate limited - reduce XP to 0
                xp_earned = 0
                rate_limited = True
            else:
                # 3. Anti-Gaming: Check for XP reduction due to suspicious activity
                should_reduce, multiplier = await anti_gaming.should_reduce_xp(str(current_user.id), db)
                if should_reduce:
                    xp_earned = int(xp_earned * multiplier)

            if xp_earned > 0:
                current_user.add_experience(xp_earned)

                # Actualizar XP de liga semanal
                user_league = db.query(UserLeague).join(LeagueGroup).join(LeagueWeek).filter(
                    UserLeague.user_id == current_user.id,
                    LeagueWeek.is_active == True
                ).first()
                if user_league:
                    user_league.weekly_xp += xp_earned

        # Descontar corazón si respuesta incorrecta (y no en grace mode ni ilimitado)
        if not is_correct and not in_grace_mode and not is_unlimited:
            try:
                use_result = hearts_service.use_heart(current_user.id, "wrong_answer", payload.question_id)
                hearts_remaining = use_result.get("hearts_remaining", 0)
            except ValueError as e:
                if str(e) == "HEARTS_EMPTY":
                    # Usuario puede entrar a grace mode
                    hearts_remaining = 0
                else:
                    raise

        db.commit()

        mastery_update_data = None
        if mastery_result and "old_score" in mastery_result:
            mastery_update_data = {
                "topic_id": str(question.topic_id),
                "old_score": mastery_result.get("old_score", 0.0),
                "new_score": mastery_result.get("new_score", 0.0)
            }

        streak_update_data = {
            "current": streak_days,
            "extended": False,
            "daily_goal_met": False
        }

        response_data = {
            "correct": is_correct,
            "correct_answer_id": (question.respuesta_correcta or "").lower(),
            "explanation": question.explanation,
            "attempt_type": attempt_type,
            "xp_earned": xp_earned,
            "xp_multiplier": xp_multiplier,
            "hearts_remaining": hearts_remaining if not in_grace_mode else None,
            "in_grace_mode": in_grace_mode,
            "mastery_update": mastery_update_data,
            "streak_update": streak_update_data
        }
        return success_response(response_data)

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="DUPLICATE_SUBMISSION")
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail=f"Error submitting answer: {str(e)}")


@router.get("/xp-preview/{question_id}")
@rate_limit(limit=100, window=60)
async def preview_xp(
    request: Request,
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Preview potential XP for a question before answering.
    """
    mastery_service = MasteryService(db)
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        attempt_type = GameEngineService.determine_attempt_type(
            db=db, user_id=current_user.id, question_id=question_id, topic_id=question.topic_id
        )
        streak_days = current_user.streak_days or 0
        xp_breakdown = GameEngineService.get_xp_breakdown(attempt_type=attempt_type, streak_days=streak_days)
        mastery = mastery_service.get_topic_mastery(db, current_user.id, question.topic_id)

        preview_data = {
            "question_id": str(question_id),
            "attempt_type": attempt_type,
            "is_valid_for_xp": attempt_type != "invalid_repeat",
            "xp_breakdown": xp_breakdown,
            "current_mastery": mastery
        }
        return success_response(preview_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing XP: {e}")
        raise HTTPException(status_code=500, detail=f"Error previewing XP: {str(e)}")


@router.get("/history")
async def get_answer_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's answer history with XP and mastery info.
    """
    history = db.query(UserQuestionHistory).filter(
        UserQuestionHistory.user_id == current_user.id
    ).order_by(
        UserQuestionHistory.created_at.desc()
    ).offset(offset).limit(limit).all()

    results = [
        {
            "id": str(r.id),
            "question_id": str(r.question_id),
            "was_correct": r.was_correct,
            "time_spent_seconds": r.time_spent_seconds,
            "attempt_number": r.attempt_number,
            "session_type": r.session_type,
            "created_at": r.created_at.isoformat() if r.created_at else None
        } for r in history
    ]
    total = db.query(UserQuestionHistory).filter_by(user_id=current_user.id).count()
    return paginated_response(results, total=total, limit=limit, offset=offset)


@router.get("/mastery/topics")
async def get_all_topic_mastery(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get mastery scores for all topics the user has practiced.
    """
    mastery_service = MasteryService(db)
    masteries = mastery_service.get_topics_mastery(current_user.id)["topics"]
    return success_response({"topics": masteries, "total_topics": len(masteries)})