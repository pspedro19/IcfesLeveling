from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import re
import requests
from urllib.parse import urlparse, parse_qs
import logging

from ..models.video_tracking import VideoTracking
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.user import User
from ..models.youtube_links import YouTubeLinks
from ..schemas.video_tracking import (
    VideoTrackingCreate,
    VideoTrackingUpdate,
    VideoProgressUpdate,
    VideoRecommendation,
    UnitVideoContent,
    VideoAnalytics
)
from .youtube_api_service import YouTubeAPIService

logger = logging.getLogger(__name__)

class VideoService:
    def __init__(self, db: Session):
        self.db = db
        self.youtube_api = YouTubeAPIService(db)
    
    def extract_youtube_id(self, youtube_url: str) -> Optional[str]:
        """Extraer el ID del video de YouTube de diferentes formatos de URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        return None
    
    def get_youtube_embed_url(self, youtube_url: str) -> str:
        """Convertir URL de YouTube a URL de embed"""
        video_id = self.extract_youtube_id(youtube_url)
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
        return youtube_url
    
    def get_video_metadata(self, youtube_url: str) -> Dict[str, Any]:
        """Obtener metadata completa de un video usando YouTube API"""
        video_id = self.extract_youtube_id(youtube_url)
        if not video_id:
            return {}
        
        # Intentar obtener desde la base de datos primero
        youtube_link = self.db.query(YouTubeLinks).filter(
            YouTubeLinks.youtube_id == video_id,
            YouTubeLinks.estado == 'activo'
        ).first()
        
        if youtube_link and youtube_link.video_title:
            return {
                "video_id": video_id,
                "title": youtube_link.video_title,
                "description": "",
                "channel_title": youtube_link.channel_name or "",
                "channel_id": youtube_link.channel_id or "",
                "duration_seconds": youtube_link.duration_seconds or 600,
                "view_count": youtube_link.view_count or 0,
                "like_count": youtube_link.like_count or 0,
                "comment_count": youtube_link.comment_count or 0,
                "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                "nivel_dificultad": youtube_link.nivel_dificultad,
                "tipo_contenido": youtube_link.tipo_contenido,
                "calidad_score": float(youtube_link.calidad_score) if youtube_link.calidad_score else 0.8,
                "relevancia_score": float(youtube_link.relevancia_score) if youtube_link.relevancia_score else 0.85
            }
        
        # Si no está en BD, usar YouTube API
        metadata = self.youtube_api.get_video_info(video_id)
        if metadata:
            return metadata
        
        # Fallback a datos básicos
        return {
            "video_id": video_id,
            "title": f"Video educativo {video_id}",
            "duration_seconds": 600,
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        }
    
    def create_video_tracking(self, user_id: str, tracking_data: VideoTrackingCreate) -> VideoTracking:
        """Crear un nuevo registro de tracking de video"""
        # Verificar si ya existe un tracking para este video
        existing_tracking = self.db.query(VideoTracking).filter(
            VideoTracking.user_id == user_id,
            VideoTracking.plan_id == tracking_data.plan_id,
            VideoTracking.unit_number == tracking_data.unit_number,
            VideoTracking.youtube_url == tracking_data.youtube_url
        ).first()
        
        if existing_tracking:
            return existing_tracking
        
        # Obtener metadata del video
        metadata = self.get_video_metadata(tracking_data.youtube_url)
        
        video_tracking = VideoTracking(
            user_id=user_id,
            plan_id=tracking_data.plan_id,
            unit_number=tracking_data.unit_number,
            youtube_url=tracking_data.youtube_url,
            video_title=tracking_data.video_title or metadata.get("title"),
            video_duration_seconds=tracking_data.video_duration_seconds or metadata.get("duration_seconds"),
            completion_threshold=tracking_data.completion_threshold
        )
        
        self.db.add(video_tracking)
        self.db.commit()
        self.db.refresh(video_tracking)
        
        return video_tracking
    
    def update_video_progress(self, user_id: str, progress_data: VideoProgressUpdate) -> VideoTracking:
        """Actualizar progreso de visualización de un video"""
        video_tracking = self.db.query(VideoTracking).filter(
            VideoTracking.user_id == user_id,
            VideoTracking.plan_id == progress_data.plan_id,
            VideoTracking.unit_number == progress_data.unit_number,
            VideoTracking.youtube_url == progress_data.youtube_url
        ).first()
        
        if not video_tracking:
            # Crear nuevo tracking si no existe
            tracking_create = VideoTrackingCreate(
                plan_id=progress_data.plan_id,
                unit_number=progress_data.unit_number,
                youtube_url=progress_data.youtube_url
            )
            video_tracking = self.create_video_tracking(user_id, tracking_create)
        
        # Actualizar progreso
        video_tracking.watched_seconds = progress_data.watched_seconds
        video_tracking.last_watched_at = datetime.utcnow()
        
        # Calcular porcentaje visto
        if video_tracking.video_duration_seconds and video_tracking.video_duration_seconds > 0:
            video_tracking.watch_percentage = (
                (progress_data.watched_seconds / video_tracking.video_duration_seconds) * 100
            )
        else:
            video_tracking.watch_percentage = 0.0
        
        # Verificar si está completado (80% mínimo)
        video_tracking.is_completed = video_tracking.watch_percentage >= video_tracking.completion_threshold
        
        self.db.commit()
        self.db.refresh(video_tracking)
        
        # Actualizar progreso ponderado del plan
        self._update_plan_video_progress(progress_data.plan_id, progress_data.unit_number)
        
        return video_tracking
    
    def _update_plan_video_progress(self, plan_id: str, unit_number: int):
        """Actualizar el progreso ponderado del plan basado en videos completados"""
        # Contar videos completados en esta unidad
        completed_videos = self.db.query(VideoTracking).filter(
            VideoTracking.plan_id == plan_id,
            VideoTracking.unit_number == unit_number,
            VideoTracking.is_completed == True
        ).count()
        
        total_videos = self.db.query(VideoTracking).filter(
            VideoTracking.plan_id == plan_id,
            VideoTracking.unit_number == unit_number
        ).count()
        
        if total_videos > 0:
            # Actualizar el progreso ponderado en plan_progress
            progress = self.db.query(PlanProgress).filter(
                PlanProgress.plan_id == plan_id,
                PlanProgress.unit_number == unit_number
            ).first()
            
            if progress:
                progress.weighted_progress["videos"]["completed"] = completed_videos
                progress.weighted_progress["videos"]["total"] = total_videos
                
                # Recalcular el score ponderado
                total_progress = 0.0
                for component, data in progress.weighted_progress.items():
                    if data["total"] > 0:
                        component_progress = (data["completed"] / data["total"]) * data["weight"]
                        total_progress += component_progress
                
                progress.score = total_progress * 100
                self.db.commit()
    
    def get_unit_video_content(self, user_id: str, plan_id: str, unit_number: int) -> UnitVideoContent:
        """Obtener contenido de videos de una unidad específica"""
        videos = self.db.query(VideoTracking).filter(
            VideoTracking.user_id == user_id,
            VideoTracking.plan_id == plan_id,
            VideoTracking.unit_number == unit_number
        ).all()
        
        video_list = []
        completed_videos = 0
        total_watch_time = 0
        
        for video in videos:
            video_data = {
                "id": str(video.id),
                "youtube_url": video.youtube_url,
                "embed_url": self.get_youtube_embed_url(video.youtube_url),
                "video_title": video.video_title,
                "video_duration_seconds": video.video_duration_seconds,
                "watched_seconds": video.watched_seconds,
                "watch_percentage": float(video.watch_percentage),
                "is_completed": video.is_completed,
                "completion_threshold": float(video.completion_threshold),
                "last_watched_at": video.last_watched_at.isoformat() if video.last_watched_at else None
            }
            video_list.append(video_data)
            
            if video.is_completed:
                completed_videos += 1
            
            total_watch_time += video.watched_seconds
        
        return UnitVideoContent(
            videos=video_list,
            total_videos=len(videos),
            completed_videos=completed_videos,
            total_watch_time=total_watch_time
        )
    
    def get_video_recommendations(self, user_id: str, subject: str, limit: int = 5) -> List[VideoRecommendation]:
        """Obtener recomendaciones de videos relacionados"""
        # En producción, aquí se implementaría un algoritmo de recomendación
        # Por ahora, simulamos recomendaciones basadas en el tema
        
        recommendations = []
        subjects_videos = {
            "Matemáticas": [
                {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "Álgebra Básica", "relevance": 0.9},
                {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "Geometría Analítica", "relevance": 0.8},
                {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "Trigonometría", "relevance": 0.85}
            ],
            "Lectura Crítica": [
                {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "Comprensión de Textos", "relevance": 0.9},
                {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "Análisis Literario", "relevance": 0.8}
            ],
            "Ciencias": [
                {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "Biología Celular", "relevance": 0.9},
                {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "Química Orgánica", "relevance": 0.85}
            ]
        }
        
        subject_videos = subjects_videos.get(subject, [])
        for video in subject_videos[:limit]:
            recommendations.append(VideoRecommendation(
                youtube_url=video["url"],
                video_title=video["title"],
                video_description=f"Video educativo sobre {video['title']}",
                thumbnail_url=f"https://img.youtube.com/vi/{self.extract_youtube_id(video['url'])}/maxresdefault.jpg",
                duration_seconds=600,
                relevance_score=video["relevance"]
            ))
        
        return recommendations
    
    def get_video_analytics(self, user_id: str) -> VideoAnalytics:
        """Obtener analytics de videos del usuario"""
        # Estadísticas generales
        total_videos = self.db.query(VideoTracking).filter(
            VideoTracking.user_id == user_id
        ).count()
        
        completed_videos = self.db.query(VideoTracking).filter(
            VideoTracking.user_id == user_id,
            VideoTracking.is_completed == True
        ).count()
        
        total_watch_time = self.db.query(func.sum(VideoTracking.watched_seconds)).filter(
            VideoTracking.user_id == user_id
        ).scalar() or 0
        
        average_completion_rate = (completed_videos / total_videos * 100) if total_videos > 0 else 0
        
        # Videos por materia (simulado)
        most_watched_subjects = [
            {"subject": "Matemáticas", "videos_watched": 15, "total_time": 4500},
            {"subject": "Lectura Crítica", "videos_watched": 12, "total_time": 3600},
            {"subject": "Ciencias", "videos_watched": 10, "total_time": 3000}
        ]
        
        # Progreso semanal (simulado)
        weekly_progress = [
            {"week": "Semana 1", "videos_completed": 5, "time_spent": 1500},
            {"week": "Semana 2", "videos_completed": 8, "time_spent": 2400},
            {"week": "Semana 3", "videos_completed": 12, "time_spent": 3600}
        ]
        
        # Tendencia de completación (simulado)
        completion_trend = [
            {"date": "2024-01-01", "completion_rate": 75.0},
            {"date": "2024-01-08", "completion_rate": 82.5},
            {"date": "2024-01-15", "completion_rate": 88.0}
        ]
        
        return VideoAnalytics(
            total_videos_watched=total_videos,
            total_watch_time_minutes=total_watch_time // 60,
            average_completion_rate=average_completion_rate,
            most_watched_subjects=most_watched_subjects,
            weekly_progress=weekly_progress,
            completion_trend=completion_trend
        )
    
    def get_personalized_video_recommendations(self, user_id: str, subject: str, 
                                             weak_topics: List[str] = None, 
                                             difficulty_level: int = 3,
                                             limit: int = 10) -> List[VideoRecommendation]:
        """
        Obtener recomendaciones personalizadas de videos basadas en el perfil del usuario
        """
        try:
            # Construir query para obtener videos relevantes
            query = self.db.query(YouTubeLinks).filter(
                YouTubeLinks.estado == 'activo',
                YouTubeLinks.area_evaluada.ilike(f"%{subject}%")
            )
            
            # Filtrar por nivel de dificultad
            if difficulty_level:
                query = query.filter(YouTubeLinks.nivel_dificultad == difficulty_level)
            
            # Filtrar por temas débiles si se especifican
            if weak_topics:
                topic_filters = []
                for topic in weak_topics:
                    topic_filters.append(YouTubeLinks.tema_principal.ilike(f"%{topic}%"))
                query = query.filter(or_(*topic_filters))
            
            # Ordenar por calidad y relevancia
            videos = query.order_by(
                YouTubeLinks.calidad_score.desc(),
                YouTubeLinks.relevancia_score.desc(),
                YouTubeLinks.orden_recomendacion.asc()
            ).limit(limit).all()
            
            recommendations = []
            for video in videos:
                # Obtener metadata completa si no está disponible
                if not video.video_title:
                    metadata = self.youtube_api.get_video_info(video.youtube_id)
                    if metadata:
                        video.video_title = metadata.get('title', '')
                        video.duration_seconds = metadata.get('duration_seconds', 600)
                        video.channel_name = metadata.get('channel_title', '')
                
                recommendations.append(VideoRecommendation(
                    youtube_url=video.youtube_url,
                    video_title=video.video_title or f"Video sobre {video.tema_principal}",
                    video_description=f"Video educativo sobre {video.tema_principal}",
                    thumbnail_url=f"https://img.youtube.com/vi/{video.youtube_id}/maxresdefault.jpg" if video.youtube_id else "",
                    duration_seconds=video.duration_seconds or 600,
                    relevance_score=float(video.relevancia_score) if video.relevancia_score else 0.8,
                    difficulty_level=video.nivel_dificultad,
                    content_type=video.tipo_contenido,
                    channel_name=video.channel_name or video.canal_sugerido or ""
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error obteniendo recomendaciones personalizadas: {e}")
            return []
    
    def search_educational_videos(self, query: str, subject: str = None, 
                                max_results: int = 10) -> List[VideoRecommendation]:
        """
        Buscar videos educativos usando YouTube API
        """
        try:
            # Construir query de búsqueda
            search_query = f"{query} {subject}" if subject else query
            search_query += " educativo explicación tutorial"
            
            # Buscar en YouTube API
            videos = self.youtube_api.search_videos(
                query=search_query,
                max_results=max_results,
                relevance_language='es',
                video_duration='medium'
            )
            
            recommendations = []
            for video in videos:
                recommendations.append(VideoRecommendation(
                    youtube_url=f"https://www.youtube.com/watch?v={video['video_id']}",
                    video_title=video['title'],
                    video_description=video['description'],
                    thumbnail_url=video['thumbnail_url'],
                    duration_seconds=600,  # Por defecto
                    relevance_score=0.8,
                    channel_name=video['channel_title']
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error buscando videos educativos: {e}")
            return []
    
    def get_video_quota_status(self) -> Dict[str, Any]:
        """Obtener estado de la cuota de YouTube API"""
        return self.youtube_api.get_quota_status() 