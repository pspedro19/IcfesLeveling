from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from ..models.guild import Guild, GuildMember, Tournament, TournamentParticipant, GuildChatMessage, SchoolRanking
from ..models.user_profile import UserProfile
from ..models.user import User
from ..models.battle import Battle
from ..schemas.guild import GuildRole, TournamentType, TournamentStatus, MessageType, RankingPeriod
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
import uuid

class GuildService:
    def __init__(self, db: Session):
        self.db = db

    def auto_detect_school(self, user_id: str, school_name: str, school_city: str = None) -> Dict[str, Any]:
        """Auto-detect school and create/join guild"""
        # Update user profile with school info
        user_profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile:
            user_profile = UserProfile(user_id=user_id)
            self.db.add(user_profile)
        
        # Note: school information is not stored in user_profile anymore
        # It's only stored in the guild system
        
        # Check if guild exists for this school
        existing_guild = self.db.query(Guild).filter(
            and_(
                Guild.school_name == school_name,
                Guild.school_city == school_city
            )
        ).first()
        
        if existing_guild:
            # Join existing guild
            guild_member = GuildMember(
                guild_id=existing_guild.id,
                user_id=user_id,
                role=GuildRole.MEMBER
            )
            self.db.add(guild_member)
            existing_guild.total_members += 1
            return {
                "success": True,
                "message": f"Unido al gremio existente: {existing_guild.guild_name}",
                "guild_id": str(existing_guild.id),
                "guild_name": existing_guild.guild_name
            }
        else:
            # Create new guild
            guild_name = f"Gremio de {school_name}"
            new_guild = Guild(
                school_name=school_name,
                school_city=school_city,
                guild_name=guild_name,
                description=f"Gremio oficial de {school_name}",
                total_members=1
            )
            self.db.add(new_guild)
            self.db.flush()  # Get the ID
            
            # Add user as leader
            guild_member = GuildMember(
                guild_id=new_guild.id,
                user_id=user_id,
                role=GuildRole.LEADER
            )
            self.db.add(guild_member)
            
            return {
                "success": True,
                "message": f"Gremio creado: {guild_name}",
                "guild_id": str(new_guild.id),
                "guild_name": guild_name
            }

    def get_user_guild(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's guild information"""
        guild_member = self.db.query(GuildMember).filter(GuildMember.user_id == user_id).first()
        if not guild_member:
            return None
        
        guild = guild_member.guild
        return {
            "guild_id": str(guild.id),
            "guild_name": guild.guild_name,
            "school_name": guild.school_name,
            "school_city": guild.school_city,
            "role": guild_member.role,
            "total_members": guild.total_members,
            "total_score": guild.total_score,
            "average_level": float(guild.average_level),
            "guild_level": guild.guild_level,
            "joined_at": guild_member.joined_at
        }

    def get_guild_members(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get all members of a guild"""
        members = self.db.query(GuildMember).filter(GuildMember.guild_id == guild_id).all()
        return [
            {
                "id": str(member.id),
                "user_id": str(member.user_id),
                "role": member.role,
                "joined_at": member.joined_at,
                "contribution_score": member.contribution_score,
                "last_activity": member.last_activity,
                "user_display_name": member.user.display_name if member.user else None,
                "user_level": member.user.level if member.user else None,
                "user_avatar_url": member.user.avatar_url if member.user else None
            }
            for member in members
        ]

    def get_school_rankings(self, period: RankingPeriod = RankingPeriod.MONTHLY) -> List[Dict[str, Any]]:
        """Get school rankings by period"""
        rankings = self.db.query(SchoolRanking).filter(
            SchoolRanking.ranking_period == period
        ).order_by(SchoolRanking.rank_position).all()
        
        return [
            {
                "id": str(ranking.id),
                "school_name": ranking.school_name,
                "school_city": ranking.school_city,
                "total_students": ranking.total_students,
                "average_score": ranking.average_score,
                "total_battles_won": ranking.total_battles_won,
                "total_experience": ranking.total_experience,
                "rank_position": ranking.rank_position,
                "ranking_period": ranking.ranking_period
            }
            for ranking in rankings
        ]

    def get_available_tournaments(self, school_name: str = None) -> List[Dict[str, Any]]:
        """Get available tournaments"""
        query = self.db.query(Tournament).filter(
            Tournament.status.in_([TournamentStatus.UPCOMING, TournamentStatus.ACTIVE])
        )
        
        if school_name:
            # Filter tournaments that include this school
            query = query.filter(Tournament.tournament_type == TournamentType.INTER_SCHOOL)
        
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

    def join_tournament(self, tournament_id: str, guild_id: str, user_id: str) -> Dict[str, Any]:
        """Join a tournament"""
        # Check if user is already participating
        existing_participant = self.db.query(TournamentParticipant).filter(
            and_(
                TournamentParticipant.tournament_id == tournament_id,
                TournamentParticipant.user_id == user_id
            )
        ).first()
        
        if existing_participant:
            return {"success": False, "message": "Ya estás participando en este torneo"}
        
        # Check if tournament is full
        tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            return {"success": False, "message": "Torneo no encontrado"}
        
        if tournament.max_participants and tournament.current_participants >= tournament.max_participants:
            return {"success": False, "message": "Torneo lleno"}
        
        # Join tournament
        participant = TournamentParticipant(
            tournament_id=tournament_id,
            guild_id=guild_id,
            user_id=user_id
        )
        self.db.add(participant)
        tournament.current_participants += 1
        
        return {"success": True, "message": "Unido al torneo exitosamente"}

    def get_tournament_participants(self, tournament_id: str) -> List[Dict[str, Any]]:
        """Get tournament participants"""
        participants = self.db.query(TournamentParticipant).filter(
            TournamentParticipant.tournament_id == tournament_id
        ).order_by(desc(TournamentParticipant.score)).all()
        
        return [
            {
                "id": str(participant.id),
                "user_id": str(participant.user_id),
                "guild_id": str(participant.guild_id),
                "score": participant.score,
                "rank_position": participant.rank_position,
                "battles_won": participant.battles_won,
                "battles_lost": participant.battles_lost,
                "joined_at": participant.joined_at,
                "user_display_name": participant.user.display_name if participant.user else None,
                "guild_name": participant.guild.guild_name if participant.guild else None
            }
            for participant in participants
        ]

    def send_guild_message(self, guild_id: str, user_id: str, message: str, message_type: MessageType = MessageType.TEXT) -> Dict[str, Any]:
        """Send a message to guild chat"""
        chat_message = GuildChatMessage(
            guild_id=guild_id,
            user_id=user_id,
            message=message,
            message_type=message_type
        )
        self.db.add(chat_message)
        
        return {"success": True, "message": "Mensaje enviado"}

    def get_guild_chat(self, guild_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get guild chat messages"""
        messages = self.db.query(GuildChatMessage).filter(
            GuildChatMessage.guild_id == guild_id
        ).order_by(desc(GuildChatMessage.created_at)).limit(limit).all()
        
        return [
            {
                "id": str(message.id),
                "user_id": str(message.user_id),
                "message": message.message,
                "message_type": message.message_type,
                "created_at": message.created_at,
                "user_display_name": message.user.display_name if message.user else None,
                "user_avatar_url": message.user.avatar_url if message.user else None
            }
            for message in messages
        ]

    def update_guild_statistics(self, guild_id: str):
        """Update guild statistics based on member activities"""
        guild = self.db.query(Guild).filter(Guild.id == guild_id).first()
        if not guild:
            return
        
        # Calculate guild statistics
        members = self.db.query(GuildMember).filter(GuildMember.guild_id == guild_id).all()
        guild.total_members = len(members)
        
        if members:
            # Calculate average level
            total_level = sum(member.user.level for member in members if member.user)
            guild.average_level = total_level / len(members) if len(members) > 0 else 0
            
            # Calculate total score
            total_score = sum(member.user.experience for member in members if member.user)
            guild.total_score = total_score
            
            # Calculate guild level (simple formula)
            guild.guild_experience = total_score
            guild.guild_level = max(1, guild.guild_experience // 10000)

    def update_school_rankings(self, period: RankingPeriod = RankingPeriod.MONTHLY):
        """Update school rankings"""
        # Get all schools with guilds
        schools = self.db.query(Guild.school_name, Guild.school_city).distinct().all()
        
        for school_name, school_city in schools:
            # Calculate school statistics
            guilds = self.db.query(Guild).filter(
                and_(
                    Guild.school_name == school_name,
                    Guild.school_city == school_city
                )
            ).all()
            
            total_students = sum(guild.total_members for guild in guilds)
            total_score = sum(guild.total_score for guild in guilds)
            total_experience = sum(guild.guild_experience for guild in guilds)
            
            # Calculate battles won (simplified)
            battles_won = total_score // 100  # Simplified calculation
            
            # Update or create ranking
            ranking = self.db.query(SchoolRanking).filter(
                and_(
                    SchoolRanking.school_name == school_name,
                    SchoolRanking.school_city == school_city,
                    SchoolRanking.ranking_period == period
                )
            ).first()
            
            if not ranking:
                ranking = SchoolRanking(
                    school_name=school_name,
                    school_city=school_city,
                    ranking_period=period
                )
                self.db.add(ranking)
            
            ranking.total_students = total_students
            ranking.average_score = total_score // total_students if total_students > 0 else 0
            ranking.total_battles_won = battles_won
            ranking.total_experience = total_experience
        
        # Update rank positions
        rankings = self.db.query(SchoolRanking).filter(
            SchoolRanking.ranking_period == period
        ).order_by(desc(SchoolRanking.average_score)).all()
        
        for i, ranking in enumerate(rankings, 1):
            ranking.rank_position = i

    def get_guild_statistics(self, guild_id: str) -> Dict[str, Any]:
        """Get detailed guild statistics"""
        guild = self.db.query(Guild).filter(Guild.id == guild_id).first()
        if not guild:
            return {}
        
        # Calculate additional statistics
        members = self.db.query(GuildMember).filter(GuildMember.guild_id == guild_id).all()
        battles_won = sum(member.user.experience // 100 for member in members if member.user)
        battles_lost = sum(member.user.level // 10 for member in members if member.user)
        
        # Tournament statistics
        tournaments_participated = self.db.query(TournamentParticipant).filter(
            TournamentParticipant.guild_id == guild_id
        ).distinct(TournamentParticipant.tournament_id).count()
        
        tournaments_won = 0  # Simplified calculation
        
        return {
            "total_members": guild.total_members,
            "total_score": guild.total_score,
            "average_level": float(guild.average_level),
            "guild_level": guild.guild_level,
            "guild_experience": guild.guild_experience,
            "battles_won": battles_won,
            "battles_lost": battles_lost,
            "tournaments_participated": tournaments_participated,
            "tournaments_won": tournaments_won
        } 