"""
Economy Models
Database models for tracking gold and XP transactions.
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base
import uuid


class GoldTransaction(Base):
    """
    Tracks all gold transactions (earning and spending).
    Used for transaction history and auditing.
    """
    __tablename__ = "gold_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # Positive for earning, negative for spending
    balance_after = Column(Integer, nullable=False)  # Balance after transaction
    transaction_type = Column(String(50), nullable=False)  # 'quest_reward', 'purchase', 'streak_bonus', etc.
    description = Column(Text, nullable=True)
    reference_id = Column(UUID(as_uuid=True), nullable=True)  # Optional reference to related entity
    reference_type = Column(String(50), nullable=True)  # 'quest', 'item', 'achievement', etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<GoldTransaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type={self.transaction_type})>"


class XPTransaction(Base):
    """
    Tracks all XP changes including source information.
    Used for analytics and level-up history.
    """
    __tablename__ = "xp_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # XP gained (always positive)
    total_xp_after = Column(Integer, nullable=False)  # Total XP after transaction
    level_before = Column(Integer, nullable=False)
    level_after = Column(Integer, nullable=False)
    leveled_up = Column(Integer, default=0)  # Number of levels gained (0 if no level up)
    source = Column(String(50), nullable=False)  # 'question_correct', 'quest_complete', 'achievement', etc.
    source_id = Column(UUID(as_uuid=True), nullable=True)  # Optional reference to source entity
    multiplier = Column(Float, default=1.0)  # XP multiplier applied (for boosts)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<XPTransaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, source={self.source})>"
