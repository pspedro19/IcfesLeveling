from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    ACHIEVEMENT = "achievement"
    REMINDER = "reminder"
    BATTLE = "battle"
    PROMOTION = "promotion"
    STUDY_PLAN = "study_plan"
    GUILD = "guild"
    SYSTEM = "system"
    SOCIAL = "social"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationBase(BaseModel):
    type: NotificationType
    title: str = Field(..., max_length=255)
    message: str
    data: Optional[Dict[str, Any]] = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    expires_at: Optional[datetime] = None

class NotificationCreate(NotificationBase):
    user_id: Optional[int] = None  # If None, uses current user

class NotificationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    priority: Optional[NotificationPriority] = None
    expires_at: Optional[datetime] = None

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    read_at: Optional[datetime] = None
    created_at: datetime
    is_read: bool
    is_expired: bool

    class Config:
        from_attributes = True

class NotificationStats(BaseModel):
    total_notifications: int
    unread_count: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    recent_count: int  # Last 24 hours

class BulkNotificationCreate(BaseModel):
    user_ids: list[int]
    notification: NotificationBase