"""
Boss Raid Schemas for ICFES Leveling API

Pydantic schemas for Boss Raid endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ===== Boss Schemas =====

class BossBase(BaseModel):
    """Base schema for Boss"""
    name: str
    description: Optional[str] = None
    hp: int = 10000
    difficulty: str = "hard"


class BossResponse(BaseModel):
    """Response schema for Boss information"""
    id: UUID
    name: str
    description: Optional[str] = None
    subject_id: Optional[UUID] = None
    subject_name: Optional[str] = None
    hp: int
    current_hp: int
    difficulty: str
    is_defeated: bool = False
    defeated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Boss Raid Status Schemas =====

class BossRaidStatusResponse(BaseModel):
    """Response for GET /boss-raid/status"""
    is_active: bool
    starts_at: datetime
    ends_at: datetime
    current_boss: Optional[BossResponse] = None
    xp_multiplier: int = 3
    my_damage_dealt: int = 0
    my_rank: Optional[int] = None
    time_remaining_seconds: Optional[int] = None
    next_raid_at: Optional[datetime] = None


# ===== Boss Raid Session Schemas =====

class QuestionOption(BaseModel):
    """Question option for display"""
    id: str
    text: Optional[str] = None
    image_url: Optional[str] = None


class RaidQuestion(BaseModel):
    """Question schema for Boss Raid"""
    id: UUID
    text: Optional[str] = None
    image_url: Optional[str] = None
    options: List[QuestionOption]


class BossRaidStartResponse(BaseModel):
    """Response for POST /boss-raid/start"""
    session_id: UUID
    boss: BossResponse
    questions: List[RaidQuestion]
    total_questions: int = 20
    xp_multiplier: int = 3
    started_at: datetime


class BossRaidStartError(BaseModel):
    """Error response when raid is not active"""
    error: str = "RAID_NOT_ACTIVE"
    message: str = "El Boss Raid solo esta disponible Domingos 10 AM - 10 PM"
    next_raid_at: Optional[datetime] = None


# ===== Answer Submission Schemas =====

class SubmitAnswerRequest(BaseModel):
    """Request for POST /boss-raid/submit-answer"""
    session_id: UUID
    question_id: UUID
    answer_id: str
    time_spent_seconds: int = Field(ge=0, le=300)  # Max 5 minutes per question


class SubmitAnswerResponse(BaseModel):
    """Response for POST /boss-raid/submit-answer"""
    correct: bool
    correct_answer_id: str
    damage_dealt: int = 0
    boss_hp_remaining: int
    xp_earned: int
    combo_count: int
    questions_remaining: int
    session_damage_total: int
    boss_defeated: bool = False


# ===== Raid Completion Schemas =====

class CompleteRaidRequest(BaseModel):
    """Request for POST /boss-raid/complete"""
    session_id: UUID


class RaidReward(BaseModel):
    """Reward earned from completing the raid"""
    type: str  # xp, gold, badge
    amount: Optional[int] = None
    name: Optional[str] = None


class CompleteRaidResponse(BaseModel):
    """Response for POST /boss-raid/complete"""
    boss_defeated: bool
    total_damage: int
    total_xp: int
    correct_answers: int
    total_questions: int
    accuracy_percentage: float
    best_combo: int
    rank_in_raid: Optional[int] = None
    rewards: List[RaidReward]
    session_duration_seconds: int


# ===== Leaderboard Schemas =====

class LeaderboardEntry(BaseModel):
    """Single entry in the Boss Raid leaderboard"""
    user_id: UUID
    user_name: str
    avatar_url: Optional[str] = None
    total_damage: int
    total_xp: int
    rank: int
    is_me: bool = False


class BossRaidLeaderboardResponse(BaseModel):
    """Response for GET /boss-raid/leaderboard"""
    boss_id: UUID
    boss_name: str
    leaderboard: List[LeaderboardEntry]
    my_entry: Optional[LeaderboardEntry] = None
    total_participants: int


# ===== Session Status Schema =====

class SessionStatusResponse(BaseModel):
    """Response for checking current session status"""
    session_id: UUID
    boss_name: str
    status: str  # in_progress, completed, abandoned
    questions_answered: int
    total_questions: int
    correct_answers: int
    total_damage: int
    total_xp_earned: int
    current_combo: int
    max_combo: int
    time_elapsed_seconds: int
    started_at: datetime
    completed_at: Optional[datetime] = None
