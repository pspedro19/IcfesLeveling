from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from ..core.database import Base

class NotificationType(enum.Enum):
    ACHIEVEMENT = "achievement"
    REMINDER = "reminder" 
    BATTLE = "battle"
    PROMOTION = "promotion"
    STUDY_PLAN = "study_plan"
    GUILD = "guild"
    SYSTEM = "system"
    SOCIAL = "social"

class NotificationPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(Enum(NotificationType), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Additional data as JSON
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # Status fields
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    
    # Relationships
    #     user = relationship("User", )

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type.value}, title='{self.title}')>"

    @property
    def is_read(self) -> bool:
        return self.read_at is not None
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "priority": self.priority.value,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_read": self.is_read,
            "is_expired": self.is_expired
        }