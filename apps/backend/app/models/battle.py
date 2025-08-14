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
    battle_type = Column(String(50), nullable=False)  # 'dungeon', 'tower', 'pvp', 'boss'
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
    
    # Campos para bosses temáticos
    is_boss_battle = Column(Boolean, default=False)
    unit_number = Column(Integer)  # Unidad asociada al boss
    boss_narrative = Column(Text)  # Narrativa del boss
    epic_rewards = Column(JSON, default=[])  # Recompensas épicas
    certificate_generated = Column(Boolean, default=False)  # Certificado de dominio
    
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
    question = relationship("Question")

class Certificate(Base):
    __tablename__ = "certificates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    unit_number = Column(Integer, nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    battle_id = Column(UUID(as_uuid=True), ForeignKey("battles.id"), nullable=False)
    certificate_data = Column(JSON, nullable=False)  # Datos del certificado
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    subject = relationship("Subject")
    battle = relationship("Battle") 