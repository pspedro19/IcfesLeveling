from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from ..core.database import get_db
from ..models.user import User
from ..models.study_plan import StudyPlan
from ..models.video_tracking import VideoTracking
from ..core.security import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/video-tracking", tags=["video-tracking"])
logger = logging.getLogger(__name__)

class VideoProgressUpdate(BaseModel):
    youtube_url: str
    video_title: str
    video_duration_seconds: int
    watched_seconds: int
    watch_percentage: float
    is_completed: bool = False

class VideoTrackingResponse(BaseModel):
    id: str
    user_id: str
    plan_id: str
    unit_number: int
    youtube_url: str
    video_title: str
    video_duration_seconds: int
    watched_seconds: int
    watch_percentage: float
    is_completed: bool
    completion_threshold: float
    last_watched_at: str
    created_at: str

@router.post("/{plan_id}/units/{unit_number}/video-progress")
async def update_video_progress(
    plan_id: str,
    unit_number: int,
    progress: VideoProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza el progreso de un video específico
    """
    try:
        # Verificar que el plan pertenezca al usuario
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id,
            StudyPlan.is_active == True
        ).first()
        
        if not study_plan:
            raise HTTPException(
                status_code=404,
                detail="Plan de estudio no encontrado"
            )
        
        # Buscar tracking existente
        video_tracking = db.query(VideoTracking).filter(
            VideoTracking.user_id == current_user.id,
            VideoTracking.plan_id == plan_id,
            VideoTracking.unit_number == unit_number,
            VideoTracking.youtube_url == progress.youtube_url
        ).first()
        
        if video_tracking:
            # Actualizar tracking existente
            video_tracking.watched_seconds = max(video_tracking.watched_seconds, progress.watched_seconds)
            video_tracking.watch_percentage = max(video_tracking.watch_percentage, progress.watch_percentage)
            video_tracking.video_duration_seconds = progress.video_duration_seconds
            
            # Verificar completación basada en threshold
            if progress.watch_percentage >= video_tracking.completion_threshold:
                video_tracking.is_completed = True
                
        else:
            # Crear nuevo tracking
            video_tracking = VideoTracking(
                user_id=current_user.id,
                plan_id=plan_id,
                unit_number=unit_number,
                youtube_url=progress.youtube_url,
                video_title=progress.video_title,
                video_duration_seconds=progress.video_duration_seconds,
                watched_seconds=progress.watched_seconds,
                watch_percentage=progress.watch_percentage,
                is_completed=progress.watch_percentage >= 80.0,  # Default threshold
                completion_threshold=80.0
            )
            db.add(video_tracking)
        
        db.commit()
        db.refresh(video_tracking)
        
        # Actualizar progreso del plan si es necesario
        await _update_plan_progress(study_plan, db)
        
        return {
            "success": True,
            "message": "Progreso de video actualizado",
            "video_tracking": {
                "id": str(video_tracking.id),
                "watched_seconds": video_tracking.watched_seconds,
                "watch_percentage": video_tracking.watch_percentage,
                "is_completed": video_tracking.is_completed
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating video progress: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error actualizando progreso de video"
        )

@router.get("/{plan_id}/video-progress")
async def get_video_progress(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el progreso de todos los videos de un plan
    """
    try:
        # Verificar que el plan pertenezca al usuario
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id
        ).first()
        
        if not study_plan:
            raise HTTPException(
                status_code=404,
                detail="Plan de estudio no encontrado"
            )
        
        # Obtener todos los trackings de video para este plan
        video_trackings = db.query(VideoTracking).filter(
            VideoTracking.user_id == current_user.id,
            VideoTracking.plan_id == plan_id
        ).all()
        
        # Organizar por unidad y video
        progress_by_unit = {}
        for tracking in video_trackings:
            unit_key = str(tracking.unit_number)
            if unit_key not in progress_by_unit:
                progress_by_unit[unit_key] = {}
            
            progress_by_unit[unit_key][tracking.youtube_url] = {
                "video_title": tracking.video_title,
                "watched_seconds": tracking.watched_seconds,
                "watch_percentage": tracking.watch_percentage,
                "is_completed": tracking.is_completed,
                "last_watched_at": tracking.last_watched_at.isoformat() if tracking.last_watched_at else None
            }
        
        # Calcular estadísticas generales
        total_videos = len(video_trackings)
        completed_videos = sum(1 for t in video_trackings if t.is_completed)
        total_watch_time = sum(t.watched_seconds for t in video_trackings)
        
        return {
            "plan_id": plan_id,
            "progress_by_unit": progress_by_unit,
            "statistics": {
                "total_videos": total_videos,
                "completed_videos": completed_videos,
                "completion_percentage": (completed_videos / total_videos * 100) if total_videos > 0 else 0,
                "total_watch_time_minutes": total_watch_time // 60
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting video progress: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo progreso de videos"
        )

@router.get("/{plan_id}/units/{unit_number}/video-metrics")
async def get_unit_video_metrics(
    plan_id: str,
    unit_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene métricas detalladas de videos para una unidad específica
    """
    try:
        # Verificar que el plan pertenezca al usuario
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id
        ).first()
        
        if not study_plan:
            raise HTTPException(
                status_code=404,
                detail="Plan de estudio no encontrado"
            )
        
        # Obtener trackings de video para esta unidad
        video_trackings = db.query(VideoTracking).filter(
            VideoTracking.user_id == current_user.id,
            VideoTracking.plan_id == plan_id,
            VideoTracking.unit_number == unit_number
        ).all()
        
        if not video_trackings:
            return {
                "unit_number": unit_number,
                "videos": [],
                "metrics": {
                    "total_videos": 0,
                    "completed_videos": 0,
                    "average_completion": 0,
                    "total_watch_time": 0,
                    "engagement_score": 0
                }
            }
        
        # Calcular métricas
        total_videos = len(video_trackings)
        completed_videos = sum(1 for t in video_trackings if t.is_completed)
        average_completion = sum(t.watch_percentage for t in video_trackings) / total_videos
        total_watch_time = sum(t.watched_seconds for t in video_trackings)
        
        # Engagement score basado en completación y tiempo visto
        engagement_score = (
            (completed_videos / total_videos) * 0.6 +
            (average_completion / 100) * 0.4
        ) * 100
        
        videos_detail = []
        for tracking in video_trackings:
            videos_detail.append({
                "youtube_url": tracking.youtube_url,
                "video_title": tracking.video_title,
                "duration_seconds": tracking.video_duration_seconds,
                "watched_seconds": tracking.watched_seconds,
                "watch_percentage": tracking.watch_percentage,
                "is_completed": tracking.is_completed,
                "last_watched_at": tracking.last_watched_at.isoformat() if tracking.last_watched_at else None,
                "engagement_level": "high" if tracking.watch_percentage > 80 else "medium" if tracking.watch_percentage > 50 else "low"
            })
        
        return {
            "unit_number": unit_number,
            "videos": videos_detail,
            "metrics": {
                "total_videos": total_videos,
                "completed_videos": completed_videos,
                "completion_percentage": (completed_videos / total_videos * 100) if total_videos > 0 else 0,
                "average_completion": round(average_completion, 2),
                "total_watch_time_seconds": total_watch_time,
                "total_watch_time_minutes": total_watch_time // 60,
                "engagement_score": round(engagement_score, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting unit video metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo métricas de videos"
        )

async def _update_plan_progress(study_plan: StudyPlan, db: Session):
    """
    Actualiza el progreso general del plan basado en videos y ejercicios completados
    """
    try:
        # Obtener todos los trackings de video del plan
        video_trackings = db.query(VideoTracking).filter(
            VideoTracking.plan_id == study_plan.id,
            VideoTracking.user_id == study_plan.user_id
        ).all()
        
        # Calcular progreso basado en videos completados
        # En una implementación completa, también incluirías ejercicios
        if video_trackings:
            completed_videos = sum(1 for t in video_trackings if t.is_completed)
            video_progress = (completed_videos / len(video_trackings)) * 100
            
            # Actualizar progreso del plan (simplificado)
            study_plan.progress_percentage = min(video_progress, 100.0)
            db.commit()
            
    except Exception as e:
        logger.error(f"Error updating plan progress: {e}")

@router.delete("/{plan_id}/video-progress")
async def reset_video_progress(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reinicia el progreso de videos de un plan (para testing o reinicio)
    """
    try:
        # Verificar que el plan pertenezca al usuario
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id
        ).first()
        
        if not study_plan:
            raise HTTPException(
                status_code=404,
                detail="Plan de estudio no encontrado"
            )
        
        # Eliminar todos los trackings de video
        deleted_count = db.query(VideoTracking).filter(
            VideoTracking.plan_id == plan_id,
            VideoTracking.user_id == current_user.id
        ).delete()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Progreso de {deleted_count} videos reiniciado",
            "deleted_trackings": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error resetting video progress: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error reiniciando progreso de videos"
        )