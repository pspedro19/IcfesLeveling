"""
Boss Raid Routes for ICFES Leveling API

Weekly Boss Raid event endpoints:
- GET /boss-raid/status - Check if raid is active (Sunday 10AM-10PM COT)
- POST /boss-raid/start - Start raid session with 20 questions
- POST /boss-raid/submit-answer - Submit answer, deal damage, get 3x XP
- POST /boss-raid/complete - Finish raid, get rewards
- GET /boss-raid/leaderboard - Get raid leaderboard
- GET /boss-raid/session/{session_id} - Get session status
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import logging

from ..core.database import get_db
from ..core.security import get_current_user, get_current_user_optional
from ..models.user import User
from ..services.boss_raid_service import BossRaidService
from ..schemas.boss_raid import (
    BossRaidStatusResponse,
    BossRaidStartResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    CompleteRaidRequest,
    CompleteRaidResponse,
    BossRaidLeaderboardResponse,
    SessionStatusResponse,
    BossResponse,
    RaidQuestion,
    QuestionOption,
    RaidReward,
    LeaderboardEntry,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/boss-raid", tags=["boss-raid"])


@router.get("/status", response_model=BossRaidStatusResponse)
async def get_raid_status(
    timezone: str = Query(default="America/Bogota", description="User timezone"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Check if Boss Raid is currently active.

    Boss Raid is available every Sunday from 10 AM to 10 PM (COT).
    Returns current boss information if raid is active.
    """
    try:
        is_active = BossRaidService.is_raid_active(timezone)
        raid_times = BossRaidService.get_raid_times(timezone)

        # Get current boss info
        boss_data = None
        my_damage = 0
        my_rank = None

        if is_active:
            boss_data = BossRaidService.get_current_boss(db)

            if boss_data and current_user:
                my_damage = BossRaidService.get_user_total_damage(
                    db, boss_data["id"], current_user.id
                )
                my_rank = BossRaidService.get_user_rank(
                    db, boss_data["id"], current_user.id
                )

        # Calculate time remaining
        time_remaining = None
        if is_active and raid_times.get("ends_at"):
            now = BossRaidService.get_current_time(timezone)
            time_remaining = int((raid_times["ends_at"] - now).total_seconds())

        # Build boss response if available
        boss_response = None
        if boss_data:
            boss_response = BossResponse(
                id=boss_data["id"],
                name=boss_data["name"],
                description=boss_data.get("description"),
                subject_id=boss_data.get("subject_id"),
                subject_name=boss_data.get("subject_name"),
                hp=boss_data["hp"],
                current_hp=boss_data["current_hp"],
                difficulty=boss_data["difficulty"],
                is_defeated=boss_data.get("is_defeated", False),
                defeated_at=boss_data.get("defeated_at")
            )

        return BossRaidStatusResponse(
            is_active=is_active,
            starts_at=raid_times["starts_at"],
            ends_at=raid_times["ends_at"],
            current_boss=boss_response,
            xp_multiplier=BossRaidService.XP_MULTIPLIER,
            my_damage_dealt=my_damage,
            my_rank=my_rank,
            time_remaining_seconds=time_remaining,
            next_raid_at=raid_times.get("next_raid_at") if not is_active else None
        )

    except Exception as e:
        logger.error(f"Error getting raid status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start", response_model=BossRaidStartResponse)
