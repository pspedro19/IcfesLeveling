from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class ReassessmentType(str, Enum):
    INITIAL = "initial"
    MONTHLY = "monthly"
    ADAPTIVE = "adaptive"

class DiagnosticTestCreate(BaseModel):
    subject_id: str
    test_type: str = "real_icfes"
    reassessment_type: Optional[ReassessmentType] = None
    original_test_id: Optional[str] = None

class DiagnosticTestQuestion(BaseModel):
    id: str
    question_text: str
    options: List[str]
    subject: str
    topic: str
    difficulty: int
    hint: Optional[str] = None

class DiagnosticTestAnswer(BaseModel):
    question_id: str = Field(..., min_length=1)
    user_answer: str = Field(..., pattern='^[A-Ea-e]?$')  # Acepta minúsculas, mayúsculas y vacío
    response_time_ms: int = Field(..., ge=0, le=2147483647)
    
    @validator('user_answer')
    def uppercase_answer(cls, v):
        if not v:  # Si está vacío, mantenerlo vacío
            return ''
        return v.upper()  # Normalizar a mayúsculas
    
    class Config:
        extra = 'forbid'  # Rechazar campos extra como test_id

class DiagnosticTestSubmit(BaseModel):
    answers: List[DiagnosticTestAnswer]
    time_spent_seconds: Optional[int] = None  # Permitir este campo del frontend
    
    @validator('answers')
    def validate_answers(cls, v):
        if not v:
            raise ValueError('Debe enviar al menos una respuesta')
        if len(v) > 100:  # Límite de seguridad
            raise ValueError('Demasiadas respuestas (máximo 100)')
        return v
    
    class Config:
        extra = 'forbid'  # Rechaza otros campos extra

class DiagnosticTestAnalysis(BaseModel):
    subject: str
    score: int
    total_questions: int
    percentage: float
    time_spent_minutes: float
    strengths: List[str]
    weaknesses: List[str]
    score_by_topic: Dict[str, float]
    recommendations: List[str]
    comparison_with_initial: Optional[Dict[str, Any]] = None
    improvement_percentage: Optional[float] = None
    new_goals: Optional[List[str]] = None

class DiagnosticTestResponse(BaseModel):
    id: str
    user_id: str
    subject_id: str
    test_type: str
    reassessment_type: Optional[str] = None
    original_test_id: Optional[str] = None
    questions_answered: int
    correct_answers: int
    time_spent_seconds: int
    score_percentage: float
    strengths: List[str]
    weaknesses: List[str]
    score_by_topic: Dict[str, float]
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    is_monthly_reassessment: bool = False
    days_since_initial: Optional[int] = None
    comparison_with_initial: Optional[Dict[str, Any]] = None
    plan_regenerated: bool = False
    new_goals_generated: bool = False
    notification_sent: bool = False

class MonthlyReassessmentRequest(BaseModel):
    subject_id: str
    user_id: str

class ReassessmentComparison(BaseModel):
    initial_score: float
    current_score: float
    improvement_percentage: float
    days_since_initial: int
    topics_improved: List[str]
    topics_declined: List[str]
    overall_trend: str  # 'improving', 'declining', 'stable'

class ReassessmentNotification(BaseModel):
    user_id: str
    subject_name: str
    reassessment_id: str
    comparison_data: ReassessmentComparison
    new_goals: List[str]
    plan_updated: bool
    message: str

class DiagnosticResultResponse(BaseModel):
    score: int
    percentage: int
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]

class DiagnosticTestConfig(BaseModel):
    subject: str
    total_questions: int
    time_limit_minutes: int
    topics: List[str]

# Configuraciones por materia
DIAGNOSTIC_TEST_CONFIGS = {
    "matemáticas": {
        "total_questions": 45,
        "time_limit_minutes": 60,
        "topics": ["álgebra", "geometría", "trigonometría", "estadística"]
    },
    "lenguaje": {
        "total_questions": 45,
        "time_limit_minutes": 60,
        "topics": ["comprensión lectora", "gramática", "literatura", "comunicación"]
    },
    "ciencias naturales": {
        "total_questions": 45,
        "time_limit_minutes": 60,
        "topics": ["biología", "química", "física", "ciencias de la tierra"]
    },
    "ciencias sociales": {
        "total_questions": 45,
        "time_limit_minutes": 60,
        "topics": ["historia", "geografía", "política", "economía"]
    },
    "inglés": {
        "total_questions": 45,
        "time_limit_minutes": 60,
        "topics": ["gramática", "vocabulario", "comprensión lectora", "comprensión auditiva"]
    }
} 