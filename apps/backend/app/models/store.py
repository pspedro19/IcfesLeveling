from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class StoreTransaction(Base):
    __tablename__ = "store_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # 'purchase', 'refund'
    currency_type = Column(String(10), nullable=False)  # 'orbs', 'crystals'
    amount_spent = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="completed")  # 'completed', 'failed', 'refunded'
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="store_transactions")
    item = relationship("Item", back_populates="store_transactions")
    
    def __repr__(self):
        return f"<StoreTransaction(id={self.id}, user_id={self.user_id}, item_id={self.item_id}, amount={self.amount_spent})>"

class UserPowerUp(Base):
    __tablename__ = "user_power_ups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    activated_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    uses_remaining = Column(Integer, default=1)
    effect_data = Column(JSON, default={})
    
    # Relationships
    user = relationship("User", back_populates="user_power_ups")
    item = relationship("Item", back_populates="user_power_ups")
    
    def __repr__(self):
        return f"<UserPowerUp(id={self.id}, user_id={self.user_id}, item_id={self.item_id}, active={self.is_active})>"
    
    def is_expired(self):
        if not self.expires_at:
            return False
        from datetime import datetime
        return datetime.utcnow() > self.expires_at
    
    def can_use(self):
        return self.is_active and not self.is_expired() and self.uses_remaining > 0
    
    def use(self):
        if self.can_use():
            self.uses_remaining -= 1
            if self.uses_remaining <= 0:
                self.is_active = False
            return True
        return False

class CurrencyEarning(Base):
    __tablename__ = "currency_earnings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    currency_type = Column(String(10), nullable=False)  # 'orbs', 'crystals'
    amount = Column(Integer, nullable=False)
    source = Column(String(50), nullable=False)  # 'unit_completion', 'achievement', 'quest', 'battle', 'streak'
    source_id = Column(UUID(as_uuid=True), nullable=True)  # ID of the specific source
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, default={})
    
    # Relationships
    user = relationship("User", back_populates="currency_earnings")
    
    def __repr__(self):
        return f"<CurrencyEarning(id={self.id}, user_id={self.user_id}, currency={self.currency_type}, amount={self.amount})>"
    
    def get_metadata(self):
        return self.metadata_json if self.metadata_json else {} 