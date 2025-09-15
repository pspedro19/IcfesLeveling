from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, JSON, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
from datetime import datetime, timedelta

class QuestTemplate(Base):
    __tablename__ = "quest_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    quest_type = Column(String(50), nullable=False)  # 'daily', 'weekly', 'monthly', 'seasonal', 'special'
    category = Column(String(50), nullable=False)    # 'study', 'battle', 'social', 'exploration', 'achievement'
    
    # Quest Parameters
    target_type = Column(String(50), nullable=False)  # What needs to be done
    target_value = Column(Integer, nullable=False)    # How much/many
    target_conditions = Column(JSON, default={})      # Additional conditions
    
    # Requirements
    min_level = Column(Integer, default=1)
    min_rank = Column(String(10), default="E")
    required_subjects = Column(JSON, default=[])      # Subject IDs if applicable
    required_achievements = Column(JSON, default=[])  # Achievement IDs if needed
    
    # Rewards
    base_experience = Column(Integer, default=50)
    base_orbs = Column(Integer, default=25)
    base_crystals = Column(Integer, default=0)
    special_rewards = Column(JSON, default=[])        # Items, titles, etc.
    
    # Quest Properties
    difficulty = Column(String(20), default="normal") # 'easy', 'normal', 'hard', 'extreme'
    rarity = Column(String(20), default="common")     # 'common', 'rare', 'epic', 'legendary'
    is_repeatable = Column(Boolean, default=True)
    max_completions = Column(Integer, default=-1)     # -1 for unlimited
    
    # Availability
    is_active = Column(Boolean, default=True)
    season_requirement = Column(String(50))           # If seasonal quest
    event_requirement = Column(String(50))            # If event quest
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<QuestTemplate(id={self.id}, name='{self.name}', type='{self.quest_type}')>"
    
    def is_available_for_user(self, user):
        """Check if quest template is available for user"""
        if not self.is_active:
            return False
        
        if user.level < self.min_level:
            return False
        
        # Check rank requirement
        rank_order = ['E', 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS']
        if rank_order.index(user.rank) < rank_order.index(self.min_rank):
            return False
        
        # TODO: Check achievement requirements
        # TODO: Check seasonal/event requirements
        
        return True
    
    def calculate_rewards(self, user_level: int, completion_quality: float = 1.0):
        """Calculate quest rewards based on user level and completion quality"""
        level_multiplier = max(1.0, user_level / 10)  # Scale with level
        
        experience = int(self.base_experience * level_multiplier * completion_quality)
        orbs = int(self.base_orbs * level_multiplier * completion_quality)
        crystals = int(self.base_crystals * completion_quality)
        
        # Rarity bonus
        rarity_multipliers = {
            'common': 1.0,
            'rare': 1.5,
            'epic': 2.0,
            'legendary': 3.0
        }
        multiplier = rarity_multipliers.get(self.rarity, 1.0)
        
        return {
            "experience": int(experience * multiplier),
            "orbs": int(orbs * multiplier),
            "crystals": int(crystals * multiplier),
            "special_rewards": self.special_rewards
        }

class EnhancedUserQuest(Base):
    __tablename__ = "enhanced_user_quests"  # Changed to avoid conflict with UserQuest table
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    quest_template_id = Column(UUID(as_uuid=True), ForeignKey("quest_templates.id"), nullable=False)
    
    # Quest Status
    status = Column(String(20), default="active")     # 'active', 'completed', 'failed', 'expired'
    progress = Column(Integer, default=0)
    target_value = Column(Integer, nullable=False)    # Copy from template for tracking
    
    # Timing
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))      # When quest expires
    completed_at = Column(DateTime(timezone=True))
    
    # Progress Tracking
    progress_data = Column(JSON, default={})          # Detailed progress information
    completion_quality = Column(DECIMAL(3, 2), default=1.0)  # Quality of completion (0.0-1.0)
    
    # Rewards Earned
    rewards_claimed = Column(Boolean, default=False)
    experience_earned = Column(Integer, default=0)
    orbs_earned = Column(Integer, default=0)
    crystals_earned = Column(Integer, default=0)
    special_rewards_earned = Column(JSON, default=[])
    
    # Relationships
    user = relationship("User")
    quest_template = relationship("QuestTemplate")
    
    def __repr__(self):
        return f"<UserQuest(id={self.id}, user_id={self.user_id}, status='{self.status}')>"
    
    def update_progress(self, increment: int = 1, metadata: dict = None):
        """Update quest progress"""
        self.progress = min(self.target_value, self.progress + increment)
        
        if metadata:
            current_data = self.progress_data or {}
            current_data.update(metadata)
            self.progress_data = current_data
        
        # Check completion
        if self.progress >= self.target_value and self.status == "active":
            self.status = "completed"
            self.completed_at = datetime.utcnow()
        
        return self.progress >= self.target_value
    
    def calculate_completion_quality(self):
        """Calculate quality of quest completion"""
        base_quality = 1.0
        
        # Time bonus (completed early)
        if self.completed_at and self.expires_at:
            time_remaining = (self.expires_at - self.completed_at).total_seconds()
            total_time = (self.expires_at - self.assigned_at).total_seconds()
            time_ratio = time_remaining / total_time
            base_quality += time_ratio * 0.2  # Up to 20% bonus for early completion
        
        # Over-completion bonus
        if self.progress > self.target_value:
            over_completion = (self.progress - self.target_value) / self.target_value
            base_quality += min(0.3, over_completion)  # Up to 30% bonus for over-completion
        
        self.completion_quality = min(1.5, base_quality)  # Cap at 150%
        return self.completion_quality
    
    def is_expired(self):
        """Check if quest has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def get_progress_percentage(self):
        """Get progress as percentage"""
        if self.target_value <= 0:
            return 100.0 if self.progress > 0 else 0.0
        return min(100.0, (self.progress / self.target_value) * 100)

class QuestChain(Base):
    __tablename__ = "quest_chains"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    chain_type = Column(String(50), nullable=False)   # 'storyline', 'mastery', 'seasonal'
    
    # Chain Properties
    total_quests = Column(Integer, default=1)
    quest_order = Column(JSON, nullable=False)        # Ordered list of quest template IDs
    unlock_conditions = Column(JSON, default={})      # Conditions to unlock chain
    
    # Rewards
    completion_rewards = Column(JSON, default={})     # Bonus for completing entire chain
    chain_title = Column(String(100))                 # Title awarded on completion
    chain_achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievements.id"))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_seasonal = Column(Boolean, default=False)
    season_start = Column(DateTime(timezone=True))
    season_end = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    chain_achievement = relationship("Achievement")
    #     user_chain_progress = # relationship("relationship("UserQuestChain",", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<QuestChain(id={self.id}, name='{self.name}', type='{self.chain_type}')>"

class UserQuestChain(Base):
    __tablename__ = "user_quest_chains"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    quest_chain_id = Column(UUID(as_uuid=True), ForeignKey("quest_chains.id"), nullable=False)
    
    # Progress
    current_quest_index = Column(Integer, default=0)  # Which quest in chain is current
    quests_completed = Column(Integer, default=0)
    chain_completed = Column(Boolean, default=False)
    
    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")
    quest_chain = relationship("QuestChain", )
    
    def __repr__(self):
        return f"<UserQuestChain(id={self.id}, user_id={self.user_id}, completed={self.chain_completed})>"
    
    def advance_to_next_quest(self):
        """Advance to next quest in chain"""
        if self.current_quest_index < len(self.quest_chain.quest_order) - 1:
            self.current_quest_index += 1
            self.quests_completed += 1
            return True
        else:
            # Chain completed
            self.chain_completed = True
            self.completed_at = datetime.utcnow()
            return False

class QuestObjective(Base):
    __tablename__ = "quest_objectives"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quest_template_id = Column(UUID(as_uuid=True), ForeignKey("quest_templates.id"), nullable=False)
    
    # Objective Details
    objective_type = Column(String(50), nullable=False)  # Type of objective
    target_value = Column(Integer, nullable=False)
    description = Column(String(500), nullable=False)
    
    # Conditions
    subject_filter = Column(JSON, default=[])            # Subject IDs if applicable
    difficulty_filter = Column(String(20))               # Difficulty requirement
    time_limit = Column(Integer)                         # Time limit in seconds
    
    # Progress Tracking
    tracking_key = Column(String(100), nullable=False)   # Key to track in progress_data
    
    # Relationships
    quest_template = relationship("QuestTemplate")
    
    def __repr__(self):
        return f"<QuestObjective(id={self.id}, type='{self.objective_type}', value={self.target_value})>"

class QuestReward(Base):
    __tablename__ = "quest_rewards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quest_template_id = Column(UUID(as_uuid=True), ForeignKey("quest_templates.id"), nullable=False)
    
    # Reward Details
    reward_type = Column(String(50), nullable=False)     # 'experience', 'orbs', 'crystals', 'item', 'title'
    reward_value = Column(Integer, default=0)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"))
    title_text = Column(String(200))
    
    # Reward Conditions
    is_bonus_reward = Column(Boolean, default=False)     # Only given for high quality completion
    min_quality = Column(DECIMAL(3, 2), default=1.0)    # Minimum completion quality needed
    
    # Relationships
    quest_template = relationship("QuestTemplate")
    item = relationship("Item")
    
    def __repr__(self):
        return f"<QuestReward(id={self.id}, type='{self.reward_type}', value={self.reward_value})>"

class SpecialEvent(Base):
    __tablename__ = "special_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    event_type = Column(String(50), nullable=False)      # 'seasonal', 'limited', 'holiday', 'anniversary'
    
    # Event Timing
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Event Properties
    special_rewards = Column(JSON, default={})           # Special event rewards
    event_quests = Column(JSON, default=[])              # Quest template IDs for this event
    event_dungeons = Column(JSON, default=[])            # Special dungeon gate IDs
    
    # Event Mechanics
    point_system = Column(JSON, default={})              # Event-specific point system
    leaderboard_enabled = Column(Boolean, default=False)
    participation_requirements = Column(JSON, default={})
    
    # Status
    is_active = Column(Boolean, default=True)
    is_recurring = Column(Boolean, default=False)        # Repeats annually
    recurrence_pattern = Column(JSON, default={})        # When it recurs
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SpecialEvent(id={self.id}, name='{self.name}', type='{self.event_type}')>"
    
    def is_currently_active(self):
        """Check if event is currently active"""
        now = datetime.utcnow()
        return self.is_active and self.start_date <= now <= self.end_date

class UserEventProgress(Base):
    __tablename__ = "user_event_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("special_events.id"), nullable=False)
    
    # Progress
    event_points = Column(Integer, default=0)
    quests_completed = Column(Integer, default=0)
    special_objectives = Column(JSON, default={})        # Track special event objectives
    
    # Rewards
    rewards_claimed = Column(JSON, default=[])           # Milestone rewards claimed
    final_reward_claimed = Column(Boolean, default=False)
    
    # Rankings
    leaderboard_rank = Column(Integer)
    
    # Timing
    first_participation = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    event = relationship("SpecialEvent")
    
    def __repr__(self):
        return f"<UserEventProgress(id={self.id}, user_id={self.user_id}, event_id={self.event_id}, points={self.event_points})>"