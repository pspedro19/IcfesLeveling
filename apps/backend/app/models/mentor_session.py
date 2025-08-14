from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class MentorSession(Base):
    __tablename__ = "mentor_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    mentor_id = Column(UUID(as_uuid=True), ForeignKey("real_mentors.id"), nullable=False)
    session_date = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(20), default="scheduled")  # 'scheduled', 'completed', 'cancelled'
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    mentor = relationship("RealMentor", back_populates="sessions")
    
    def __repr__(self):
        return f"<MentorSession(id={self.id}, user_id={self.user_id}, mentor_id={self.mentor_id})>" 