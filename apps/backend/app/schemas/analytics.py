"""
Analytics schemas for event tracking and reporting.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AnalyticsPeriod(str, Enum):
    """Time period for analytics queries."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class EventTrackRequest(BaseModel):
    """Request to track a single analytics event."""
    event_type: str = Field(..., description="Type of event (e.g., 'question_answered', 'video_watched')")
    event_data: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    timestamp: Optional[datetime] = Field(default=None, description="Event timestamp (defaults to now)")
    session_id: Optional[str] = Field(default=None, description="Session identifier")


class BatchEventTrackRequest(BaseModel):
    """Request to track multiple analytics events."""
    events: List[EventTrackRequest] = Field(..., description="List of events to track")


class UserAnalyticsResponse(BaseModel):
    """User-specific analytics summary."""
    user_id: str
    total_questions_answered: int = 0
    correct_answers: int = 0
    accuracy_rate: float = 0.0
    total_study_time_minutes: int = 0
    videos_watched: int = 0
    sessions_count: int = 0
    streak_days: int = 0
    subjects_studied: List[str] = Field(default_factory=list)
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)
    period: AnalyticsPeriod = AnalyticsPeriod.WEEK


class GlobalAnalyticsResponse(BaseModel):
    """Global platform analytics summary."""
    total_users: int = 0
    active_users_today: int = 0
    active_users_week: int = 0
    total_questions_answered: int = 0
    average_accuracy: float = 0.0
    popular_subjects: List[Dict[str, Any]] = Field(default_factory=list)
    user_growth_rate: float = 0.0
    period: AnalyticsPeriod = AnalyticsPeriod.WEEK
