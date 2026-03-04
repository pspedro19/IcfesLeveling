"""
Node Progress Models - User progress through Kingdoms and Nodes
ICFES Leveling - Conquest Mode
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base
import uuid


class UserKingdomProgress(Base):
    """Track user's overall progress in a Kingdom (subject area)"""
    __tablename__ = "user_kingdom_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    kingdom_id = Column(String(50), nullable=False)  # 'math', 'reading', 'science', etc.
    diagnostic_completed = Column(Boolean, default=False)
    overall_mastery = Column(DECIMAL(5, 2), default=0.00)
    rank = Column(String(10), default='E')
    boss_defeated = Column(Boolean, default=False)
    total_stars = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        {'schema': None},  # Use default schema
    )


class UserNodeProgress(Base):
    """Track user's progress on individual nodes within a Kingdom"""
    __tablename__ = "user_node_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    node_id = Column(String(100), nullable=False)  # 'math_node_1', 'reading_node_3'
    kingdom_id = Column(String(50), nullable=False)
    mastery_percent = Column(DECIMAL(5, 2), default=0.00)
    stars_earned = Column(Integer, default=0)  # 0-3 stars
    times_completed = Column(Integer, default=0)
    best_accuracy = Column(DECIMAL(5, 2), default=0.00)
    questions_seen = Column(JSONB, default=[])
    is_unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        {'schema': None},  # Use default schema
    )
