from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class AIExplanationRequest(BaseModel):
    question_id: str
    user_answer: str
    correct_answer: str
    question_text: str
    topic: Optional[str] = None

class AIExplanationResponse(BaseModel):
    explanation: str
    confidence_score: float
    additional_tips: Optional[List[str]] = None

class StudyPlanRequest(BaseModel):
    user_id: str
    weak_topics: List[str]
    target_date: Optional[datetime] = None
    hours_per_day: Optional[int] = 2

class StudyPlanResponse(BaseModel):
    plan_id: str
    daily_tasks: List[Dict[str, Any]]
    estimated_improvement: float
    recommendations: List[str]

# New schemas for AI tips
class BattleTipsRequest(BaseModel):
    battle_id: str
    current_topic: str
    difficulty: int
    battle_type: str = "normal"

class BattleTipsResponse(BaseModel):
    tips: List[str]
    generated: bool
    accuracy: Optional[float] = None
    weak_areas: Optional[List[str]] = None

class QuestionExplanationRequest(BaseModel):
    question_id: str
    user_answer: str
    is_correct: bool

class QuestionExplanationResponse(BaseModel):
    explanation: str
    correct_answer: str
    hint: Optional[str] = None
    generated: bool

class StudyTipsRequest(BaseModel):
    weak_areas: Optional[List[Dict[str, Any]]] = None
    time_available: Optional[int] = 60  # minutes per day
    target_score: Optional[int] = None

class StudyTipsResponse(BaseModel):
    objectives: List[str]
    strategies: List[str]
    daily_time: str
    resources: List[str]
    generated: bool

class LearningPatternResponse(BaseModel):
    pattern: str
    metrics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]

class MotivationalMessageRequest(BaseModel):
    context: str  # "level_up", "streak", "battle_won", "achievement"
    achievement_name: Optional[str] = None