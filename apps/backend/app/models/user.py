from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
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
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(100), default="")  # Ahora existe en la tabla
    # avatar_url = Column(String(500))  # No existe en la tabla
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
    streak_days = Column(Integer, default=0)  # Ahora existe en la tabla
    # last_login = Column(DateTime(timezone=True))  # No existe en la tabla
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Premium fields
    # is_premium = Column(Boolean, default=False)  # No existe en la tabla
    # premium_expires_at = Column(DateTime(timezone=True), nullable=True)  # No existe en la tabla
    premium_plan = Column(String(50), default="free")  # Este sí existe
    # ai_requests_used = Column(Integer, default=0)  # No existe en la tabla
    # ai_requests_limit = Column(Integer, default=5)  # No existe en la tabla
    # simulacros_used = Column(Integer, default=0)  # No existe en la tabla
    # simulacros_limit = Column(Integer, default=2)  # No existe en la tabla
    is_active = Column(Boolean, default=True)  # Este sí existe
    
    # Relationships
    battles = relationship("Battle", back_populates="user", cascade="all, delete-orphan")
    user_quests = relationship("UserQuest", back_populates="user", cascade="all, delete-orphan")
    leaderboard_entries = relationship("Leaderboard", back_populates="user", cascade="all, delete-orphan")
    ai_explanations = relationship("AIExplanation", back_populates="user", cascade="all, delete-orphan")
    user_items = relationship("UserItem", back_populates="user", cascade="all, delete-orphan")
    user_events = relationship("UserEvent", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    diagnostic_tests = relationship("DiagnosticTest", back_populates="user", cascade="all, delete-orphan")
    study_plans = relationship("StudyPlan", back_populates="user", cascade="all, delete-orphan")
    video_tracking = relationship("VideoTracking", back_populates="user", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="user", cascade="all, delete-orphan")
    user_achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    store_transactions = relationship("StoreTransaction", back_populates="user", cascade="all, delete-orphan")
    user_power_ups = relationship("UserPowerUp", back_populates="user", cascade="all, delete-orphan")
    currency_earnings = relationship("CurrencyEarning", back_populates="user", cascade="all, delete-orphan")
    
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