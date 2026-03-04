"""
Mobile API Routes - ICFES Leveling Mobile App
Offline-First & Adaptive Learning Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date, timedelta, timezone
from uuid import UUID
import logging # New import

from ..core.database import get_db
from ..core.security import get_current_user
from ..models import User, Question, Topic, Subject
from ..services.mobile_service import MobileService
from ..schemas.mobile import (
    # Questions
    QuestionResponse, QuestionOption, QuestionBatchResponse, NextQuestionResponse,
    # Answers
    AnswerSubmitRequest, AnswerSubmitResponse,
    # Sync
    SyncAnswersRequest, SyncAnswersResponse, SyncStateRequest, SyncStateResponse,
    SyncStatusResponse, ConflictItem,
    # Hearts
    HeartsStatusResponse, HeartsUseRequest, HeartsUseResponse,
    HeartsRefillRequest, HeartsRefillResponse,
    # Streaks
    StreakStatusResponse, StreakExtendRequest, StreakExtendResponse,
    StreakFreezeResponse, DailyGoalInfo, StreakUpdate,
    StreakRepairRequest, StreakRepairResponse, StreakFreezeRequest,  # NEW: Repair schemas
    # Leagues
    LeagueCurrentResponse, LeaderboardResponse, LeaderboardEntry,
    LeagueJoinResponse, LeagueHistoryResponse, LeagueHistoryEntry, DivisionInfo,
    LeagueZone,  # NEW: Zone enum for league positions
    # Mastery
    MasteryTopicsResponse, WeakAreasResponse,
    # Notifications
    NotificationRegisterRequest, NotificationRegisterResponse,
    NotificationPreferences, NotificationPreferencesResponse,
    # Common
    APIResponse, APIErrorResponse, ErrorDetail
)
from ..services.streak_service import StreakService
from ..middleware.rate_limit import rate_limit

# Create router
router = APIRouter(prefix="/mobile", tags=["Mobile API"])


# ============================================
# HELPER: Get current user ID from JWT
# ============================================
async def get_current_user_id(
    current_user: User = Depends(get_current_user)
) -> UUID:
    """Extract user ID from JWT-authenticated user"""
    return current_user.id


# ============================================
# QUESTIONS ENDPOINTS
# ============================================

@router.get("/questions/next", response_model=NextQuestionResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def get_next_question(
    request: Request,
    subject_id: Optional[UUID] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get next adaptive question for the user.
    Uses adaptive algorithm to prioritize weak areas.
    """
    service = MobileService(db)
    question = service.get_next_adaptive_question(user_id, subject_id)

    if not question:
        raise HTTPException(status_code=404, detail="No questions available")

    # Get topic and subject info
    topic = db.query(Topic).filter(Topic.id == question.topic_id).first()
    subject = db.query(Subject).filter(Subject.id == topic.subject_id).first() if topic else None

    # Parse options - use new ICFES format
    options = []
    option_texts = [
        (getattr(question, 'opcion_a_texto', None), getattr(question, 'opcion_a_imagen', None)),
        (getattr(question, 'opcion_b_texto', None), getattr(question, 'opcion_b_imagen', None)),
        (getattr(question, 'opcion_c_texto', None), getattr(question, 'opcion_c_imagen', None)),
        (getattr(question, 'opcion_d_texto', None), getattr(question, 'opcion_d_imagen', None)),
    ]

    for i, (text, img) in enumerate(option_texts):
        if text:
            options.append(QuestionOption(
                id=chr(65 + i),  # A, B, C, D
                text=text,
                image_url=img
            ))

    # Fallback to legacy options field
    if not options and question.options:
        for i, opt in enumerate(question.options):
            options.append(QuestionOption(
                id=chr(65 + i),
                text=opt if isinstance(opt, str) else str(opt),
                image_url=None
            ))

    # Count cached questions
    cached_count = len(service.get_question_batch(user_id, limit=10, subject_id=subject_id))

    return NextQuestionResponse(
        question=QuestionResponse(
            id=question.id,
            text=getattr(question, 'pregunta_texto', None) or question.question_text or "",
            image_url=getattr(question, 'pregunta_imagen', None),
            topic_id=question.topic_id,
            topic_name=topic.name if topic else "Unknown",
            subject_id=subject.id if subject else question.topic_id,
            subject_name=subject.name if subject else "Unknown",
            difficulty=getattr(question, 'difficulty', 'medium') or 'medium',
            options=options
        ),
        cached_count=cached_count
    )


