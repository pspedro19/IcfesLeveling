from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class QuestionBase(BaseModel):
    question_text: str
    difficulty: int
    correct_answer: str
    options: Dict[str, str]
    explanation: Optional[str] = None
    hint: Optional[str] = None
    tags: Optional[List[str]] = None

class QuestionCreate(QuestionBase):
    topic_id: UUID
    subject_id: UUID

class QuestionResponse(QuestionBase):
    id: UUID
    topic_id: UUID
    subject_id: UUID
    question_type: str
    power_stats: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    difficulty: Optional[int] = None
    correct_answer: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    explanation: Optional[str] = None
    hint: Optional[str] = None
    tags: Optional[List[str]] = None 