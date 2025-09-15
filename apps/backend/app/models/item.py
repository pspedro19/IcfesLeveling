from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class Item(Base):
    __tablename__ = "items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    item_type = Column(String(50), nullable=False)  # 'consumable', 'cosmetic', 'pet'
    rarity = Column(String(20), default="common")  # 'common', 'rare', 'epic', 'legendary'
    icon_url = Column(String(500))
    effects = Column(JSON, default={})
    drop_rate = Column(Numeric(5, 4), default=0.01)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Store fields
    store_price_orbs = Column(Integer, default=0)
    store_price_crystals = Column(Integer, default=0)
    is_available_in_store = Column(Boolean, default=False)
    is_cosmetic = Column(Boolean, default=False)
    is_power_up = Column(Boolean, default=False)
    power_up_effect = Column(JSON, default={})
    
    # Relationships
    user_items = relationship("UserItem", cascade="all, delete-orphan")
    store_transactions = relationship("StoreTransaction", cascade="all, delete-orphan")
    user_power_ups = relationship("UserPowerUp", cascade="all, delete-orphan")

class UserItem(Base):
    __tablename__ = "user_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False)
    quantity = Column(Integer, default=1)
    equipped = Column(Boolean, default=False)
    acquired_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships - Temporalmente comentado para arreglar SQLAlchemy
    # user = relationship("User")
    item = relationship("Item") 