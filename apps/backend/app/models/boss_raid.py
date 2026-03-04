"""
Boss Raid Models for ICFES Leveling

Weekly Boss Raid event:
- Available every Sunday from 10 AM to 10 PM (COT - Colombia Time)
- 20 questions per session
- 3x XP multiplier for correct answers
- Collaborative damage to defeat weekly boss
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid


class Boss(Base):
    """Weekly Boss for Boss Raid events"""
    __tablename__ = "bosses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Boss identification
    week_number = Column(Integer, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True)

    # Boss attributes
    name = Column(String(100), nullable=False)
    description = Column(Text)
    hp = Column(Integer, nullable=False, default=10000)
    current_hp = Column(Integer, nullable=False, default=10000)
    difficulty = Column(String(20), default="hard")  # easy, medium, hard, legendary

    # Boss rewards
    base_xp_reward = Column(Integer, default=100)
    gold_reward = Column(Integer, default=500)

    # Status
    is_defeated = Column(Boolean, default=False)
    defeated_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subject = relationship("Subject")
    raid_sessions = relationship("BossRaidSession", back_populates="boss")

    def __repr__(self):
        return f"<Boss {self.name} (Week {self.week_number}/{self.year})>"


class BossRaidSession(Base):
    """Individual user session in a Boss Raid"""
    __tablename__ = "boss_raid_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    boss_id = Column(UUID(as_uuid=True), ForeignKey("bosses.id"), nullable=False, index=True)

    # Session stats
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    status = Column(String(20), default="in_progress")  # in_progress, completed, abandoned

    # Performance metrics
    total_questions = Column(Integer, default=20)
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_damage = Column(Integer, default=0)
    total_xp_earned = Column(Integer, default=0)
    combo_max = Column(Integer, default=0)
    current_combo = Column(Integer, default=0)

    # Time tracking
    total_time_seconds = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    boss = relationship("Boss", back_populates="raid_sessions")
    answers = relationship("BossRaidAnswer", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BossRaidSession {self.id} User:{self.user_id}>"


class BossRaidAnswer(Base):
    """Individual answer in a Boss Raid session"""
    __tablename__ = "boss_raid_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    session_id = Column(UUID(as_uuid=True), ForeignKey("boss_raid_sessions.id"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)

    # Answer data
    user_answer = Column(String(10))
    correct_answer = Column(String(10))
    is_correct = Column(Boolean, nullable=False)

    # Performance data
    time_spent_seconds = Column(Integer, default=0)
    damage_dealt = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)
    combo_count = Column(Integer, default=0)

    # Timestamps
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("BossRaidSession", back_populates="answers")
    question = relationship("Question")

    def __repr__(self):
        return f"<BossRaidAnswer {self.id} Correct:{self.is_correct}>"


class BossRaidLeaderboard(Base):
    """Leaderboard entry for Boss Raid rankings"""
    __tablename__ = "boss_raid_leaderboard"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    boss_id = Column(UUID(as_uuid=True), ForeignKey("bosses.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Aggregate stats for this boss/user
    total_damage = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    total_xp_earned = Column(Integer, default=0)
    best_combo = Column(Integer, default=0)
    rank = Column(Integer)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    boss = relationship("Boss")
    user = relationship("User")

    def __repr__(self):
        return f"<BossRaidLeaderboard Boss:{self.boss_id} User:{self.user_id} Rank:{self.rank}>"
