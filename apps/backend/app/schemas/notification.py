from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, time
from enum import Enum
from uuid import UUID

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


# ============================================
# Push Notification Schemas (FCM)
# ============================================

class Platform(str, Enum):
    """Supported mobile platforms for push notifications."""
    IOS = "ios"
    ANDROID = "android"


class DeviceInfo(BaseModel):
    """Device information for push notification registration."""
    model: Optional[str] = Field(None, description="Device model (e.g., 'iPhone 14 Pro')")
    os_version: Optional[str] = Field(None, description="OS version (e.g., '16.0')")
    app_version: Optional[str] = Field(None, description="App version (e.g., '1.0.0')")
    manufacturer: Optional[str] = Field(None, description="Device manufacturer")


class RegisterDeviceRequest(BaseModel):
    """Request schema for registering FCM device token."""
    token: str = Field(..., min_length=10, description="FCM device token")
    platform: Platform = Field(..., description="Device platform (ios or android)")
    device_info: Optional[DeviceInfo] = Field(None, description="Optional device information")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "dM3kQ5v8R9e:APA91bFqGh...",
                "platform": "android",
                "device_info": {
                    "model": "Samsung Galaxy S23",
                    "os_version": "14",
                    "app_version": "1.0.0"
                }
            }
        }


class RegisterDeviceResponse(BaseModel):
    """Response schema for device registration."""
    registered: bool = Field(..., description="Whether registration was successful")
    message: Optional[str] = Field(None, description="Additional information")


class NotificationPreferences(BaseModel):
    """User notification preferences schema."""
    # Streak reminders
    streak_reminder_6pm: bool = Field(True, description="6 PM streak at risk reminder")
    streak_reminder_9pm: bool = Field(True, description="9 PM streak at risk reminder")
    streak_reminder_330am: bool = Field(True, description="3:30 AM last chance reminder")

    # Heart/Mana notifications
    hearts_refilled: bool = Field(True, description="Notification when hearts are refilled")

    # League notifications
    league_updates: bool = Field(True, description="League promotion/relegation notifications")

    # Event notifications
    boss_raid_starting: bool = Field(True, description="Boss raid event starting notification")

    # Daily goal notifications
    daily_goal_reminder: bool = Field(True, description="Daily goal reminder")
    daily_goal_achieved: bool = Field(True, description="Daily goal achieved notification")

    # Achievement notifications
    achievement_unlocked: bool = Field(True, description="Achievement unlocked notification")

    # Level up notifications
    level_up: bool = Field(True, description="Level up notification")

    # Weekly summary
    weekly_summary: bool = Field(True, description="Weekly progress summary")

    # Quiet hours (no notifications during these hours)
    quiet_hours_enabled: bool = Field(False, description="Enable quiet hours")
    quiet_hours_start: Optional[str] = Field(
        "22:00",
        description="Quiet hours start time (HH:MM format)",
        pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    quiet_hours_end: Optional[str] = Field(
        "08:00",
        description="Quiet hours end time (HH:MM format)",
        pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "streak_reminder_6pm": True,
                "streak_reminder_9pm": True,
                "streak_reminder_330am": False,
                "hearts_refilled": True,
                "league_updates": True,
                "boss_raid_starting": True,
                "daily_goal_reminder": True,
                "daily_goal_achieved": True,
                "achievement_unlocked": True,
                "level_up": True,
                "weekly_summary": True,
                "quiet_hours_enabled": True,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "08:00"
            }
        }


class NotificationPreferencesResponse(BaseModel):
    """Response schema for notification preferences."""
    user_id: UUID
    preferences: NotificationPreferences
    updated_at: datetime

    class Config:
        from_attributes = True


class UnregisterDeviceRequest(BaseModel):
    """Request schema for unregistering device token."""
    token: Optional[str] = Field(None, description="Specific token to unregister, or None for all")


class SendNotificationRequest(BaseModel):
    """Request schema for sending a push notification (admin use)."""
    user_id: UUID = Field(..., description="Target user ID")
    template: str = Field(..., description="Notification template name")
    data: Optional[Dict[str, Any]] = Field(None, description="Template variables")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "template": "streak_at_risk_6pm",
                "data": {"streak": 7}
            }
        }


class SendNotificationResponse(BaseModel):
    """Response schema for sending a push notification."""
    success: bool
    message: str