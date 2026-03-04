from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class PracticeConfigRequest(BaseModel):
    session_type: str = Field(default="practice", description="practice, failed_questions, boss_battle")
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    difficulty: int = Field(default=5, ge=1, le=10)
    max_questions: int = Field(default=15, ge=5, le=30)


class LifelinesStatus(BaseModel):
    fifty_fifty: bool = True
    ask_ai: bool = True
    skip: bool = True


class PracticeSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    session_type: str
    status: str

    max_questions: int
    current_question_index: int
    questions_answered: int
    correct_answers: int
    current_streak: int

    lifelines: LifelinesStatus

    total_xp_earned: int
    total_gold_earned: int

    started_at: datetime

    class Config:
        from_attributes = True


class AnswerSubmitRequest(BaseModel):
    question_id: UUID
    selected_answer: str = Field(..., pattern="^[ABCD]$")
    response_time_ms: int = Field(..., ge=0)


class AnswerResultResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None

    xp_earned: int
    gold_earned: int

    current_streak: int
    session_progress: int  # Porcentaje completado

    next_question_available: bool
    session_complete: bool


class LifelineResultResponse(BaseModel):
    lifeline_type: str
    eliminated_options: Optional[List[str]] = None  # Para 50/50
    hint: Optional[str] = None  # Para ask_ai
    success: bool


class SessionResultsResponse(BaseModel):
    session_id: UUID

    # Estadísticas
    total_questions: int
    correct_answers: int
    wrong_answers: int
    skipped: int
    accuracy: float  # Porcentaje

    max_streak: int
    total_time_seconds: int
    avg_response_time_ms: float

    # Recompensas
    xp_earned: int
    gold_earned: int
    orbs_earned: int

    # Logros desbloqueados en esta sesión
    achievements_unlocked: List[str]

    # Mejoras de dominio por tema
    mastery_improvements: Dict[str, float]
