from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas.video_tracking import (
    VideoTrackingCreate,
    VideoTrackingUpdate,
    VideoProgressUpdate,
    VideoRecommendation,
    UnitVideoContent,
    VideoAnalytics,
    VideoTrackingResponse
)
from ..services.video_service import VideoService
from ..models.user import User
from ..models.video_tracking import VideoTracking

router = APIRouter(prefix="/videos", tags=["videos"])

@router.post("/tracking", response_model=VideoTrackingResponse)
async def create_video_tracking(
    tracking_data: VideoTrackingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear un nuevo registro de tracking de video"""
    try:
        video_service = VideoService(db)
        video_tracking = video_service.create_video_tracking(str(current_user.id), tracking_data)
        
        return VideoTrackingResponse(
            id=str(video_tracking.id),
            user_id=str(video_tracking.user_id),
            plan_id=str(video_tracking.plan_id),
            unit_number=video_tracking.unit_number,
            youtube_url=video_tracking.youtube_url,
            video_title=video_tracking.video_title,
            video_duration_seconds=video_tracking.video_duration_seconds,
            watched_seconds=video_tracking.watched_seconds,
            watch_percentage=float(video_tracking.watch_percentage),
            is_completed=video_tracking.is_completed,
            completion_threshold=float(video_tracking.completion_threshold),
            last_watched_at=video_tracking.last_watched_at,
            created_at=video_tracking.created_at,
            updated_at=video_tracking.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando tracking de video: {str(e)}")

@router.post("/progress", response_model=VideoTrackingResponse)
async def update_video_progress(
    progress_data: VideoProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar progreso de visualización de un video"""
    try:
        video_service = VideoService(db)
        video_tracking = video_service.update_video_progress(str(current_user.id), progress_data)
        
        return VideoTrackingResponse(
            id=str(video_tracking.id),
            user_id=str(video_tracking.user_id),
            plan_id=str(video_tracking.plan_id),
            unit_number=video_tracking.unit_number,
            youtube_url=video_tracking.youtube_url,
            video_title=video_tracking.video_title,
            video_duration_seconds=video_tracking.video_duration_seconds,
            watched_seconds=video_tracking.watched_seconds,
            watch_percentage=float(video_tracking.watch_percentage),
            is_completed=video_tracking.is_completed,
            completion_threshold=float(video_tracking.completion_threshold),
            last_watched_at=video_tracking.last_watched_at,
            created_at=video_tracking.created_at,
            updated_at=video_tracking.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando progreso de video: {str(e)}")

@router.get("/unit-content/{plan_id}/{unit_number}", response_model=UnitVideoContent)
async def get_unit_video_content(
    plan_id: str,
    unit_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener contenido de videos de una unidad específica"""
    try:
        video_service = VideoService(db)
        unit_content = video_service.get_unit_video_content(str(current_user.id), plan_id, unit_number)
        return unit_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo contenido de videos: {str(e)}")

@router.get("/recommendations", response_model=List[VideoRecommendation])
async def get_video_recommendations(
    subject: str = Query(..., description="Materia para recomendaciones"),
    limit: int = Query(5, ge=1, le=20, description="Número máximo de recomendaciones"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener recomendaciones de videos relacionados"""
    try:
        video_service = VideoService(db)
        recommendations = video_service.get_video_recommendations(str(current_user.id), subject, limit)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo recomendaciones: {str(e)}")

@router.get("/analytics", response_model=VideoAnalytics)
async def get_video_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener analytics de videos del usuario"""
    try:
        video_service = VideoService(db)
        analytics = video_service.get_video_analytics(str(current_user.id))
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo analytics: {str(e)}")

@router.get("/embed-url")
async def get_youtube_embed_url(
    youtube_url: str = Query(..., description="URL de YouTube"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener URL de embed para un video de YouTube"""
    try:
        video_service = VideoService(db)
        embed_url = video_service.get_youtube_embed_url(youtube_url)
        return {"embed_url": embed_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo URL de embed: {str(e)}")

@router.get("/metadata")
async def get_video_metadata(
    youtube_url: str = Query(..., description="URL de YouTube"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener metadata de un video de YouTube"""
    try:
        video_service = VideoService(db)
        metadata = video_service.get_video_metadata(youtube_url)
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo metadata: {str(e)}") 