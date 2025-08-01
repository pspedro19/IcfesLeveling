from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class DailyQuest(Base):
    __tablename__ = "daily_quests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    quest_type = Column(String(50), nullable=False)  # 'battles', 'correct_answers', 'streak'
    target_value = Column(Integer, nullable=False)
    reward_type = Column(String(50), nullable=False)  # 'experience', 'orbs', 'crystals', 'item'
    reward_value = Column(Integer, nullable=False)
    reward_item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_quests = relationship("UserQuest", back_populates="quest", cascade="all, delete-orphan")

class UserQuest(Base):
    __tablename__ = "user_quests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    quest_id = Column(UUID(as_uuid=True), ForeignKey("daily_quests.id"), nullable=False)
    progress = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_quests")
    quest = relationship("DailyQuest", back_populates="user_quests") 