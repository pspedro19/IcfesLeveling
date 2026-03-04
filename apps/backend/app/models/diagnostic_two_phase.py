"""
Two-Phase Diagnostic System Models
ICFES Leveling Backend

Phase 1: Quick Diagnostic (15 questions - 3 per subject)
Phase 2: Deep Diagnostic (15-20 questions per subject)

Based on API_CONTRACT.md and BACKEND_TASKS_CLAUDE.md specifications.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, UniqueConstraint, Index, Enum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
import enum


class DiagnosticType(str, enum.Enum):
    """Type of diagnostic test"""
    QUICK = "quick"
    DEEP = "deep"


class DiagnosticStatus(str, enum.Enum):
    """Status of diagnostic test"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class TwoPhaseDignostic(Base):
    """
    Two-Phase Diagnostic Test Model

    Quick: 15 questions (3 per subject) - Initial assessment
    Deep: 15-20 questions per subject - Detailed skill mapping
    """
    __tablename__ = "two_phase_diagnostics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Type of diagnostic: 'quick' or 'deep'
    diagnostic_type = Column(String(20), nullable=False, default="quick")

    # Subject ID - NULL for quick diagnostic (covers all subjects), set for deep diagnostic
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Test metrics
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, default=0)

    # IRT Theta estimate (-3.0 to 3.0)
    theta_estimate = Column(Float, nullable=True)

    # Status: 'in_progress', 'completed', 'abandoned'
    status = Column(String(20), default="in_progress")

    # Results data
    weak_areas = Column(JSONB, default=[])  # List of weak subjects/topics
    skill_tree = Column(JSONB, default={})  # Deep diagnostic skill mapping

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        # Ensure unique quick diagnostic per user (only one quick allowed)
        Index('idx_two_phase_user_type', 'user_id', 'diagnostic_type'),
        # Ensure unique deep diagnostic per user per subject
        Index('idx_two_phase_user_subject', 'user_id', 'subject_id'),
    )

    # Relationships
    answers = relationship(
        "TwoPhaseDiagnosticAnswer",
        back_populates="diagnostic",
        cascade="all, delete-orphan"
    )
    subject = relationship("Subject")


class TwoPhaseDiagnosticAnswer(Base):
    """
    Individual answers for two-phase diagnostic tests
    """
    __tablename__ = "two_phase_diagnostic_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diagnostic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("two_phase_diagnostics.id", ondelete="CASCADE"),
        nullable=False
    )
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)

    # User's answer (A, B, C, D, or E)
    answer_id = Column(String(10), nullable=False)

    # Was the answer correct
    was_correct = Column(Boolean, nullable=False)

    # Time spent on this question in seconds
    time_spent_seconds = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_diagnostic_answer_diag', 'diagnostic_id'),
        UniqueConstraint('diagnostic_id', 'question_id', name='uq_diagnostic_question'),
    )

    # Relationships
    diagnostic = relationship("TwoPhaseDignostic", back_populates="answers")
    question = relationship("Question")


class UserEngagement(Base):
    """
    User engagement tracking for hearts, grace mode, and streak
    Based on BACKEND_TASKS_CLAUDE.md specifications
    """
    __tablename__ = "user_engagement"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Hearts/Mana System (max 5, regen 1 every 4 hours)
    hearts = Column(Integer, default=5)
    max_hearts = Column(Integer, default=5)
    last_heart_used_at = Column(DateTime(timezone=True), nullable=True)
    heart_regen_interval = Column(Integer, default=14400)  # 4 hours in seconds

    # Grace Mode (practice without XP when hearts = 0)
    grace_mode_active = Column(Boolean, default=False)
    grace_mode_started_at = Column(DateTime(timezone=True), nullable=True)

    # Streak tracking
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    previous_streak = Column(Integer, default=0)  # For streak repair
    streak_lost_at = Column(DateTime(timezone=True), nullable=True)  # 24h repair window

    # Daily activity
    today_xp = Column(Integer, default=0)
    weekly_xp = Column(Integer, default=0)
    last_activity_date = Column(DateTime(timezone=True), nullable=True)

    # Economy
    gold = Column(Integer, default=0)

    # Ad tracking
    ad_repairs_today = Column(Integer, default=0)
    ads_watched_today = Column(Integer, default=0)

    # Diagnostic completion flags
    quick_diagnostic_completed = Column(Boolean, default=False)

    # User timezone for streak calculation
    timezone = Column(String(50), default="America/Bogota")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class QuestionAttempt(Base):
    """
    Question attempt tracking for anti-gaming XP system
    Based on BACKEND_TASKS_CLAUDE.md anti-gaming specifications
    """
    __tablename__ = "question_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)

    was_correct = Column(Boolean, nullable=False)
    xp_awarded = Column(Integer, default=0)

    # Type: 'new', 'valid_review', 'invalid_repeat'
    attempt_type = Column(String(20), default="new")

    attempted_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_question_attempts_user_topic', 'user_id', 'topic_id', 'attempted_at'),
        Index('idx_question_attempts_user_question', 'user_id', 'question_id'),
    )


class TopicMastery(Base):
    """
    Topic mastery tracking for adaptive learning
    Based on BACKEND_TASKS_CLAUDE.md specifications
    """
    __tablename__ = "topic_mastery"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)

    # Mastery score from 0.0 to 1.0
    mastery_score = Column(Float, default=0.0)

    questions_seen = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)

    last_practiced_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'topic_id', name='uq_user_topic_mastery'),
    )
