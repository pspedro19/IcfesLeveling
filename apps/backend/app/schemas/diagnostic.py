"""
Two-Phase Diagnostic Schemas
ICFES Leveling Backend

Based on API_CONTRACT.md specifications for:
- POST /diagnostic/quick/start
- POST /diagnostic/quick/submit
- POST /diagnostic/deep/start/{subject_id}
- POST /diagnostic/deep/submit
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


# =============================================================================
# ENUMS
# =============================================================================

class DiagnosticTypeEnum(str, Enum):
    QUICK = "quick"
    DEEP = "deep"


class WeakAreaPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SkillStatus(str, Enum):
    WEAK = "weak"
    LEARNING = "learning"
    STRONG = "strong"


class Rank(str, Enum):
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"


# =============================================================================
# SHARED SCHEMAS
# =============================================================================

class DiagnosticAnswerInput(BaseModel):
    """Input schema for a single diagnostic answer"""
    question_id: UUID = Field(..., description="UUID of the question")
    answer_id: str = Field(..., min_length=1, max_length=10, description="Answer ID (A, B, C, D, or E)")
    time_spent_seconds: int = Field(..., ge=0, le=3600, description="Time spent in seconds (max 1 hour)")

    @validator('answer_id')
    def uppercase_answer(cls, v):
        """Normalize answer to uppercase"""
        return v.upper() if v else v

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "123e4567-e89b-12d3-a456-426614174000",
                "answer_id": "B",
                "time_spent_seconds": 45
            }
        }


class QuestionOption(BaseModel):
    """Schema for question option"""
    id: str = Field(..., description="Option ID (A, B, C, D)")
    text: str = Field(..., description="Option text")
    image_url: Optional[str] = Field(None, description="Optional image URL for option")


class DiagnosticQuestion(BaseModel):
    """Schema for a diagnostic question"""
    id: UUID = Field(..., description="Question UUID")
    text: str = Field(..., description="Question text")
    image_url: Optional[str] = Field(None, description="Optional image URL")
    subject_id: UUID = Field(..., description="Subject UUID")
    subject_name: str = Field(..., description="Subject name")
    options: List[QuestionOption] = Field(..., description="Answer options")
    topic_id: Optional[UUID] = Field(None, description="Topic UUID (for deep diagnostic)")
    topic_name: Optional[str] = Field(None, description="Topic name (for deep diagnostic)")
    difficulty: Optional[str] = Field(None, description="Difficulty level: easy, medium, hard")

    class Config:
        from_attributes = True


# =============================================================================
# QUICK DIAGNOSTIC SCHEMAS
# =============================================================================

class QuickDiagnosticStartResponse(BaseModel):
    """Response schema for POST /diagnostic/quick/start"""
    diagnostic_id: UUID = Field(..., description="Diagnostic test UUID")
    questions: List[DiagnosticQuestion] = Field(..., description="15 questions (3 per subject)")
    total: int = Field(default=15, description="Total number of questions")
    time_limit_minutes: int = Field(default=10, description="Time limit in minutes")

    class Config:
        json_schema_extra = {
            "example": {
                "diagnostic_id": "123e4567-e89b-12d3-a456-426614174000",
                "total": 15,
                "time_limit_minutes": 10,
                "questions": []
            }
        }


class WeakArea(BaseModel):
    """Schema for a weak area identified in diagnostic"""
    subject_id: UUID = Field(..., description="Subject UUID")
    subject_name: str = Field(..., description="Subject name")
    score: float = Field(..., ge=0.0, le=1.0, description="Score from 0.0 to 1.0")
    priority: WeakAreaPriority = Field(..., description="Priority level: high, medium, low")

    class Config:
        json_schema_extra = {
            "example": {
                "subject_id": "123e4567-e89b-12d3-a456-426614174000",
                "subject_name": "Matematicas",
                "score": 0.33,
                "priority": "high"
            }
        }


class QuickDiagnosticSubmitRequest(BaseModel):
    """Request schema for POST /diagnostic/quick/submit"""
    diagnostic_id: UUID = Field(..., description="Diagnostic test UUID")
    answers: List[DiagnosticAnswerInput] = Field(..., min_length=1, max_length=20)

    @validator('answers')
    def validate_answers_count(cls, v):
        if len(v) > 20:
            raise ValueError('Too many answers (max 20)')
        return v


class QuickDiagnosticSubmitResponse(BaseModel):
    """Response schema for POST /diagnostic/quick/submit"""
    completed: bool = Field(default=True, description="Diagnostic completed flag")
    correct: int = Field(..., ge=0, description="Number of correct answers")
    total: int = Field(default=15, description="Total questions")
    rank: Rank = Field(..., description="Assigned rank: E, D, C, B, A, S")
    theta: float = Field(..., ge=-3.0, le=3.0, description="IRT theta estimate")
    weak_areas: List[WeakArea] = Field(..., description="List of weak areas by subject")

    class Config:
        json_schema_extra = {
            "example": {
                "completed": True,
                "correct": 9,
                "total": 15,
                "rank": "C",
                "theta": 0.5,
                "weak_areas": [
                    {
                        "subject_id": "123e4567-e89b-12d3-a456-426614174000",
                        "subject_name": "Matematicas",
                        "score": 0.33,
                        "priority": "high"
                    }
                ]
            }
        }


# =============================================================================
# DEEP DIAGNOSTIC SCHEMAS
# =============================================================================

class DeepDiagnosticStartResponse(BaseModel):
    """Response schema for POST /diagnostic/deep/start/{subject_id}"""
    diagnostic_id: UUID = Field(..., description="Diagnostic test UUID")
    subject_id: UUID = Field(..., description="Subject UUID")
    subject_name: str = Field(..., description="Subject name")
    questions: List[DiagnosticQuestion] = Field(..., description="15-20 questions for the subject")
    total: int = Field(..., ge=15, le=20, description="Total number of questions")

    class Config:
        json_schema_extra = {
            "example": {
                "diagnostic_id": "123e4567-e89b-12d3-a456-426614174000",
                "subject_id": "123e4567-e89b-12d3-a456-426614174001",
                "subject_name": "Matematicas",
                "total": 20,
                "questions": []
            }
        }


class SkillTreeItem(BaseModel):
    """Schema for a skill tree item (topic mastery)"""
    topic_id: UUID = Field(..., description="Topic UUID")
    topic_name: str = Field(..., description="Topic name")
    mastery_score: float = Field(..., ge=0.0, le=1.0, description="Mastery score from 0.0 to 1.0")
    status: SkillStatus = Field(..., description="Status: weak, learning, strong")
    questions_to_unlock: int = Field(..., ge=0, description="Questions needed to unlock next level")

    class Config:
        json_schema_extra = {
            "example": {
                "topic_id": "123e4567-e89b-12d3-a456-426614174000",
                "topic_name": "Algebra",
                "mastery_score": 0.45,
                "status": "learning",
                "questions_to_unlock": 3
            }
        }


class DeepDiagnosticSubmitRequest(BaseModel):
    """Request schema for POST /diagnostic/deep/submit"""
    diagnostic_id: UUID = Field(..., description="Diagnostic test UUID")
    answers: List[DiagnosticAnswerInput] = Field(..., min_length=1, max_length=25)

    @validator('answers')
    def validate_answers_count(cls, v):
        if len(v) > 25:
            raise ValueError('Too many answers (max 25)')
        return v


class DeepDiagnosticSubmitResponse(BaseModel):
    """Response schema for POST /diagnostic/deep/submit"""
    completed: bool = Field(default=True, description="Diagnostic completed flag")
    subject_id: UUID = Field(..., description="Subject UUID")
    correct: int = Field(..., ge=0, description="Number of correct answers")
    total: int = Field(..., description="Total questions")
    skill_tree: List[SkillTreeItem] = Field(..., description="Skill tree with topic mastery")

    class Config:
        json_schema_extra = {
            "example": {
                "completed": True,
                "subject_id": "123e4567-e89b-12d3-a456-426614174000",
                "correct": 12,
                "total": 20,
                "skill_tree": [
                    {
                        "topic_id": "123e4567-e89b-12d3-a456-426614174001",
                        "topic_name": "Algebra",
                        "mastery_score": 0.75,
                        "status": "strong",
                        "questions_to_unlock": 0
                    }
                ]
            }
        }


# =============================================================================
# ERROR SCHEMAS
# =============================================================================

class DiagnosticErrorResponse(BaseModel):
    """Error response schema for diagnostic endpoints"""
    success: bool = Field(default=False)
    error: Dict[str, Any] = Field(..., description="Error details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "DIAGNOSTIC_COMPLETED",
                    "message": "Quick diagnostic already completed"
                }
            }
        }


# =============================================================================
# DIAGNOSTIC STATUS SCHEMAS
# =============================================================================

class DiagnosticStatusResponse(BaseModel):
    """Response schema for diagnostic status check"""
    quick_completed: bool = Field(..., description="Whether quick diagnostic is completed")
    deep_completed: Dict[str, bool] = Field(..., description="Deep diagnostic completion by subject")
    current_rank: Optional[Rank] = Field(None, description="Current user rank")
    theta: Optional[float] = Field(None, description="Current theta estimate")

    class Config:
        json_schema_extra = {
            "example": {
                "quick_completed": True,
                "deep_completed": {
                    "matematicas": True,
                    "lenguaje": False,
                    "ciencias_naturales": False,
                    "ciencias_sociales": False,
                    "ingles": False
                },
                "current_rank": "C",
                "theta": 0.5
            }
        }


# =============================================================================
# IRT ADAPTIVE TESTING SCHEMAS
# =============================================================================

class ThetaProgressionItem(BaseModel):
    """Schema for a single item in theta progression"""
    item_number: int = Field(..., description="Item number in sequence")
    question_id: str = Field(..., description="Question UUID as string")
    is_correct: bool = Field(..., description="Whether the response was correct")
    theta_estimate: float = Field(..., description="Theta estimate after this response")
    standard_error: float = Field(..., description="Standard error after this response")
    difficulty_b: Optional[float] = Field(None, description="Question difficulty parameter (b)")


class SubjectAbility(BaseModel):
    """Schema for subject-specific ability estimate"""
    theta: float = Field(..., description="Theta estimate for this subject")
    standard_error: float = Field(..., description="Standard error of estimate")
    converged: bool = Field(..., description="Whether MLE converged")
    response_count: int = Field(..., description="Number of responses for this subject")
    subject_name: str = Field(..., description="Subject name")
    rank: str = Field(..., description="Rank based on subject theta")


class IRTMetrics(BaseModel):
    """Schema for comprehensive IRT metrics"""
    theta_estimate: float = Field(..., ge=-5.0, le=5.0, description="Final theta estimate")
    standard_error: float = Field(..., ge=0.0, description="Standard error of theta estimate")
    confidence_interval_95: List[float] = Field(..., description="95% confidence interval [lower, upper]")
    percentile: int = Field(..., ge=1, le=99, description="Percentile rank (1-99)")
    theta_progression: List[ThetaProgressionItem] = Field(..., description="Theta estimates after each response")
    subject_abilities: Dict[str, SubjectAbility] = Field(..., description="Subject-specific ability estimates")

    class Config:
        json_schema_extra = {
            "example": {
                "theta_estimate": 0.5,
                "standard_error": 0.35,
                "confidence_interval_95": [-0.19, 1.19],
                "percentile": 69,
                "theta_progression": [
                    {
                        "item_number": 1,
                        "question_id": "123e4567-e89b-12d3-a456-426614174000",
                        "is_correct": True,
                        "theta_estimate": 0.3,
                        "standard_error": 0.8,
                        "difficulty_b": 0.0
                    }
                ],
                "subject_abilities": {
                    "123e4567-e89b-12d3-a456-426614174001": {
                        "theta": 0.5,
                        "standard_error": 0.4,
                        "converged": True,
                        "response_count": 3,
                        "subject_name": "Matematicas",
                        "rank": "C"
                    }
                }
            }
        }


class QuickDiagnosticSubmitResponseIRT(BaseModel):
    """Enhanced response schema with IRT metrics for POST /diagnostic/quick/submit"""
    completed: bool = Field(default=True, description="Diagnostic completed flag")
    correct: int = Field(..., ge=0, description="Number of correct answers")
    total: int = Field(default=15, description="Total questions")
    rank: Rank = Field(..., description="Assigned rank: E, D, C, B, A, S")
    theta: float = Field(..., ge=-5.0, le=5.0, description="IRT theta estimate")
    weak_areas: List[WeakArea] = Field(..., description="List of weak areas by subject")
    irt_metrics: IRTMetrics = Field(..., description="Comprehensive IRT analysis metrics")

    class Config:
        json_schema_extra = {
            "example": {
                "completed": True,
                "correct": 9,
                "total": 15,
                "rank": "C",
                "theta": 0.5,
                "weak_areas": [],
                "irt_metrics": {
                    "theta_estimate": 0.5,
                    "standard_error": 0.35,
                    "confidence_interval_95": [-0.19, 1.19],
                    "percentile": 69,
                    "theta_progression": [],
                    "subject_abilities": {}
                }
            }
        }


class AdaptiveNextQuestionRequest(BaseModel):
    """Request schema for adaptive question selection"""
    current_theta: float = Field(
        default=0.0,
        ge=-5.0, le=5.0,
        description="Current ability estimate (theta)"
    )
    answered_question_ids: List[str] = Field(
        default=[],
        description="List of already answered question UUIDs"
    )
    subject_id: Optional[str] = Field(
        None,
        description="Optional subject UUID to filter questions"
    )
    topic_id: Optional[str] = Field(
        None,
        description="Optional topic UUID for deep diagnostic"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "current_theta": 0.5,
                "answered_question_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "123e4567-e89b-12d3-a456-426614174001"
                ],
                "subject_id": "123e4567-e89b-12d3-a456-426614174002"
            }
        }


class AdaptiveNextQuestionResponse(BaseModel):
    """Response schema for adaptive question selection"""
    question: DiagnosticQuestion = Field(..., description="Next optimal question")
    information_value: float = Field(
        ..., ge=0.0,
        description="Fisher information value at current theta"
    )
    expected_probability: float = Field(
        ..., ge=0.0, le=1.0,
        description="Expected probability of correct response"
    )
    remaining_questions: int = Field(
        ..., ge=0,
        description="Number of remaining questions in pool"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "text": "Question text here",
                    "subject_id": "123e4567-e89b-12d3-a456-426614174001",
                    "subject_name": "Matematicas",
                    "options": [],
                    "difficulty": "medium"
                },
                "information_value": 0.85,
                "expected_probability": 0.65,
                "remaining_questions": 45
            }
        }


class AdaptiveAnswerRequest(BaseModel):
    """Request schema for submitting an answer in adaptive testing"""
    question_id: UUID = Field(..., description="Question UUID")
    answer_id: str = Field(..., min_length=1, max_length=10, description="Answer ID (A, B, C, D)")
    time_spent_seconds: int = Field(..., ge=0, le=3600, description="Time spent on question")
    current_theta: float = Field(
        default=0.0, ge=-5.0, le=5.0,
        description="Current theta before this answer"
    )
    current_se: float = Field(
        default=1.0, ge=0.0,
        description="Current standard error before this answer"
    )

    @validator('answer_id')
    def uppercase_answer(cls, v):
        return v.upper() if v else v


class AdaptiveAnswerResponse(BaseModel):
    """Response schema for an answer in adaptive testing"""
    is_correct: bool = Field(..., description="Whether the answer was correct")
    correct_answer: str = Field(..., description="The correct answer")
    new_theta: float = Field(..., ge=-5.0, le=5.0, description="Updated theta estimate")
    new_se: float = Field(..., ge=0.0, description="Updated standard error")
    theta_change: float = Field(..., description="Change in theta from this response")
    percentile: int = Field(..., ge=1, le=99, description="Current percentile rank")
    rank: Rank = Field(..., description="Current rank based on theta")
    confidence_interval_95: List[float] = Field(..., description="95% confidence interval")

    class Config:
        json_schema_extra = {
            "example": {
                "is_correct": True,
                "correct_answer": "B",
                "new_theta": 0.65,
                "new_se": 0.42,
                "theta_change": 0.15,
                "percentile": 74,
                "rank": "C",
                "confidence_interval_95": [-0.17, 1.47]
            }
        }


class AdaptiveSessionState(BaseModel):
    """Schema for adaptive testing session state"""
    session_id: UUID = Field(..., description="Adaptive session UUID")
    user_id: UUID = Field(..., description="User UUID")
    subject_id: Optional[UUID] = Field(None, description="Subject UUID if subject-specific")
    current_theta: float = Field(..., description="Current ability estimate")
    current_se: float = Field(..., description="Current standard error")
    questions_answered: int = Field(..., ge=0, description="Number of questions answered")
    correct_answers: int = Field(..., ge=0, description="Number of correct answers")
    answered_question_ids: List[str] = Field(..., description="List of answered question IDs")
    theta_progression: List[ThetaProgressionItem] = Field(..., description="Theta progression history")
    started_at: datetime = Field(..., description="Session start time")
    status: str = Field(..., description="Session status: in_progress, completed, abandoned")
