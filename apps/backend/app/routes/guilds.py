from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..services.guild_service import GuildService
from ..schemas.guild import (
    GuildCreate, GuildResponse, GuildMemberResponse, TournamentResponse,
    TournamentParticipantResponse, GuildChatMessageCreate, GuildChatMessageResponse,
    SchoolRankingResponse, UserSchoolInfo, GuildSearchRequest, TournamentSearchRequest,
    GuildStatistics, SchoolStatistics, RankingPeriod, TournamentType, TournamentStatus,
    MessageType
)
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/guilds", tags=["guilds"])

@router.post("/auto-detect-school")
async def auto_detect_school(
    user_id: str,
    school_name: str,
    school_city: str = None,
    db: Session = Depends(get_db)
):
    """Auto-detect school and create/join guild"""
    guild_service = GuildService(db)
    result = guild_service.auto_detect_school(user_id, school_name, school_city)
    
    if result["success"]:
        guild_service.update_guild_statistics(result["guild_id"])
        guild_service.update_school_rankings()
    
    return result

@router.get("/user-guild/{user_id}")
async def get_user_guild(user_id: str, db: Session = Depends(get_db)):
    """Get user's guild information"""
    guild_service = GuildService(db)
    guild_info = guild_service.get_user_guild(user_id)
    
    if not guild_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no pertenece a ningún gremio"
        )
    
    return guild_info

@router.get("/{guild_id}/members")
async def get_guild_members(guild_id: str, db: Session = Depends(get_db)):
    """Get all members of a guild"""
    guild_service = GuildService(db)
    members = guild_service.get_guild_members(guild_id)
    return members

@router.get("/school-rankings")
async def get_school_rankings(
    period: RankingPeriod = RankingPeriod.MONTHLY,
    db: Session = Depends(get_db)
):
    """Get school rankings by period"""
    guild_service = GuildService(db)
    rankings = guild_service.get_school_rankings(period)
    return rankings

@router.get("/tournaments/available")
async def get_available_tournaments(
    school_name: str = None,
    db: Session = Depends(get_db)
):
    """Get available tournaments"""
    guild_service = GuildService(db)
    tournaments = guild_service.get_available_tournaments(school_name)
    return tournaments

@router.post("/tournaments/{tournament_id}/join")
async def join_tournament(
    tournament_id: str,
    guild_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Join a tournament"""
    guild_service = GuildService(db)
    result = guild_service.join_tournament(tournament_id, guild_id, user_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result

@router.get("/tournaments/{tournament_id}/participants")
async def get_tournament_participants(
    tournament_id: str,
    db: Session = Depends(get_db)
):
    """Get tournament participants"""
    guild_service = GuildService(db)
    participants = guild_service.get_tournament_participants(tournament_id)
    return participants

@router.post("/{guild_id}/chat/send")
async def send_guild_message(
    guild_id: str,
    message_data: GuildChatMessageCreate,
    db: Session = Depends(get_db)
):
    """Send a message to guild chat"""
    guild_service = GuildService(db)
    result = guild_service.send_guild_message(
        guild_id=guild_id,
        user_id=message_data.user_id,
        message=message_data.message,
        message_type=message_data.message_type
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result

@router.get("/{guild_id}/chat")
async def get_guild_chat(
    guild_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get guild chat messages"""
    guild_service = GuildService(db)
    messages = guild_service.get_guild_chat(guild_id, limit)
    return messages

@router.get("/{guild_id}/statistics")
async def get_guild_statistics(guild_id: str, db: Session = Depends(get_db)):
    """Get detailed guild statistics"""
    guild_service = GuildService(db)
    statistics = guild_service.get_guild_statistics(guild_id)
    
    if not statistics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gremio no encontrado"
        )
    
    return statistics

@router.get("/schools/{school_name}/statistics")
async def get_school_statistics(school_name: str, db: Session = Depends(get_db)):
    """Get school statistics"""
    guild_service = GuildService(db)
    
    # Get all guilds for this school
    from ..models.guild import Guild
    guilds = db.query(Guild).filter(Guild.school_name == school_name).all()
    
    if not guilds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Escuela no encontrada"
        )
    
    total_students = sum(guild.total_members for guild in guilds)
    total_score = sum(guild.total_score for guild in guilds)
    total_experience = sum(guild.guild_experience for guild in guilds)
    battles_won = sum(guild.total_score // 100 for guild in guilds)
    
    # Get active tournaments
    from ..models.guild import Tournament
    active_tournaments = db.query(Tournament).filter(
        Tournament.status.in_([TournamentStatus.ACTIVE, TournamentStatus.UPCOMING])
    ).count()
    
    return {
        "school_name": school_name,
        "total_students": total_students,
        "average_score": total_score // total_students if total_students > 0 else 0,
        "total_battles_won": battles_won,
        "total_experience": total_experience,
        "guilds_count": len(guilds),
        "active_tournaments": active_tournaments
    }

@router.get("/search")
async def search_guilds(
    school_name: str = None,
    school_city: str = None,
    guild_name: str = None,
    db: Session = Depends(get_db)
):
    """Search for guilds"""
    from ..models.guild import Guild
    from sqlalchemy import and_
    
    query = db.query(Guild)
    
    if school_name:
        query = query.filter(Guild.school_name.ilike(f"%{school_name}%"))
    if school_city:
        query = query.filter(Guild.school_city.ilike(f"%{school_city}%"))
    if guild_name:
        query = query.filter(Guild.guild_name.ilike(f"%{guild_name}%"))
    
    guilds = query.all()
    
    return [
        {
            "id": str(guild.id),
            "guild_name": guild.guild_name,
            "school_name": guild.school_name,
            "school_city": guild.school_city,
            "description": guild.description,
            "total_members": guild.total_members,
            "total_score": guild.total_score,
            "average_level": float(guild.average_level),
            "guild_level": guild.guild_level
        }
        for guild in guilds
    ]

@router.get("/tournaments/search")
async def search_tournaments(
    tournament_type: TournamentType = None,
    status: TournamentStatus = None,
    school_name: str = None,
    db: Session = Depends(get_db)
):
    """Search for tournaments"""
    from ..models.guild import Tournament
    from sqlalchemy import and_
    
    query = db.query(Tournament)
    
    if tournament_type:
        query = query.filter(Tournament.tournament_type == tournament_type)
    if status:
        query = query.filter(Tournament.status == status)
    
    tournaments = query.order_by(Tournament.start_date).all()
    
    return [
        {
            "id": str(tournament.id),
            "name": tournament.name,
            "description": tournament.description,
            "tournament_type": tournament.tournament_type,
            "start_date": tournament.start_date,
            "end_date": tournament.end_date,
            "status": tournament.status,
            "max_participants": tournament.max_participants,
            "current_participants": tournament.current_participants,
            "prize_pool": tournament.prize_pool
        }
        for tournament in tournaments
    ]

@router.post("/update-rankings")
async def update_school_rankings(
    period: RankingPeriod = RankingPeriod.MONTHLY,
    db: Session = Depends(get_db)
):
    """Update school rankings (admin function)"""
    guild_service = GuildService(db)
    guild_service.update_school_rankings(period)
    return {"success": True, "message": "Rankings actualizados"}

@router.get("/user/{user_id}/school-info")
async def get_user_school_info(user_id: str, db: Session = Depends(get_db)):
    """Get user's school information"""
    from ..models.user_profile import UserProfile
    
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    if not user_profile:
        return {"school_name": None, "school_city": None, "school_type": None}
    
    return {
        "school_name": None,
        "school_city": None,
        "school_type": None
    } 