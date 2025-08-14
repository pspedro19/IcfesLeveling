"""
Esquemas Pydantic para el Sistema de Video Learning ICFES
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import re

# =====================================================
# ESQUEMAS BASE
# =====================================================

class VideoProgressBase(BaseModel):
    """Base para progreso de video"""
    user_id: UUID
    video_id: str = Field(..., min_length=11, max_length=11)
    plan_id: UUID
    unit_number: int = Field(..., ge=1)
    codigo_tema: str = Field(..., min_length=1, max_length=50)
    watched_seconds: float = Field(..., ge=0)
    watched_percentage: float = Field(..., ge=0, le=100)
    is_completed: bool = False
    replay_count: int = Field(0, ge=0)
    speed_preference: str = Field("1.0", pattern="^(0\.5|0\.75|1\.0|1\.25|1\.5|2\.0)$")

    @validator('video_id')
    def validate_youtube_id(cls, v):
        """Validar que sea un ID válido de YouTube"""
        if not re.match(r'^[A-Za-z0-9_-]{11}$', v):
            raise ValueError('ID de YouTube inválido')
        return v

    @validator('watched_percentage')
    def validate_percentage(cls, v):
        """Validar porcentaje entre 0 y 100"""
        if not 0 <= v <= 100:
            raise ValueError('Porcentaje debe estar entre 0 y 100')
        return v

class VideoProgressCreate(VideoProgressBase):
    """Esquema para crear progreso de video"""
    pass

class VideoProgressUpdate(BaseModel):
    """Esquema para actualizar progreso de video"""
    watched_seconds: Optional[float] = Field(None, ge=0)
    watched_percentage: Optional[float] = Field(None, ge=0, le=100)
    is_completed: Optional[bool] = None
    replay_count: Optional[int] = Field(None, ge=0)
    speed_preference: Optional[str] = Field(None, pattern="^(0\.5|0\.75|1\.0|1\.25|1\.5|2\.0)$")

class VideoProgress(VideoProgressBase):
    """Esquema completo de progreso de video"""
    id: UUID
    last_watched_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# =====================================================
# ESQUEMAS DE PLANES Y UNIDADES
# =====================================================

class UnitContentBase(BaseModel):
    """Base para contenido de unidad"""
    unit_number: int = Field(..., ge=1)
    codigo_tema: str = Field(..., min_length=1, max_length=50)
    content_type: str = Field(..., pattern="^(video|exercise|quiz)$")
    content_id: str = Field(..., min_length=1, max_length=255)
    video_weight: float = Field(0.33, ge=0, le=1)
    difficulty_level: int = Field(1, ge=1, le=5)
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    prerequisites: Optional[List[str]] = []

class UnitContentCreate(UnitContentBase):
    """Esquema para crear contenido de unidad"""
    pass

class UnitContent(UnitContentBase):
    """Esquema completo de contenido de unidad"""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class PlanProgressBase(BaseModel):
    """Base para progreso de plan"""
    user_id: UUID
    plan_id: UUID
    unit_number: int = Field(..., ge=1)
    weighted_progress: float = Field(0, ge=0, le=100)
    is_completed: bool = False

class PlanProgressCreate(PlanProgressBase):
    """Esquema para crear progreso de plan"""
    pass

class PlanProgress(PlanProgressBase):
    """Esquema completo de progreso de plan"""
    id: UUID
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# =====================================================
# ESQUEMAS DE SEGURIDAD
# =====================================================

class SecurityEventBase(BaseModel):
    """Base para eventos de seguridad"""
    user_id: UUID
    video_id: Optional[str] = Field(None, min_length=11, max_length=11)
    alert_type: str = Field(..., pattern="^(INVALID_HASH|SUSPICIOUS_JUMP|MULTIPLE_TAB_SWITCHES|RATE_LIMIT_EXCEEDED)$")
    severity: str = Field("MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    details: Optional[Dict[str, Any]] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class SecurityEventCreate(SecurityEventBase):
    """Esquema para crear evento de seguridad"""
    pass

class SecurityEvent(SecurityEventBase):
    """Esquema completo de evento de seguridad"""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# =====================================================
# ESQUEMAS DE ANALYTICS
# =====================================================

class VideoAnalyticsBase(BaseModel):
    """Base para analytics de video"""
    video_id: str = Field(..., min_length=11, max_length=11)
    codigo_tema: str = Field(..., min_length=1, max_length=50)
    total_views: int = Field(0, ge=0)
    total_watch_time_seconds: int = Field(0, ge=0)
    average_completion_rate: float = Field(0, ge=0, le=100)
    difficult_segments: Optional[List[Dict[str, Any]]] = []
    learning_style_preferences: Optional[Dict[str, float]] = {}

class VideoAnalyticsCreate(VideoAnalyticsBase):
    """Esquema para crear analytics de video"""
    pass

class VideoAnalytics(VideoAnalyticsBase):
    """Esquema completo de analytics de video"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# =====================================================
# ESQUEMAS DE RECOMENDACIONES
# =====================================================

class VideoRecommendationBase(BaseModel):
    """Base para recomendaciones de video"""
    user_id: UUID
    video_id: str = Field(..., min_length=11, max_length=11)
    codigo_tema: str = Field(..., min_length=1, max_length=50)
    recommendation_reason: str = Field(..., min_length=1)
    priority: int = Field(1, ge=1, le=5)
    is_watched: bool = False

