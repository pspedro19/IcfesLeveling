from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class TopicRecommendation(BaseModel):
    topic: str
    reason: str
    priority: str  # high, medium, low
    suggested_questions: int
    estimated_time: str

class DifficultyRange(BaseModel):
    min: int
    max: int

class DifficultyRecommendation(BaseModel):
    current_optimal: int
    suggested_range: DifficultyRange
    progression_strategy: str
    description: str
    challenge_mode: bool = False

class TimeSlot(BaseModel):
    time: str
    period: str
    effectiveness: str

class StudyScheduleRecommendation(BaseModel):
    recommended_duration: str
    optimal_time_slots: List[TimeSlot]
    frequency: str
    rest_days: List[str] = []
    focus_distribution: Dict[str, int]
    note: Optional[str] = None

class BattleStrategyRecommendation(BaseModel):
    name: str
    description: str
    tips: List[str]
    expected_improvement: Optional[str] = None

class LearningResource(BaseModel):
    topic: str
    resource_type: str
    recommendation: Dict[str, str]
    estimated_time: str
    priority: str

class Goal(BaseModel):
    goal: str
    current: Optional[str] = None
    target: Optional[str] = None
    actions: List[str]
    deadline: str

class GoalsRecommendation(BaseModel):
    short_term: List[Goal] = []
    medium_term: List[Goal] = []
    long_term: List[Goal] = []

class RecommendationResponse(BaseModel):
    next_topics: List[TopicRecommendation]
    difficulty_adjustment: DifficultyRecommendation
    study_schedule: StudyScheduleRecommendation
    battle_strategies: List[BattleStrategyRecommendation]
    learning_resources: List[LearningResource]
    goals: GoalsRecommendation
    generated_at: str
    confidence_score: float

class PerformanceAnalysis(BaseModel):
    strengths: List[Dict[str, Any]]
    weaknesses: List[Dict[str, Any]]
    optimal_difficulty: int
    learning_velocity: float
    consistency_score: float
    peak_performance_hours: List[int]
    improvement_areas: List[Dict[str, Any]]