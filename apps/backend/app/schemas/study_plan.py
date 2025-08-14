from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Esquemas para unidades de estudio
class StudyTopic(BaseModel):
    name: str
    difficulty: int = Field(..., ge=1, le=5)
    questions: int
    tags: Optional[List[str]] = []

class UnitRecommendations(BaseModel):
    priority: str = Field(..., pattern="^(high|medium|low)$")
    weak_areas: Optional[List[str]] = []
    focus_topics: Optional[List[str]] = []
    study_time: str

class StudyUnit(BaseModel):
    unit_number: int
    name: str
    description: str
    topics: List[StudyTopic]
    recommendations: UnitRecommendations
    unlocked: bool
    progress: float = Field(..., ge=0, le=100)
    ai_recommended: bool = False

# Esquemas para recomendaciones personalizadas
class PersonalizedRecommendations(BaseModel):
    overall_accuracy: float
    weak_topics: List[Dict[str, Any]]
    strong_topics: List[Dict[str, Any]]
    suggested_focus: List[str]
    study_schedule: Dict[str, Any]
    estimated_improvement: Dict[str, Any]

# Esquemas para progreso detallado
class UnitProgressDetail(BaseModel):
    unit_number: int
    unit_name: str
    is_completed: bool
    score: float
    progress_percentage: float
    weighted_progress: Dict[str, Any]

class ProgressDetails(BaseModel):
    overall_progress: float
    completed_units: int
    unit_details: List[UnitProgressDetail]

# Esquemas principales
class StudyPlanCreate(BaseModel):
    subject_id: str
    plan_name: str
    plan_data: Dict[str, Any]

class StudyPlanResponse(BaseModel):
    id: str
    user_id: str
    subject_id: str
    plan_name: str
    plan_data: Dict[str, Any]
    total_units: int
    completed_units: int
    progress_percentage: float
    is_active: bool
    generated_at: datetime
    updated_at: datetime

class StudyPlanDetail(BaseModel):
    id: str
    plan_name: str
    subject: str
    title: str
    description: str
    units: List[StudyUnit]
    total_units: int
    completed_units: int
    progress_percentage: float
    estimated_time: str
    difficulty_curve: str
    icfes_weight: float
    exam_sections: List[str]
    personalized_recommendations: Optional[PersonalizedRecommendations] = None
    progress_details: ProgressDetails
    last_updated: Optional[str] = None

class StudyPlanList(BaseModel):
    plans: List[StudyPlanDetail]
    total_plans: int
    active_plans: int

class UnitProgressUpdate(BaseModel):
    videos_completed: Optional[int] = 0
    exercises_completed: Optional[int] = 0
    readings_completed: Optional[int] = 0
    score: Optional[float] = Field(None, ge=0, le=100)

class StudyRecommendations(BaseModel):
    subject_id: str
    user_level: int
    performance_analysis: Dict[str, Any]
    suggested_focus: List[str]
    study_schedule: Dict[str, Any]
    improvement_estimate: Dict[str, Any]
    next_steps: List[str]

class AvailableSubject(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    color: Optional[str] = None
    has_active_plan: bool
    icfes_weight: float

class AvailableSubjectsResponse(BaseModel):
    subjects: List[AvailableSubject]
    total_subjects: int
    subjects_with_plans: int

# Esquemas para estadísticas y análisis
class PlanStatistics(BaseModel):
    plan_id: str
    total_units: int
    completed_units: int
    overall_progress: float
    average_score: float
    time_spent_hours: float
    weak_areas: List[str]
    strong_areas: List[str]
    estimated_completion_days: int

class StudyPlanDashboard(BaseModel):
    total_plans: int
    active_plans: int
    completed_plans: int
    overall_progress: float
    recent_activity: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    upcoming_deadlines: List[Dict[str, Any]] 