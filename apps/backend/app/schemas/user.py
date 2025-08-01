from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    username: str
    email: EmailStr
    display_name: str

class UserCreate(UserBase):
    password: str

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

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None 