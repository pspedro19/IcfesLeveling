from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class QuizCreate(BaseModel):
    plan_id: str = Field(..., description="ID del plan de estudio")
    unit_number: int = Field(..., ge=1, description="Número de unidad")
    quiz_name: str = Field(..., description="Nombre del quiz")
    total_questions: int = Field(10, ge=5, le=20, description="Número total de preguntas")
    passing_score: float = Field(80.0, ge=50.0, le=100.0, description="Puntaje mínimo para aprobar")
    time_limit_minutes: int = Field(15, ge=5, le=60, description="Límite de tiempo en minutos")

class QuizAnswerCreate(BaseModel):
    question_id: str = Field(..., description="ID de la pregunta")
    user_answer: str = Field(..., description="Respuesta del usuario")
    response_time_ms: int = Field(..., ge=0, description="Tiempo de respuesta en milisegundos")

class QuizAnswerResponse(BaseModel):
    id: str
    quiz_id: str
    question_id: str
    user_answer: str
    is_correct: bool
    response_time_ms: int
    ai_explanation: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class QuizResponse(BaseModel):
    id: str
    user_id: str
    plan_id: str
    unit_number: int
    quiz_name: str
    total_questions: int
    passing_score: float
    time_limit_minutes: int
    status: str
    score: float
    correct_answers: int
    time_taken_seconds: int
    ai_feedback: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuizQuestionResponse(BaseModel):
    id: str
    question_text: str
    question_type: str
    difficulty: int
    correct_answer: str
    options: Dict[str, str]
    explanation: Optional[str] = None
    hint: Optional[str] = None
    tags: Optional[List[str]] = None

    class Config:
        from_attributes = True

class QuizGenerationRequest(BaseModel):
    plan_id: str = Field(..., description="ID del plan de estudio")
    unit_number: int = Field(..., ge=1, description="Número de unidad")
    user_level: Optional[int] = Field(None, description="Nivel del usuario para adaptar dificultad")

class QuizGenerationResponse(BaseModel):
    quiz_id: str
    unit_id: str
    questions: List[QuizQuestionResponse]
    passing_score: float = 80.0
    time_limit_minutes: int = 15
    rewards: Dict[str, Any] = Field(default_factory=dict)

class QuizFeedback(BaseModel):
    quiz_id: str
    overall_score: float
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    ai_analysis: Dict[str, Any]

class QuizProgressUpdate(BaseModel):
    quiz_id: str
    current_question: int
    total_questions: int
    correct_answers: int
    time_remaining_seconds: int
    score_percentage: float 