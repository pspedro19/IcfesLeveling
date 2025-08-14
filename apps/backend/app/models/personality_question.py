from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class PersonalityQuestion(Base):
    __tablename__ = "personality_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # 'motivation', 'learning_style', etc.
    options = Column(JSON, nullable=False)
    weight_factors = Column(JSON, default={})
    order_index = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<PersonalityQuestion(id={self.id}, type='{self.question_type}', order={self.order_index})>"
    
    def get_options(self):
        """Get options as dictionary"""
        return self.options if self.options else {}
    
    def get_weight_factors(self):
        """Get weight factors as dictionary"""
        return self.weight_factors if self.weight_factors else {} 