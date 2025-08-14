from sqlalchemy import Column, String, Integer, DateTime, Text, DECIMAL, Date, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class PredictiveAnalytics(Base):
    __tablename__ = "predictive_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    predicted_icfes_score = Column(DECIMAL(5, 2))
    confidence_level = Column(DECIMAL(3, 2))
    improvement_potential = Column(DECIMAL(5, 2))
    recommended_focus_areas = Column(JSON)
    next_milestone_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<PredictiveAnalytics(id={self.id}, user_id={self.user_id})>" 