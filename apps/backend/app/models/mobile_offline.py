"""
Models for Mobile Offline-First Features
ICFES Leveling Mobile App

Includes:
- UserQuestionHistory: Detailed answer history for adaptive learning
- UserTopicMastery: Topic mastery scores
- PendingAnswerSync: Offline sync queue
- HeartTransaction: Heart usage/regeneration log
- UserDailyActivity: Daily activity tracking
- StreakFreeze: Streak freeze items
- LeagueDivision: League division definitions
- LeagueWeek: Weekly league periods
- LeagueGroup: Groups within leagues
- UserLeague: User participation in leagues
- UserLeagueHistory: Historical league results
- DailyChallenge: Daily challenge definitions
- UserDailyChallenge: User progress on challenges
- UserDeviceToken: Push notification tokens
- NotificationHistory: Notification log
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, Text,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid


# ============================================
# ADAPTIVE LEARNING MODELS
# ============================================

class UserQuestionHistory(Base):
    """Historial detallado de respuestas para Adaptive Learning"""
    __tablename__ = "user_question_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)

    was_correct = Column(Boolean, nullable=False)
    time_spent_seconds = Column(Integer)
    attempt_number = Column(Integer, default=1)

    session_type = Column(String(30))  # 'practice', 'battle', 'simulacro', 'daily_challenge'
    session_id = Column(UUID(as_uuid=True))

    client_timestamp = Column(DateTime(timezone=True))
    synced_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_question_history_user', 'user_id', 'created_at'),
        Index('idx_question_history_question', 'question_id'),
    )


class UserTopicMastery(Base):
    """Puntaje de maestria por tema para algoritmo adaptativo"""
    __tablename__ = "user_topic_mastery"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)

    mastery_score = Column(Float, default=0.0)  # 0.0 to 1.0
    questions_seen = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)

    last_practiced_at = Column(DateTime(timezone=True))
    next_review_at = Column(DateTime(timezone=True))

    consecutive_correct = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def status(self) -> str:
        """Return mastery status based on score"""
        if self.questions_seen == 0:
            return "new"
        elif self.mastery_score < 0.3:
            return "learning"
        elif self.mastery_score < 0.7:
            return "practiced"
        else:
            return "mastered"


# ============================================
# OFFLINE SYNC MODELS
# ============================================

class PendingAnswerSync(Base):
    """Cola de respuestas pendientes de sincronizar"""
    __tablename__ = "pending_answer_sync"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    question_id = Column(UUID(as_uuid=True), nullable=False)
    answer_id = Column(String(50), nullable=False)
    was_correct = Column(Boolean, nullable=False)
    time_spent_seconds = Column(Integer)
    session_type = Column(String(30))
    session_id = Column(UUID(as_uuid=True))

    client_id = Column(String(100))
    client_timestamp = Column(DateTime(timezone=True), nullable=False)

    sync_status = Column(String(20), default='pending')  # 'pending', 'synced', 'failed'
    sync_attempts = Column(Integer, default=0)
    last_sync_attempt = Column(DateTime(timezone=True))
    sync_error = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================
# HEARTS SYSTEM MODELS
# ============================================

class HeartTransaction(Base):
    """Log de transacciones de corazones"""
    __tablename__ = "heart_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    transaction_type = Column(String(30), nullable=False)
    # Types: 'lost', 'regenerated', 'purchased', 'rewarded', 'practice_earned', 'refilled'

    amount = Column(Integer, nullable=False)  # +1 or -1
    hearts_after = Column(Integer, nullable=False)

    source_id = Column(UUID(as_uuid=True))
    source_type = Column(String(30))  # 'battle', 'question', 'ad', 'purchase'

    client_timestamp = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================
# STREAK SYSTEM MODELS
# ============================================

class UserDailyActivity(Base):
    """Actividad diaria detallada para rachas"""
    __tablename__ = "user_daily_activity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_date = Column(Date, nullable=False)

    xp_earned = Column(Integer, default=0)
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)  # Matches DB schema
    study_time_minutes = Column(Integer, default=0)  # Matches DB schema
    session_count = Column(Integer, default=0)  # Matches DB schema
    battles_played = Column(Integer, default=0)  # Matches DB schema
    battles_won = Column(Integer, default=0)  # Matches DB schema

    daily_goal_met = Column(Boolean, default=False)
    streak_extended = Column(Boolean, default=False)

    first_session_at = Column(DateTime(timezone=True))
    last_session_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'activity_date', name='uq_user_daily_activity'),
    )


class StreakFreeze(Base):
    """Streak freezes disponibles para el usuario"""
    __tablename__ = "streak_freezes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    source = Column(String(20), nullable=False)  # 'purchased', 'rewarded', 'premium' - matches DB
    acquired_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True))
    used_for_date = Column(Date)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================
# LEAGUE SYSTEM MODELS
# ============================================

class LeagueDivision(Base):
    """Definicion de divisiones de liga"""
    __tablename__ = "league_divisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(30), nullable=False)
    tier = Column(Integer, nullable=False, unique=True)  # 1=Bronce, 2=Plata, etc.

    icon_url = Column(Text)
    color_hex = Column(String(7))

    min_xp_to_stay = Column(Integer, default=0)
    promotion_spots = Column(Integer, default=10)
    relegation_spots = Column(Integer, default=5)
    demotion_protection = Column(Integer, default=3)

    weekly_gem_reward = Column(Integer, default=0)
    weekly_xp_bonus = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    groups = relationship("LeagueGroup", back_populates="division")


class LeagueWeek(Base):
    """Semanas de competencia de liga"""
    __tablename__ = "league_weeks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_number = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    is_active = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('year', 'week_number', name='uq_league_week'),
    )

    # Relationships
    groups = relationship("LeagueGroup", back_populates="week")


class LeagueGroup(Base):
    """Grupos de liga (30 usuarios por grupo)"""
    __tablename__ = "league_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    league_week_id = Column(UUID(as_uuid=True), ForeignKey("league_weeks.id", ondelete="CASCADE"), nullable=False)
    division_id = Column(UUID(as_uuid=True), ForeignKey("league_divisions.id", ondelete="CASCADE"), nullable=False)

    group_number = Column(Integer, nullable=False)
    max_members = Column(Integer, default=30)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('league_week_id', 'division_id', 'group_number', name='uq_league_group'),
    )

    # Relationships
    week = relationship("LeagueWeek", back_populates="groups")
    division = relationship("LeagueDivision", back_populates="groups")
    members = relationship("UserLeague", back_populates="group")


class UserLeague(Base):
    """Participacion del usuario en liga"""
    __tablename__ = "user_league"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    league_group_id = Column(UUID(as_uuid=True), ForeignKey("league_groups.id", ondelete="CASCADE"), nullable=False)

    weekly_xp = Column(Integer, default=0)
    current_rank = Column(Integer)

    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_xp_update = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'league_group_id', name='uq_user_league'),
    )

    # Relationships
    group = relationship("LeagueGroup", back_populates="members")


class UserLeagueHistory(Base):
    """Historial de resultados de liga"""
    __tablename__ = "user_league_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    league_week_id = Column(UUID(as_uuid=True), ForeignKey("league_weeks.id", ondelete="CASCADE"), nullable=False)
    division_id = Column(UUID(as_uuid=True), ForeignKey("league_divisions.id", ondelete="CASCADE"), nullable=False)

    final_xp = Column(Integer, nullable=False)
    final_rank = Column(Integer, nullable=False)
    total_participants = Column(Integer)

    status = Column(String(20), nullable=False)  # 'promoted', 'relegated', 'stayed'
    gems_earned = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'league_week_id', name='uq_user_league_history'),
    )


# ============================================
# DAILY CHALLENGE MODELS
# ============================================

class DailyChallenge(Base):
    """Definicion de desafios diarios"""
    __tablename__ = "daily_challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    challenge_date = Column(Date, nullable=False)

    title = Column(String(100), nullable=False)
    description = Column(Text)

    challenge_type = Column(String(30), nullable=False)  # 'answer_n', 'streak_n', 'time_n', 'perfect_n'
    target_value = Column(Integer, nullable=False)

    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    difficulty = Column(String(20))  # 'easy', 'medium', 'hard'

    xp_reward = Column(Integer, default=50)
    gem_reward = Column(Integer, default=5)
    bonus_hearts = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserDailyChallenge(Base):
    """Progreso del usuario en desafios diarios"""
    __tablename__ = "user_daily_challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("daily_challenges.id", ondelete="CASCADE"), nullable=False)

    current_progress = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))

    rewards_claimed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'challenge_id', name='uq_user_daily_challenge'),
    )


# ============================================
# PUSH NOTIFICATION MODELS
# ============================================

class UserDeviceToken(Base):
    """Tokens de dispositivo para push notifications"""
    __tablename__ = "user_device_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    device_token = Column(Text, nullable=False, unique=True)
    platform = Column(String(20), nullable=False)  # 'ios', 'android'
    device_info = Column(JSONB)

    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), server_default=func.now())

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NotificationHistory(Base):
    """Historial de notificaciones enviadas"""
    __tablename__ = "notification_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    notification_type = Column(String(50), nullable=False)
    title = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    data = Column(JSONB)

    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    opened_at = Column(DateTime(timezone=True))

    platform = Column(String(20))
    success = Column(Boolean, default=True)
    error_message = Column(Text)
