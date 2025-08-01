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
    
    # Relationships
    user_items = relationship("UserItem", back_populates="item", cascade="all, delete-orphan")

class UserItem(Base):
    __tablename__ = "user_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False)
    quantity = Column(Integer, default=1)
    equipped = Column(Boolean, default=False)
    acquired_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_items")
    item = relationship("Item", back_populates="user_items") 