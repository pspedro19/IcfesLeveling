from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class Battle(Base):
    __tablename__ = "battles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    battle_type = Column(String(50), nullable=False)  # 'dungeon', 'tower', 'pvp'
    enemy_name = Column(String(100))
    enemy_level = Column(Integer)
    enemy_hp = Column(Integer)
    user_hp_start = Column(Integer)
    user_hp_end = Column(Integer)
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_damage_dealt = Column(Integer, default=0)
    total_damage_received = Column(Integer, default=0)
    experience_gained = Column(Integer, default=0)
    orbs_gained = Column(Integer, default=0)
    items_dropped = Column(JSON, default=[])
    duration_seconds = Column(Integer)
    status = Column(String(20), default="in_progress")  # 'in_progress', 'completed', 'failed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="battles")
    battle_answers = relationship("BattleAnswer", back_populates="battle", cascade="all, delete-orphan")

class BattleAnswer(Base):
    __tablename__ = "battle_answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    battle_id = Column(UUID(as_uuid=True), ForeignKey("battles.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    user_answer = Column(String(10))
    is_correct = Column(Boolean)
    response_time_ms = Column(Integer)
    damage_dealt = Column(Integer, default=0)
    damage_received = Column(Integer, default=0)
    critical_hit = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    battle = relationship("Battle", back_populates="battle_answers")
    question = relationship("Question", back_populates="battle_answers") 