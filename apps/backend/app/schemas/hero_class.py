from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

class HeroClassBase(BaseModel):
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    stats_boost: Dict[str, Any] = {}
    special_ability: Optional[str] = None
    element: Optional[str] = None
    color_theme: Optional[str] = None

class HeroClassCreate(HeroClassBase):
    pass

class HeroClassUpdate(HeroClassBase):
    pass

class HeroClassResponse(HeroClassBase):
    id: UUID
    class_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class HeroClassWithStats(HeroClassResponse):
    """Hero class with calculated stats"""
    total_stats: Dict[str, int]
    
    class Config:
        from_attributes = True 