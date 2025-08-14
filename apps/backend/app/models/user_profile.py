from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    hero_class_id = Column(UUID(as_uuid=True), ForeignKey("hero_classes.id"))
    personality_answers = Column(JSON)
    avatar_customization = Column(JSON, default={})
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")
    hero_class = relationship("HeroClass", back_populates="user_profiles")
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, user_id={self.user_id}, hero_class_id={self.hero_class_id})>"
    
    def get_personality_answers(self):
        """Get personality answers as dictionary"""
        return self.personality_answers if self.personality_answers else {}
    
    def get_avatar_customization(self):
        """Get avatar customization as dictionary"""
        return self.avatar_customization if self.avatar_customization else {}
    
    def get_school_info(self):
        """Get school information as dictionary (placeholder for future implementation)"""
        return {
            "school_name": None,
            "school_city": None,
            "school_type": None
        } 