@router.get("/questions/batch", response_model=QuestionBatchResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def get_question_batch(
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    subject_id: Optional[UUID] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get batch of questions for offline cache.
    Returns questions user hasn't seen recently.
    """
    service = MobileService(db)
    questions = service.get_question_batch(user_id, limit, subject_id)

    result_questions = []
    for q in questions:
        topic = db.query(Topic).filter(Topic.id == q.topic_id).first()
        subject = db.query(Subject).filter(Subject.id == topic.subject_id).first() if topic else None

        # Parse options - use new ICFES format
        options = []
        option_texts = [
            (getattr(q, 'opcion_a_texto', None), getattr(q, 'opcion_a_imagen', None)),
            (getattr(q, 'opcion_b_texto', None), getattr(q, 'opcion_b_imagen', None)),
            (getattr(q, 'opcion_c_texto', None), getattr(q, 'opcion_c_imagen', None)),
            (getattr(q, 'opcion_d_texto', None), getattr(q, 'opcion_d_imagen', None)),
        ]

        for i, (text, img) in enumerate(option_texts):
            if text:
                options.append(QuestionOption(
                    id=chr(65 + i),
                    text=text,
                    image_url=img
                ))

        # Fallback to legacy options field
        if not options and q.options:
            for i, opt in enumerate(q.options):
                options.append(QuestionOption(
                    id=chr(65 + i),
                    text=opt if isinstance(opt, str) else str(opt),
                    image_url=None
                ))

        result_questions.append(QuestionResponse(
            id=q.id,
            text=getattr(q, 'pregunta_texto', None) or q.question_text or "",
            image_url=getattr(q, 'pregunta_imagen', None),
            topic_id=q.topic_id,
            topic_name=topic.name if topic else "Unknown",
            subject_id=subject.id if subject else q.topic_id,
            subject_name=subject.name if subject else "Unknown",
            difficulty=str(getattr(q, 'difficulty', 'medium') or 'medium'),
            options=options
        ))

    return QuestionBatchResponse(
        questions=result_questions,
        total=len(result_questions)
    )


# ============================================
# ANSWERS ENDPOINTS
# ============================================

@router.post("/answers/submit", response_model=AnswerSubmitResponse)
@rate_limit(limit=60, window=60)
async def submit_answer(
    http_request: Request,
    request: AnswerSubmitRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Submit an answer to a question.
    This is an atomic transaction that updates XP, mastery, and hearts.
    """
    service = MobileService(db)

    try:
        correct, xp_earned, mastery_update, streak_update, hearts_remaining = service.submit_answer(
            user_id=user_id,
            question_id=request.question_id,
            answer_id=request.answer_id,
            time_spent_seconds=request.time_spent_seconds,
            session_type=request.session_type.value,
            session_id=request.session_id
        )

        question = db.query(Question).filter(Question.id == request.question_id).first()
        correct_answer_id = getattr(question, 'respuesta_correcta', None) or question.correct_answer or ""
        
        # Get latest hearts status to check for unlimited hearts
        hearts_status = service.get_hearts_status(user_id)
        in_grace_mode = hearts_status.get("grace_mode_active", False)

        return AnswerSubmitResponse(
            correct=correct,
            correct_answer_id=correct_answer_id.upper(),
            explanation=getattr(question, 'explanation', None),
            xp_earned=xp_earned,
            hearts_remaining=hearts_remaining,
            mastery_update=mastery_update,
            streak_update=streak_update,
            # These fields are placeholders as they are part of another refactor
            attempt_type="new", 
            xp_multiplier=1.0,
            in_grace_mode=in_grace_mode
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # The service's atomic method should handle rollback, but we can log here
        logging.error(f"An error occurred in submit_answer endpoint: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")


# ============================================
# SYNC ENDPOINTS
# ============================================

@router.post("/sync/answers", response_model=SyncAnswersResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for sync
async def sync_answers(
    http_request: Request,
    request: SyncAnswersRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Sync offline answers to server.
    Processes batch of answers collected while offline.
    """
    service = MobileService(db)

    synced_count, failed, server_state = service.sync_answers(user_id, request.actions)

    return SyncAnswersResponse(
        synced_count=synced_count,
        failed=failed,
        server_state=server_state
    )


@router.post("/sync/state", response_model=SyncStateResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for sync
async def sync_state(
    http_request: Request,
    request: SyncStateRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Reconcile client state with server.
    Server state is authoritative for conflicts.
    """
    service = MobileService(db)
    server_state = service.get_server_state(user_id)

    conflicts = []

    # Check hearts
    if request.hearts != server_state.hearts:
        conflicts.append(ConflictItem(
            field="hearts",
            client_value=request.hearts,
            server_value=server_state.hearts,
            resolution="server"
        ))

    # Check streak
    if request.streak != server_state.streak:
        conflicts.append(ConflictItem(
            field="streak",
            client_value=request.streak,
            server_value=server_state.streak,
            resolution="server"
        ))

    return SyncStateResponse(
        server_state=server_state,
        conflicts=conflicts
    )


@router.get("/sync/status", response_model=SyncStatusResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def get_sync_status(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get current sync status.
    """
    from ..models import PendingAnswerSync

    pending_count = db.query(PendingAnswerSync).filter(
        PendingAnswerSync.user_id == user_id,
        PendingAnswerSync.sync_status == 'pending'
    ).count()

    last_sync = db.query(PendingAnswerSync.synced_at).filter(
        PendingAnswerSync.user_id == user_id,
        PendingAnswerSync.sync_status == 'synced'
    ).order_by(PendingAnswerSync.synced_at.desc()).first()

    return SyncStatusResponse(
        pending_count=pending_count,
        last_sync=last_sync[0] if last_sync else None,
        server_time=datetime.now(timezone.utc)
    )


# ============================================
# HEARTS ENDPOINTS
# ============================================

@router.get("/hearts/status", response_model=HeartsStatusResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def get_hearts_status(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get current hearts status including regeneration timer.
    """
    service = MobileService(db)

    # First regenerate any pending hearts
    service.regenerate_hearts(user_id)

    status = service.get_hearts_status(user_id)

    return HeartsStatusResponse(**status)


@router.post("/hearts/use", response_model=HeartsUseResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def use_heart(
    http_request: Request,
    request: HeartsUseRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Use a heart (e.g., for wrong answer).
    """
    service = MobileService(db)

    try:
        remaining = service.use_heart(user_id, request.reason, request.source_id)
        status = service.get_hearts_status(user_id)

        return HeartsUseResponse(
            hearts_remaining=remaining,
            next_regen_at=status["next_regen_at"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "HEARTS_EMPTY",
                "message": str(e),
                "data": service.get_hearts_status(user_id)
            }
        )


@router.post("/hearts/refill", response_model=HeartsRefillResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def refill_hearts(
    http_request: Request,
    request: HeartsRefillRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Refill hearts using gems, ad, or purchase.
    """
    service = MobileService(db)

    try:
        hearts, gems = service.refill_hearts(user_id, request.method, request.gems_spent)
        status = service.get_hearts_status(user_id)

        return HeartsRefillResponse(
            hearts=hearts,
            max_hearts=status["max_hearts"],
            gems_remaining=gems
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# STREAK ENDPOINTS
# ============================================

@router.get("/streak/status", response_model=StreakStatusResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def get_streak_status(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get current streak status and daily goal progress.
    """
    service = MobileService(db)
    status = service.get_streak_status(user_id)

    return StreakStatusResponse(**status)


@router.post("/streak/extend", response_model=StreakExtendResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def extend_streak(
    http_request: Request,
    request: StreakExtendRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Record XP earned and extend streak if daily goal met.
    """
    service = MobileService(db)

    # Update daily activity
    from ..models import UserDailyActivity, User

    today = request.activity_date or date.today()
    user = db.query(User).filter(User.id == user_id).first()

    activity = db.query(UserDailyActivity).filter(
        UserDailyActivity.user_id == user_id,
        UserDailyActivity.activity_date == today
    ).first()

    first_time = activity is None

    if not activity:
        activity = UserDailyActivity(
            user_id=user_id,
            activity_date=today,
            first_session_at=datetime.utcnow()
        )
        db.add(activity)

    activity.xp_earned = (activity.xp_earned or 0) + request.xp_earned
    activity.last_session_at = datetime.utcnow()

    daily_goal = getattr(user, 'daily_goal_xp', 20) or 20
    goal_met = activity.xp_earned >= daily_goal
    activity.daily_goal_met = goal_met

    streak_extended = False
    current_streak = getattr(user, 'current_streak', 0) or 0

    if goal_met and not activity.streak_extended:
        activity.streak_extended = True
        streak_extended = True

        if user:
            yesterday = today - timedelta(days=1)
            if getattr(user, 'last_activity_date', None) == yesterday:
                user.current_streak = (user.current_streak or 0) + 1
            elif getattr(user, 'last_activity_date', None) != today:
                user.current_streak = 1

            user.longest_streak = max(user.longest_streak or 0, user.current_streak)
            user.last_activity_date = today
            current_streak = user.current_streak

    db.commit()

    return StreakExtendResponse(
        streak=StreakUpdate(
            current=current_streak,
            extended=streak_extended,
            daily_goal_met=goal_met
        ),
        daily_goal=DailyGoalInfo(
            xp_earned=activity.xp_earned,
            target=daily_goal,
            met=goal_met,
            first_time_today=first_time
        )
    )


@router.post("/streak/freeze", response_model=StreakFreezeResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def use_streak_freeze(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Use a streak freeze to protect streak.
    """
    service = MobileService(db)

    try:
        remaining, freeze_date = service.use_streak_freeze(user_id)
        return StreakFreezeResponse(
            freezes_remaining=remaining,
            freeze_date=freeze_date
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_FREEZES", "message": str(e)}
        )


@router.post("/streak/repair", response_model=StreakRepairResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def repair_streak(
    http_request: Request,
    request: StreakRepairRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Repair a lost streak within 24h window.

    Available repair methods:
    - "gold": Costs 300 gold
    - "ad": Watch an ad (1 per day)

    The streak can only be repaired if:
    1. The streak was recently lost (within 24 hours)
    2. There was a previous streak to restore

    Error codes:
    - NO_STREAK_TO_REPAIR: No streak to repair
    - STREAK_REPAIR_EXPIRED: 24h repair window has passed
    - AD_REPAIR_USED: Already used ad repair today
    - NOT_ENOUGH_GOLD: Insufficient gold (need 300)
    """
    streak_service = StreakService(db)

    try:
        result = streak_service.repair_streak(user_id, request.method.value)
        return StreakRepairResponse(**result)

    except ValueError as e:
        error_code = str(e)

        if error_code == "NO_STREAK_TO_REPAIR":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "NO_STREAK_TO_REPAIR",
                    "message": "No hay racha para reparar"
                }
            )
        elif error_code == "STREAK_REPAIR_EXPIRED":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "STREAK_REPAIR_EXPIRED",
                    "message": "Ventana de reparacion de 24h expirada"
                }
            )
        elif error_code == "AD_REPAIR_USED":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "AD_REPAIR_USED",
                    "message": "Ya usaste el anuncio para reparar hoy"
                }
            )
        elif error_code == "NOT_ENOUGH_GOLD":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "NOT_ENOUGH_GOLD",
                    "message": "No tienes suficiente oro (necesitas 300)"
                }
            )
        else:
            raise HTTPException(status_code=400, detail=str(e))


# ============================================
# MASTERY ENDPOINTS
# ============================================

@router.get("/mastery/topics", response_model=MasteryTopicsResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def get_mastery_topics(
    request: Request,
    subject_id: Optional[UUID] = None,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get mastery scores for all topics.
    """
    service = MobileService(db)
    topics = service.get_topic_mastery(user_id, subject_id)

    return MasteryTopicsResponse(topics=topics)


@router.get("/mastery/weak-areas", response_model=WeakAreasResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def get_weak_areas(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get weak areas that need practice.
    """
    service = MobileService(db)
    weak_areas = service.get_weak_areas(user_id)

    return WeakAreasResponse(weak_areas=weak_areas)


# ============================================
# LEAGUES ENDPOINTS (Simplified for MVP)
# ============================================

# League Zone Constants (NEW: Updated thresholds per API contract)
LEAGUE_GROUP_SIZE = 30  # Fixed group size
PROMOTION_TOP_N = 10    # Top 10 get promoted (33%)
RELEGATION_BOTTOM_N = 5 # Bottom 5 get relegated (17%)
# Safe zone: positions 11-25 (50%)


def calculate_league_zone(rank: int, total_participants: int) -> LeagueZone:
    """
    Calculate which zone a player is in based on their rank.

    Zone breakdown for 30 participants:
    - Promotion: Top 10 (positions 1-10, 33%)
    - Safe: Middle 15 (positions 11-25, 50%)
    - Relegation: Bottom 5 (positions 26-30, 17%)
    """
    if rank <= PROMOTION_TOP_N:
        return LeagueZone.PROMOTION
    elif rank > total_participants - RELEGATION_BOTTOM_N:
        return LeagueZone.RELEGATION
    else:
        return LeagueZone.SAFE


@router.get("/leagues/current", response_model=LeagueCurrentResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def get_current_league(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get current league status for user.

    Returns zone information:
    - zone: "promotion" | "safe" | "relegation"
    - promotion_threshold: 10 (Top 10 of 30)
    - relegation_threshold: 26 (positions 26-30 are bottom 5)
    - participants: 30
    """
    from ..models import UserLeague, LeagueGroup, LeagueDivision, LeagueWeek

    # Get active week
    week = db.query(LeagueWeek).filter(LeagueWeek.is_active == True).first()

    if not week:
        raise HTTPException(status_code=404, detail="No active league week")

    # Get user's league entry
    user_league = db.query(UserLeague).join(LeagueGroup).filter(
        UserLeague.user_id == user_id,
        LeagueGroup.league_week_id == week.id
    ).first()

    if not user_league:
        raise HTTPException(status_code=404, detail="User not in league. Use POST /leagues/join")

    group = db.query(LeagueGroup).filter(LeagueGroup.id == user_league.league_group_id).first()
    division = db.query(LeagueDivision).filter(LeagueDivision.id == group.division_id).first()

    # Count participants (should be 30, but handle edge cases)
    participants = db.query(UserLeague).filter(
        UserLeague.league_group_id == group.id
    ).count()

    # Calculate user's current rank dynamically based on XP
    user_rank = db.query(UserLeague).filter(
        UserLeague.league_group_id == group.id,
        UserLeague.weekly_xp > user_league.weekly_xp
    ).count() + 1

    # Calculate zone based on rank
    zone = calculate_league_zone(user_rank, participants)

    # Calculate relegation threshold (position where relegation starts)
    # For 30 participants with bottom 5 relegated: threshold = 30 - 5 + 1 = 26
    relegation_threshold = participants - RELEGATION_BOTTOM_N + 1

    return LeagueCurrentResponse(
        division=DivisionInfo(
            id=division.id,
            name=division.name,
            tier=division.tier,
            color=division.color_hex or "#FFFFFF"
        ),
        group_id=group.id,
        rank=user_rank,
        zone=zone,  # NEW: Zone field
        weekly_xp=user_league.weekly_xp,
        week_ends_at=datetime.combine(week.week_end, datetime.max.time()),
        promotion_threshold=PROMOTION_TOP_N,  # Fixed: Top 10
        relegation_threshold=relegation_threshold,  # Dynamic: 26 for 30 participants
        participants=participants
    )


@router.get("/leagues/leaderboard", response_model=LeaderboardResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def get_leaderboard(
    request: Request,
    limit: int = Query(30, ge=1, le=50),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get leaderboard for user's current league group with zone information.

    Zone breakdown:
    - Top 10 (rank <= 10): zone = "promotion"
    - Positions 11-25: zone = "safe"
    - Bottom 5 (rank > total - 5): zone = "relegation"

    Returns my_zone in response for quick access to current user's zone.
    """
    from ..models import UserLeague, LeagueGroup, LeagueWeek

    # Get user's current group
    week = db.query(LeagueWeek).filter(LeagueWeek.is_active == True).first()
    if not week:
        raise HTTPException(status_code=404, detail="No active league week")

    user_league = db.query(UserLeague).join(LeagueGroup).filter(
        UserLeague.user_id == user_id,
        LeagueGroup.league_week_id == week.id
    ).first()

    if not user_league:
        raise HTTPException(status_code=404, detail="User not in league")

    # Get total participants first for zone calculation
    total = db.query(UserLeague).filter(
        UserLeague.league_group_id == user_league.league_group_id
    ).count()

    # Get all members of the group ordered by XP
    members = db.query(UserLeague, User).join(
        User, UserLeague.user_id == User.id
    ).filter(
        UserLeague.league_group_id == user_league.league_group_id
    ).order_by(UserLeague.weekly_xp.desc()).limit(limit).all()

    leaderboard = []
    my_rank = 0
    my_xp = 0
    my_zone = LeagueZone.SAFE  # Default

    for rank, (league, user) in enumerate(members, 1):
        is_me = league.user_id == user_id

        # Calculate zone for this participant
        zone = calculate_league_zone(rank, total)

        if is_me:
            my_rank = rank
            my_xp = league.weekly_xp
            my_zone = zone

        leaderboard.append(LeaderboardEntry(
            user_id=user.id,
            name=user.display_name or user.username,
            avatar_url=None,
            xp=league.weekly_xp,
            rank=rank,
            zone=zone,  # NEW: Zone for each participant
            is_me=is_me
        ))

    return LeaderboardResponse(
        leaderboard=leaderboard,
        my_rank=my_rank,
        my_xp=my_xp,
        my_zone=my_zone,  # NEW: Current user's zone
        total_participants=total
    )


@router.post("/leagues/join", response_model=LeagueJoinResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def join_league(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Join the current week's league.
    New users start in Bronze division.
    """
    from ..models import UserLeague, LeagueGroup, LeagueDivision, LeagueWeek

    # Get active week
    week = db.query(LeagueWeek).filter(LeagueWeek.is_active == True).first()

    if not week:
        # Create new week if none exists
        from datetime import timedelta
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        week = LeagueWeek(
            week_number=today.isocalendar()[1],
            year=today.year,
            week_start=week_start,
            week_end=week_end,
            is_active=True
        )
        db.add(week)
        db.flush()

    # Check if already in league
    existing = db.query(UserLeague).join(LeagueGroup).filter(
        UserLeague.user_id == user_id,
        LeagueGroup.league_week_id == week.id
    ).first()

    if existing:
        group = db.query(LeagueGroup).filter(LeagueGroup.id == existing.league_group_id).first()
        division = db.query(LeagueDivision).filter(LeagueDivision.id == group.division_id).first()

        return LeagueJoinResponse(
            group_id=group.id,
            division=DivisionInfo(
                id=division.id,
                name=division.name,
                tier=division.tier,
                color=division.color_hex or "#FFFFFF"
            ),
            position=existing.current_rank or 0,
            week_ends_at=datetime.combine(week.week_end, datetime.max.time())
        )

    # Get Bronze division
    bronze = db.query(LeagueDivision).filter(LeagueDivision.tier == 1).first()
    if not bronze:
        bronze = LeagueDivision(name="Bronce", tier=1, color_hex="#CD7F32")
        db.add(bronze)
        db.flush()

    # Find or create a group with space
    group = db.query(LeagueGroup).filter(
        LeagueGroup.league_week_id == week.id,
        LeagueGroup.division_id == bronze.id
    ).first()

    if not group:
        group = LeagueGroup(
            league_week_id=week.id,
            division_id=bronze.id,
            group_number=1
        )
        db.add(group)
        db.flush()

    # Count current members
    member_count = db.query(UserLeague).filter(
        UserLeague.league_group_id == group.id
    ).count()

    # Create new group if full
    if member_count >= group.max_members:
        group = LeagueGroup(
            league_week_id=week.id,
            division_id=bronze.id,
            group_number=group.group_number + 1
        )
        db.add(group)
        db.flush()

    # Join the group
    user_league = UserLeague(
        user_id=user_id,
        league_group_id=group.id,
        weekly_xp=0,
        current_rank=member_count + 1
    )
    db.add(user_league)
    db.commit()

    return LeagueJoinResponse(
        group_id=group.id,
        division=DivisionInfo(
            id=bronze.id,
            name=bronze.name,
            tier=bronze.tier,
            color=bronze.color_hex or "#CD7F32"
        ),
        position=member_count + 1,
        week_ends_at=datetime.combine(week.week_end, datetime.max.time())
    )


@router.get("/leagues/history", response_model=LeagueHistoryResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def get_league_history(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get user's league history.
    """
    from ..models import UserLeagueHistory, LeagueWeek, LeagueDivision

    history = db.query(UserLeagueHistory, LeagueWeek, LeagueDivision).join(
        LeagueWeek, UserLeagueHistory.league_week_id == LeagueWeek.id
    ).join(
        LeagueDivision, UserLeagueHistory.division_id == LeagueDivision.id
    ).filter(
        UserLeagueHistory.user_id == user_id
    ).order_by(LeagueWeek.week_start.desc()).limit(10).all()

    weeks = []
    for entry, week, division in history:
        weeks.append(LeagueHistoryEntry(
            week_id=week.id,
            week_start=week.week_start,
            week_end=week.week_end,
            division_name=division.name,
            final_rank=entry.final_rank,
            final_xp=entry.final_xp,
            status=entry.status,
            gems_earned=entry.gems_earned
        ))

    return LeagueHistoryResponse(weeks=weeks)


# ============================================
# NOTIFICATION ENDPOINTS
# ============================================

@router.post("/notifications/register", response_model=NotificationRegisterResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def register_device(
    http_request: Request,
    request: NotificationRegisterRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Register device token for push notifications.
    """
    from ..models import UserDeviceToken

    # Check if token exists
    existing = db.query(UserDeviceToken).filter(
        UserDeviceToken.device_token == request.token
    ).first()

    if existing:
        existing.user_id = user_id
        existing.platform = request.platform.value
        existing.is_active = True
        existing.last_used_at = datetime.utcnow()
        if request.device_info:
            existing.device_info = request.device_info.dict()
    else:
        token = UserDeviceToken(
            user_id=user_id,
            device_token=request.token,
            platform=request.platform.value,
            device_info=request.device_info.dict() if request.device_info else None
        )
        db.add(token)

    db.commit()

    return NotificationRegisterResponse(registered=True)


@router.put("/notifications/preferences", response_model=NotificationPreferencesResponse)
@rate_limit(limit=100, window=60)  # 100 requests per minute for general endpoints
async def update_notification_preferences(
    request: Request,
    preferences: NotificationPreferences,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update notification preferences.
    """
    # For now, just return the preferences
    # In production, store in user preferences table
    return NotificationPreferencesResponse(preferences=preferences)
