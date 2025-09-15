from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

from ..core.database import Base

class TrainingMode(str, Enum):
    """Training zone modes"""
    RECOVERY = "recovery"              # 20 preguntas priorizadas por recencia/severidad
    FULL_REVIEW = "full_review"        # Todas las preguntas falladas
    SPRINT = "sprint"                  # Top 10 críticas en 10 minutos
    SPACED_REPETITION = "spaced_rep"   # Basado en algoritmo de repetición espaciada
    MONTHLY_FOCUS = "monthly_focus"    # Enfoque mensual específico

class DifficultyLevel(str, Enum):
    """Difficulty levels for adaptive training"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class TrainingZone(Base):
    """
    Main training zone model that tracks student's dedicated learning environment
    for practicing failed ICFES questions with adaptive difficulty and spaced repetition
    """
    __tablename__ = "training_zones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    
    # Monthly rotation system
    current_month = Column(Integer, nullable=False)  # 1-12
    current_year = Column(Integer, nullable=False)
    last_rotation_date = Column(DateTime(timezone=True), server_default=func.now())
    rotation_triggered_by_diagnostic = Column(Boolean, default=False)
    
    # Training configuration
    preferred_mode = Column(String(50), default=TrainingMode.RECOVERY.value)
    adaptive_difficulty = Column(String(50), default=DifficultyLevel.INTERMEDIATE.value)
    daily_goal_questions = Column(Integer, default=10)
    session_time_limit_minutes = Column(Integer, default=30)
    
    # Progress tracking (separate from diagnostic)
    total_training_sessions = Column(Integer, default=0)
    total_questions_practiced = Column(Integer, default=0)
    total_correct_answers = Column(Integer, default=0)
    current_training_streak = Column(Integer, default=0)  # Days with training activity
    max_training_streak = Column(Integer, default=0)
    
    # Performance metrics
    average_session_accuracy = Column(Float, default=0.0)
    improvement_rate = Column(Float, default=0.0)  # % improvement over time
    mastery_level = Column(Float, default=0.0)     # Overall mastery of failed questions
    
    # Spaced repetition algorithm data
    spaced_rep_settings = Column(JSON, default={
        "initial_interval": 1,      # days
        "ease_factor": 2.5,
        "interval_modifier": 1.0,
        "max_interval": 365
    })
    
    # Monthly analytics
    monthly_stats = Column(JSON, default={})  # Stats per month
    monthly_goals = Column(JSON, default={})  # Goals per month
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    #     user = relationship("User", )
    subject = relationship("Subject")
    #     training_sessions = # relationship("relationship("TrainingSession",", cascade="all, delete-orphan")
    #     failed_questions = # relationship("relationship("TrainingZoneQuestion",", cascade="all, delete-orphan")

class TrainingZoneQuestion(Base):
    """
    Individual failed questions in the training zone with spaced repetition tracking
    """
    __tablename__ = "training_zone_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_zone_id = Column(UUID(as_uuid=True), ForeignKey("training_zones.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Source of failure
    source_diagnostic_id = Column(UUID(as_uuid=True), ForeignKey("diagnostic_tests.id"), nullable=False)
    original_failure_date = Column(DateTime(timezone=True), nullable=False)
    original_answer = Column(String(10), nullable=True)
    original_time_seconds = Column(Integer, nullable=False)
    
    # Spaced repetition algorithm
    ease_factor = Column(Float, default=2.5)
    interval_days = Column(Integer, default=1)
    next_review_date = Column(DateTime(timezone=True), nullable=False)
    repetition_number = Column(Integer, default=0)
    
    # Training performance
    training_attempts = Column(Integer, default=0)
    successful_attempts = Column(Integer, default=0)
    consecutive_correct = Column(Integer, default=0)
    consecutive_incorrect = Column(Integer, default=0)
    
    # Mastery tracking
    is_mastered = Column(Boolean, default=False)
    mastery_achieved_date = Column(DateTime(timezone=True), nullable=True)
    mastery_score = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Performance analytics
    best_time_seconds = Column(Integer, nullable=True)
    average_time_seconds = Column(Float, nullable=True)
    time_improvement_percent = Column(Float, default=0.0)
    
    # AI and video integration
    has_ai_explanation = Column(Boolean, default=False)
    ai_explanation_quality = Column(Float, nullable=True)  # User rating
    recommended_videos = Column(JSON, default=[])  # YouTube video IDs
    videos_watched = Column(JSON, default=[])       # Tracking watched videos
    
    # Monthly rotation tracking
    added_in_month = Column(Integer, nullable=False)
    added_in_year = Column(Integer, nullable=False)
    last_practiced_month = Column(Integer, nullable=True)
    priority_level = Column(Integer, default=3)  # 1-5, 5 being highest priority
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    training_zone = relationship("TrainingZone", )
    question = relationship("Question")
    user = relationship("User")
    diagnostic_test = relationship("DiagnosticTest")
    #     training_attempts_rel = # relationship("relationship("TrainingAttempt",", cascade="all, delete-orphan")
    
    def calculate_next_review_date(self, quality: int) -> datetime:
        """
        Calculate next review date using spaced repetition algorithm
        Quality: 0-5 (0=total blackout, 5=perfect response)
        """
        if quality < 3:
            # Reset for incorrect answers
            self.repetition_number = 0
            self.interval_days = 1
        else:
            if self.repetition_number == 0:
                self.interval_days = 1
            elif self.repetition_number == 1:
                self.interval_days = 6
            else:
                self.interval_days = int(self.interval_days * self.ease_factor)
            
            self.repetition_number += 1
        
        # Adjust ease factor based on quality
        if quality >= 3:
            self.ease_factor = self.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        # Ensure ease factor stays within bounds
        self.ease_factor = max(1.3, self.ease_factor)
        
        return datetime.now() + timedelta(days=self.interval_days)
    
    def calculate_priority_score(self) -> float:
        """Calculate priority score for question selection"""
        score = 0.0
        
        # Recency factor (40%)
        days_since_failure = (datetime.now() - self.original_failure_date).days
        if days_since_failure <= 7:
            score += 0.4
        elif days_since_failure <= 30:
            score += 0.25
        else:
            score += 0.1
        
        # Performance factor (30%)
        if self.training_attempts == 0:
            score += 0.3  # Never practiced
        else:
            accuracy = self.successful_attempts / self.training_attempts
            if accuracy < 0.5:
                score += 0.25  # Poor performance
            elif accuracy < 0.8:
                score += 0.15  # Moderate performance
            else:
                score += 0.05  # Good performance
        
        # Spaced repetition factor (20%)
        if datetime.now() >= self.next_review_date:
            days_overdue = (datetime.now() - self.next_review_date).days
            score += min(0.2, 0.05 + (days_overdue * 0.01))
        
        # Priority level factor (10%)
        score += (self.priority_level / 5) * 0.1
        
        return min(1.0, score)

class TrainingSession(Base):
    """
    Individual training sessions within the training zone
    """
    __tablename__ = "training_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_zone_id = Column(UUID(as_uuid=True), ForeignKey("training_zones.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session configuration
    mode = Column(String(50), nullable=False)
    target_questions = Column(Integer, nullable=False)
    time_limit_minutes = Column(Integer, nullable=False)
    
    # Session progress
    status = Column(String(20), default="active")  # active, completed, paused, abandoned
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    max_streak_in_session = Column(Integer, default=0)
    
    # Performance metrics
    total_time_seconds = Column(Integer, default=0)
    average_response_time = Column(Float, default=0.0)
    session_accuracy = Column(Float, default=0.0)
    
    # AI and help usage
    ai_explanations_requested = Column(Integer, default=0)
    videos_watched = Column(Integer, default=0)
    hints_used = Column(Integer, default=0)
    
    # Gamification elements
    experience_gained = Column(Integer, default=0)
    achievements_unlocked = Column(JSON, default=[])
    difficulty_progression = Column(JSON, default=[])
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    training_zone = relationship("TrainingZone", )
    user = relationship("User")
    #     training_attempts = # relationship("relationship("TrainingAttempt",", cascade="all, delete-orphan")

class TrainingAttempt(Base):
    """
    Individual question attempts within training sessions
    """
    __tablename__ = "training_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_session_id = Column(UUID(as_uuid=True), ForeignKey("training_sessions.id"), nullable=False)
    training_question_id = Column(UUID(as_uuid=True), ForeignKey("training_zone_questions.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Answer details
    user_answer = Column(String(10), nullable=True)
    is_correct = Column(Boolean, nullable=False)
    response_time_seconds = Column(Integer, nullable=False)
    confidence_level = Column(Integer, default=3)  # 1-5 scale
    
    # Learning context
    attempt_number = Column(Integer, nullable=False)  # Order in session
    was_reviewed = Column(Boolean, default=False)     # If student reviewed explanation
    difficulty_at_attempt = Column(String(50), nullable=False)
    
    # Help and resources used
    ai_explanation_requested = Column(Boolean, default=False)
    ai_explanation_helpful = Column(Boolean, nullable=True)  # User feedback
    video_watched_before = Column(Boolean, default=False)
    video_watched_after = Column(Boolean, default=False)
    hints_requested = Column(Integer, default=0)
    
    # Spaced repetition quality rating
    quality_rating = Column(Integer, nullable=True)  # 0-5 for spaced repetition
    
    # Performance impact
    time_improvement = Column(Float, default=0.0)  # vs original diagnostic time
    mastery_gain = Column(Float, default=0.0)      # Estimated learning gain
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    training_session = relationship("TrainingSession", )
    training_question = relationship("TrainingZoneQuestion", )
    question = relationship("Question")
    user = relationship("User")
    ai_explanation = relationship("TrainingAIExplanation", uselist=False, cascade="all, delete-orphan")

class TrainingAIExplanation(Base):
    """
    AI-generated explanations for training questions
    """
    __tablename__ = "training_ai_explanations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_attempt_id = Column(UUID(as_uuid=True), ForeignKey("training_attempts.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Explanation content
    explanation_text = Column(Text, nullable=False)
    explanation_type = Column(String(50), nullable=False)  # conceptual, step_by_step, hint, error_analysis
    difficulty_level = Column(String(50), nullable=False)
    
    # Personalization
    user_error_analysis = Column(Text, nullable=True)  # Why the student got it wrong
    personalized_tips = Column(Text, nullable=True)    # Specific advice for this student
    related_concepts = Column(JSON, default=[])        # Connected topics to review
    
    # Content quality
    explanation_quality = Column(Float, nullable=True)  # User rating 1-5
    was_helpful = Column(Boolean, nullable=True)        # User feedback
    reading_time_seconds = Column(Integer, default=0)
    
    # AI metadata
    ai_model_used = Column(String(100), nullable=False)
    generation_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    tokens_used = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    training_attempt = relationship("TrainingAttempt", )
    question = relationship("Question")
    user = relationship("User")

class TrainingVideoRecommendation(Base):
    """
    YouTube video recommendations for training questions
    """
    __tablename__ = "training_video_recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_question_id = Column(UUID(as_uuid=True), ForeignKey("training_zone_questions.id"), nullable=False)
    youtube_video_id = Column(UUID(as_uuid=True), ForeignKey("youtube_catalog.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    
    # Recommendation metrics
    relevance_score = Column(Float, nullable=False)  # AI-calculated relevance
    topic_match_score = Column(Float, nullable=False)
    difficulty_match = Column(Boolean, default=True)
    recommendation_reason = Column(Text, nullable=True)
    
    # User interaction
    times_recommended = Column(Integer, default=1)
    times_clicked = Column(Integer, default=0)
    times_watched_full = Column(Integer, default=0)
    user_rating = Column(Float, nullable=True)  # 1-5 stars
    
    # Performance impact
    helped_with_question = Column(Boolean, nullable=True)  # If user got question right after watching
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    training_question = relationship("TrainingZoneQuestion")
    youtube_video = relationship("YoutubeCatalog")
    question = relationship("Question")

class MonthlyTrainingReport(Base):
    """
    Monthly training zone reports and analytics
    """
    __tablename__ = "monthly_training_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    
    # Time period
    report_month = Column(Integer, nullable=False)  # 1-12
    report_year = Column(Integer, nullable=False)
    
    # Training statistics
    total_sessions = Column(Integer, default=0)
    total_questions_practiced = Column(Integer, default=0)
    total_correct_answers = Column(Integer, default=0)
    average_session_accuracy = Column(Float, default=0.0)
    
    # Progress metrics
    questions_mastered = Column(Integer, default=0)
    new_failures_added = Column(Integer, default=0)  # From diagnostic updates
    improvement_rate = Column(Float, default=0.0)
    time_spent_minutes = Column(Integer, default=0)
    
    # Engagement metrics
    days_active = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    ai_explanations_used = Column(Integer, default=0)
    videos_watched = Column(Integer, default=0)
    
    # Performance by difficulty
    beginner_accuracy = Column(Float, default=0.0)
    intermediate_accuracy = Column(Float, default=0.0)
    advanced_accuracy = Column(Float, default=0.0)
    expert_accuracy = Column(Float, default=0.0)
    
    # Detailed analytics
    topic_performance = Column(JSON, default={})     # Performance by topic
    error_patterns = Column(JSON, default={})        # Common error types
    learning_insights = Column(JSON, default={})     # AI-generated insights
    
    # Recommendations for next month
    recommended_focus_areas = Column(JSON, default=[])
    suggested_goals = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    subject = relationship("Subject")