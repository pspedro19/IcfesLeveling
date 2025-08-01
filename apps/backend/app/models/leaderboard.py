from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class Leaderboard(Base):
    __tablename__ = "leaderboard"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    score = Column(Integer, default=0)
    rank_position = Column(Integer)
    leaderboard_type = Column(String(50), default="global")  # 'global', 'weekly', 'monthly'
    period_start = Column(Date)
    period_end = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="leaderboard_entries") 