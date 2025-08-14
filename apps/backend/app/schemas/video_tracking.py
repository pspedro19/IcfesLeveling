from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class VideoTrackingCreate(BaseModel):
    plan_id: str = Field(..., description="ID del plan de estudio")
    unit_number: int = Field(..., ge=1, description="Número de unidad")
    youtube_url: str = Field(..., description="URL del video de YouTube")
    video_title: Optional[str] = Field(None, description="Título del video")
    video_duration_seconds: Optional[int] = Field(None, ge=0, description="Duración del video en segundos")
    completion_threshold: Optional[float] = Field(80.0, ge=0, le=100, description="Porcentaje mínimo para completar")

class VideoTrackingUpdate(BaseModel):
    watched_seconds: Optional[int] = Field(None, ge=0, description="Segundos vistos")
    watch_percentage: Optional[float] = Field(None, ge=0, le=100, description="Porcentaje visto")
    is_completed: Optional[bool] = Field(None, description="¿Está completado?")

class VideoTrackingResponse(BaseModel):
    id: str
    user_id: str
    plan_id: str
    unit_number: int
    youtube_url: str
    video_title: Optional[str]
    video_duration_seconds: Optional[int]
    watched_seconds: int
    watch_percentage: float
    is_completed: bool
    completion_threshold: float
    last_watched_at: datetime
    created_at: datetime
    updated_at: datetime

class VideoProgressUpdate(BaseModel):
    plan_id: str = Field(..., description="ID del plan")
    unit_number: int = Field(..., ge=1, description="Número de unidad")
    youtube_url: str = Field(..., description="URL del video")
    watched_seconds: int = Field(..., ge=0, description="Segundos vistos")
    video_duration_seconds: Optional[int] = Field(None, ge=0, description="Duración total del video")

class VideoRecommendation(BaseModel):
    youtube_url: str
    video_title: str
    video_description: Optional[str]
    thumbnail_url: Optional[str]
    duration_seconds: Optional[int]
    relevance_score: float = Field(..., ge=0, le=1, description="Puntuación de relevancia")

class UnitVideoContent(BaseModel):
    videos: List[dict] = Field(default_factory=list, description="Lista de videos de la unidad")
    total_videos: int = Field(0, description="Total de videos en la unidad")
    completed_videos: int = Field(0, description="Videos completados")
    total_watch_time: int = Field(0, description="Tiempo total de visualización en segundos")

    @validator('videos', pre=True)
    def validate_videos(cls, v):
        if isinstance(v, list):
            return v
        return []

class VideoAnalytics(BaseModel):
    total_videos_watched: int
    total_watch_time_minutes: int
    average_completion_rate: float
    most_watched_subjects: List[dict]
    weekly_progress: List[dict]
    completion_trend: List[dict] 