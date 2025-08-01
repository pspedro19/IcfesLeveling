from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class AIExplanation(Base):
    __tablename__ = "ai_explanations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    explanation_text = Column(Text, nullable=False)
    explanation_type = Column(String(50), default="wrong_answer")  # 'wrong_answer', 'study_plan', 'hint'
    tokens_used = Column(Integer)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="ai_explanations")
    question = relationship("Question", back_populates="ai_explanations") 