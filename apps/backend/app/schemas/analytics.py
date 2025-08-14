from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class SubjectProgress(BaseModel):
    subject_id: str
    subject_name: str
    questions_answered: int
    correct_answers: int
    accuracy_percentage: float
    average_difficulty: float
    total_experience: int
    level_progress: float
    last_activity: datetime

class ICFESProjection(BaseModel):
    current_score: float
    projected_score: float
    improvement_rate: float
    target_score: float
    weeks_to_target: int
    confidence_level: float

class NationalComparison(BaseModel):
    user_percentile: float
    national_average: float
    user_score: float
    difference_from_average: float
    ranking_position: int
    total_students: int

class StrengthWeaknessHeatmap(BaseModel):
    subject: str
    topics: List[str]
    strength_scores: List[float]
    weakness_scores: List[float]
    overall_strength: float
    overall_weakness: float

class PersonalAnalytics(BaseModel):
    user_id: str
    username: str
    current_level: int
    current_rank: str
    total_experience: int
    
    # Progreso por materia
    subjects_progress: List[SubjectProgress]
    
    # Proyección ICFES
    icfes_projection: ICFESProjection
    
    # Comparación nacional
    national_comparison: NationalComparison
    
    # Heatmap de fortalezas/debilidades
    strength_weakness_heatmap: List[StrengthWeaknessHeatmap]
    
    # Métricas adicionales
    total_battles: int
    win_rate: float
    average_session_duration: int
    streak_days: int
    total_questions_answered: int
    overall_accuracy: float
    
    # Tendencias temporales
    weekly_progress: List[Dict[str, float]]
    monthly_trends: List[Dict[str, float]]
    
    generated_at: datetime


# New schemas for advanced analytics
class AnalyticsPeriod(str, Enum):
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class EventTrackRequest(BaseModel):
    event_type: str
    event_data: Dict[str, Any]
    session_id: Optional[str] = None
    platform: str = "web"


class BatchEventTrackRequest(BaseModel):
    events: List[EventTrackRequest]


class EventTrackItem(BaseModel):
    event_type: str
    event_data: Dict[str, Any]
    session_id: Optional[str] = None
    platform: str = "web"
    event_time: Optional[datetime] = None


class BattleStatsResponse(BaseModel):
    total_battles: int
    total_questions: int
    total_correct: int
    accuracy: float
    avg_duration: float
    total_experience: int
    total_orbs: int


class TopicPerformanceResponse(BaseModel):
    topic_id: str
    questions_count: int
    correct_count: int
    accuracy: float
    avg_response_time: float


class DailyActivityResponse(BaseModel):
    date: str
    battles_count: int
    accuracy: float


class ProgressionResponse(BaseModel):
    recorded_at: str
    level: int
    experience: int
    rank: str
    streak_days: int


class UserAnalyticsResponse(BaseModel):
    battle_stats: BattleStatsResponse
    topic_performance: List[TopicPerformanceResponse]
    daily_activity: List[DailyActivityResponse]
    progression: List[ProgressionResponse]


class GlobalStatsResponse(BaseModel):
    unique_users: int
    total_events: int
    total_sessions: int


class EventDistributionResponse(BaseModel):
    event_type: str
    count: int


class TopPlayerResponse(BaseModel):
    user_id: str
    total_experience: int
    battles_count: int
    accuracy: float


class PopularBattleResponse(BaseModel):
    battle_type: str
    count: int
    avg_questions: float
    avg_accuracy: float


class DailyMetricsResponse(BaseModel):
    date: str
    active_users: int
    total_battles: int
    total_questions: int
    correct_answers: int
    total_experience: int
    accuracy: float


class GlobalAnalyticsResponse(BaseModel):
    overall_stats: GlobalStatsResponse
    event_distribution: List[EventDistributionResponse]
    top_players: List[TopPlayerResponse]
    popular_battles: List[PopularBattleResponse]
    daily_metrics: List[DailyMetricsResponse] 