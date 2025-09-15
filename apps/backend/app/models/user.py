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
    # display_name = Column(String(100), default="")  # Commented out: column does not exist in the table
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
    # streak_days = Column(Integer, default=0)  # Commented out: column does not exist in the table
    # last_login = Column(DateTime(timezone=True))  # No existe en la tabla
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Premium fields
    # is_premium = Column(Boolean, default=False)  # No existe en la tabla
    # premium_expires_at = Column(DateTime(timezone=True), nullable=True)  # No existe en la tabla
    # premium_plan = Column(String(50), default="free")  # No existe en la tabla
    # ai_requests_used = Column(Integer, default=0)  # No existe en la tabla
    # ai_requests_limit = Column(Integer, default=5)  # No existe en la tabla
    # simulacros_used = Column(Integer, default=0)  # No existe en la tabla
    # simulacros_limit = Column(Integer, default=2)  # No existe en la tabla
    is_active = Column(Boolean, default=True)  # Este sí existe
    
    # Relationships - Temporarily commented out to fix SQLAlchemy mapping issues
    # battles = relationship("Battle", cascade="all, delete-orphan")
    # user_quests = relationship("UserQuest", cascade="all, delete-orphan")  
    # leaderboard_entries = relationship("Leaderboard", cascade="all, delete-orphan")
    # diagnostic_tests = relationship("DiagnosticTest", cascade="all, delete-orphan")
    # user_items = relationship("UserItem", cascade="all, delete-orphan")
    
    # Temporarily commenting out problematic relationships that have foreign key issues
    # Will be re-enabled once FK relationships are properly defined
    # ai_explanations = relationship("AIExplanation", cascade="all, delete-orphan")
    # user_events = relationship("UserEvent", cascade="all, delete-orphan")
    # notifications = relationship("Notification", cascade="all, delete-orphan")
    # study_plans = relationship("StudyPlan", cascade="all, delete-orphan")
    # user_achievements = relationship("UserAchievement", cascade="all, delete-orphan")
    # store_transactions = relationship("StoreTransaction", cascade="all, delete-orphan")
    # user_power_ups = relationship("UserPowerUp", cascade="all, delete-orphan")
    # currency_earnings = relationship("CurrencyEarning", cascade="all, delete-orphan")
    # certificates = relationship("Certificate", cascade="all, delete-orphan")
    # subscription = relationship("Subscription", cascade="all, delete-orphan")
    # payments = relationship("Payment", cascade="all, delete-orphan")
    # payment_methods = relationship("PaymentMethod", cascade="all, delete-orphan")
    # invoices = relationship("Invoice", cascade="all, delete-orphan")
    # profile = relationship("UserProfile", cascade="all, delete-orphan", uselist=False)
    # practice_sessions = relationship("PracticeSession", cascade="all, delete-orphan")
    # ai_tutoring_sessions = relationship("AITutoringSession", cascade="all, delete-orphan")
    # responses = relationship("Response", cascade="all, delete-orphan")
    # quizzes = relationship("Quiz", cascade="all, delete-orphan")
    # video_tracking = relationship("VideoTracking", cascade="all, delete-orphan")
    # training_zones = relationship("TrainingZone", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', level={self.level})>"
    
    @property
    def rank_info(self):
        """
        Get rank information based on actual performance data.
        
        NOTE: This property now returns the stored rank from diagnostic test performance.
        For live rank calculation based on theta scores, use PerformanceRankService.
        """
        # Return the stored rank (calculated from actual diagnostic test performance)
        return self.rank or 'E'
    
    @property 
    def legacy_rank_info(self):
        """Legacy rank calculation based on level (kept for compatibility)"""
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
        """
        Add experience and handle level up.
        
        NOTE: Rank updates are now handled by PerformanceRankService based on 
        actual diagnostic test performance data, not just level.
        """
        self.experience += exp_amount
        
        # Calculate new level using improved XP curve: level = sqrt(exp/50) + 1
        import math
        new_level = int(math.sqrt(self.experience / 50)) + 1
        new_level = max(1, min(new_level, 999))  # Cap at level 999
        
        level_up_occurred = new_level > self.level
        if level_up_occurred:
            self.level = new_level
            # Note: Rank is no longer automatically updated here
            # Use PerformanceRankService.update_user_rank_and_level() for rank updates
        
        return level_up_occurred
    
    def add_test_experience(self, xp_from_questions: int):
        """
        Add XP earned from diagnostic test questions (Puntos_XP field).
        
        Args:
            xp_from_questions: Total XP earned from correctly answered questions
        
        Returns:
            bool: Whether a level up occurred
        """
        return self.add_experience(xp_from_questions) 