class VideoRecommendationCreate(VideoRecommendationBase):
    """Esquema para crear recomendación de video"""
    pass

class VideoRecommendation(VideoRecommendationBase):
    """Esquema completo de recomendación de video"""
    id: UUID
    recommended_at: datetime
    watched_at: Optional[datetime]

    class Config:
        from_attributes = True

# =====================================================
# ESQUEMAS DE ENGAGEMENT
# =====================================================

class EngagementMetricsBase(BaseModel):
    """Base para métricas de engagement"""
    user_id: UUID
    session_id: str = Field(..., min_length=1, max_length=255)
    current_video_id: Optional[str] = Field(None, min_length=11, max_length=11)
    engagement_score: float = Field(0, ge=0, le=100)
    focus_time_seconds: int = Field(0, ge=0)
    tab_switches: int = Field(0, ge=0)
    is_active: bool = True

class EngagementMetricsCreate(EngagementMetricsBase):
    """Esquema para crear métricas de engagement"""
    pass

class EngagementMetrics(EngagementMetricsBase):
    """Esquema completo de métricas de engagement"""
    id: UUID
    last_activity: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# =====================================================
# ESQUEMAS DE RESPUESTA
# =====================================================

class VideoProgressResponse(BaseModel):
    """Respuesta de progreso de video"""
    status: str = "success"
    message: str
    data: VideoProgress
    xp_earned: int = 0
    security_warnings: Optional[List[str]] = []

class VideoAnalyticsResponse(BaseModel):
    """Respuesta de analytics de video"""
    status: str = "success"
    data: VideoAnalytics
    insights: List[str] = []
    recommendations: List[str] = []

class EngagementResponse(BaseModel):
    """Respuesta de engagement"""
    status: str = "success"
    engagement_score: float
    focus_time_minutes: float
    tab_switches: int
    warnings: List[str] = []

class VideoRecommendationResponse(BaseModel):
    """Respuesta de recomendación de video"""
    status: str = "success"
    video_id: str
    reason: str
    estimated_time: int
    difficulty_adjustment: float
    next_videos: List[str] = []

# =====================================================
# ESQUEMAS DE VALIDACIÓN
# =====================================================

class VideoValidationRequest(BaseModel):
    """Request para validar progreso de video"""
    user_id: UUID
    video_id: str
    current_time: float
    validation_hash: str
    session_data: Dict[str, Any] = {}

class VideoSecurityCheck(BaseModel):
    """Request para verificación de seguridad"""
    user_id: UUID
    video_id: str
    action_type: str = Field(..., pattern="^(play|pause|seek|complete|replay)$")
    timestamp: datetime
    metadata: Dict[str, Any] = {}

# =====================================================
# ESQUEMAS DE CONFIGURACIÓN
# =====================================================

class VideoPlayerConfig(BaseModel):
    """Configuración del reproductor de video"""
    autoplay: bool = False
    controls: bool = True
    modestbranding: bool = True
    rel: int = 0
    showinfo: int = 0
    iv_load_policy: int = 3
    cc_load_policy: int = 1
    playsinline: int = 1
    enablejsapi: int = 1
    origin: str = "http://localhost:3000"

class SecurityConfig(BaseModel):
    """Configuración de seguridad"""
    max_tab_switches: int = 3
    max_time_jump_seconds: int = 60
    rate_limit_updates_per_minute: int = 20
    engagement_threshold: float = 0.5
    suspicious_behavior_threshold: int = 5

# =====================================================
# ESQUEMAS DE ESTADÍSTICAS
# =====================================================

class UserVideoStats(BaseModel):
    """Estadísticas de video del usuario"""
    total_videos_watched: int
    total_watch_time_hours: float
    average_completion_rate: float
    favorite_topics: List[str]
    learning_streak_days: int
    xp_earned: int
    level: int
    next_level_xp: int

class VideoHeatmapData(BaseModel):
    """Datos de mapa de calor de video"""
    video_id: str
    segments: List[Dict[str, Any]]
    total_views: int
    average_replay_rate: float
    difficult_segments: List[Dict[str, Any]]

# =====================================================
# ESQUEMAS DE NOTIFICACIONES
# =====================================================

class VideoNotification(BaseModel):
    """Notificación relacionada con video"""
    type: str = Field(..., pattern="^(milestone|completion|recommendation|security|achievement)$")
    title: str
    message: str
    video_id: Optional[str] = None
    codigo_tema: Optional[str] = None
    priority: str = "normal"
    action_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# =====================================================
# ESQUEMAS DE ERRORES
# =====================================================

class VideoLearningError(BaseModel):
    """Error del sistema de video learning"""
    error_code: str
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[UUID] = None
    video_id: Optional[str] = None

# =====================================================
# ESQUEMAS DE WEBHOOK
# =====================================================

class VideoWebhookPayload(BaseModel):
    """Payload para webhooks de video"""
    event_type: str
    user_id: UUID
    video_id: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signature: Optional[str] = None

# =====================================================
# ESQUEMAS DE BATCH OPERATIONS
# =====================================================

class BatchVideoProgressUpdate(BaseModel):
    """Actualización en lote de progreso de videos"""
    updates: List[VideoProgressCreate]
    batch_id: str
    user_id: UUID
    session_id: str

class BatchVideoProgressResponse(BaseModel):
    """Respuesta de actualización en lote"""
    status: str
    batch_id: str
    processed_count: int
    success_count: int
    error_count: int
    errors: List[Dict[str, Any]] = []
    xp_total_earned: int = 0
