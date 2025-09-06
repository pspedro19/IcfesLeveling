from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, JSON, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class DungeonGate(Base):
    __tablename__ = "dungeon_gates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    gate_type = Column(String(50), nullable=False)  # 'normal', 'red', 'boss', 'instant'
    difficulty_rank = Column(String(10), nullable=False)  # E, D, C, B, A, S
    
    # Gate Properties
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    topic_focus = Column(String(200))  # Specific topic this gate focuses on
    recommended_level = Column(Integer, default=1)
    max_participants = Column(Integer, default=1)  # 1 for solo, more for raids
    
    # Dungeon Layout
    total_rooms = Column(Integer, default=5)
    boss_room = Column(Integer, default=5)  # Which room has the boss
    room_configuration = Column(JSON, default={})  # Room layout and monsters
    
    # Gate Mechanics
    time_limit_minutes = Column(Integer, default=60)  # Time limit for completion
    entry_cost_orbs = Column(Integer, default=0)
    entry_cost_crystals = Column(Integer, default=0)
    min_rank_requirement = Column(String(10), default="E")
    
    # Rewards
    base_experience_reward = Column(Integer, default=100)
    base_orb_reward = Column(Integer, default=50)
    base_crystal_reward = Column(Integer, default=0)
    possible_item_drops = Column(JSON, default=[])  # List of possible item drops
    boss_guaranteed_drops = Column(JSON, default=[])  # Guaranteed boss drops
    
    # Gate Status
    is_active = Column(Boolean, default=True)
    is_raid_gate = Column(Boolean, default=False)
    is_seasonal = Column(Boolean, default=False)
    seasonal_start = Column(DateTime(timezone=True))
    seasonal_end = Column(DateTime(timezone=True))
    
    # Statistics
    times_entered = Column(Integer, default=0)
    times_completed = Column(Integer, default=0)
    average_completion_time = Column(Integer, default=0)  # In seconds
    success_rate = Column(DECIMAL(5, 2), default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    subject = relationship("Subject")
    dungeon_runs = relationship("DungeonRun", back_populates="gate", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DungeonGate(id={self.id}, name='{self.name}', type='{self.gate_type}', rank='{self.difficulty_rank}')>"

class DungeonRun(Base):
    __tablename__ = "dungeon_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gate_id = Column(UUID(as_uuid=True), ForeignKey("dungeon_gates.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Run Status
    status = Column(String(20), default="in_progress")  # 'in_progress', 'completed', 'failed', 'abandoned'
    current_room = Column(Integer, default=1)
    
    # Performance Tracking
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    completion_time = Column(DateTime(timezone=True))
    total_time_seconds = Column(Integer)
    
    # Combat Stats
    monsters_defeated = Column(Integer, default=0)
    boss_defeated = Column(Boolean, default=False)
    total_damage_dealt = Column(Integer, default=0)
    total_damage_taken = Column(Integer, default=0)
    questions_answered = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)
    
    # Resources Used
    hp_potions_used = Column(Integer, default=0)
    mp_potions_used = Column(Integer, default=0)
    power_ups_used = Column(JSON, default=[])
    shadows_summoned = Column(Integer, default=0)
    
    # Rewards Earned
    experience_gained = Column(Integer, default=0)
    orbs_gained = Column(Integer, default=0)
    crystals_gained = Column(Integer, default=0)
    items_dropped = Column(JSON, default=[])  # Items found during run
    
    # Special Achievements
    perfect_clear = Column(Boolean, default=False)  # No damage taken
    speed_clear = Column(Boolean, default=False)   # Completed under time threshold
    no_items_used = Column(Boolean, default=False)  # No consumables used
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    gate = relationship("DungeonGate", back_populates="dungeon_runs")
    user = relationship("User")
    room_encounters = relationship("DungeonEncounter", back_populates="dungeon_run", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DungeonRun(id={self.id}, gate_id={self.gate_id}, user_id={self.user_id}, status='{self.status}')>"

class DungeonEncounter(Base):
    __tablename__ = "dungeon_encounters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dungeon_run_id = Column(UUID(as_uuid=True), ForeignKey("dungeon_runs.id"), nullable=False)
    room_number = Column(Integer, nullable=False)
    
    # Encounter Type
    encounter_type = Column(String(50), nullable=False)  # 'monster', 'boss', 'treasure', 'puzzle'
    enemy_name = Column(String(200))
    enemy_level = Column(Integer)
    enemy_type = Column(String(50))  # Type of enemy encountered
    
    # Combat Details
    questions_faced = Column(JSON, default=[])  # Question IDs faced
    answers_given = Column(JSON, default=[])    # User answers
    combat_rounds = Column(Integer, default=1)
    
    # Results
    encounter_won = Column(Boolean, default=False)
    damage_dealt = Column(Integer, default=0)
    damage_taken = Column(Integer, default=0)
    experience_gained = Column(Integer, default=0)
    
    # Rewards from this encounter
    items_dropped = Column(JSON, default=[])
    orbs_gained = Column(Integer, default=0)
    special_effects = Column(JSON, default=[])  # Special effects like buffs/debuffs
    
    # Shadow Army Interaction
    shadows_used = Column(JSON, default=[])  # Shadows that participated
    shadow_extraction_attempted = Column(Boolean, default=False)
    shadow_extraction_successful = Column(Boolean, default=False)
    
    encounter_time = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    dungeon_run = relationship("DungeonRun", back_populates="room_encounters")
    
    def __repr__(self):
        return f"<DungeonEncounter(id={self.id}, room={self.room_number}, type='{self.encounter_type}')>"

class DungeonMonster(Base):
    __tablename__ = "dungeon_monsters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    monster_type = Column(String(50), nullable=False)  # 'beast', 'undead', 'elemental', 'humanoid'
    rank = Column(String(10), nullable=False)  # E, D, C, B, A, S
    
    # Combat Stats
    level = Column(Integer, default=1)
    health = Column(Integer, default=100)
    attack = Column(Integer, default=10)
    defense = Column(Integer, default=5)
    magic_power = Column(Integer, default=5)
    speed = Column(Integer, default=10)
    
    # Monster Abilities
    special_abilities = Column(JSON, default=[])  # List of special abilities
    resistances = Column(JSON, default=[])        # Damage resistances
    weaknesses = Column(JSON, default=[])         # Damage weaknesses
    
    # Question Generation
    preferred_subjects = Column(JSON, default=[])  # Subject IDs this monster uses for questions
    question_difficulty = Column(String(20), default="medium")  # 'easy', 'medium', 'hard'
    questions_per_encounter = Column(Integer, default=3)
    
    # Loot Table
    drop_rate_common = Column(DECIMAL(5, 2), default=70.0)
    drop_rate_rare = Column(DECIMAL(5, 2), default=20.0)
    drop_rate_epic = Column(DECIMAL(5, 2), default=8.0)
    drop_rate_legendary = Column(DECIMAL(5, 2), default=2.0)
    
    possible_drops = Column(JSON, default=[])  # List of item IDs
    orb_drop_min = Column(Integer, default=5)
    orb_drop_max = Column(Integer, default=15)
    
    # Shadow Extraction
    can_be_extracted = Column(Boolean, default=True)
    extraction_difficulty = Column(DECIMAL(5, 2), default=30.0)  # Base extraction chance
    shadow_type = Column(String(50))  # What type of shadow this becomes
    
    # Monster Behavior
    aggression_level = Column(Integer, default=5)  # 1-10, affects encounter behavior
    intelligence = Column(Integer, default=5)      # Affects question selection
    pack_behavior = Column(Boolean, default=False) # Appears with other monsters
    
    is_boss = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<DungeonMonster(id={self.id}, name='{self.name}', type='{self.monster_type}', rank='{self.rank}')>"

class RaidParticipant(Base):
    __tablename__ = "raid_participants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dungeon_run_id = Column(UUID(as_uuid=True), ForeignKey("dungeon_runs.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="damage_dealer")  # 'tank', 'healer', 'damage_dealer', 'support'
    
    # Participation Stats
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True))
    is_leader = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Performance in Raid
    damage_dealt = Column(Integer, default=0)
    damage_taken = Column(Integer, default=0)
    healing_done = Column(Integer, default=0)
    questions_answered = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)
    
    # Contribution Score
    contribution_score = Column(Integer, default=0)
    mvp_votes = Column(Integer, default=0)
    
    # Rewards
    individual_rewards = Column(JSON, default={})
    
    # Relationships
    dungeon_run = relationship("DungeonRun")
    user = relationship("User")
    
    def __repr__(self):
        return f"<RaidParticipant(id={self.id}, user_id={self.user_id}, role='{self.role}')>"