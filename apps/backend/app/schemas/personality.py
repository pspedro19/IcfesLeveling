from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID

class PersonalityQuestionBase(BaseModel):
    question_text: str
    question_type: str
    options: Dict[str, str]
    weight_factors: Dict[str, Any] = {}
    order_index: int
    is_active: bool = True

class PersonalityQuestionCreate(PersonalityQuestionBase):
    pass

class PersonalityQuestionUpdate(PersonalityQuestionBase):
    pass

class PersonalityQuestionResponse(PersonalityQuestionBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class PersonalityTestRequest(BaseModel):
    user_id: str
    answers: Dict[str, str]  # question_type -> answer

class PersonalityTestResponse(BaseModel):
    hero_class: Dict[str, Any]
    personality_answers: Dict[str, str]
    cutscene_data: Dict[str, Any]
    stats_boost: Dict[str, int]

class UserProfileBase(BaseModel):
    personality_answers: Optional[Dict[str, str]] = None
    avatar_customization: Dict[str, Any] = {}

class UserProfileCreate(UserProfileBase):
    user_id: UUID
    hero_class_id: UUID

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    id: UUID
    user_id: UUID
    hero_class_id: UUID
    assigned_at: datetime
    hero_class: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True 