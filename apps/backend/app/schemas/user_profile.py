from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserProfileResponse(BaseModel):
    user_id: str
    display_name: str
    avatar_url: Optional[str] = None
    hero_class: str
    level: int
    experience: int
    rank: str
    hp: int
    mp: int
    power: int
    wisdom: int
    speed: int
    orbs: int
    crystals: int
    premium_status: str
    premium_until: Optional[datetime] = None
    streak_days: int
    last_login: Optional[datetime] = None
    achievements_count: int
    battles_won: int
    battles_lost: int
    questions_answered: int
    correct_answers: int
    guild_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    hero_class: Optional[str] = None
    level: Optional[int] = None
    experience: Optional[int] = None
    rank: Optional[str] = None
    hp: Optional[int] = None
    mp: Optional[int] = None
    power: Optional[int] = None
    wisdom: Optional[int] = None
    speed: Optional[int] = None
    orbs: Optional[int] = None
    crystals: Optional[int] = None
    premium_status: Optional[str] = None
    premium_until: Optional[datetime] = None
    streak_days: Optional[int] = None
    last_login: Optional[datetime] = None
    achievements_count: Optional[int] = None
    battles_won: Optional[int] = None
    battles_lost: Optional[int] = None
    questions_answered: Optional[int] = None
    correct_answers: Optional[int] = None
    guild_id: Optional[str] = None 