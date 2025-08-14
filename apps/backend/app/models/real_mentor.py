from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class RealMentor(Base):
    __tablename__ = "real_mentors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    bio = Column(Text)
    avatar_url = Column(String(500))
    rating = Column(DECIMAL(3, 2), default=0.0)
    hourly_rate = Column(DECIMAL(10, 2))
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subject = relationship("Subject")
    sessions = relationship("MentorSession", back_populates="mentor")
    
    def __repr__(self):
        return f"<RealMentor(id={self.id}, name='{self.name}')>" 