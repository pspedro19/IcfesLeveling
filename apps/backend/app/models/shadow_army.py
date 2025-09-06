from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, JSON, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class ShadowSoldier(Base):
    __tablename__ = "shadow_soldiers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    shadow_type = Column(String(50), nullable=False)  # 'knight', 'mage', 'archer', 'assassin', 'beast'
    rank = Column(String(10), default="E")  # E, D, C, B, A, S, SS
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    
    # Combat Stats
    attack_power = Column(Integer, default=10)
    defense = Column(Integer, default=5)
    magic_power = Column(Integer, default=5)
    speed = Column(Integer, default=10)
    health = Column(Integer, default=100)
    mana = Column(Integer, default=50)
    
    # Shadow-specific properties
    loyalty = Column(Integer, default=100)  # Loyalty to the shadow monarch
    extraction_source = Column(String(200))  # Where the shadow was extracted from
    special_abilities = Column(JSON, default=[])  # List of special abilities
    equipment = Column(JSON, default={})  # Equipped items
    
    # Status
    is_active = Column(Boolean, default=True)
    is_summoned = Column(Boolean, default=False)
    last_battle = Column(DateTime(timezone=True))
    battles_won = Column(Integer, default=0)
    battles_lost = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    battle_participations = relationship("ShadowBattle", back_populates="shadow_soldier", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ShadowSoldier(id={self.id}, name='{self.name}', type='{self.shadow_type}', rank='{self.rank}')>"
    
    def get_combat_power(self):
        """Calculate total combat power"""
        return self.attack_power + self.defense + self.magic_power + self.speed
    
    def can_evolve(self):
        """Check if shadow can evolve to next rank"""
        evolution_requirements = {
            'E': 100, 'D': 500, 'C': 2000, 'B': 8000, 'A': 20000, 'S': 50000
        }
        required_exp = evolution_requirements.get(self.rank, 100000)
        return self.experience >= required_exp
    
    def evolve(self):
        """Evolve shadow to next rank"""
        if not self.can_evolve():
            return False
        
        rank_progression = ['E', 'D', 'C', 'B', 'A', 'S', 'SS']
        current_index = rank_progression.index(self.rank)
        
        if current_index < len(rank_progression) - 1:
            self.rank = rank_progression[current_index + 1]
            # Increase stats on evolution
            stat_increase = (current_index + 1) * 5
            self.attack_power += stat_increase
            self.defense += stat_increase
            self.magic_power += stat_increase
            self.speed += stat_increase
            self.health += stat_increase * 2
            self.mana += stat_increase
            return True
        return False

class ShadowFormation(Base):
    __tablename__ = "shadow_formations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    formation_type = Column(String(50), nullable=False)  # 'attack', 'defense', 'balanced', 'speed'
    shadow_positions = Column(JSON, nullable=False)  # Position mapping for shadows
    formation_bonuses = Column(JSON, default={})  # Bonuses granted by formation
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<ShadowFormation(id={self.id}, name='{self.name}', type='{self.formation_type}')>"

class ShadowBattle(Base):
    __tablename__ = "shadow_battles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    battle_id = Column(UUID(as_uuid=True), ForeignKey("battles.id"), nullable=False)
    shadow_soldier_id = Column(UUID(as_uuid=True), ForeignKey("shadow_soldiers.id"), nullable=False)
    
    # Battle Performance
    damage_dealt = Column(Integer, default=0)
    damage_taken = Column(Integer, default=0)
    abilities_used = Column(JSON, default=[])  # List of abilities used
    kills = Column(Integer, default=0)
    experience_gained = Column(Integer, default=0)
    
    # Battle Status
    was_summoned = Column(Boolean, default=False)
    survived_battle = Column(Boolean, default=True)
    performed_special_action = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    battle = relationship("Battle")
    shadow_soldier = relationship("ShadowSoldier", back_populates="battle_participations")
    
    def __repr__(self):
        return f"<ShadowBattle(id={self.id}, battle_id={self.battle_id}, shadow_id={self.shadow_soldier_id})>"

class ShadowExtraction(Base):
    __tablename__ = "shadow_extractions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    source_enemy = Column(String(200), nullable=False)  # Name of defeated enemy
    source_battle_id = Column(UUID(as_uuid=True), ForeignKey("battles.id"))
    extraction_success = Column(Boolean, default=False)
    shadow_soldier_id = Column(UUID(as_uuid=True), ForeignKey("shadow_soldiers.id"))
    
    # Extraction conditions
    enemy_level = Column(Integer, nullable=False)
    user_level_at_extraction = Column(Integer, nullable=False)
    extraction_chance = Column(DECIMAL(5, 2), nullable=False)  # Percentage chance
    
    # Extraction results
    extraction_power_used = Column(Integer, default=0)  # Mana/energy used
    extraction_attempt_count = Column(Integer, default=1)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    battle = relationship("Battle")
    shadow_soldier = relationship("ShadowSoldier")
    
    def __repr__(self):
        return f"<ShadowExtraction(id={self.id}, source='{self.source_enemy}', success={self.extraction_success})>"

class ShadowAbility(Base):
    __tablename__ = "shadow_abilities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    ability_type = Column(String(50), nullable=False)  # 'active', 'passive', 'ultimate'
    shadow_type_requirement = Column(String(50))  # Required shadow type
    rank_requirement = Column(String(10), default="E")  # Minimum rank required
    
    # Ability Effects
    damage_multiplier = Column(DECIMAL(5, 2), default=1.0)
    healing_amount = Column(Integer, default=0)
    buff_effects = Column(JSON, default={})  # Status effects applied
    debuff_effects = Column(JSON, default={})  # Status effects applied to enemies
    
    # Resource Costs
    mana_cost = Column(Integer, default=10)
    cooldown_turns = Column(Integer, default=1)
    
    # Availability
    is_learnable = Column(Boolean, default=True)
    is_unique = Column(Boolean, default=False)  # One per shadow type
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ShadowAbility(id={self.id}, name='{self.name}', type='{self.ability_type}')>"

class UserShadowStats(Base):
    __tablename__ = "user_shadow_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Shadow Monarch Stats
    monarch_level = Column(Integer, default=1)
    monarch_experience = Column(Integer, default=0)
    shadow_capacity = Column(Integer, default=5)  # Max shadows that can be maintained
    extraction_power = Column(Integer, default=100)  # Power available for extractions
    
    # Shadow Army Stats
    total_shadows_extracted = Column(Integer, default=0)
    active_shadows = Column(Integer, default=0)
    highest_rank_shadow = Column(String(10), default="E")
    total_shadow_battles = Column(Integer, default=0)
    total_shadow_victories = Column(Integer, default=0)
    
    # Special Abilities Unlocked
    monarch_abilities = Column(JSON, default=[])  # List of monarch abilities
    can_command_multiple = Column(Boolean, default=False)  # Can command multiple shadows
    can_shadow_exchange = Column(Boolean, default=False)  # Can exchange shadows with others
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserShadowStats(user_id={self.user_id}, monarch_level={self.monarch_level}, shadows={self.active_shadows})>"
    
    def can_extract_shadow(self):
        """Check if user can extract new shadow"""
        return self.active_shadows < self.shadow_capacity and self.extraction_power > 0
    
    def get_extraction_chance(self, enemy_level: int, user_level: int):
        """Calculate extraction chance based on levels"""
        base_chance = 30.0  # Base 30% chance
        level_difference = user_level - enemy_level
        
        # Adjust based on level difference
        if level_difference > 0:
            base_chance += level_difference * 5  # +5% per level above
        else:
            base_chance += level_difference * 10  # -10% per level below
        
        # Monarch level bonus
        base_chance += self.monarch_level * 2
        
        return max(5.0, min(95.0, base_chance))  # Between 5% and 95%