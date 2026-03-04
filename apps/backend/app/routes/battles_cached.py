from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import random
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..services.game_engine_service import calculate_damage, calculate_experience_gain, calculate_orbs_gain
from ..models.user import User
from ..models.user_profile import UserProfile
from ..models.battle import Battle, BattleAnswer
from ..models.question import Question
from ..models.subject import Subject
from ..schemas.battle import BattleCreate, BattleResponse, BattleAnswerCreate
from ..services.cache_service import cache_service
from ..services.clickhouse_service import clickhouse_service

router = APIRouter(prefix="/battles/cached", tags=["battles-cached"])
logger = logging.getLogger(__name__)

@router.post("/start", response_model=BattleResponse)
async def start_cached_battle(
    battle_create: BattleCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new battle with caching"""
    # Get user profile from cache or DB
    user_profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    
    # Create battle (using User model fields for hp, not UserProfile)
    battle = Battle(
        user_id=current_user.id,
        battle_type=battle_create.battle_type,
        enemy_name=battle_create.enemy_name,
        enemy_level=battle_create.enemy_level,
        enemy_hp=battle_create.enemy_level * 50,
        user_hp_start=current_user.hp,
        user_hp_end=current_user.hp,
        status="in_progress"
    )
    
    db.add(battle)
    db.commit()
    db.refresh(battle)
    
    # Cache battle state
    battle_state = {
        "battle_id": str(battle.id),
        "user_id": str(battle.user_id),
        "battle_type": battle.battle_type,
        "enemy_name": battle.enemy_name,
        "enemy_level": battle.enemy_level,
        "enemy_hp": battle.enemy_hp,
        "enemy_max_hp": battle.enemy_max_hp,
        "player_hp": battle.player_hp,
        "player_max_hp": battle.player_max_hp,
        "player_mp": battle.player_mp,
        "player_max_mp": battle.player_max_mp,
        "questions_answered": 0,
        "correct_answers": 0,
        "total_damage_dealt": 0,
        "total_damage_received": 0,
        "combo_count": 0,
        "max_combo": 0,
        "status": battle.status,
        "start_time": datetime.utcnow().isoformat()
    }
    
    cache_service.cache_battle_state(str(battle.id), battle_state)
    
    # Track event
    background_tasks.add_task(
        clickhouse_service.track_event,
        event_type="battle_started",
        user_id=str(current_user.id),
        event_data={
            "battle_id": str(battle.id),
            "battle_type": battle.battle_type,
            "enemy_name": battle.enemy_name,
            "enemy_level": battle.enemy_level
        }
    )
    
    return BattleResponse(**battle_state)

@router.get("/{battle_id}/state")
async def get_cached_battle_state(
    battle_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current battle state from cache"""
    # Try cache first
    cached_state = cache_service.get_battle_state(battle_id)
    if cached_state:
        logger.info(f"Cache hit for battle state: {battle_id}")
        # Verify user owns this battle
        if cached_state.get("user_id") != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")
        return cached_state
    
    # Cache miss - fetch from DB
    logger.info(f"Cache miss for battle state: {battle_id}")
    battle = db.query(Battle).filter(
        Battle.id == battle_id,
        Battle.user_id == current_user.id
    ).first()
    
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    
    # Rebuild state and cache it
    battle_state = {
        "battle_id": str(battle.id),
        "user_id": str(battle.user_id),
        "battle_type": battle.battle_type,
        "enemy_name": battle.enemy_name,
        "enemy_level": battle.enemy_level,
        "enemy_hp": battle.enemy_hp,
        "enemy_max_hp": battle.enemy_max_hp,
        "player_hp": battle.player_hp,
        "player_max_hp": battle.player_max_hp,
        "player_mp": battle.player_mp,
        "player_max_mp": battle.player_max_mp,
        "questions_answered": battle.questions_answered,
        "correct_answers": battle.correct_answers,
        "total_damage_dealt": battle.total_damage_dealt,
        "total_damage_received": battle.total_damage_received,
        "combo_count": battle.combo_count,
        "max_combo": battle.max_combo,
        "status": battle.status,
        "created_at": battle.created_at.isoformat()
    }
    
    if battle.status == "in_progress":
        cache_service.cache_battle_state(battle_id, battle_state)
    
    return battle_state

@router.post("/{battle_id}/answer")
async def submit_cached_answer(
    battle_id: str,
    answer: BattleAnswerCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit answer with cache update"""
    # Get battle state from cache
    battle_state = cache_service.get_battle_state(battle_id)
    
    if not battle_state:
        # Fallback to DB
        battle = db.query(Battle).filter(
            Battle.id == battle_id,
            Battle.user_id == current_user.id
        ).first()
        
        if not battle:
            raise HTTPException(status_code=404, detail="Battle not found")
        
        if battle.status != "in_progress":
            raise HTTPException(status_code=400, detail="Battle already finished")
        
        # Convert to state dict
        battle_state = {
            "battle_id": str(battle.id),
            "user_id": str(battle.user_id),
            "enemy_hp": battle.enemy_hp,
            "enemy_max_hp": battle.enemy_max_hp,
            "player_hp": battle.player_hp,
            "player_max_hp": battle.player_max_hp,
            "player_mp": battle.player_mp,
            "questions_answered": battle.questions_answered,
            "correct_answers": battle.correct_answers,
            "total_damage_dealt": battle.total_damage_dealt,
            "total_damage_received": battle.total_damage_received,
            "combo_count": battle.combo_count,
            "max_combo": battle.max_combo,
            "enemy_level": battle.enemy_level
        }
    
    # Verify ownership
    if battle_state.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get question
    question = db.query(Question).filter(Question.id == answer.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Get user profile for stats
    user_profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    
    # Check answer
    is_correct = answer.user_answer == question.correct_answer
    
    # Calculate damage
    damage_dealt = 0
    damage_received = 0
    critical_hit = False
    
    if is_correct:
        # Player deals damage
        damage_dealt = calculate_damage(
            user_profile.power,
            user_profile.wisdom,
            question.difficulty,
            battle_state["combo_count"]
        )
        
        # Critical hit chance
        if random.random() < 0.1 + (user_profile.speed * 0.001):
            damage_dealt = int(damage_dealt * 1.5)
            critical_hit = True
        
        battle_state["enemy_hp"] = max(0, battle_state["enemy_hp"] - damage_dealt)
        battle_state["combo_count"] += 1
        battle_state["correct_answers"] += 1
    else:
        # Enemy deals damage
        damage_received = battle_state["enemy_level"] * 10
        battle_state["player_hp"] = max(0, battle_state["player_hp"] - damage_received)
        battle_state["combo_count"] = 0
    
    # Update statistics
    battle_state["questions_answered"] += 1
    battle_state["total_damage_dealt"] += damage_dealt
    battle_state["total_damage_received"] += damage_received
    battle_state["max_combo"] = max(battle_state["max_combo"], battle_state["combo_count"])
    
    # Check battle end conditions
    battle_won = False
    battle_lost = False
    
    if battle_state["enemy_hp"] <= 0:
        battle_won = True
        battle_state["status"] = "completed"
    elif battle_state["player_hp"] <= 0:
        battle_lost = True
        battle_state["status"] = "failed"
    
    # Save answer to DB
    battle_answer = BattleAnswer(
        battle_id=uuid.UUID(battle_id),
        question_id=question.id,
        user_answer=answer.user_answer,
        is_correct=is_correct,
        damage_dealt=damage_dealt,
        damage_received=damage_received,
        response_time=answer.response_time
    )
    db.add(battle_answer)
    
    # Update battle in DB
    battle = db.query(Battle).filter(Battle.id == battle_id).first()
    battle.enemy_hp = battle_state["enemy_hp"]
    battle.player_hp = battle_state["player_hp"]
    battle.questions_answered = battle_state["questions_answered"]
    battle.correct_answers = battle_state["correct_answers"]
    battle.total_damage_dealt = battle_state["total_damage_dealt"]
    battle.total_damage_received = battle_state["total_damage_received"]
    battle.combo_count = battle_state["combo_count"]
    battle.max_combo = battle_state["max_combo"]
    battle.status = battle_state["status"]
    
    if battle_won or battle_lost:
        battle.completed_at = datetime.utcnow()
        
        # Calculate rewards
        if battle_won:
            experience_gained = calculate_experience_gain(
                battle.enemy_level,
                battle.correct_answers,
                battle.questions_answered
            )
            orbs_gained = calculate_orbs_gain(
                battle.enemy_level,
                battle.correct_answers
            )
            
            battle.experience_gained = experience_gained
            battle.orbs_gained = orbs_gained
            
            # Update user profile
            user_profile.experience += experience_gained
            user_profile.orbs += orbs_gained
            user_profile.battles_won += 1
            
            # Track analytics
            background_tasks.add_task(
                clickhouse_service.track_battle_analytics,
                {
                    "battle_id": str(battle.id),
                    "user_id": str(current_user.id),
                    "battle_type": battle.battle_type,
                    "enemy_name": battle.enemy_name,
                    "enemy_level": battle.enemy_level,
                    "questions_answered": battle.questions_answered,
                    "correct_answers": battle.correct_answers,
                    "total_damage_dealt": battle.total_damage_dealt,
                    "total_damage_received": battle.total_damage_received,
                    "experience_gained": experience_gained,
                    "orbs_gained": orbs_gained,
                    "duration_seconds": int((battle.completed_at - battle.created_at).total_seconds()),
                    "status": "completed",
                    "created_at": battle.created_at,
                    "completed_at": battle.completed_at
                }
            )
        else:
            user_profile.battles_lost += 1
        
        # Invalidate user profile cache
        background_tasks.add_task(
            cache_service.invalidate_user_profile,
            str(current_user.id)
        )
        
        # Remove battle from cache
        cache_service.delete(f"battle:state:{battle_id}")
    else:
        # Update cache if battle continues
        cache_service.cache_battle_state(battle_id, battle_state)
    
    # Update question stats
    user_profile.questions_answered += 1
    if is_correct:
        user_profile.correct_answers += 1
    
    db.commit()
    
    # Track answer event
    background_tasks.add_task(
        clickhouse_service.track_question_performance,
        {
            "question_id": str(question.id),
            "user_id": str(current_user.id),
            "subject_id": str(question.subject_id),
            "topic_id": question.topic or "general",
            "difficulty": question.difficulty,
            "user_answer": answer.user_answer,
            "correct_answer": question.correct_answer,
            "is_correct": is_correct,
            "response_time_ms": answer.response_time,
            "damage_dealt": damage_dealt,
            "damage_received": damage_received,
            "critical_hit": critical_hit,
            "battle_id": battle_id
        }
    )
    
    return {
        "is_correct": is_correct,
        "damage_dealt": damage_dealt,
        "damage_received": damage_received,
        "critical_hit": critical_hit,
        "combo_count": battle_state["combo_count"],
        "enemy_hp": battle_state["enemy_hp"],
        "player_hp": battle_state["player_hp"],
        "battle_won": battle_won,
        "battle_lost": battle_lost,
        "experience_gained": battle.experience_gained if battle_won else 0,
        "orbs_gained": battle.orbs_gained if battle_won else 0,
        "correct_answer": question.correct_answer,
        "explanation": question.explanation
    }

@router.post("/cache/warmup")
async def warmup_battle_cache(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Warmup cache with user's active battles (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get all in-progress battles
    active_battles = db.query(Battle).filter(
        Battle.status == "in_progress"
    ).limit(100).all()
    
    cached_count = 0
    for battle in active_battles:
        battle_state = {
            "battle_id": str(battle.id),
            "user_id": str(battle.user_id),
            "battle_type": battle.battle_type,
            "enemy_name": battle.enemy_name,
            "enemy_level": battle.enemy_level,
            "enemy_hp": battle.enemy_hp,
            "enemy_max_hp": battle.enemy_max_hp,
            "player_hp": battle.player_hp,
            "player_max_hp": battle.player_max_hp,
            "player_mp": battle.player_mp,
            "player_max_mp": battle.player_max_mp,
            "questions_answered": battle.questions_answered,
            "correct_answers": battle.correct_answers,
            "total_damage_dealt": battle.total_damage_dealt,
            "total_damage_received": battle.total_damage_received,
            "combo_count": battle.combo_count,
            "max_combo": battle.max_combo,
            "status": battle.status,
            "created_at": battle.created_at.isoformat()
        }
        
        if cache_service.cache_battle_state(str(battle.id), battle_state):
            cached_count += 1
    
    return {
        "message": f"Warmed up cache with {cached_count} active battles",
        "total_active_battles": len(active_battles)
    }