from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import redis
import json

from ..core.database import get_db
from ..core.security import get_current_user
from ..core.config import settings
from ..models.user import User
from ..models.leaderboard import Leaderboard

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

# Conexión a Redis para cache
redis_client = redis.from_url(settings.REDIS_URL)

@router.get("/global")
async def get_global_leaderboard(
    limit: int = Query(10, ge=1, le=100, description="Número de jugadores a mostrar"),
    offset: int = Query(0, ge=0, description="Posición inicial"),
    db: Session = Depends(get_db)
):
    """Obtener leaderboard global"""
    cache_key = f"leaderboard:global:{limit}:{offset}"
    
    # Verificar cache
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Obtener leaderboard desde base de datos
    leaderboard = db.query(Leaderboard).filter(
        Leaderboard.leaderboard_type == "global"
    ).order_by(Leaderboard.score.desc()).offset(offset).limit(limit).all()
    
    # Obtener información de usuarios
    result = []
    for entry in leaderboard:
        user = db.query(User).filter(User.id == entry.user_id).first()
        if user:
            result.append({
                "rank": entry.rank_position,
                "user_id": str(user.id),
                "username": user.username,
                "display_name": user.display_name,
                "level": user.level,
                "rank_letter": user.rank,
                "score": entry.score,
                "avatar_url": user.avatar_url
            })
    
    # Guardar en cache por 5 minutos
    redis_client.setex(cache_key, 300, json.dumps(result))
    
    return result

@router.get("/weekly")
async def get_weekly_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtener leaderboard semanal"""
    cache_key = f"leaderboard:weekly:{limit}"
    
    # Verificar cache
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Obtener leaderboard semanal
    leaderboard = db.query(Leaderboard).filter(
        Leaderboard.leaderboard_type == "weekly"
    ).order_by(Leaderboard.score.desc()).limit(limit).all()
    
    result = []
    for entry in leaderboard:
        user = db.query(User).filter(User.id == entry.user_id).first()
        if user:
            result.append({
                "rank": entry.rank_position,
                "user_id": str(user.id),
                "username": user.username,
                "display_name": user.display_name,
                "level": user.level,
                "rank_letter": user.rank,
                "score": entry.score,
                "avatar_url": user.avatar_url
            })
    
    # Guardar en cache por 5 minutos
    redis_client.setex(cache_key, 300, json.dumps(result))
    
    return result

@router.get("/monthly")
async def get_monthly_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtener leaderboard mensual"""
    cache_key = f"leaderboard:monthly:{limit}"
    
    # Verificar cache
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Obtener leaderboard mensual
    leaderboard = db.query(Leaderboard).filter(
        Leaderboard.leaderboard_type == "monthly"
    ).order_by(Leaderboard.score.desc()).limit(limit).all()
    
    result = []
    for entry in leaderboard:
        user = db.query(User).filter(User.id == entry.user_id).first()
        if user:
            result.append({
                "rank": entry.rank_position,
                "user_id": str(user.id),
                "username": user.username,
                "display_name": user.display_name,
                "level": user.level,
                "rank_letter": user.rank,
                "score": entry.score,
                "avatar_url": user.avatar_url
            })
    
    # Guardar en cache por 5 minutos
    redis_client.setex(cache_key, 300, json.dumps(result))
    
    return result

@router.get("/user/position")
async def get_user_position(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener posición del usuario en el leaderboard global"""
    # Buscar entrada del usuario en leaderboard global
    entry = db.query(Leaderboard).filter(
        Leaderboard.user_id == current_user.id,
        Leaderboard.leaderboard_type == "global"
    ).first()
    
    if not entry:
        return {
            "rank": None,
            "score": 0,
            "total_players": 0
        }
    
    # Contar total de jugadores
    total_players = db.query(Leaderboard).filter(
        Leaderboard.leaderboard_type == "global"
    ).count()
    
    return {
        "rank": entry.rank_position,
        "score": entry.score,
        "total_players": total_players
    }

@router.get("/user/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas del usuario para leaderboard"""
    # Obtener todas las entradas del usuario
    entries = db.query(Leaderboard).filter(
        Leaderboard.user_id == current_user.id
    ).all()
    
    stats = {
        "global_rank": None,
        "weekly_rank": None,
        "monthly_rank": None,
        "best_score": 0,
        "total_battles": 0,
        "win_rate": 0.0
    }
    
    for entry in entries:
        if entry.leaderboard_type == "global":
            stats["global_rank"] = entry.rank_position
        elif entry.leaderboard_type == "weekly":
            stats["weekly_rank"] = entry.rank_position
        elif entry.leaderboard_type == "monthly":
            stats["monthly_rank"] = entry.rank_position
        
        if entry.score > stats["best_score"]:
            stats["best_score"] = entry.score
    
    # Obtener estadísticas de batallas
    from ..models.battle import Battle
    battles = db.query(Battle).filter(Battle.user_id == current_user.id).all()
    stats["total_battles"] = len(battles)
    
    if battles:
        wins = sum(1 for battle in battles if battle.status == "completed")
        stats["win_rate"] = wins / len(battles)
    
    return stats 