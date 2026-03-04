"""
Dungeon Routes for ICFES Leveling API

Solo Leveling-inspired dungeon system endpoints:
- GET /dungeons/gates - Get available dungeon gates for user
- POST /dungeons/{gate_id}/enter - Enter a dungeon gate, start a run
- GET /dungeons/encounters/{encounter_id}/questions - Get questions for encounter
- POST /dungeons/encounters/{encounter_id}/submit - Submit encounter answers
- GET /dungeons/history - Get user's dungeon run history
- GET /dungeons/{gate_id}/leaderboard - Get gate leaderboard
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import logging

from ..core.database import get_db
from ..core.security import get_current_user, get_current_user_optional
from ..models.user import User
from ..services.dungeon_service import DungeonService
from ..schemas.dungeon import (
    # Gate schemas
    GateResponse,
    GateEntryCosts,
    GateRewards,
    GateStats,
    AvailableGatesResponse,
    # Enter gate schemas
    EnterGateRequest,
    EnterGateResponse,
    GateInfo,
    EncounterInfo,
    EnemyInfo,
    # Questions schemas
    DungeonQuestion,
    EncounterQuestionsResponse,
    # Submit answers schemas
    SubmitEncounterAnswersRequest,
    SubmitEncounterAnswersResponse,
    EncounterResults,
    ShadowExtractionResult,
    # History schemas
    DungeonRunHistory,
    DungeonRunRewards,
    DungeonRunStats,
    DungeonHistoryResponse,
    # Leaderboard schemas
    DungeonLeaderboardEntry,
    GateLeaderboardResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dungeons", tags=["dungeons"])


@router.get("/gates", response_model=AvailableGatesResponse)
async def get_available_gates(
    gate_type: Optional[str] = Query(default=None, description="Filter by gate type (regular, boss, raid, seasonal)"),
    difficulty: Optional[str] = Query(default=None, description="Filter by difficulty rank (E, D, C, B, A, S, SS, SSS)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get available dungeon gates for the authenticated user.

    Gates are filtered based on:
    - User level and rank requirements
    - Currency availability (orbs, crystals)
    - Gate type and difficulty filters
    - Seasonal availability

    Returns a list of gates the user can currently enter.
    """
    try:
        dungeon_service = DungeonService(db)
        gates_data = dungeon_service.get_available_gates(
            user_id=str(current_user.id),
            gate_type=gate_type,
            difficulty=difficulty
        )

        # Convert to response models
        gates = []
        for gate_data in gates_data:
            gates.append(GateResponse(
                id=gate_data["id"],
                name=gate_data["name"],
                description=gate_data.get("description"),
                type=gate_data["type"],
                difficulty_rank=gate_data["difficulty_rank"],
                recommended_level=gate_data["recommended_level"],
                time_limit=gate_data.get("time_limit"),
                entry_costs=GateEntryCosts(
                    orbs=gate_data["entry_costs"].get("orbs", 0),
                    crystals=gate_data["entry_costs"].get("crystals", 0)
                ),
                rewards=GateRewards(
                    experience=gate_data["rewards"].get("experience", 0),
                    orbs=gate_data["rewards"].get("orbs", 0),
                    crystals=gate_data["rewards"].get("crystals", 0)
                ),
                stats=GateStats(
                    times_entered=gate_data["stats"].get("times_entered", 0),
                    times_completed=gate_data["stats"].get("times_completed", 0),
                    success_rate=gate_data["stats"].get("success_rate", 0.0),
                    avg_completion_time=gate_data["stats"].get("avg_completion_time")
                ),
                is_raid=gate_data.get("is_raid", False),
                max_participants=gate_data.get("max_participants", 1),
                is_seasonal=gate_data.get("is_seasonal", False)
            ))

        return AvailableGatesResponse(
            gates=gates,
            total=len(gates),
            user_level=current_user.level,
            user_rank=current_user.rank or "E"
        )

    except Exception as e:
        logger.error(f"Error getting available gates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{gate_id}/enter", response_model=EnterGateResponse)
