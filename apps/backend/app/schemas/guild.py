from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

class GuildRole(str, Enum):
    LEADER = "leader"
    OFFICER = "officer"
    MEMBER = "member"

class TournamentType(str, Enum):
    INTER_SCHOOL = "inter_school"
    REGIONAL = "regional"
    NATIONAL = "national"

class TournamentStatus(str, Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MessageType(str, Enum):
    TEXT = "text"
    SYSTEM = "system"
    ACHIEVEMENT = "achievement"

class RankingPeriod(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"

# Guild Schemas
class GuildBase(BaseModel):
    school_name: str
    school_city: Optional[str] = None
    guild_name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None

class GuildCreate(GuildBase):
    pass

class GuildResponse(GuildBase):
    id: str
    total_members: int
    total_score: int
    average_level: Decimal
    guild_level: int
    guild_experience: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Guild Member Schemas
class GuildMemberBase(BaseModel):
    guild_id: str
    user_id: str
    role: GuildRole = GuildRole.MEMBER

class GuildMemberCreate(GuildMemberBase):
    pass

class GuildMemberResponse(GuildMemberBase):
    id: str
    joined_at: datetime
    contribution_score: int
    last_activity: datetime
    user_display_name: Optional[str] = None
    user_level: Optional[int] = None
    user_avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

# Tournament Schemas
class TournamentBase(BaseModel):
    name: str
    description: Optional[str] = None
    tournament_type: TournamentType
    start_date: datetime
    end_date: datetime
    max_participants: Optional[int] = None
    prize_pool: Dict[str, Any] = {}
    rules: Dict[str, Any] = {}

class TournamentCreate(TournamentBase):
    pass

class TournamentResponse(TournamentBase):
    id: str
    status: TournamentStatus
    current_participants: int
    created_at: datetime

    class Config:
        from_attributes = True

# Tournament Participant Schemas
class TournamentParticipantBase(BaseModel):
    tournament_id: str
    guild_id: str
    user_id: str

class TournamentParticipantCreate(TournamentParticipantBase):
    pass

class TournamentParticipantResponse(TournamentParticipantBase):
    id: str
    score: int
    rank_position: Optional[int] = None
    battles_won: int
    battles_lost: int
    joined_at: datetime
    user_display_name: Optional[str] = None
    guild_name: Optional[str] = None

    class Config:
        from_attributes = True

# Guild Chat Schemas
class GuildChatMessageBase(BaseModel):
    guild_id: str
    user_id: str
    message: str
    message_type: MessageType = MessageType.TEXT

class GuildChatMessageCreate(GuildChatMessageBase):
    pass

class GuildChatMessageResponse(GuildChatMessageBase):
    id: str
    created_at: datetime
    user_display_name: Optional[str] = None
    user_avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

# School Ranking Schemas
class SchoolRankingBase(BaseModel):
    school_name: str
    school_city: Optional[str] = None
    ranking_period: RankingPeriod = RankingPeriod.MONTHLY
    period_start: Optional[date] = None
    period_end: Optional[date] = None

class SchoolRankingResponse(SchoolRankingBase):
    id: str
    total_students: int
    average_score: int
    total_battles_won: int
    total_experience: int
    rank_position: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# User School Info Schema
class UserSchoolInfo(BaseModel):
    school_name: Optional[str] = None
    school_city: Optional[str] = None
    school_type: Optional[str] = None

# Guild Search Schema
class GuildSearchRequest(BaseModel):
    school_name: Optional[str] = None
    school_city: Optional[str] = None
    guild_name: Optional[str] = None

# Tournament Search Schema
class TournamentSearchRequest(BaseModel):
    tournament_type: Optional[TournamentType] = None
    status: Optional[TournamentStatus] = None
    school_name: Optional[str] = None

# Guild Statistics Schema
class GuildStatistics(BaseModel):
    total_members: int
    total_score: int
    average_level: Decimal
    guild_level: int
    guild_experience: int
    battles_won: int
    battles_lost: int
    tournaments_participated: int
    tournaments_won: int

# School Statistics Schema
class SchoolStatistics(BaseModel):
    school_name: str
    school_city: Optional[str] = None
    total_students: int
    average_score: int
    total_battles_won: int
    total_experience: int
    rank_position: int
    guilds_count: int
    active_tournaments: int 