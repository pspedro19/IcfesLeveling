from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.quest import DailyQuest, UserQuest

router = APIRouter(prefix="/quests", tags=["quests"])

@router.get("/daily")
async def get_daily_quests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener misiones diarias del usuario"""
    # Obtener quests diarios activos
    daily_quests = db.query(DailyQuest).filter(DailyQuest.active == True).all()
    
    # Obtener progreso del usuario para cada quest
    user_quests = db.query(UserQuest).filter(
        UserQuest.user_id == current_user.id
    ).all()
    
    # Crear diccionario de progreso
    progress_dict = {uq.quest_id: uq for uq in user_quests}
    
    result = []
    for quest in daily_quests:
        user_quest = progress_dict.get(quest.id)
        
        quest_data = {
            "id": str(quest.id),
            "title": quest.title,
            "description": quest.description,
            "quest_type": quest.quest_type,
            "target_value": quest.target_value,
            "reward_type": quest.reward_type,
            "reward_value": quest.reward_value,
            "progress": user_quest.progress if user_quest else 0,
            "completed": user_quest.completed if user_quest else False,
            "completed_at": user_quest.completed_at.isoformat() if user_quest and user_quest.completed_at else None
        }
        
        result.append(quest_data)
    
    return result

@router.post("/{quest_id}/complete")
async def complete_quest(
    quest_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Completar una misión"""
    # Verificar que la quest existe y está activa
    quest = db.query(DailyQuest).filter(
        DailyQuest.id == quest_id,
        DailyQuest.active == True
    ).first()
    
    if not quest:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    
    # Obtener progreso del usuario
    user_quest = db.query(UserQuest).filter(
        UserQuest.user_id == current_user.id,
        UserQuest.quest_id == quest_id
    ).first()
    
    if not user_quest:
        raise HTTPException(status_code=404, detail="Progreso de misión no encontrado")
    
    if user_quest.completed:
        raise HTTPException(status_code=400, detail="Misión ya completada")
    
    if user_quest.progress < quest.target_value:
        raise HTTPException(status_code=400, detail="Misión no completada aún")
    
    # Marcar como completada
    user_quest.completed = True
    user_quest.completed_at = datetime.utcnow()
    
    # Otorgar recompensa
    if quest.reward_type == "experience":
        current_user.experience += quest.reward_value
    elif quest.reward_type == "orbs":
        current_user.orbs += quest.reward_value
    elif quest.reward_type == "crystals":
        current_user.crystals += quest.reward_value
    elif quest.reward_type == "item" and quest.reward_item_id:
        # Agregar item al inventario del usuario
        from ..models.item import UserItem
        user_item = UserItem(
            user_id=current_user.id,
            item_id=quest.reward_item_id,
            quantity=quest.reward_value
        )
        db.add(user_item)
    
    db.commit()
    
    return {
        "message": "Misión completada exitosamente",
        "reward_type": quest.reward_type,
        "reward_value": quest.reward_value,
        "completed_at": user_quest.completed_at.isoformat()
    }

@router.get("/progress")
async def get_quest_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener progreso general de quests"""
    # Obtener todas las quests activas
    active_quests = db.query(DailyQuest).filter(DailyQuest.active == True).all()
    
    # Obtener progreso del usuario
    user_quests = db.query(UserQuest).filter(
        UserQuest.user_id == current_user.id
    ).all()
    
    progress_dict = {uq.quest_id: uq for uq in user_quests}
    
    total_quests = len(active_quests)
    completed_quests = 0
    total_progress = 0
    
    for quest in active_quests:
        user_quest = progress_dict.get(quest.id)
        if user_quest and user_quest.completed:
            completed_quests += 1
        elif user_quest:
            progress_percentage = min(100, (user_quest.progress / quest.target_value) * 100)
            total_progress += progress_percentage
    
    average_progress = total_progress / total_quests if total_quests > 0 else 0
    
    return {
        "total_quests": total_quests,
        "completed_quests": completed_quests,
        "completion_rate": (completed_quests / total_quests) * 100 if total_quests > 0 else 0,
        "average_progress": average_progress,
        "streak_days": current_user.streak_days
    }

@router.post("/update-progress")
async def update_quest_progress(
    quest_type: str,
    value: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar progreso de quests (llamado desde otros endpoints)"""
    # Obtener quests activas del tipo especificado
    quests = db.query(DailyQuest).filter(
        DailyQuest.active == True,
        DailyQuest.quest_type == quest_type
    ).all()
    
    updated_quests = []
    
    for quest in quests:
        # Obtener o crear progreso del usuario
        user_quest = db.query(UserQuest).filter(
            UserQuest.user_id == current_user.id,
            UserQuest.quest_id == quest.id
        ).first()
        
        if not user_quest:
            user_quest = UserQuest(
                user_id=current_user.id,
                quest_id=quest.id,
                progress=0
            )
            db.add(user_quest)
        
        # Actualizar progreso si no está completada
        if not user_quest.completed:
            user_quest.progress = min(quest.target_value, user_quest.progress + value)
            
            # Verificar si se completó
            if user_quest.progress >= quest.target_value:
                user_quest.completed = True
                user_quest.completed_at = datetime.utcnow()
            
            updated_quests.append({
                "quest_id": str(quest.id),
                "title": quest.title,
                "progress": user_quest.progress,
                "target": quest.target_value,
                "completed": user_quest.completed
            })
    
    db.commit()
    
    return {
        "updated_quests": updated_quests,
        "message": f"Progreso actualizado para {len(updated_quests)} misiones"
    } 