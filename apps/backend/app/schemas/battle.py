from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class BattleBase(BaseModel):
    battle_type: str
    enemy_name: Optional[str] = None
    enemy_level: Optional[int] = None
    enemy_hp: Optional[int] = None

class BattleCreate(BattleBase):
    pass

class BattleResponse(BattleBase):
    id: UUID
    user_id: UUID
    user_hp_start: int
    user_hp_end: int
    questions_answered: int
    correct_answers: int
    total_damage_dealt: int
    total_damage_received: int
    experience_gained: int
    orbs_gained: int
    items_dropped: List[Dict[str, Any]]
    duration_seconds: Optional[int] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BattleAnswer(BaseModel):
    question_id: UUID
    user_answer: str
    response_time_ms: int

class BattleAnswerResponse(BaseModel):
    is_correct: bool
    damage_dealt: int
    damage_received: int
    critical_hit: bool
    experience_gained: int
    orbs_gained: int
    combo_count: int
    user_hp_remaining: int
    enemy_hp_remaining: int 