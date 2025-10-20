from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
import uuid
from datetime import datetime, timedelta

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User

router = APIRouter(prefix="/simple-recommendations", tags=["simple-recommendations"])

@router.post("/generate-for-subject/{subject_id}")
async def generate_simple_recommendations(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generar recomendaciones simples de videos para una materia
    """
    try:
        # Obtener información de la materia
        subject_query = text("SELECT name FROM subjects WHERE id = :subject_id")
        subject_result = db.execute(subject_query, {"subject_id": subject_id}).fetchone()
        
        if not subject_result:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        subject_name = subject_result[0]
        
        # Obtener videos para esta materia
        videos_query = text("""
            SELECT yc.id, yc.youtube_id, yc.youtube_url, yc.title, 
                   yc.channel_name, yc.duration_minutes, yc.quality_score,
                   yc.topics_covered, yc.codigo_tema
            FROM youtube_catalog yc
            WHERE yc.subject_id = :subject_id
            AND yc.is_active = TRUE
            ORDER BY yc.quality_score DESC, yc.duration_minutes ASC
            LIMIT 10
        """)
        
        video_results = db.execute(videos_query, {"subject_id": subject_id}).fetchall()
        
        # Formatear videos para respuesta
        recommended_videos = []
        for row in video_results:
            video = {
                "video_id": str(row[0]),
                "youtube_id": row[1],
                "youtube_url": row[2],
                "title": row[3],
                "channel_name": row[4] or "Canal Educativo",
                "duration_minutes": row[5] or 15,
                "quality_score": float(row[6]) if row[6] else 0.8,
                "topics_covered": row[7] if row[7] else [],
                "codigo_tema": row[8],
                "thumbnail_url": f"https://img.youtube.com/vi/{row[1]}/maxresdefault.jpg"
            }
            recommended_videos.append(video)
        
        # Crear respuesta
        recommendation = {
            "recommendation_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "subject_id": subject_id,
            "subject_name": subject_name,
            "recommended_videos": recommended_videos,
            "total_videos": len(recommended_videos),
            "estimated_study_time_hours": len(recommended_videos) * 0.5,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        return recommendation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@router.get("/videos-by-topic/{subject_id}")
async def get_videos_by_topic(
    subject_id: str,
    topic: str = None,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Obtener videos filtrados por tópico específico
    """
    try:
        base_query = """
            SELECT yc.id, yc.youtube_id, yc.youtube_url, yc.title, 
                   yc.channel_name, yc.duration_minutes, yc.quality_score,
                   yc.topics_covered, yc.codigo_tema
            FROM youtube_catalog yc
            WHERE yc.subject_id = :subject_id
            AND yc.is_active = TRUE
        """
        
        params = {"subject_id": subject_id, "limit": limit}
        
        if topic:
            base_query += " AND (yc.title ILIKE :topic_pattern OR :topic = ANY(yc.topics_covered))"
            params["topic"] = topic
            params["topic_pattern"] = f"%{topic}%"
        
        base_query += " ORDER BY yc.quality_score DESC LIMIT :limit"
        
        results = db.execute(text(base_query), params).fetchall()
        
        videos = []
        for row in results:
            video = {
                "video_id": str(row[0]),
                "youtube_id": row[1],
                "youtube_url": row[2],
                "title": row[3],
                "channel_name": row[4] or "Canal Educativo",
                "duration_minutes": row[5] or 15,
                "quality_score": float(row[6]) if row[6] else 0.8,
                "topics_covered": row[7] if row[7] else [],
                "codigo_tema": row[8],
                "thumbnail_url": f"https://img.youtube.com/vi/{row[1]}/maxresdefault.jpg"
            }
            videos.append(video)
        
        return {
            "subject_id": subject_id,
            "topic_filter": topic,
            "videos": videos,
            "total_found": len(videos)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting videos: {str(e)}")

@router.get("/catalog-stats")
async def get_catalog_stats(db: Session = Depends(get_db)):
    """
    Obtener estadísticas del catálogo de videos
    """
    try:
        # Estadísticas generales
        stats_query = text("""
            SELECT 
                s.name as subject_name,
                COUNT(yc.id) as video_count,
                AVG(yc.duration_minutes) as avg_duration,
                AVG(yc.quality_score) as avg_quality
            FROM subjects s
            LEFT JOIN youtube_catalog yc ON s.id = yc.subject_id
            WHERE yc.is_active = TRUE OR yc.id IS NULL
            GROUP BY s.id, s.name
            ORDER BY video_count DESC
        """)
        
        results = db.execute(stats_query).fetchall()
        
        stats = {
            "by_subject": [],
            "total_videos": 0,
            "total_subjects": len(results)
        }
        
        for row in results:
            subject_stats = {
                "subject_name": row[0],
                "video_count": row[1] or 0,
                "avg_duration_minutes": round(float(row[2]) if row[2] else 0, 1),
                "avg_quality_score": round(float(row[3]) if row[3] else 0, 2)
            }
            stats["by_subject"].append(subject_stats)
            stats["total_videos"] += subject_stats["video_count"]
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting catalog stats: {str(e)}")

@router.post("/report-video-error")
async def report_video_error(
    error_data: dict,
    db: Session = Depends(get_db)
):
    """
    Reportar un video que no funciona para marcarlo como inactivo
    """
    try:
        youtube_id = error_data.get('youtube_id')
        if not youtube_id:
            raise HTTPException(status_code=400, detail="youtube_id is required")
        
        # Marcar video como inactivo
        update_query = text("""
            UPDATE youtube_catalog 
            SET is_active = FALSE,
                description = COALESCE(description, '') || ' [REPORTED: Video unavailable]',
                updated_at = NOW()
            WHERE youtube_id = :youtube_id
        """)
        
        result = db.execute(update_query, {"youtube_id": youtube_id})
        db.commit()
        
        if result.rowcount > 0:
            return {
                "success": True,
                "message": f"Video {youtube_id} marked as unavailable",
                "youtube_id": youtube_id
            }
        else:
            return {
                "success": False,
                "message": f"Video {youtube_id} not found in catalog"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reporting video error: {str(e)}")

@router.get("/working-videos/{subject_id}")
async def get_working_videos(
    subject_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Obtener solo videos que sabemos que funcionan (marcados como activos)
    """
    try:
        query = text("""
            SELECT yc.id, yc.youtube_id, yc.youtube_url, yc.title, 
                   yc.channel_name, yc.duration_minutes, yc.quality_score,
                   yc.topics_covered, yc.icfes_competence, yc.icfes_component
            FROM youtube_catalog yc
            WHERE yc.subject_id = :subject_id
            AND yc.is_active = TRUE
            AND yc.description NOT LIKE '%REPORTED%'
            ORDER BY yc.quality_score DESC, yc.created_at DESC
            LIMIT :limit
        """)
        
        results = db.execute(query, {"subject_id": subject_id, "limit": limit}).fetchall()
        
        videos = []
        for row in results:
            video = {
                "video_id": str(row[0]),
                "youtube_id": row[1],
                "youtube_url": row[2],
                "title": row[3],
                "channel_name": row[4] or "Canal Educativo",
                "duration_minutes": row[5] or 15,
                "quality_score": float(row[6]) if row[6] else 0.8,
                "topics_covered": row[7] if row[7] else [],
                "icfes_competence": row[8],
                "icfes_component": row[9],
                "thumbnail_url": f"https://img.youtube.com/vi/{row[1]}/maxresdefault.jpg",
                "status": "verified_working"
            }
            videos.append(video)
        
        return {
            "subject_id": subject_id,
            "working_videos": videos,
            "total_found": len(videos)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting working videos: {str(e)}")
