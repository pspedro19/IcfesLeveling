from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)  # 'unit_completion', 'score_improvement', 'study_streak', 'secret'
    achievement_type = Column(String(50), nullable=False)  # 'single', 'progressive', 'milestone'
    icon_url = Column(String(500))
    rarity = Column(String(20), default="common")  # 'common', 'rare', 'epic', 'legendary'
    points = Column(Integer, default=10)
    requirements = Column(JSON)  # Flexible requirements structure
    is_secret = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    #     user_achievements = # relationship("relationship("UserAchievement",", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Achievement(id={self.id}, title='{self.title}', category='{self.category}')>"
    
    def get_requirements(self):
        """Get requirements as dictionary"""
        return self.requirements if self.requirements else {}
    
    def get_rarity_color(self):
        """Get CSS color for rarity"""
        colors = {
            "common": "#6c757d",
            "rare": "#007bff", 
            "epic": "#6f42c1",
            "legendary": "#fd7e14"
        }
        return colors.get(self.rarity, "#6c757d")

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievements.id"), nullable=False)
    progress = Column(Integer, default=0)
    is_unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime(timezone=True))
    progress_data = Column(JSON)  # Store detailed progress information
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships - Temporalmente comentado para arreglar SQLAlchemy
    # user = relationship("User", )
    achievement = relationship("Achievement", )
    
    def __repr__(self):
        return f"<UserAchievement(user_id={self.user_id}, achievement_id={self.achievement_id}, unlocked={self.is_unlocked})>"
    
    def get_progress_data(self):
        """Get progress data as dictionary"""
        return self.progress_data if self.progress_data else {}
    
    def get_progress_percentage(self):
        """Calculate progress percentage based on achievement requirements"""
        if not self.achievement:
            return 0
        
        requirements = self.achievement.get_requirements()
        if not requirements:
            return 0 if self.progress == 0 else 100
        
        # Get the first requirement value as target
        target = next(iter(requirements.values()), 1)
        if target <= 0:
            return 100 if self.progress > 0 else 0
        
        percentage = min(100, (self.progress / target) * 100)
        return round(percentage, 1) 