"""
Schemas for Mobile Offline-First API
ICFES Leveling Mobile App
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime, date
from uuid import UUID
from enum import Enum


# ============================================
# ENUMS
# ============================================

class SessionType(str, Enum):
    PRACTICE = "practice"
    BATTLE = "battle"
    SIMULACRO = "simulacro"
    DAILY_CHALLENGE = "daily_challenge"


class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"


class HeartTransactionType(str, Enum):
    LOST = "lost"
    REGENERATED = "regenerated"
    PURCHASED = "purchased"
    REWARDED = "rewarded"
    PRACTICE_EARNED = "practice_earned"
    REFILLED = "refilled"


class LeagueStatus(str, Enum):
    PROMOTED = "promoted"
    RELEGATED = "relegated"
    STAYED = "stayed"


class Platform(str, Enum):
    IOS = "ios"
    ANDROID = "android"


# ============================================
# BASE RESPONSE
# ============================================

class APIResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    meta: Optional[dict] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class APIErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


# ============================================
# QUESTION SCHEMAS
# ============================================

class QuestionOption(BaseModel):
    id: str
    text: str
    image_url: Optional[str] = None


class QuestionResponse(BaseModel):
    id: UUID
    text: str
    image_url: Optional[str] = None
    topic_id: UUID
    topic_name: str
    subject_id: UUID
    subject_name: str
    difficulty: str
    options: List[QuestionOption]

    class Config:
        from_attributes = True


class QuestionBatchResponse(BaseModel):
    questions: List[QuestionResponse]
    total: int


class NextQuestionResponse(BaseModel):
    question: QuestionResponse
    cached_count: int


# ============================================
# ANSWER SCHEMAS
# ============================================

class AnswerSubmitRequest(BaseModel):
    question_id: UUID
    answer_id: str
    time_spent_seconds: int = Field(ge=0, le=3600)
    session_type: SessionType
    session_id: Optional[UUID] = None


class MasteryUpdate(BaseModel):
    topic_id: UUID
    old_score: float
    new_score: float


class StreakUpdate(BaseModel):
    current: int
    extended: bool
    daily_goal_met: bool


class AnswerSubmitResponse(BaseModel):
    correct: bool
    correct_answer_id: str
    explanation: Optional[str] = None
    xp_earned: int
    hearts_remaining: Optional[int] = None
    mastery_update: Optional[MasteryUpdate] = None
    streak_update: Optional[StreakUpdate] = None


# ============================================
# SYNC SCHEMAS
# ============================================

class SyncAction(BaseModel):
    """Represents an offline answer action to be synced.

    SECURITY NOTE: The was_correct field is provided by the client but
    is NEVER trusted. The server always validates the answer by comparing
    answer_id against the question's correct answer in the database.
    The was_correct field is kept for backwards compatibility and debugging
    but has no effect on XP or mastery calculations.
    """
    id: UUID
    question_id: UUID
    answer_id: str
    was_correct: bool  # IGNORED - server validates answer_id against database
    time_spent_seconds: int
    session_type: Optional[SessionType] = None
    client_timestamp: datetime


class SyncAnswersRequest(BaseModel):
    actions: List[SyncAction]


class SyncFailedItem(BaseModel):
    id: UUID
    error: str


class ServerState(BaseModel):
    xp: int
    level: int
    hearts: int
    streak: int
    last_activity_date: Optional[date] = None


class SyncAnswersResponse(BaseModel):
    synced_count: int
    failed: List[SyncFailedItem]
    server_state: ServerState


class SyncStateRequest(BaseModel):
    hearts: int
    streak: int
    last_activity_date: Optional[date] = None
    today_xp: int


class ConflictItem(BaseModel):
    field: str
    client_value: Any
    server_value: Any
    resolution: str  # 'client' or 'server'


class SyncStateResponse(BaseModel):
    server_state: ServerState
    conflicts: List[ConflictItem]


class SyncStatusResponse(BaseModel):
    pending_count: int
    last_sync: Optional[datetime] = None
    server_time: datetime


# ============================================
# HEARTS SCHEMAS
# ============================================

class HeartsStatusResponse(BaseModel):
    hearts: int
    max_hearts: int
    next_regen_at: Optional[datetime] = None
    unlimited_until: Optional[datetime] = None
    is_unlimited: bool


class HeartsUseRequest(BaseModel):
    reason: str = "wrong_answer"
    source_id: Optional[UUID] = None


class HeartsUseResponse(BaseModel):
    hearts_remaining: int
    next_regen_at: Optional[datetime] = None


class HeartsRefillRequest(BaseModel):
    method: str  # 'gems', 'ad', 'purchase'
    gems_spent: Optional[int] = None


class HeartsRefillResponse(BaseModel):
    hearts: int
    max_hearts: int
    gems_remaining: Optional[int] = None


# ============================================
# STREAK SCHEMAS
# ============================================

class StreakStatusResponse(BaseModel):
    """Enhanced streak status with timezone awareness and repair info"""
    current: int
    longest: int
    today_xp: int
    daily_goal: int
    goal_met: bool
    last_activity_date: Optional[date] = None
    freezes_available: int
    at_risk: bool
    # NEW: Timezone-aware fields
    day_resets_at: str = "04:00"  # 4 AM local time
    timezone: str = "America/Bogota"
    # NEW: XP multiplier based on streak length (1.0, 1.2, 1.5, 2.0)
    multiplier: float = 1.0
    # NEW: Streak repair fields
    can_repair: bool = False
    repair_window_ends_at: Optional[datetime] = None


class StreakExtendRequest(BaseModel):
    xp_earned: int
    activity_date: Optional[date] = None


class DailyGoalInfo(BaseModel):
    xp_earned: int
    target: int
    met: bool
    first_time_today: bool


class StreakBonusInfo(BaseModel):
    """Bonus rewards for streak milestones"""
    gold_earned: int
    badge_earned: Optional[str] = None


class StreakExtendResponse(BaseModel):
    streak: StreakUpdate
    daily_goal: DailyGoalInfo
    bonus: Optional[StreakBonusInfo] = None


class StreakRepairMethod(str, Enum):
    """Available streak repair methods"""
    GOLD = "gold"
    AD = "ad"


class StreakRepairRequest(BaseModel):
    """Request to repair a lost streak"""
    method: StreakRepairMethod  # "gold" costs 300, "ad" 1 per day


class StreakRepairResponse(BaseModel):
    """Response after repairing streak"""
    streak_repaired: bool
    current_streak: int
    gold_remaining: Optional[int] = None


class StreakFreezeMethod(str, Enum):
    """Available streak freeze methods"""
    GOLD = "gold"
    ITEM = "item"


class StreakFreezeRequest(BaseModel):
    """Request to use a streak freeze"""
    method: StreakFreezeMethod = StreakFreezeMethod.ITEM
    gold_cost: int = 200  # Cost if using gold method


class StreakFreezeResponse(BaseModel):
    freezes_remaining: int
    freeze_date: date
    gold_remaining: Optional[int] = None


# ============================================
# LEAGUE SCHEMAS
# ============================================

class LeagueZone(str, Enum):
    PROMOTION = "promotion"
    SAFE = "safe"
    RELEGATION = "relegation"


class DivisionInfo(BaseModel):
    id: UUID
    name: str
    tier: int
    color: str

    class Config:
        from_attributes = True


class LeagueCurrentResponse(BaseModel):
    division: DivisionInfo
    group_id: UUID
    rank: int
    zone: LeagueZone  # NEW: User's current zone
    weekly_xp: int
    week_ends_at: datetime
    promotion_threshold: int  # Top 10 (positions 1-10)
    relegation_threshold: int  # Bottom 5 starts at position 26 (30 - 5 + 1)
    participants: int  # Always 30 per group


class LeaderboardEntry(BaseModel):
    user_id: UUID
    name: str
    avatar_url: Optional[str] = None
    xp: int
    rank: int
    zone: LeagueZone  # NEW: Zone for each participant
    is_me: bool = False


class LeaderboardResponse(BaseModel):
    leaderboard: List[LeaderboardEntry]
    my_rank: int
    my_xp: int
    my_zone: LeagueZone  # NEW: Current user's zone
    total_participants: int


class LeagueJoinResponse(BaseModel):
    group_id: UUID
    division: DivisionInfo
    position: int
    week_ends_at: datetime


class LeagueHistoryEntry(BaseModel):
    week_id: UUID
    week_start: date
    week_end: date
    division_name: str
    final_rank: int
    final_xp: int
    status: LeagueStatus
    gems_earned: int


class LeagueHistoryResponse(BaseModel):
    weeks: List[LeagueHistoryEntry]


# ============================================
# MASTERY SCHEMAS
# ============================================

class TopicMasteryInfo(BaseModel):
    id: UUID
    name: str
    subject_id: UUID
    subject_name: str
    mastery_score: float
    questions_seen: int
    questions_correct: int
    last_practiced_at: Optional[datetime] = None
    status: str  # 'new', 'learning', 'practiced', 'mastered'


class MasteryTopicsResponse(BaseModel):
    topics: List[TopicMasteryInfo]


class WeakAreaInfo(BaseModel):
    topic_id: UUID
    topic_name: str
    subject_id: UUID
    subject_name: str
    mastery_score: float
    priority: str  # 'high', 'medium', 'low'
    suggested_practice: int


class WeakAreasResponse(BaseModel):
    weak_areas: List[WeakAreaInfo]


# ============================================
# NOTIFICATION SCHEMAS
# ============================================

class DeviceInfo(BaseModel):
    model: Optional[str] = None
    os_version: Optional[str] = None


class NotificationRegisterRequest(BaseModel):
    token: str
    platform: Platform
    device_info: Optional[DeviceInfo] = None


class NotificationRegisterResponse(BaseModel):
    registered: bool


class NotificationPreferences(BaseModel):
    streak_reminder: bool = True
    streak_at_risk: bool = True
    daily_goal_reminder: bool = True
    league_updates: bool = True
    new_content: bool = True
    quiet_hours_start: Optional[str] = None  # "HH:MM"
    quiet_hours_end: Optional[str] = None  # "HH:MM"


class NotificationPreferencesResponse(BaseModel):
    preferences: NotificationPreferences


# ============================================
# DAILY CHALLENGE SCHEMAS
# ============================================

class DailyChallengeInfo(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    challenge_type: str
    target_value: int
    current_progress: int
    is_completed: bool
    xp_reward: int
    gem_reward: int
    bonus_hearts: int
    rewards_claimed: bool


class DailyChallengesResponse(BaseModel):
    challenges: List[DailyChallengeInfo]


class DailyChallengeClaimResponse(BaseModel):
    success: bool
    xp_earned: int
    gems_earned: int
    hearts_earned: int


# ============================================
# USER MOBILE PROFILE
# ============================================

class UserMobileProfile(BaseModel):
    id: UUID
    email: str
    name: str
    level: int
    xp: int
    rank: str
    hearts: int
    max_hearts: int
    current_streak: int
    longest_streak: int
    daily_goal_xp: int
    today_xp: int

    class Config:
        from_attributes = True
