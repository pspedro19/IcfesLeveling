from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class VideoTracking(Base):
    __tablename__ = "video_tracking"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("study_plans.id"), nullable=False)
    unit_number = Column(Integer, nullable=False)
    youtube_url = Column(String(500), nullable=False)
    video_title = Column(String(200))
    video_duration_seconds = Column(Integer)
    watched_seconds = Column(Integer, default=0)
    watch_percentage = Column(DECIMAL(5,2), default=0.00)
    is_completed = Column(Boolean, default=False)
    completion_threshold = Column(DECIMAL(5,2), default=80.00)  # 80% mínimo
    last_watched_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="video_tracking")
    plan = relationship("StudyPlan", back_populates="video_tracking") 