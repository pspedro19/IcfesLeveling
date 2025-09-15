from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, JSON, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("study_plans.id"), nullable=False)
    unit_number = Column(Integer, nullable=False)
    quiz_name = Column(String(200), nullable=False)
    total_questions = Column(Integer, default=10)
    passing_score = Column(DECIMAL(5,2), default=80.00)  # 80% para aprobar
    time_limit_minutes = Column(Integer, default=15)
    status = Column(String(20), default="in_progress")  # 'in_progress', 'completed', 'failed'
    score = Column(DECIMAL(5,2), default=0.00)
    correct_answers = Column(Integer, default=0)
    time_taken_seconds = Column(Integer, default=0)
    ai_feedback = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    #     user = relationship("User", )
    plan = relationship("StudyPlan", )
    #     quiz_answers = # relationship("relationship("QuizAnswer",", cascade="all, delete-orphan")

class QuizAnswer(Base):
    __tablename__ = "quiz_answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    user_answer = Column(String(10))
    is_correct = Column(Boolean)
    response_time_ms = Column(Integer)
    ai_explanation = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    quiz = relationship("Quiz", )
    question = relationship("Question", ) 