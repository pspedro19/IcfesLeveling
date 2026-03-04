from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from ..core.database import Base

class Response(Base):
    """Model for student responses to questions"""
    __tablename__ = "responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    answer = Column(String(10), nullable=False)  # A, B, C, D, E
    is_correct = Column(Boolean, nullable=False, default=False)
    time_taken = Column(Integer, nullable=True)  # Time in seconds
    confidence_level = Column(Float, nullable=True)  # 0.0 to 1.0
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    #     user = relationship("User", )
    question = relationship("Question", )
    
    def __repr__(self):
        return f"<Response(user_id={self.user_id}, question_id={self.question_id}, answer={self.answer}, is_correct={self.is_correct})>"