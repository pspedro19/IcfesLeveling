"""
YouTube API Routes
Endpoints para funcionalidades avanzadas de YouTube API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..services.video_service import VideoService
from ..services.youtube_api_service import YouTubeAPIService
from ..models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/youtube", tags=["YouTube API"])

@router.get("/recommendations/personalized")
async def get_personalized_video_recommendations(
    subject: str = Query(..., description="Materia para buscar videos"),
    weak_topics: Optional[str] = Query(None, description="Temas débiles separados por coma"),
    difficulty_level: Optional[int] = Query(3, ge=1, le=5, description="Nivel de dificultad (1-5)"),
    limit: int = Query(10, ge=1, le=50, description="Número máximo de videos"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener recomendaciones personalizadas de videos basadas en el perfil del usuario
    """
    try:
        video_service = VideoService(db)
        
        # Parsear temas débiles
        weak_topics_list = None
        if weak_topics:
            weak_topics_list = [topic.strip() for topic in weak_topics.split(",")]
        
        recommendations = video_service.get_personalized_video_recommendations(
            user_id=str(current_user.id),
            subject=subject,
            weak_topics=weak_topics_list,
            difficulty_level=difficulty_level,
            limit=limit
        )
        
        return {
            "success": True,
            "data": {
                "recommendations": [rec.dict() for rec in recommendations],
                "total": len(recommendations),
                "filters": {
                    "subject": subject,
                    "weak_topics": weak_topics_list,
                    "difficulty_level": difficulty_level,
                    "limit": limit
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones personalizadas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/search")
async def search_educational_videos(
    query: str = Query(..., description="Término de búsqueda"),
    subject: Optional[str] = Query(None, description="Materia para filtrar"),
    max_results: int = Query(10, ge=1, le=50, description="Número máximo de resultados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Buscar videos educativos usando YouTube API
    """
    try:
        video_service = VideoService(db)
        
        videos = video_service.search_educational_videos(
            query=query,
            subject=subject,
            max_results=max_results
        )
        
        return {
            "success": True,
            "data": {
                "videos": [video.dict() for video in videos],
                "total": len(videos),
                "search_params": {
                    "query": query,
                    "subject": subject,
                    "max_results": max_results
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error buscando videos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/video/{video_id}/info")
async def get_video_detailed_info(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener información detallada de un video específico
    """
    try:
        youtube_api = YouTubeAPIService(db)
        
        video_info = youtube_api.get_video_info(video_id)
        if not video_info:
            raise HTTPException(status_code=404, detail="Video no encontrado")
        
        return {
            "success": True,
            "data": video_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo información del video: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/playlist/{playlist_id}/videos")
async def get_playlist_videos(
    playlist_id: str,
    max_results: int = Query(50, ge=1, le=100, description="Número máximo de videos"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener videos de una playlist específica
    """
    try:
        youtube_api = YouTubeAPIService(db)
        
        videos = youtube_api.get_playlist_videos(playlist_id, max_results)
        
        return {
            "success": True,
            "data": {
                "playlist_id": playlist_id,
                "videos": videos,
                "total": len(videos)
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo videos de playlist: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/channel/{channel_id}/info")
async def get_channel_info(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener información de un canal específico
    """
    try:
        youtube_api = YouTubeAPIService(db)
        
        channel_info = youtube_api.get_channel_info(channel_id)
        if not channel_info:
            raise HTTPException(status_code=404, detail="Canal no encontrado")
        
        return {
            "success": True,
            "data": channel_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo información del canal: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/metadata/update")
async def update_youtube_metadata(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar metadata de videos en la base de datos
    Solo para administradores
    """
    try:
        # Verificar si el usuario es administrador
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        youtube_api = YouTubeAPIService(db)
        
        result = youtube_api.update_youtube_links_metadata()
        
        return {
            "success": result['success'],
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando metadata: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/quota/status")
async def get_youtube_quota_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener estado actual de la cuota de YouTube API
    """
    try:
        video_service = VideoService(db)
        
        quota_status = video_service.get_video_quota_status()
        
        return {
            "success": True,
            "data": quota_status
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de cuota: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/recommendations/by-topic")
async def get_video_recommendations_by_topic(
    topic_code: str = Query(..., description="Código del tema ICFES"),
    limit: int = Query(10, ge=1, le=50, description="Número máximo de videos"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener videos recomendados por código de tema ICFES
    """
    try:
        from sqlalchemy import text
        
        # Buscar videos por código de tema
        result = db.execute(text("""
            SELECT 
                youtube_url,
                video_title,
                tema_principal,
                canal_sugerido,
                nivel_dificultad,
                tipo_contenido,
                calidad_score,
                relevancia_score,
                duration_seconds
            FROM youtube_links 
            WHERE codigo_tema = :topic_code 
            AND estado = 'activo'
            ORDER BY calidad_score DESC, relevancia_score DESC
            LIMIT :limit
        """), {
            'topic_code': topic_code,
            'limit': limit
        })
        
        videos = result.fetchall()
        
        video_list = []
        for video in videos:
            video_list.append({
                "youtube_url": video.youtube_url,
                "video_title": video.video_title or f"Video sobre {video.tema_principal}",
                "topic": video.tema_principal,
                "channel": video.canal_sugerido,
                "difficulty_level": video.nivel_dificultad,
                "content_type": video.tipo_contenido,
                "quality_score": float(video.calidad_score) if video.calidad_score else 0.8,
                "relevance_score": float(video.relevancia_score) if video.relevancia_score else 0.85,
                "duration_seconds": video.duration_seconds or 600
            })
        
        return {
            "success": True,
            "data": {
                "topic_code": topic_code,
                "videos": video_list,
                "total": len(video_list)
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo videos por tema: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/recommendations/for-yml-plan")
async def get_videos_for_yml_plan(
    subject: str = Query(..., description="Materia del plan"),
    weak_topics: Optional[str] = Query(None, description="Temas débiles separados por coma"),
    strong_topics: Optional[str] = Query(None, description="Temas fuertes separados por coma"),
    learning_style: Optional[str] = Query(None, description="Estilo de aprendizaje"),
    limit_per_topic: int = Query(3, ge=1, le=10, description="Videos por tema"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener videos específicos para un plan YML personalizado
    """
    try:
        video_service = VideoService(db)
        
        # Parsear temas
        weak_topics_list = [topic.strip() for topic in weak_topics.split(",")] if weak_topics else []
        strong_topics_list = [topic.strip() for topic in strong_topics.split(",")] if strong_topics else []
        
        # Obtener videos para temas débiles (prioridad alta)
        weak_topic_videos = []
        for topic in weak_topics_list[:5]:  # Máximo 5 temas débiles
            videos = video_service.get_personalized_video_recommendations(
                user_id=str(current_user.id),
                subject=subject,
                weak_topics=[topic],
                difficulty_level=2,  # Dificultad media para temas débiles
                limit=limit_per_topic
            )
            weak_topic_videos.extend(videos)
        
        # Obtener videos para temas fuertes (refuerzo)
        strong_topic_videos = []
        for topic in strong_topics_list[:3]:  # Máximo 3 temas fuertes
            videos = video_service.get_personalized_video_recommendations(
                user_id=str(current_user.id),
                subject=subject,
                weak_topics=[topic],
                difficulty_level=4,  # Dificultad alta para temas fuertes
                limit=limit_per_topic
            )
            strong_topic_videos.extend(videos)
        
        # Combinar y ordenar por relevancia
        all_videos = weak_topic_videos + strong_topic_videos
        all_videos.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return {
            "success": True,
            "data": {
                "subject": subject,
                "weak_topics": weak_topics_list,
                "strong_topics": strong_topics_list,
                "learning_style": learning_style,
                "videos": {
                    "weak_topics": [v.dict() for v in weak_topic_videos],
                    "strong_topics": [v.dict() for v in strong_topic_videos],
                    "all_videos": [v.dict() for v in all_videos[:20]]  # Máximo 20 videos total
                },
                "total_videos": len(all_videos)
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo videos para plan YML: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
