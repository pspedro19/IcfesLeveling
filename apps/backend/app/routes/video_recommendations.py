"""
API Routes para Recomendaciones de Videos
Endpoints para obtener videos educativos recomendados
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.video_recommendation_service import VideoRecommendationService
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["Video Recommendations"])

@router.get("/recommendations")
async def get_video_recommendations(
    topic_codes: Optional[str] = Query(None, description="Códigos de tema separados por coma"),
    difficulty_level: Optional[int] = Query(None, ge=1, le=5, description="Nivel de dificultad (1-5)"),
    content_type: Optional[str] = Query(None, description="Tipo de contenido"),
    limit: int = Query(10, ge=1, le=50, description="Número máximo de videos"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener recomendaciones de videos basadas en criterios específicos
    """
    try:
        # Parse topic codes
        topic_list = None
        if topic_codes:
            topic_list = [code.strip() for code in topic_codes.split(",")]
        
        service = VideoRecommendationService(db)
        videos = service.get_video_recommendations(
            user_id=str(current_user.id),
            topic_codes=topic_list,
            difficulty_level=difficulty_level,
            content_type=content_type,
            limit=limit
        )
        
        return {
            "success": True,
            "data": {
                "videos": videos,
                "total": len(videos),
                "filters": {
                    "topic_codes": topic_list,
                    "difficulty_level": difficulty_level,
                    "content_type": content_type,
                    "limit": limit
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones de videos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/personalized")
async def get_personalized_video_recommendations(
    limit: int = Query(15, ge=1, le=50, description="Número máximo de videos por categoría"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener recomendaciones personalizadas basadas en el perfil del usuario
    """
    try:
        # Fetch real diagnostic results from DB
        from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
        from ..models.question import Question

        latest_test = db.query(DiagnosticTest).filter(
            DiagnosticTest.user_id == current_user.id
        ).order_by(DiagnosticTest.created_at.desc()).first()

        diagnostic_results = {"weaknesses": [], "strengths": [], "score_percentage": 50}

        if latest_test:
            answers = db.query(DiagnosticTestAnswer).filter(
                DiagnosticTestAnswer.diagnostic_test_id == latest_test.id
            ).all()
            total = len(answers)
            correct = sum(1 for a in answers if a.is_correct)
            diagnostic_results["score_percentage"] = (correct / total * 100) if total > 0 else 50

        user_id = str(current_user.id)
        service = VideoRecommendationService(db)
        recommendations = service.get_personalized_video_recommendations(
            user_id=user_id,
            diagnostic_results=diagnostic_results,
            limit=limit
        )

        return {
            "success": True,
            "data": {
                "recommendations": recommendations,
                "user_id": user_id,
                "total_videos": sum(len(videos) for videos in recommendations.values())
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones personalizadas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/topic/{topic_code}")
async def get_video_by_topic(
    topic_code: str,
    difficulty_level: Optional[int] = Query(None, ge=1, le=5, description="Nivel de dificultad"),
    content_type: Optional[str] = Query(None, description="Tipo de contenido"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener un video específico para un tema
    """
    try:
        service = VideoRecommendationService(db)
        video = service.get_video_by_topic(
            topic_code=topic_code,
            difficulty_level=difficulty_level,
            content_type=content_type
        )
        
        if not video:
            raise HTTPException(status_code=404, detail="No se encontraron videos para este tema")
        
        return {
            "success": True,
            "data": {
                "video": video,
                "topic_code": topic_code
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo video para tema {topic_code}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/random")
async def get_random_video_recommendation(
    area_evaluada: Optional[str] = Query(None, description="Área de evaluación"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener una recomendación aleatoria de video
    """
    try:
        service = VideoRecommendationService(db)
        video = service.get_random_video_recommendation(
            user_id=str(current_user.id),
            area_evaluada=area_evaluada
        )
        
        if not video:
            raise HTTPException(status_code=404, detail="No se encontraron videos disponibles")
        
        return {
            "success": True,
            "data": {
                "video": video,
                "type": "random_recommendation"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo video aleatorio: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/playlist/study-plan")
async def get_video_playlist_for_study_plan(
    limit_per_unit: int = Query(5, ge=1, le=20, description="Videos por unidad"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generar playlist de videos para un plan de estudio
    """
    try:
        user_id = str(current_user.id)

        # Fetch real study plan from DB
        from ..models.study_plan import StudyPlan
        user_plan = db.query(StudyPlan).filter(
            StudyPlan.user_id == current_user.id
        ).order_by(StudyPlan.created_at.desc()).first()

        if user_plan and hasattr(user_plan, 'plan_data') and user_plan.plan_data:
            study_plan = user_plan.plan_data
        else:
            study_plan = {"units": []}

        service = VideoRecommendationService(db)
        playlist = service.get_video_playlist_for_study_plan(
            user_id=user_id,
            study_plan=study_plan,
            limit_per_unit=limit_per_unit
        )

        return {
            "success": True,
            "data": {
                "playlist": playlist,
                "user_id": user_id,
                "total_units": len(playlist),
                "total_videos": sum(len(videos) for videos in playlist.values())
            }
        }
        
    except Exception as e:
        logger.error(f"Error generando playlist: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/search")
async def search_videos(
    query: str = Query(..., description="Término de búsqueda"),
    area_evaluada: Optional[str] = Query(None, description="Área de evaluación"),
    difficulty_level: Optional[int] = Query(None, ge=1, le=5, description="Nivel de dificultad"),
    limit: int = Query(20, ge=1, le=50, description="Número máximo de resultados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Buscar videos por término de búsqueda
    """
    try:
        service = VideoRecommendationService(db)
        
        # Construir query de búsqueda
        search_query = f"""
            SELECT * FROM youtube_links 
            WHERE estado = 'activo'
            AND (
                tema_principal ILIKE :query 
                OR query_sugerida ILIKE :query
                OR area_evaluada ILIKE :query
            )
        """
        
        params = {"query": f"%{query}%"}
        
        if area_evaluada:
            search_query += " AND area_evaluada = :area"
            params["area"] = area_evaluada
        
        if difficulty_level:
            search_query += " AND nivel_dificultad = :difficulty"
            params["difficulty"] = difficulty_level
        
        search_query += """
            ORDER BY 
                calidad_score DESC, 
                relevancia_score DESC
            LIMIT :limit
        """
        params["limit"] = limit
        
        # Ejecutar búsqueda
        result = db.execute(text(search_query), params)
        videos = result.fetchall()
        
        # Convertir a diccionarios
        video_list = []
        for video in videos:
            video_dict = {
                'id': str(video.id),
                'codigo_tema': video.codigo_tema,
                'area_evaluada': video.area_evaluada,
                'tema_principal': video.tema_principal,
                'youtube_url': video.youtube_url,
                'youtube_id': video.youtube_id,
                'video_title': video.video_title,
                'channel_name': video.channel_name,
                'duration_seconds': video.duration_seconds,
                'puntos_xp': video.puntos_xp
            }
            video_list.append(video_dict)
        
        return {
            "success": True,
            "data": {
                "videos": video_list,
                "query": query,
                "total": len(video_list),
                "filters": {
                    "area_evaluada": area_evaluada,
                    "difficulty_level": difficulty_level,
                    "limit": limit
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error buscando videos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/stats")
async def get_video_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas de videos disponibles
    """
    try:
        # Estadísticas generales
        total_videos = db.execute(text("SELECT COUNT(*) FROM youtube_links WHERE estado = 'activo'"))
        total_videos = total_videos.scalar()
        
        # Videos por área
        videos_by_area = db.execute(text("""
            SELECT area_evaluada, COUNT(*) as count 
            FROM youtube_links 
            WHERE estado = 'activo' 
            GROUP BY area_evaluada
        """))
        videos_by_area = videos_by_area.fetchall()
        
        # Videos por nivel de dificultad
        videos_by_difficulty = db.execute(text("""
            SELECT nivel_dificultad, COUNT(*) as count 
            FROM youtube_links 
            WHERE estado = 'activo' 
            GROUP BY nivel_dificultad
            ORDER BY nivel_dificultad
        """))
        videos_by_difficulty = videos_by_difficulty.fetchall()
        
        return {
            "success": True,
            "data": {
                "total_videos": total_videos,
                "videos_by_area": [{"area": row.area_evaluada, "count": row.count} for row in videos_by_area],
                "videos_by_difficulty": [{"level": row.nivel_dificultad, "count": row.count} for row in videos_by_difficulty]
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de videos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
