from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class UserEvent(Base):
    __tablename__ = "user_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, default={})
    ip_address = Column(String(45))  # IPv6 max length
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_events") 