from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500))
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    rank = Column(String(10), default="E")
    hp = Column(Integer, default=100)
    mp = Column(Integer, default=50)
    power = Column(Integer, default=10)
    wisdom = Column(Integer, default=10)
    speed = Column(Integer, default=10)
    orbs = Column(Integer, default=1000)
    crystals = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    battles = relationship("Battle", back_populates="user", cascade="all, delete-orphan")
    user_quests = relationship("UserQuest", back_populates="user", cascade="all, delete-orphan")
    leaderboard_entries = relationship("Leaderboard", back_populates="user", cascade="all, delete-orphan")
    ai_explanations = relationship("AIExplanation", back_populates="user", cascade="all, delete-orphan")
    user_items = relationship("UserItem", back_populates="user", cascade="all, delete-orphan")
    user_events = relationship("UserEvent", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', level={self.level})>"
    
    @property
    def rank_info(self):
        """Get rank information based on level"""
        ranks = ['E', 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS']
        if self.level <= 10:
            return ranks[0]
        elif self.level <= 25:
            return ranks[1]
        elif self.level <= 50:
            return ranks[2]
        elif self.level <= 75:
            return ranks[3]
        elif self.level <= 100:
            return ranks[4]
        elif self.level <= 150:
            return ranks[5]
        elif self.level <= 200:
            return ranks[6]
        else:
            return ranks[7]
    
    def add_experience(self, exp_amount: int):
        """Add experience and handle level up"""
        self.experience += exp_amount
        
        # Calculate new level (simple formula: level = sqrt(exp/100))
        new_level = int((self.experience / 100) ** 0.5) + 1
        
        if new_level > self.level:
            self.level = new_level
            self.rank = self.rank_info
            return True  # Level up occurred
        return False  # No level up 