async def start_raid(
    timezone: str = Query(default="America/Bogota", description="User timezone"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a Boss Raid session.

    Requirements:
    - Boss Raid must be active (Sunday 10 AM - 10 PM COT)
    - User must be authenticated

    Returns:
    - Session ID
    - Current boss information
    - 20 questions for the raid
    """
    try:
        session, error, questions = BossRaidService.start_raid_session(
            db=db,
            user_id=current_user.id,
            timezone=timezone
        )

        if error:
            if error == "RAID_NOT_ACTIVE":
                raid_times = BossRaidService.get_raid_times(timezone)
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "RAID_NOT_ACTIVE",
                        "message": "El Boss Raid solo esta disponible Domingos 10 AM - 10 PM",
                        "next_raid_at": raid_times.get("next_raid_at").isoformat() if raid_times.get("next_raid_at") else None
                    }
                )
            elif error == "BOSS_ALREADY_DEFEATED":
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "BOSS_ALREADY_DEFEATED",
                        "message": "El jefe de esta semana ya ha sido derrotado"
                    }
                )
            else:
                raise HTTPException(status_code=400, detail=error)

        # Get boss info
        boss_data = BossRaidService.get_current_boss(db)
        boss_response = BossResponse(
            id=boss_data["id"],
            name=boss_data["name"],
            description=boss_data.get("description"),
            subject_id=boss_data.get("subject_id"),
            subject_name=boss_data.get("subject_name"),
            hp=boss_data["hp"],
            current_hp=boss_data["current_hp"],
            difficulty=boss_data["difficulty"],
            is_defeated=boss_data.get("is_defeated", False)
        )

        # Format questions
        raid_questions = []
        for q in questions:
            options = []

            # Build options from question data
            option_texts = {
                "A": q.opcion_a_texto or getattr(q, 'option_a', None),
                "B": q.opcion_b_texto or getattr(q, 'option_b', None),
                "C": q.opcion_c_texto or getattr(q, 'option_c', None),
                "D": q.opcion_d_texto or getattr(q, 'option_d', None),
            }

            option_images = {
                "A": q.opcion_a_imagen,
                "B": q.opcion_b_imagen,
                "C": q.opcion_c_imagen,
                "D": q.opcion_d_imagen,
            }

            for opt_id in ["A", "B", "C", "D"]:
                text = option_texts.get(opt_id)
                image = option_images.get(opt_id)
                if text or image:
                    options.append(QuestionOption(
                        id=opt_id,
                        text=text,
                        image_url=image
                    ))

            raid_questions.append(RaidQuestion(
                id=q.id,
                text=q.pregunta_texto or q.text,
                image_url=q.pregunta_imagen or getattr(q, 'image_url', None),
                options=options
            ))

        return BossRaidStartResponse(
            session_id=session.id,
            boss=boss_response,
            questions=raid_questions,
            total_questions=len(raid_questions),
            xp_multiplier=BossRaidService.XP_MULTIPLIER,
            started_at=session.started_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting raid: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    request: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit an answer during a Boss Raid session.

    Correct answers:
    - Deal damage to the boss (base + combo bonus)
    - Earn 3x XP
    - Increase combo counter

    Incorrect answers:
    - Break combo
    - No damage or XP
    """
    try:
        result, error = BossRaidService.submit_answer(
            db=db,
            session_id=request.session_id,
            question_id=request.question_id,
            answer_id=request.answer_id,
            time_spent_seconds=request.time_spent_seconds,
            user_id=current_user.id
        )

        if error:
            error_messages = {
                "SESSION_NOT_FOUND": "Sesion de raid no encontrada",
                "SESSION_NOT_ACTIVE": "La sesion de raid ya no esta activa",
                "QUESTION_ALREADY_ANSWERED": "Esta pregunta ya fue respondida",
                "QUESTION_NOT_FOUND": "Pregunta no encontrada"
            }
            raise HTTPException(
                status_code=400,
                detail=error_messages.get(error, error)
            )

        return SubmitAnswerResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete", response_model=CompleteRaidResponse)
async def complete_raid(
    request: CompleteRaidRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete a Boss Raid session and receive rewards.

    Calculates:
    - Total damage dealt
    - Total XP earned (with 3x multiplier)
    - Accuracy percentage
    - Final rank in the raid
    - Earned rewards (gold, badges)
    """
    try:
        result, error = BossRaidService.complete_raid(
            db=db,
            session_id=request.session_id,
            user_id=current_user.id
        )

        if error:
            error_messages = {
                "SESSION_NOT_FOUND": "Sesion de raid no encontrada"
            }
            raise HTTPException(
                status_code=400,
                detail=error_messages.get(error, error)
            )

        # Convert rewards to proper format
        rewards = [
            RaidReward(
                type=r["type"],
                amount=r.get("amount"),
                name=r.get("name")
            )
            for r in result.get("rewards", [])
        ]

        return CompleteRaidResponse(
            boss_defeated=result["boss_defeated"],
            total_damage=result["total_damage"],
            total_xp=result["total_xp"],
            correct_answers=result["correct_answers"],
            total_questions=result["total_questions"],
            accuracy_percentage=result["accuracy_percentage"],
            best_combo=result["best_combo"],
            rank_in_raid=result.get("rank_in_raid"),
            rewards=rewards,
            session_duration_seconds=result["session_duration_seconds"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing raid: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard", response_model=BossRaidLeaderboardResponse)
async def get_leaderboard(
    limit: int = Query(default=50, le=100, description="Max entries to return"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get the current Boss Raid leaderboard.

    Shows top participants ranked by total damage dealt.
    """
    try:
        # Get current boss
        boss_data = BossRaidService.get_current_boss(db)
        if not boss_data:
            raise HTTPException(
                status_code=404,
                detail="No hay jefe activo esta semana"
            )

        user_id = current_user.id if current_user else None

        result = BossRaidService.get_leaderboard(
            db=db,
            boss_id=boss_data["id"],
            user_id=user_id,
            limit=limit
        )

        # Convert to response models
        leaderboard = [
            LeaderboardEntry(**entry)
            for entry in result.get("leaderboard", [])
        ]

        my_entry = None
        if result.get("my_entry"):
            my_entry = LeaderboardEntry(**result["my_entry"])

        return BossRaidLeaderboardResponse(
            boss_id=result["boss_id"],
            boss_name=result["boss_name"],
            leaderboard=leaderboard,
            my_entry=my_entry,
            total_participants=result["total_participants"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current status of a Boss Raid session.

    Used to resume an interrupted session or check progress.
    """
    from ..models.boss_raid import BossRaidSession, Boss

    try:
        session = db.query(BossRaidSession).filter(
            BossRaidSession.id == session_id,
            BossRaidSession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Sesion de raid no encontrada"
            )

        boss = db.query(Boss).filter(Boss.id == session.boss_id).first()
        boss_name = boss.name if boss else "Unknown Boss"

        # Calculate elapsed time
        from datetime import datetime
        if session.completed_at:
            elapsed = int((session.completed_at - session.started_at).total_seconds())
        else:
            elapsed = int((datetime.utcnow() - session.started_at).total_seconds())

        return SessionStatusResponse(
            session_id=session.id,
            boss_name=boss_name,
            status=session.status,
            questions_answered=session.questions_answered,
            total_questions=session.total_questions,
            correct_answers=session.correct_answers,
            total_damage=session.total_damage,
            total_xp_earned=session.total_xp_earned,
            current_combo=session.current_combo,
            max_combo=session.combo_max,
            time_elapsed_seconds=elapsed,
            started_at=session.started_at,
            completed_at=session.completed_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
