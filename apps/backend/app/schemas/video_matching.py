from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

class ErrorType(Enum):
    """Types of errors students make"""
    CONCEPTUAL = "conceptual"
    PROCEDURAL = "procedural"
    COMPUTATIONAL = "computational"
    INTERPRETIVE = "interpretive"
    ATTENTION = "attention"
    KNOWLEDGE_GAP = "knowledge_gap"
    LINGUISTIC = "linguistic"
    STRATEGIC = "strategic"

class MatchingStrategy(Enum):
    """Video matching strategies"""
    DIRECT_REMEDIATION = "direct_remediation"
    CONCEPT_REVIEW = "concept_review"
    SKILL_BUILDING = "skill_building"
    PREREQUISITE_FILLING = "prerequisite_filling"
    STRATEGIC_TRAINING = "strategic_training"
    COMPREHENSIVE = "comprehensive"

class MatchingConfidence(Enum):
    """Confidence levels for matches"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"

@dataclass
class FailedQuestion:
    """Represents a failed question with context"""
    question_id: Union[int, str]
    student_id: str
    
    question_text: str
    question_type: str
    correct_answer: str
    student_answer: str
    distractors: List[str]
    
    subject_area: str
    topic: str
    subtopic: str
    competency: str
    component: str
    cognitive_level: str
    
    time_spent_seconds: int
    attempt_number: int
    failed_at: datetime
    diagnostic_session_id: Optional[str] = None
    
    student_theta: float = 0.0
    question_difficulty: float = 0.0
    success_probability: float = 0.0
    
    question_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorAnalysis:
    """Analysis of why a question was answered incorrectly"""
    question_id: Union[int, str]
    student_id: str
    
    primary_error_type: ErrorType
    secondary_error_types: List[ErrorType]
    error_confidence: float
    
    distractor_analysis: Dict[str, Any]
    common_error_pattern: str
    error_frequency: float
    
    time_pressure_indicator: float
    prerequisite_gaps: List[str]
    conceptual_misunderstandings: List[str]
    
    intervention_priority: int
    recommended_strategies: List[MatchingStrategy]
    
    analysis_timestamp: datetime
    analysis_confidence: float

@dataclass
class VideoMatch:
    """A matched video with detailed scoring"""
    video_id: Union[int, str]
    video_title: str
    video_url: str
    
    semantic_similarity_score: float
    topic_relevance_score: float
    difficulty_appropriateness_score: float
    
    overall_match_score: float
    confidence_level: MatchingConfidence
    
    match_reasons: List[str]
    addressing_error_types: List[ErrorType]
    matching_strategies: List[MatchingStrategy]
    
    predicted_outcomes: Dict[str, Any] # Learning impact, estimated watch time, success prob improvement
    
    duration_minutes: int
    channel_name: str
    engagement_metrics: Dict[str, float]
    
    matched_at: datetime
    matching_algorithm_version: str

@dataclass
class MatchingRequest:
    """Request for video matching"""
    failed_question: FailedQuestion
    student_profile: Optional[Dict[str, Any]] = None # Use Dict[str, Any] as StudentProfile is not defined
    
    max_videos: int = 10
    min_confidence: float = 0.4
    preferred_strategies: List[MatchingStrategy] = field(default_factory=list)
    max_duration_minutes: int = 30
    
    exclude_watched_videos: bool = True
    require_high_engagement: bool = False
    language_preference: str = "es"
    
    session_context: Dict[str, Any] = field(default_factory=dict)
    request_timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class MatchingResult:
    """Complete result of video matching"""
    request_id: str
    failed_question: FailedQuestion
    error_analysis: ErrorAnalysis
    
    video_matches: List[VideoMatch]
    total_matches_found: int
    
    matching_time_ms: float
    algorithms_used: List[str]
    
    average_match_confidence: float
    coverage_score: float
    
    recommended_viewing_order: List[Union[int, str]]
    estimated_total_study_time: int
    
    result_timestamp: datetime
    cache_hit: bool = False
