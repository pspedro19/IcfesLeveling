"""
Dungeon Schemas for ICFES Leveling API

Pydantic schemas for Dungeon (Gate) endpoints.
Solo Leveling-inspired dungeon system with gates, encounters, and monsters.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ===== Gate Schemas =====

class GateEntryCosts(BaseModel):
    """Entry costs for a dungeon gate"""
    orbs: int = 0
    crystals: int = 0


class GateRewards(BaseModel):
    """Potential rewards from a dungeon gate"""
    experience: int = 0
    orbs: int = 0
    crystals: int = 0


class GateStats(BaseModel):
    """Statistics for a dungeon gate"""
    times_entered: int = 0
    times_completed: int = 0
    success_rate: float = 0.0
    avg_completion_time: Optional[int] = None


class GateResponse(BaseModel):
    """Response schema for a dungeon gate"""
    id: str
    name: str
    description: Optional[str] = None
    type: str  # regular, boss, raid, seasonal
    difficulty_rank: str  # E, D, C, B, A, S, SS, SSS
    recommended_level: int
    time_limit: Optional[int] = None  # in minutes
    entry_costs: GateEntryCosts
    rewards: GateRewards
    stats: GateStats
    is_raid: bool = False
    max_participants: int = 1
    is_seasonal: bool = False

    class Config:
        from_attributes = True


class AvailableGatesResponse(BaseModel):
    """Response for GET /dungeons/gates"""
    gates: List[GateResponse]
    total: int
    user_level: int
    user_rank: str


# ===== Enter Gate Schemas =====

class EnterGateRequest(BaseModel):
    """Request for POST /dungeons/{gate_id}/enter (optional body params)"""
    # Future use: party_id for raid gates
    party_id: Optional[str] = None


class EnemyInfo(BaseModel):
    """Enemy information in an encounter"""
    name: str
    level: int
    type: str
    health: int
    description: Optional[str] = None


class EncounterInfo(BaseModel):
    """Encounter information after entering a gate"""
    encounter_id: str
    room_number: int
    encounter_type: str  # monster, boss, treasure, event
    enemy: EnemyInfo
    questions_required: int = 3


class GateInfo(BaseModel):
    """Gate information for a dungeon run"""
    name: str
    total_rooms: int
    time_limit: Optional[int] = None  # in minutes


class EnterGateResponse(BaseModel):
    """Response for POST /dungeons/{gate_id}/enter"""
    success: bool
    message: str
    run_id: Optional[str] = None
    gate_info: Optional[GateInfo] = None
    current_encounter: Optional[EncounterInfo] = None


# ===== Encounter Questions Schemas =====

class DungeonQuestion(BaseModel):
    """Question schema for dungeon encounters"""
    id: str
    question_text: str
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    image_url: Optional[str] = None
    difficulty: int = 3


class EncounterQuestionsResponse(BaseModel):
    """Response for GET /dungeons/encounters/{encounter_id}/questions"""
    encounter_id: str
    questions: List[DungeonQuestion]
    total_questions: int
    time_limit_seconds: Optional[int] = None


# ===== Submit Answers Schemas =====

class SubmitEncounterAnswersRequest(BaseModel):
    """Request for POST /dungeons/encounters/{encounter_id}/submit"""
    answers: List[str] = Field(..., description="List of answers (A, B, C, or D) in order of questions")
    shadows_used: Optional[List[str]] = Field(default=None, description="List of shadow IDs used in battle")


class EncounterResults(BaseModel):
    """Results of an encounter battle"""
    accuracy: float
    correct_answers: int
    total_questions: int
    damage_dealt: int
    damage_taken: int
    experience_gained: int
    orbs_gained: int


class ShadowExtractionResult(BaseModel):
    """Result of attempting to extract a shadow from defeated monster"""
    success: bool
    shadow_name: Optional[str] = None
    shadow_level: Optional[int] = None
    shadow_type: Optional[str] = None
    message: str


class SubmitEncounterAnswersResponse(BaseModel):
    """Response for POST /dungeons/encounters/{encounter_id}/submit"""
    success: bool
    encounter_results: EncounterResults
    dungeon_status: str  # in_progress, completed, failed
    current_room: int
    shadow_extraction: Optional[ShadowExtractionResult] = None
    next_encounter: Optional[EncounterInfo] = None
    completion_stats: Optional[Dict[str, Any]] = None
    rewards: Optional[Dict[str, Any]] = None
    final_score: Optional[int] = None
    message: Optional[str] = None


# ===== Dungeon History Schemas =====

class DungeonRunRewards(BaseModel):
    """Rewards from a dungeon run"""
    experience: int = 0
    orbs: int = 0
    crystals: int = 0


class DungeonRunStats(BaseModel):
    """Stats from a dungeon run"""
    monsters_defeated: int = 0
    boss_defeated: bool = False
    accuracy: float = 0.0
    perfect_clear: bool = False
    speed_clear: bool = False


class DungeonRunHistory(BaseModel):
    """History entry for a dungeon run"""
    id: str
    gate_name: str
    status: str  # in_progress, completed, failed
    completion_time: Optional[int] = None  # in seconds
    score: int = 0
    rewards: DungeonRunRewards
    stats: DungeonRunStats
    date: datetime

    class Config:
        from_attributes = True


class DungeonHistoryResponse(BaseModel):
    """Response for GET /dungeons/history"""
    runs: List[DungeonRunHistory]
    total: int
    total_completed: int
    total_failed: int
    best_score: int = 0


# ===== Leaderboard Schemas =====

class DungeonLeaderboardEntry(BaseModel):
    """Single entry in the dungeon gate leaderboard"""
    rank: int
    user_id: str
    user_name: str
    score: int
    completion_time: int  # in seconds
    perfect_clear: bool = False
    speed_clear: bool = False
    date: Optional[datetime] = None

    class Config:
        from_attributes = True


class GateLeaderboardResponse(BaseModel):
    """Response for GET /dungeons/{gate_id}/leaderboard"""
    gate_id: str
    gate_name: str
    leaderboard: List[DungeonLeaderboardEntry]
    total_participants: int
    my_entry: Optional[DungeonLeaderboardEntry] = None
    my_best_score: Optional[int] = None