async def enter_gate(
    gate_id: str,
    request: Optional[EnterGateRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enter a dungeon gate and start a new run.

    Requirements:
    - User must meet level and rank requirements
    - User must have sufficient currency for entry cost
    - User must not have an active dungeon run

    Returns:
    - Run ID for tracking the dungeon session
    - Gate information (rooms, time limit)
    - First encounter with enemy information
    """
    try:
        dungeon_service = DungeonService(db)
        result = dungeon_service.enter_gate(
            user_id=str(current_user.id),
            gate_id=gate_id
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "GATE_ENTRY_FAILED",
                    "message": result.get("message", "No se pudo entrar al portal")
                }
            )

        # Build gate info
        gate_info = None
        if result.get("gate_info"):
            gate_info = GateInfo(
                name=result["gate_info"]["name"],
                total_rooms=result["gate_info"]["total_rooms"],
                time_limit=result["gate_info"].get("time_limit")
            )

        # Build encounter info
        current_encounter = None
        if result.get("current_encounter"):
            enc = result["current_encounter"]
            enemy_info = EnemyInfo(
                name=enc["enemy"]["name"],
                level=enc["enemy"]["level"],
                type=enc["enemy"]["type"],
                health=enc["enemy"]["health"],
                description=enc["enemy"].get("description")
            )
            current_encounter = EncounterInfo(
                encounter_id=enc["encounter_id"],
                room_number=enc["room_number"],
                encounter_type=enc["encounter_type"],
                enemy=enemy_info,
                questions_required=enc.get("questions_required", 3)
            )

        return EnterGateResponse(
            success=True,
            message=result.get("message", "Entraste al portal exitosamente"),
            run_id=result.get("run_id"),
            gate_info=gate_info,
            current_encounter=current_encounter
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error entering gate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/encounters/{encounter_id}/questions", response_model=EncounterQuestionsResponse)
async def get_encounter_questions(
    encounter_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get questions for a dungeon encounter.

    Questions are selected based on:
    - Monster's preferred subjects
    - Monster's difficulty level
    - User's current abilities

    Returns a list of questions to answer to defeat the enemy.
    """
    try:
        dungeon_service = DungeonService(db)
        questions_data = dungeon_service.get_questions_for_encounter(encounter_id)

        if not questions_data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "ENCOUNTER_NOT_FOUND",
                    "message": "Encuentro no encontrado o sin preguntas disponibles"
                }
            )

        # Convert to response models
        questions = []
        for q in questions_data:
            questions.append(DungeonQuestion(
                id=q["id"],
                question_text=q["question_text"],
                option_a=q.get("option_a"),
                option_b=q.get("option_b"),
                option_c=q.get("option_c"),
                option_d=q.get("option_d"),
                image_url=q.get("image_url"),
                difficulty=q.get("difficulty", 3)
            ))

        return EncounterQuestionsResponse(
            encounter_id=encounter_id,
            questions=questions,
            total_questions=len(questions),
            time_limit_seconds=300  # 5 minutes per encounter by default
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting encounter questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/encounters/{encounter_id}/submit", response_model=SubmitEncounterAnswersResponse)
async def submit_encounter_answers(
    encounter_id: str,
    request: SubmitEncounterAnswersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit answers for a dungeon encounter.

    Combat calculation:
    - Accuracy determines damage dealt (60%+ to win)
    - Shadows provide bonus damage
    - Correct answers reduce damage taken

    Results:
    - Win: Advance to next room, gain rewards
    - Lose: Dungeon run ends (failed status)
    - Dungeon Complete: All rooms cleared, receive completion bonus
    """
    try:
        dungeon_service = DungeonService(db)
        result = dungeon_service.submit_encounter_answers(
            encounter_id=encounter_id,
            user_id=str(current_user.id),
            answers=request.answers,
            shadows_used=request.shadows_used
        )

        if not result.get("success") and result.get("message"):
            # Check for specific errors
            if result["message"] == "Encounter not found":
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "ENCOUNTER_NOT_FOUND",
                        "message": "Encuentro no encontrado"
                    }
                )
            elif result["message"] == "Not your encounter":
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "NOT_YOUR_ENCOUNTER",
                        "message": "Este encuentro no te pertenece"
                    }
                )

        # Build encounter results
        enc_results = None
        if result.get("encounter_results"):
            enc = result["encounter_results"]
            enc_results = EncounterResults(
                accuracy=enc.get("accuracy", 0.0),
                correct_answers=enc.get("correct_answers", 0),
                total_questions=enc.get("total_questions", 0),
                damage_dealt=enc.get("damage_dealt", 0),
                damage_taken=enc.get("damage_taken", 0),
                experience_gained=enc.get("experience_gained", 0),
                orbs_gained=enc.get("orbs_gained", 0)
            )

        # Build shadow extraction result if present
        shadow_extraction = None
        if result.get("shadow_extraction"):
            se = result["shadow_extraction"]
            shadow_extraction = ShadowExtractionResult(
                success=se.get("success", False),
                shadow_name=se.get("shadow_name"),
                shadow_level=se.get("shadow_level"),
                shadow_type=se.get("shadow_type"),
                message=se.get("message", "")
            )

        # Build next encounter if present
        next_encounter = None
        if result.get("next_encounter"):
            ne = result["next_encounter"]
            if ne.get("enemy"):
                enemy_info = EnemyInfo(
                    name=ne["enemy"]["name"],
                    level=ne["enemy"]["level"],
                    type=ne["enemy"]["type"],
                    health=ne["enemy"]["health"],
                    description=ne["enemy"].get("description")
                )
                next_encounter = EncounterInfo(
                    encounter_id=ne["encounter_id"],
                    room_number=ne["room_number"],
                    encounter_type=ne["encounter_type"],
                    enemy=enemy_info,
                    questions_required=ne.get("questions_required", 3)
                )

        return SubmitEncounterAnswersResponse(
            success=result.get("success", False),
            encounter_results=enc_results,
            dungeon_status=result.get("dungeon_status", "in_progress"),
            current_room=result.get("current_room", 1),
            shadow_extraction=shadow_extraction,
            next_encounter=next_encounter,
            completion_stats=result.get("completion_stats"),
            rewards=result.get("rewards"),
            final_score=result.get("final_score"),
            message=result.get("message")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting encounter answers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=DungeonHistoryResponse)
async def get_dungeon_history(
    limit: int = Query(default=20, le=100, description="Maximum number of runs to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the user's dungeon run history.

    Returns recent dungeon runs with:
    - Gate name and status
    - Completion time and score
    - Rewards earned
    - Combat statistics
    """
    try:
        dungeon_service = DungeonService(db)
        history_data = dungeon_service.get_user_dungeon_history(
            user_id=str(current_user.id),
            limit=limit
        )

        # Convert to response models
        runs = []
        total_completed = 0
        total_failed = 0
        best_score = 0

        for run_data in history_data:
            runs.append(DungeonRunHistory(
                id=run_data["id"],
                gate_name=run_data["gate_name"],
                status=run_data["status"],
                completion_time=run_data.get("completion_time"),
                score=run_data.get("score", 0),
                rewards=DungeonRunRewards(
                    experience=run_data["rewards"].get("experience", 0),
                    orbs=run_data["rewards"].get("orbs", 0),
                    crystals=run_data["rewards"].get("crystals", 0)
                ),
                stats=DungeonRunStats(
                    monsters_defeated=run_data["stats"].get("monsters_defeated", 0),
                    boss_defeated=run_data["stats"].get("boss_defeated", False),
                    accuracy=run_data["stats"].get("accuracy", 0.0),
                    perfect_clear=run_data["stats"].get("perfect_clear", False),
                    speed_clear=run_data["stats"].get("speed_clear", False)
                ),
                date=run_data["date"]
            ))

            # Calculate totals
            if run_data["status"] == "completed":
                total_completed += 1
                if run_data.get("score", 0) > best_score:
                    best_score = run_data["score"]
            elif run_data["status"] == "failed":
                total_failed += 1

        return DungeonHistoryResponse(
            runs=runs,
            total=len(runs),
            total_completed=total_completed,
            total_failed=total_failed,
            best_score=best_score
        )

    except Exception as e:
        logger.error(f"Error getting dungeon history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{gate_id}/leaderboard", response_model=GateLeaderboardResponse)
async def get_gate_leaderboard(
    gate_id: str,
    limit: int = Query(default=10, le=100, description="Maximum number of entries to return"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get the leaderboard for a specific dungeon gate.

    Shows top players ranked by:
    - Completion score (combination of accuracy, speed, and perfection)

    Special badges:
    - Perfect Clear: No damage taken
    - Speed Clear: Completed in under half the time limit
    """
    try:
        dungeon_service = DungeonService(db)
        leaderboard_data = dungeon_service.get_gate_leaderboards(
            gate_id=gate_id,
            limit=limit
        )

        if not leaderboard_data:
            # Return empty leaderboard if no data
            return GateLeaderboardResponse(
                gate_id=gate_id,
                gate_name="Unknown Gate",
                leaderboard=[],
                total_participants=0,
                my_entry=None,
                my_best_score=None
            )

        # Get gate name from first entry or fetch from DB
        from ..models.dungeon import DungeonGate
        gate = db.query(DungeonGate).filter(DungeonGate.id == gate_id).first()
        gate_name = gate.name if gate else "Unknown Gate"

        # Convert to response models
        leaderboard = []
        my_entry = None
        my_best_score = None

        for entry_data in leaderboard_data:
            entry = DungeonLeaderboardEntry(
                rank=entry_data["rank"],
                user_id=entry_data["user_id"],
                user_name=entry_data["user_name"],
                score=entry_data["score"],
                completion_time=entry_data["completion_time"],
                perfect_clear=entry_data.get("perfect_clear", False),
                speed_clear=entry_data.get("speed_clear", False),
                date=entry_data.get("date")
            )
            leaderboard.append(entry)

            # Check if this is the current user's entry
            if current_user and entry_data["user_id"] == str(current_user.id):
                my_entry = entry
                my_best_score = entry_data["score"]

        return GateLeaderboardResponse(
            gate_id=gate_id,
            gate_name=gate_name,
            leaderboard=leaderboard,
            total_participants=len(leaderboard_data),
            my_entry=my_entry,
            my_best_score=my_best_score
        )

    except Exception as e:
        logger.error(f"Error getting gate leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))
