from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, JSON, DECIMAL, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class Guild(Base):
    __tablename__ = "guilds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_name = Column(String(200), nullable=False)
    school_city = Column(String(100))
    guild_name = Column(String(100), nullable=False)
    description = Column(Text)
    avatar_url = Column(String(500))
    total_members = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    average_level = Column(DECIMAL(5, 2), default=0.0)
    guild_level = Column(Integer, default=1)
    guild_experience = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    #     members = # relationship("relationship("GuildMember",", cascade="all, delete-orphan")
    tournaments = relationship("TournamentParticipant", )
    #     chat_messages = # relationship("relationship("GuildChatMessage",", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Guild(id={self.id}, guild_name='{self.guild_name}', school_name='{self.school_name}')>"

class GuildMember(Base):
    __tablename__ = "guild_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id = Column(UUID(as_uuid=True), ForeignKey("guilds.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member")  # 'leader', 'officer', 'member'
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    contribution_score = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    guild = relationship("Guild", )
    user = relationship("User")
    
    def __repr__(self):
        return f"<GuildMember(id={self.id}, guild_id={self.guild_id}, user_id={self.user_id})>"

class Tournament(Base):
    __tablename__ = "tournaments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    tournament_type = Column(String(50), nullable=False)  # 'inter_school', 'regional', 'national'
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="upcoming")  # 'upcoming', 'active', 'completed', 'cancelled'
    max_participants = Column(Integer)
    current_participants = Column(Integer, default=0)
    prize_pool = Column(JSON, default={})
    rules = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    #     participants = # relationship("relationship("TournamentParticipant",", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tournament(id={self.id}, name='{self.name}', status='{self.status}')>"

class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"), nullable=False)
    guild_id = Column(UUID(as_uuid=True), ForeignKey("guilds.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    score = Column(Integer, default=0)
    rank_position = Column(Integer)
    battles_won = Column(Integer, default=0)
    battles_lost = Column(Integer, default=0)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tournament = relationship("Tournament", )
    guild = relationship("Guild")
    user = relationship("User")
    
    def __repr__(self):
        return f"<TournamentParticipant(id={self.id}, tournament_id={self.tournament_id}, user_id={self.user_id})>"

class GuildChatMessage(Base):
    __tablename__ = "guild_chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id = Column(UUID(as_uuid=True), ForeignKey("guilds.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # 'text', 'system', 'achievement'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    guild = relationship("Guild", )
    user = relationship("User")
    
    def __repr__(self):
        return f"<GuildChatMessage(id={self.id}, guild_id={self.guild_id}, user_id={self.user_id})>"

class SchoolRanking(Base):
    __tablename__ = "school_rankings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_name = Column(String(200), nullable=False)
    school_city = Column(String(100))
    total_students = Column(Integer, default=0)
    average_score = Column(Integer, default=0)
    total_battles_won = Column(Integer, default=0)
    total_experience = Column(Integer, default=0)
    ranking_period = Column(String(20), default="monthly")  # 'weekly', 'monthly', 'all_time'
    period_start = Column(Date)
    period_end = Column(Date)
    rank_position = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SchoolRanking(id={self.id}, school_name='{self.school_name}', rank_position={self.rank_position})>" 