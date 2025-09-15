"""
Enhanced AI Tutoring Session model for tracking student learning progress
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class AITutoringSession(Base):
    """Tracks comprehensive AI tutoring sessions for students"""
    __tablename__ = "ai_tutoring_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    
    # Session metadata
    session_start = Column(DateTime(timezone=True), server_default=func.now())
    session_end = Column(DateTime(timezone=True))
    total_duration_seconds = Column(Integer)
    
    # Student analysis at session start
    estimated_student_level = Column(String(20))  # beginner, intermediate, advanced
    explanation_complexity_used = Column(String(20))  # simple, moderate, detailed
    vocabulary_level_used = Column(String(20))  # basic, standard, advanced
    
    # Answer tracking
    user_answer = Column(String(10))
    correct_answer = Column(String(10))
    is_correct = Column(Boolean, default=False)
    attempt_number = Column(Integer, default=1)
    
    # Error analysis
    error_type = Column(String(50))  # conceptual, procedural, common_misconception, etc.
    error_analysis = Column(Text)
    
    # AI explanation details
    explanation_type = Column(String(30))  # ai_generated, fallback, correct_answer
    main_explanation = Column(Text)
    detailed_explanation = Column(JSON)  # Structured explanation components
    confidence_score = Column(Float)
    
    # Hints and tutoring
    hints_provided = Column(JSON)  # List of hints given
    hint_levels_used = Column(JSON)  # Progression of hint levels
    max_hints_available = Column(Integer)
    
    # Learning resources
    related_concepts = Column(JSON)  # Concepts identified
    recommended_resources = Column(JSON)  # Resources suggested
    suggested_actions = Column(JSON)  # Next steps recommended
    
    # Effectiveness tracking
    student_satisfaction_rating = Column(Integer)  # 1-5 rating if provided
    explanation_helpfulness = Column(Integer)  # 1-5 rating if provided
    follow_up_questions_asked = Column(Integer, default=0)
    
    # AI model metadata
    ai_model_used = Column(String(50))  # gpt-3.5-turbo, fallback, etc.
    tokens_used = Column(Integer)
    response_time_ms = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    #     user = relationship("User", )
    question = relationship("Question", )
    
    def calculate_session_duration(self):
        """Calculate and update session duration"""
        if self.session_start and self.session_end:
            delta = self.session_end - self.session_start
            self.total_duration_seconds = int(delta.total_seconds())
    
    def add_hint(self, hint_text: str, hint_level: int):
        """Add a hint to the session tracking"""
        if not self.hints_provided:
            self.hints_provided = []
        if not self.hint_levels_used:
            self.hint_levels_used = []
        
        self.hints_provided.append(hint_text)
        self.hint_levels_used.append(hint_level)
    
    def get_learning_effectiveness_score(self) -> float:
        """Calculate a learning effectiveness score based on session data"""
        score = 0.0
        total_factors = 0
        
        # Factor 1: Correctness (40% weight)
        if self.is_correct:
            score += 0.4
        total_factors += 0.4
        
        # Factor 2: Efficiency (30% weight) - fewer attempts is better
        if self.attempt_number:
            efficiency = max(0, (4 - self.attempt_number) / 3)  # Normalize to 0-1
            score += 0.3 * efficiency
        total_factors += 0.3
        
        # Factor 3: AI confidence (20% weight)
        if self.confidence_score:
            score += 0.2 * self.confidence_score
        total_factors += 0.2
        
        # Factor 4: Student satisfaction (10% weight)
        if self.student_satisfaction_rating:
            satisfaction = (self.student_satisfaction_rating - 1) / 4  # Normalize 1-5 to 0-1
            score += 0.1 * satisfaction
        total_factors += 0.1
        
        return score / total_factors if total_factors > 0 else 0.0

class AILearningProgress(Base):
    """Tracks long-term learning progress and patterns for students"""
    __tablename__ = "ai_learning_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Progress tracking period
    tracking_period_start = Column(DateTime(timezone=True))
    tracking_period_end = Column(DateTime(timezone=True))
    
    # Academic level progression
    initial_estimated_level = Column(String(20))
    current_estimated_level = Column(String(20))
    level_progression_trend = Column(String(20))  # improving, stable, declining
    
    # Performance metrics
    total_sessions = Column(Integer, default=0)
    total_questions_attempted = Column(Integer, default=0)
    total_correct_answers = Column(Integer, default=0)
    overall_accuracy_percentage = Column(Float)
    
    # Error pattern analysis
    common_error_types = Column(JSON)  # Most frequent error types
    improvement_areas = Column(JSON)  # Areas showing improvement
    persistent_weaknesses = Column(JSON)  # Areas still needing work
    
    # Hint usage patterns
    average_hints_per_question = Column(Float)
    hint_effectiveness_score = Column(Float)
    self_reliance_trend = Column(String(20))  # more_independent, stable, more_dependent
    
    # Learning preferences discovered
    preferred_explanation_complexity = Column(String(20))
    preferred_resource_types = Column(JSON)
    optimal_study_session_length = Column(Integer)  # in minutes
    
    # Engagement metrics
    average_session_duration = Column(Float)
    follow_up_engagement_rate = Column(Float)
    satisfaction_trend = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    #     user = relationship("User", )
    
    def update_metrics_from_sessions(self, sessions: list):
        """Update progress metrics based on recent tutoring sessions"""
        if not sessions:
            return
        
        self.total_sessions = len(sessions)
        self.total_questions_attempted = len([s for s in sessions if s.user_answer])
        self.total_correct_answers = len([s for s in sessions if s.is_correct])
        
        if self.total_questions_attempted > 0:
            self.overall_accuracy_percentage = (self.total_correct_answers / self.total_questions_attempted) * 100
        
        # Calculate average hints per question
        total_hints = sum(len(s.hints_provided or []) for s in sessions)
        self.average_hints_per_question = total_hints / self.total_questions_attempted if self.total_questions_attempted > 0 else 0
        
        # Calculate average session duration
        durations = [s.total_duration_seconds for s in sessions if s.total_duration_seconds]
        self.average_session_duration = sum(durations) / len(durations) if durations else 0
        
        # Analyze error patterns
        error_types = [s.error_type for s in sessions if s.error_type and s.error_type != 'none']
        error_counts = {}
        for error_type in error_types:
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        # Store top 3 most common error types
        self.common_error_types = dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:3])
        
        # Calculate satisfaction trend
        satisfaction_ratings = [s.student_satisfaction_rating for s in sessions if s.student_satisfaction_rating]
        self.satisfaction_trend = sum(satisfaction_ratings) / len(satisfaction_ratings) if satisfaction_ratings else 0