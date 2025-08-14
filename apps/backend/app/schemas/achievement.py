from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class AchievementCategory(str, Enum):
    UNIT_COMPLETION = "unit_completion"
    SCORE_IMPROVEMENT = "score_improvement"
    STUDY_STREAK = "study_streak"
    SECRET = "secret"

class AchievementType(str, Enum):
    SINGLE = "single"
    PROGRESSIVE = "progressive"
    MILESTONE = "milestone"

class AchievementRarity(str, Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

class AchievementBase(BaseModel):
    title: str = Field(..., description="Achievement title")
    description: Optional[str] = Field(None, description="Achievement description")
    category: AchievementCategory = Field(..., description="Achievement category")
    achievement_type: AchievementType = Field(..., description="Achievement type")
    icon_url: Optional[str] = Field(None, description="Icon URL")
    rarity: AchievementRarity = Field(AchievementRarity.COMMON, description="Achievement rarity")
    points: int = Field(10, description="Points awarded")
    requirements: Dict[str, Any] = Field(default_factory=dict, description="Requirements structure")
    is_secret: bool = Field(False, description="Is secret achievement")

class AchievementCreate(AchievementBase):
    pass

class AchievementResponse(AchievementBase):
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserAchievementBase(BaseModel):
    progress: int = Field(0, description="Current progress")
    is_unlocked: bool = Field(False, description="Is achievement unlocked")
    unlocked_at: Optional[datetime] = Field(None, description="When unlocked")
    progress_data: Dict[str, Any] = Field(default_factory=dict, description="Detailed progress data")

class UserAchievementCreate(UserAchievementBase):
    user_id: str
    achievement_id: str

class UserAchievementResponse(UserAchievementBase):
    id: str
    user_id: str
    achievement_id: str
    created_at: datetime
    achievement: AchievementResponse
    progress_percentage: float = Field(0, description="Progress percentage")
    
    class Config:
        from_attributes = True

class AchievementProgress(BaseModel):
    achievement_id: str
    progress: int
    target: int
    percentage: float
    is_unlocked: bool

class UserAchievementSummary(BaseModel):
    total_achievements: int
    unlocked_achievements: int
    total_points: int
    secret_achievements_found: int
    achievements_by_category: Dict[str, int]
    recent_achievements: List[UserAchievementResponse]

class AchievementUnlockRequest(BaseModel):
    achievement_id: str
    progress_increment: int = Field(1, description="Progress increment")

class AchievementProgressUpdate(BaseModel):
    category: Optional[AchievementCategory] = Field(None, description="Category to update")
    value: int = Field(1, description="Value to increment")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class AchievementShowcase(BaseModel):
    user_id: str
    display_name: str
    avatar_url: Optional[str]
    total_points: int
    unlocked_achievements: int
    rarest_achievement: Optional[UserAchievementResponse]
    recent_achievements: List[UserAchievementResponse]
    achievements_by_rarity: Dict[str, int] 