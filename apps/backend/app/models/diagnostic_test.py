from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..core.database import Base

class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    test_type = Column(String(50), default="real_icfes")  # 'real_icfes', 'monthly_reassessment'
    reassessment_type = Column(String(50), nullable=True)  # 'initial', 'monthly', 'adaptive'
    original_test_id = Column(UUID(as_uuid=True), ForeignKey("diagnostic_tests.id"), nullable=True)
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, default=0)
    score_percentage = Column(Float, default=0.0)
    strengths = Column(JSON, default=[])
    weaknesses = Column(JSON, default=[])
    score_by_topic = Column(JSON, default={})
    status = Column(String(20), default="in_progress")  # 'in_progress', 'completed'
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Monthly reassessment specific fields
    is_monthly_reassessment = Column(Boolean, default=False)
    days_since_initial = Column(Integer, nullable=True)
    comparison_with_initial = Column(JSON, nullable=True)  # Store comparison data
    plan_regenerated = Column(Boolean, default=False)
    new_goals_generated = Column(Boolean, default=False)
    notification_sent = Column(Boolean, default=False)
    
    # Relationships
    #     user = relationship("User", )
    subject = relationship("Subject")
    original_test = relationship("DiagnosticTest", remote_side=[id])
    #     answers = # relationship("relationship("DiagnosticTestAnswer",", cascade="all, delete-orphan", foreign_keys="DiagnosticTestAnswer.diagnostic_test_id")

class DiagnosticTestAnswer(Base):
    __tablename__ = "diagnostic_test_answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diagnostic_test_id = Column(UUID(as_uuid=True), ForeignKey("diagnostic_tests.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    user_answer = Column(String(10), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    response_time_ms = Column(Integer, default=0)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    hints_used = Column(Integer, default=0)  # Number of hints requested for this question
    hint_levels_requested = Column(JSON, default=[])  # Array of hint levels requested [1,2,3]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    #     test = # relationship("relationship("DiagnosticTest",", foreign_keys=[diagnostic_test_id])
    question = relationship("Question")
    topic = relationship("Topic")

class DiagnosticTestResult(Base):
    """
    Individual diagnostic test results with IRT theta tracking.
    This table tracks every individual question attempt with adaptive testing metrics.
    """
    __tablename__ = "diagnostic_test_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    user_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=False)
    response_time = Column(Integer, nullable=False)  # Response time in milliseconds
    theta_before = Column(Float(precision=4), nullable=True)  # IRT theta before question
    theta_after = Column(Float(precision=4), nullable=True)   # IRT theta after question
    hints_used = Column(Integer, default=0)  # Number of hints requested for this question
    hint_levels_requested = Column(JSON, default=[])  # Array of hint levels requested [1,2,3]
    
    # Tracking metrics as requested
    tiempo_estimado_baseline = Column(Integer, nullable=True)  # Baseline response time from question data (seconds)
    nivel_dificultad = Column(Integer, nullable=True)  # Difficulty level attempted (1-10 scale)
    nivel_desempeno_esperado = Column(String(20), nullable=True)  # Performance level achieved (e.g., "Mínimo", "Satisfactorio", "Avanzado")
    puntos_xp_earned = Column(Integer, default=0)  # XP points earned for this question
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    subject = relationship("Subject")
    question = relationship("Question") 