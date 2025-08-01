from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import time
from sqlalchemy import func

from ..core.database import get_db
from ..core.security import get_current_user, calculate_damage, calculate_experience_gain, calculate_orbs_gain, calculate_level, calculate_rank
from ..schemas.battle import BattleCreate, BattleResponse, BattleAnswer, BattleAnswerResponse
from ..models.user import User
from ..models.battle import Battle, BattleAnswer as BattleAnswerModel
from ..models.question import Question

router = APIRouter(prefix="/battles", tags=["battles"])

# Almacenamiento temporal para WebSocket connections
active_connections = {}

@router.post("/", response_model=BattleResponse)
async def create_battle(
    battle_data: BattleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear una nueva batalla"""
    # Crear batalla
    battle = Battle(
        user_id=current_user.id,
        battle_type=battle_data.battle_type,
        enemy_name=battle_data.enemy_name or f"Enemigo {battle_data.battle_type}",
        enemy_level=battle_data.enemy_level or current_user.level,
        enemy_hp=battle_data.enemy_hp or 100,
        user_hp_start=current_user.hp,
        user_hp_end=current_user.hp,
        status="in_progress"
    )
    
    db.add(battle)
    db.commit()
    db.refresh(battle)
    
    return battle

@router.post("/{battle_id}/answer", response_model=BattleAnswerResponse)
async def answer_question(
    battle_id: str,
    answer_data: BattleAnswer,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Responder una pregunta en batalla"""
    # Obtener batalla
    battle = db.query(Battle).filter(
        Battle.id == battle_id,
        Battle.user_id == current_user.id
    ).first()
    
    if not battle:
        raise HTTPException(status_code=404, detail="Batalla no encontrada")
    
    if battle.status != "in_progress":
        raise HTTPException(status_code=400, detail="Batalla ya finalizada")
    
    # Obtener pregunta
    question = db.query(Question).filter(Question.id == answer_data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    
    # Verificar respuesta
    is_correct = answer_data.user_answer == question.correct_answer
    
    # Calcular daño
    damage_dealt = calculate_damage(
        user_power=current_user.power,
        user_wisdom=current_user.wisdom,
        is_correct=is_correct,
        response_time_ms=answer_data.response_time_ms,
        difficulty=question.difficulty
    )
    
    # Calcular daño recibido (si es incorrecto)
    damage_received = 0
    if not is_correct:
        damage_received = question.difficulty * 5
    
    # Verificar crítico
    critical_hit = answer_data.response_time_ms < 3000 and is_correct
    
    # Calcular experiencia y orbes
    experience_gained = calculate_experience_gain(
        is_correct=is_correct,
        difficulty=question.difficulty,
        response_time_ms=answer_data.response_time_ms
    )
    
    orbs_gained = calculate_orbs_gain(
        is_correct=is_correct,
        difficulty=question.difficulty,
        critical_hit=critical_hit
    )
    
    # Actualizar HP del usuario y enemigo
    battle.user_hp_end = max(0, battle.user_hp_end - damage_received)
    battle.enemy_hp = max(0, battle.enemy_hp - damage_dealt)
    
    # Actualizar contadores
    battle.questions_answered += 1
    if is_correct:
        battle.correct_answers += 1
    
    battle.total_damage_dealt += damage_dealt
    battle.total_damage_received += damage_received
    battle.experience_gained += experience_gained
    battle.orbs_gained += orbs_gained
    
    # Verificar si la batalla terminó
    if battle.user_hp_end <= 0:
        battle.status = "failed"
        battle.completed_at = db.query(func.now()).scalar()
    elif battle.enemy_hp <= 0:
        battle.status = "completed"
        battle.completed_at = db.query(func.now()).scalar()
    
    # Guardar respuesta
    battle_answer = BattleAnswerModel(
        battle_id=battle.id,
        question_id=answer_data.question_id,
        user_answer=answer_data.user_answer,
        is_correct=is_correct,
        response_time_ms=answer_data.response_time_ms,
        damage_dealt=damage_dealt,
        damage_received=damage_received,
        critical_hit=critical_hit
    )
    
    db.add(battle_answer)
    
    # Actualizar usuario si la batalla terminó
    if battle.status in ["completed", "failed"]:
        current_user.experience += battle.experience_gained
        current_user.orbs += battle.orbs_gained
        
        # Recalcular nivel y rango
        new_level = calculate_level(current_user.experience)
        if new_level > current_user.level:
            current_user.level = new_level
            current_user.rank = calculate_rank(new_level)
            # Bonus por subir de nivel
            current_user.hp = min(150, current_user.hp + 10)
            current_user.mp = min(75, current_user.mp + 5)
    
    db.commit()
    
    # Enviar actualización por WebSocket si hay conexión activa
    if battle_id in active_connections:
        try:
            await active_connections[battle_id].send_text(json.dumps({
                "type": "battle_update",
                "battle_id": str(battle.id),
                "user_hp": battle.user_hp_end,
                "enemy_hp": battle.enemy_hp,
                "damage_dealt": damage_dealt,
                "damage_received": damage_received,
                "is_correct": is_correct,
                "critical_hit": critical_hit,
                "experience_gained": experience_gained,
                "orbs_gained": orbs_gained,
                "battle_status": battle.status
            }))
        except:
            pass
    
    return BattleAnswerResponse(
        is_correct=is_correct,
        damage_dealt=damage_dealt,
        damage_received=damage_received,
        critical_hit=critical_hit,
        experience_gained=experience_gained,
        orbs_gained=orbs_gained,
        combo_count=battle.correct_answers,
        user_hp_remaining=battle.user_hp_end,
        enemy_hp_remaining=battle.enemy_hp
    )

@router.get("/{battle_id}", response_model=BattleResponse)
async def get_battle(
    battle_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener información de una batalla"""
    battle = db.query(Battle).filter(
        Battle.id == battle_id,
        Battle.user_id == current_user.id
    ).first()
    
    if not battle:
        raise HTTPException(status_code=404, detail="Batalla no encontrada")
    
    return battle

@router.get("/", response_model=List[BattleResponse])
async def get_user_battles(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener historial de batallas del usuario"""
    battles = db.query(Battle).filter(
        Battle.user_id == current_user.id
    ).order_by(Battle.created_at.desc()).offset(offset).limit(limit).all()
    
    return battles

@router.websocket("/ws/{battle_id}")
async def websocket_battle(websocket: WebSocket, battle_id: str):
    """WebSocket para actualizaciones de batalla en tiempo real"""
    await websocket.accept()
    active_connections[battle_id] = websocket
    
    try:
        while True:
            # Mantener conexión activa
            data = await websocket.receive_text()
            # Procesar mensajes si es necesario
    except WebSocketDisconnect:
        if battle_id in active_connections:
            del active_connections[battle_id] 