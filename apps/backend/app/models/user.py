from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Date, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
from ..services.game_engine_service import GameEngineService

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(100), default="")  # Display name for user
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    rank = Column(String(10), default="E")
    hp = Column(Integer, default=100)
    mp = Column(Integer, default=50)
    power = Column(Integer, default=10)
    wisdom = Column(Integer, default=10)
    speed = Column(Integer, default=10)
    gold = Column(Integer, default=1000)  # Primary currency per spec (gold coins)
    orbs = Column(Integer, default=0)  # Secondary currency (knowledge orbs)
    crystals = Column(Integer, default=0)  # Premium currency
    streak_days = Column(Integer, default=0)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Streak System Fields (for mobile app)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    previous_streak = Column(Integer, default=0)
    streak_lost_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_date = Column(Date, nullable=True)
    daily_goal_xp = Column(Integer, default=20)
    ad_repairs_today = Column(Integer, default=0)
    timezone = Column(String(50), default='America/Bogota')

    # Hearts System Fields (for mobile app)
    hearts = Column(Integer, default=5)
    max_hearts = Column(Integer, default=5)
    hearts_last_regeneration = Column(DateTime(timezone=True), nullable=True)
    unlimited_hearts_until = Column(DateTime(timezone=True), nullable=True)

    # Streak Freeze & Ads Fields (per spec)
    streak_freeze_count = Column(Integer, default=0)  # Number of streak freezes available
    ads_watched_today = Column(Integer, default=0)  # Max 3 per day for heart recovery
    ads_watched_date = Column(Date, nullable=True)  # Date to reset ads_watched_today

    # Onboarding & Projections
    onboarding_completed = Column(Boolean, default=False)  # Tutorial completed
    onboarding_preferences = Column(JSON, nullable=True)  # Steps 2-5 preferences (goal, level, subjects, time)
    projected_icfes_score = Column(Integer, nullable=True)  # AI-projected score (0-500)

    # Premium/Subscription Fields
    premium_plan = Column(String(50), default="free", nullable=False)  # free, basic, premium, elite
    premium_expires_at = Column(DateTime(timezone=True), nullable=True)
    is_admin = Column(Boolean, default=False)  # For admin access checks

    is_active = Column(Boolean, default=True)
    
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
    
    # @property 
    # def legacy_rank_info(self):
    #     """DEPRECATED: Legacy rank calculation based on level. Use GameEngineService.calculate_rank instead."""
    #     ranks = ['E', 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS']
    #     if self.level <= 10:
    #         return ranks[0]
    #     elif self.level <= 25:
    #         return ranks[1]
    #     elif self.level <= 50:
    #         return ranks[2]
    #     elif self.level <= 75:
    #         return ranks[3]
    #     elif self.level <= 100:
    #         return ranks[4]
    #     elif self.level <= 150:
    #         return ranks[5]
    #     elif self.level <= 200:
    #         return ranks[6]
    #     else:
    #         return ranks[7]
    
    def add_experience(self, exp_amount: int):
        """
        Add experience and handle level up.
        
        NOTE: Rank updates are now handled by PerformanceRankService based on 
        actual diagnostic test performance data, not just level.
        """
        self.experience += exp_amount
        
        # Calculate new level using the unified GameEngineService
        new_level = GameEngineService.calculate_level_for_xp(self.experience)
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