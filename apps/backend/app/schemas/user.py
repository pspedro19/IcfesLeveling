from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import re

class UserBase(BaseModel):
    username: str
    email: EmailStr
    display_name: str

class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        description="Password must be at least 8 characters long"
    )

    @validator('password')
    def password_complexity(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[\W_]', v): # At least one special character
            raise ValueError('Password must contain at least one special character')
        return v


class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: UUID
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
    streak_days: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    # Computed properties for Flutter compatibility
    @property
    def name(self) -> str:
        """Alias for display_name - used by Flutter app."""
        return self.display_name or self.username

    @property
    def xp(self) -> int:
        """Alias for experience - used by Flutter app."""
        return self.experience

    @property
    def hearts(self) -> int:
        """Alias for hp - used by Flutter app."""
        return self.hp

    @property
    def current_streak(self) -> int:
        """Alias for streak_days - used by Flutter app."""
        return self.streak_days

    def model_dump(self, **kwargs) -> dict:
        """Override to include computed properties in JSON serialization."""
        data = super().model_dump(**kwargs)
        # Add Flutter-compatible field aliases
        data['name'] = self.name
        data['xp'] = self.xp
        data['hearts'] = self.hearts
        data['current_streak'] = self.current_streak
        return data

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

class GuestData(BaseModel):
    initialScore: float
    questionsAnswered: int
    timeSpent: int
    areasExplored: List[str]

class GuestUserCreate(UserBase):
    password: str
    guestData: GuestData 