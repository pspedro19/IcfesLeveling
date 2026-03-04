"""
Spaced Repetition (SM-2) Schemas - ICFES Leveling
Pydantic schemas for spaced repetition endpoints.

The SM-2 algorithm schedules reviews at optimal intervals for long-term retention.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


# ============================================
# ENUMS
# ============================================

class ReviewResult(str, Enum):
    """
    Possible results when reviewing a spaced repetition item.
    Based on SM-2 algorithm quality ratings.
    """
    AGAIN = "again"   # Failed, show again soon (quality 0-1)
    HARD = "hard"     # Difficult, shorter interval (quality 2)
    GOOD = "good"     # Normal, standard interval (quality 3)
    EASY = "easy"     # Easy, longer interval (quality 4-5)


class ItemStatus(str, Enum):
    """Status of a spaced repetition item"""
    NEW = "new"
    LEARNING = "learning"
    REVIEW = "review"
    GRADUATED = "graduated"
    SUSPENDED = "suspended"


# ============================================
# SPACED ITEM SCHEMAS
# ============================================

class SpacedItemBase(BaseModel):
    """Base schema for spaced repetition items"""
    item_id: str
    question_id: Optional[str] = None
    topic_id: Optional[str] = None
    content_type: str = "question"  # question, concept, formula


class SpacedItemResponse(BaseModel):
    """
    Response schema for a spaced repetition item.
    Contains SM-2 algorithm parameters and scheduling data.
    """
    item_id: str
    question_id: Optional[str] = None
    question_text: Optional[str] = None
    topic_name: Optional[str] = None
    content_type: str = "question"

    # SM-2 Algorithm parameters
    ease_factor: float = Field(default=2.5, ge=1.3, le=4.0, description="SM-2 ease factor")
    interval: int = Field(default=1, ge=0, description="Review interval in days")
    repetitions: int = Field(default=0, ge=0, description="Number of successful repetitions")
    due_date: datetime

    # Item status
    status: str = "new"

    # Additional metrics
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    total_reviews: int = Field(default=0, ge=0)
    average_response_time_ms: Optional[float] = None
    difficulty_rating: float = Field(default=0.5, ge=0.0, le=1.0)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "item_id": "concept-plan123-0",
                "question_id": "q-uuid-here",
                "question_text": "Cual es la derivada de x^2?",
                "topic_name": "Calculo Diferencial",
                "content_type": "question",
                "ease_factor": 2.5,
                "interval": 4,
                "repetitions": 3,
                "due_date": "2024-01-20T10:00:00Z",
                "status": "review",
                "success_rate": 0.85,
                "total_reviews": 7,
                "average_response_time_ms": 12500.0,
                "difficulty_rating": 0.6
            }
        }


# ============================================
# DAILY REVIEWS SCHEMAS
# ============================================

class DailyReviewsResponse(BaseModel):
    """
    Response for GET /spaced-repetition/daily-reviews
    Contains all items due for review today.
    """
    date: datetime
    user_id: Optional[str] = None
    total_due: int = Field(ge=0, description="Total items due for review")
    new_items: int = Field(ge=0, description="New items to learn")
    review_items: int = Field(ge=0, description="Items to review")
    learning_items: int = Field(ge=0, description="Items in learning phase")
    items: List[SpacedItemResponse]

    # Session information
    estimated_duration_minutes: Optional[int] = None
    difficulty_balance: Optional[Dict[str, Any]] = None
    retention_prediction: Optional[float] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "date": "2024-01-15T00:00:00Z",
                "user_id": "user-uuid-here",
                "total_due": 15,
                "new_items": 5,
                "review_items": 8,
                "learning_items": 2,
                "items": [],
                "estimated_duration_minutes": 25,
                "difficulty_balance": {"easy": 5, "medium": 7, "hard": 3},
                "retention_prediction": 0.87
            }
        }


# ============================================
# REVIEW SUBMISSION SCHEMAS
# ============================================

class SubmitReviewRequest(BaseModel):
    """
    Request for POST /spaced-repetition/review/{item_id}
    Submit the result of reviewing an item.
    """
    result: ReviewResult = Field(description="Review result (again, hard, good, easy)")
    response_time_ms: int = Field(ge=0, le=600000, description="Time to answer in milliseconds")
    additional_data: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "result": "good",
                "response_time_ms": 8500,
                "additional_data": {"confidence": "high"}
            }
        }


class SubmitReviewResponse(BaseModel):
    """
    Response for POST /spaced-repetition/review/{item_id}
    Contains updated scheduling information after review.
    """
    success: bool
    item_id: str
    result: str

    # Updated SM-2 parameters
    new_ease_factor: float = Field(ge=1.3, le=4.0)
    new_interval: int = Field(ge=0, description="New interval in days")
    next_review_date: datetime
    new_status: str

    # Rewards and progress
    xp_earned: int = Field(ge=0, default=0)
    streak_bonus: Optional[int] = None

    # Learning analytics
    retention_prediction: Optional[float] = None
    learning_progress: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "success": True,
                "item_id": "concept-plan123-0",
                "result": "good",
                "new_ease_factor": 2.6,
                "new_interval": 10,
                "next_review_date": "2024-01-25T10:00:00Z",
                "new_status": "review",
                "xp_earned": 15,
                "streak_bonus": 5,
                "retention_prediction": 0.92,
                "learning_progress": {"mastery_level": 0.75}
            }
        }


# ============================================
# SCHEDULE CREATION SCHEMAS
# ============================================

class CreateScheduleRequest(BaseModel):
    """
    Request for POST /spaced-repetition/schedule
    Create a spaced repetition schedule for a study plan.
    """
    plan_id: str = Field(description="Study plan ID to create schedule for")
    topics: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional list of topics to include. If not provided, extracted from plan."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "plan-uuid-here",
                "topics": [
                    {"topic_id": "t1", "name": "Algebra", "difficulty": 2},
                    {"topic_id": "t2", "name": "Geometria", "difficulty": 3}
                ]
            }
        }


class CreateScheduleResponse(BaseModel):
    """
    Response for POST /spaced-repetition/schedule
    Contains the created spaced repetition system.
    """
    success: bool
    system_id: str
    plan_id: str
    total_items: int

    # Performance estimates
    estimated_retention_rate: float = Field(ge=0.0, le=1.0)
    optimal_review_frequency: str

    # Algorithm settings
    algorithm_type: str = "Enhanced SM-2"
    ease_factor_range: List[float]
    learning_steps: List[int]

    # Initial schedule summary
    items_summary: Dict[str, int]
    first_review_date: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "success": True,
                "system_id": "spaced-user123-plan456",
                "plan_id": "plan456",
                "total_items": 50,
                "estimated_retention_rate": 0.85,
                "optimal_review_frequency": "daily",
                "algorithm_type": "Enhanced SM-2",
                "ease_factor_range": [1.3, 4.0],
                "learning_steps": [1, 10, 1440],
                "items_summary": {"concepts": 10, "questions": 40},
                "first_review_date": "2024-01-15T10:00:00Z"
            }
        }


# ============================================
# ANALYTICS SCHEMAS
# ============================================

class RetentionAnalyticsResponse(BaseModel):
    """
    Response for GET /spaced-repetition/analytics
    Comprehensive retention analytics for spaced repetition.
    """
    user_id: Optional[str] = None
    plan_id: Optional[str] = None
    analysis_period_days: int
    analysis_date: datetime

    # Core metrics
    overall_retention_rate: float = Field(ge=0.0, le=1.0)
    average_ease_factor: float = Field(ge=1.3, le=4.0)
    total_reviews: int = Field(ge=0)
    total_items: int = Field(ge=0)
    items_graduated: int = Field(ge=0)
    graduation_rate: float = Field(ge=0.0, le=1.0)

    # Distribution data
    status_distribution: Dict[str, int]
    difficulty_distribution: Optional[Dict[str, Any]] = None

    # Trend data
    retention_trend: Optional[List[Dict[str, Any]]] = None
    performance_trends: Optional[Dict[str, Any]] = None

    # Recommendations
    insights: Optional[List[str]] = None
    optimization_suggestions: Optional[List[str]] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": "user-uuid-here",
                "plan_id": "plan-uuid-here",
                "analysis_period_days": 30,
                "analysis_date": "2024-01-15T10:00:00Z",
                "overall_retention_rate": 0.87,
                "average_ease_factor": 2.45,
                "total_reviews": 450,
                "total_items": 50,
                "items_graduated": 35,
                "graduation_rate": 0.70,
                "status_distribution": {
                    "new": 5,
                    "learning": 10,
                    "review": 35,
                    "graduated": 35
                },
                "difficulty_distribution": {"easy": 15, "medium": 25, "hard": 10},
                "insights": [
                    "Tu tasa de retencion ha mejorado 12% este mes",
                    "Los temas de algebra muestran alto dominio"
                ],
                "optimization_suggestions": [
                    "Considera aumentar las sesiones de revision matutinas",
                    "Enfocate mas en temas de geometria"
                ]
            }
        }


# ============================================
# STATISTICS SCHEMAS
# ============================================

class SpacedRepetitionStatsResponse(BaseModel):
    """
    Response for GET /spaced-repetition/stats
    User's overall spaced repetition statistics.
    """
    user_id: str

    # Overall stats
    total_items: int = Field(ge=0)
    items_mastered: int = Field(ge=0)
    items_learning: int = Field(ge=0)
    items_new: int = Field(ge=0)

    # Review stats
    total_reviews_completed: int = Field(ge=0)
    reviews_today: int = Field(ge=0)
    reviews_due_today: int = Field(ge=0)
    reviews_due_tomorrow: int = Field(ge=0)

    # Streak and performance
    current_streak_days: int = Field(ge=0)
    longest_streak_days: int = Field(ge=0)
    average_accuracy: float = Field(ge=0.0, le=1.0)
    average_response_time_ms: Optional[float] = None

    # Time stats
    total_study_time_minutes: int = Field(ge=0)
    average_session_minutes: Optional[float] = None
    last_review_date: Optional[datetime] = None

    # XP and rewards
    total_xp_earned: int = Field(ge=0, default=0)
    xp_earned_today: int = Field(ge=0, default=0)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": "user-uuid-here",
                "total_items": 100,
                "items_mastered": 45,
                "items_learning": 35,
                "items_new": 20,
                "total_reviews_completed": 850,
                "reviews_today": 15,
                "reviews_due_today": 20,
                "reviews_due_tomorrow": 12,
                "current_streak_days": 14,
                "longest_streak_days": 30,
                "average_accuracy": 0.82,
                "average_response_time_ms": 9500.0,
                "total_study_time_minutes": 1200,
                "average_session_minutes": 25.5,
                "last_review_date": "2024-01-15T09:30:00Z",
                "total_xp_earned": 3500,
                "xp_earned_today": 75
            }
        }


# ============================================
# ERROR SCHEMAS
# ============================================

class SpacedRepetitionError(BaseModel):
    """Error response for spaced repetition endpoints"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "code": "ITEM_NOT_FOUND",
                "message": "El item de repaso espaciado no fue encontrado",
                "details": {"item_id": "invalid-id"}
            }
        }
