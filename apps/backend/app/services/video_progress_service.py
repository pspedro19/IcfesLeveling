"""
Servicio de Video Progress para el Sistema ICFES Video Learning
Implementa tracking seguro, analytics y detección de trampas
"""

import hashlib
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, func
import redis.asyncio as redis
from fastapi import HTTPException, Depends
from uuid import UUID

from ..schemas.video_learning import (
    VideoProgressCreate, VideoProgressUpdate, VideoProgress,
    SecurityEventCreate, VideoAnalyticsCreate, EngagementMetricsCreate,
    VideoRecommendationCreate, UserVideoStats, VideoHeatmapData
)
from ..core.database import get_db
from ..core.config import settings

logger = logging.getLogger(__name__)

class VideoSecurity:
    """Clase para manejo de seguridad en videos"""
    
    @staticmethod
    async def verify_hash(user_id: str, video_id: str, time: float, hash: str) -> bool:
        """Verifica hash de seguridad del progreso"""
        expected = hashlib.sha256(
            f"{user_id}-{video_id}-{int(time)}".encode()
        ).hexdigest()
        return expected == hash
    
    @staticmethod
    async def check_rate_limit(redis_client: redis.Redis, user_id: str) -> bool:
        """Verifica rate limiting por usuario"""
        key = f"video_progress:{user_id}"
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, 60)  # 1 minuto
        return count <= 20  # Max 20 updates por minuto
    
    @staticmethod
    async def detect_suspicious_behavior(
        db: Session, 
        user_id: str, 
        video_id: str, 
        current_time: float,
        previous_time: float
    ) -> Optional[str]:
        """Detecta comportamiento sospechoso"""
        time_diff = current_time - previous_time
        
        # Salto de más de 60 segundos
        if time_diff > 60:
            return "SUSPICIOUS_JUMP"
        
        # Tiempo negativo (imposible)
        if time_diff < 0:
            return "NEGATIVE_TIME_JUMP"
        
        # Salto muy grande pero posible
        if time_diff > 30:
            return "LARGE_TIME_JUMP"
        
        return None

class VideoProgressService:
    """Servicio principal para manejo de progreso de videos"""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    async def update_video_progress(
        self, 
        progress: VideoProgressCreate,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Actualiza progreso de video con validaciones de seguridad"""
        
        try:
            # 1. Verificar rate limiting
            if not await VideoSecurity.check_rate_limit(self.redis_client, str(progress.user_id)):
                await self._log_security_event(
                    progress.user_id, progress.video_id, 
                    "RATE_LIMIT_EXCEEDED", "HIGH", 
                    {"updates_attempted": 20}, client_ip, user_agent
                )
                raise HTTPException(429, "Demasiadas solicitudes. Intenta de nuevo en 1 minuto.")
            
            # 2. Obtener progreso anterior para validación
            last_progress = await self._get_last_progress(progress.user_id, progress.video_id)
            
            # 3. Detectar comportamiento sospechoso
            if last_progress:
                suspicious_behavior = await VideoSecurity.detect_suspicious_behavior(
                    self.db, str(progress.user_id), progress.video_id,
                    progress.watched_seconds, last_progress['watched_seconds']
                )
                
                if suspicious_behavior:
                    await self._log_security_event(
                        progress.user_id, progress.video_id,
                        suspicious_behavior, "MEDIUM",
                        {
                            "current_time": progress.watched_seconds,
                            "previous_time": last_progress['watched_seconds'],
                            "time_diff": progress.watched_seconds - last_progress['watched_seconds']
                        },
                        client_ip, user_agent
                    )
            
            # 4. Guardar progreso en base de datos
            video_progress = await self._save_video_progress(progress)
            
            # 5. Actualizar analytics del video
            await self._update_video_analytics(progress)
            
            # 6. Actualizar progreso del plan
            if progress.is_completed:
                await self._update_plan_progress(progress)
                xp_earned = await self._award_xp_and_badges(progress)
            else:
                xp_earned = 0
            
            # 7. Cache para acceso rápido
            await self._cache_progress(progress)
            
            # 8. Generar recomendaciones si es necesario
            recommendations = await self._generate_recommendations(progress)
            
            return {
                "status": "success",
                "message": "Progreso actualizado exitosamente",
                "data": video_progress,
                "xp_earned": xp_earned,
                "security_warnings": [],
                "recommendations": recommendations
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error actualizando progreso de video: {e}")
            raise HTTPException(500, f"Error interno: {str(e)}")
    
    async def _get_last_progress(self, user_id: UUID, video_id: str) -> Optional[Dict]:
        """Obtiene el último progreso del usuario para un video"""
        query = text("""
            SELECT watched_seconds, watched_percentage, is_completed
            FROM video_tracking 
            WHERE user_id = :user_id AND video_id = :video_id 
            ORDER BY created_at DESC LIMIT 1
        """)
        
        result = self.db.execute(query, {"user_id": user_id, "video_id": video_id})
        row = result.fetchone()
        
        if row:
            return {
                "watched_seconds": row.watched_seconds,
                "watched_percentage": row.watched_percentage,
                "is_completed": row.is_completed
            }
        return None
    
    async def _save_video_progress(self, progress: VideoProgressCreate) -> VideoProgress:
        """Guarda el progreso del video en la base de datos"""
        
        # Usar UPSERT para evitar duplicados
        query = text("""
            INSERT INTO video_tracking 
            (user_id, video_id, plan_id, unit_number, codigo_tema,
             watched_seconds, watched_percentage, is_completed, 
             replay_count, speed_preference, last_watched_at)
            VALUES (:user_id, :video_id, :plan_id, :unit_number, :codigo_tema,
                    :watched_seconds, :watched_percentage, :is_completed,
                    :replay_count, :speed_preference, NOW())
            ON CONFLICT (user_id, video_id) 
            DO UPDATE SET 
                watched_seconds = GREATEST(video_tracking.watched_seconds, EXCLUDED.watched_seconds),
                watched_percentage = GREATEST(video_tracking.watched_percentage, EXCLUDED.watched_percentage),
                is_completed = EXCLUDED.is_completed,
                replay_count = video_tracking.replay_count + EXCLUDED.replay_count,
                speed_preference = EXCLUDED.speed_preference,
                last_watched_at = NOW(),
                updated_at = NOW()
            RETURNING *
        """)
        
        result = self.db.execute(query, {
            "user_id": progress.user_id,
            "video_id": progress.video_id,
            "plan_id": progress.plan_id,
            "unit_number": progress.unit_number,
            "codigo_tema": progress.codigo_tema,
            "watched_seconds": progress.watched_seconds,
            "watched_percentage": progress.watched_percentage,
            "is_completed": progress.is_completed,
            "replay_count": progress.replay_count,
            "speed_preference": progress.speed_preference
        })
        
        row = result.fetchone()
        self.db.commit()
        
        return VideoProgress(
            id=row.id,
            user_id=row.user_id,
            video_id=row.video_id,
            plan_id=row.plan_id,
            unit_number=row.unit_number,
            codigo_tema=row.codigo_tema,
            watched_seconds=row.watched_seconds,
            watched_percentage=row.watched_percentage,
            is_completed=row.is_completed,
            replay_count=row.replay_count,
            speed_preference=row.speed_preference,
            last_watched_at=row.last_watched_at,
            created_at=row.created_at,
            updated_at=row.updated_at
        )
    
    async def _update_video_analytics(self, progress: VideoProgressCreate):
        """Actualiza analytics agregados del video"""
        
        query = text("""
            INSERT INTO video_analytics 
            (video_id, codigo_tema, total_views, total_watch_time_seconds, average_completion_rate)
            VALUES (:video_id, :codigo_tema, 1, :watch_time, :completion_rate)
            ON CONFLICT (video_id) 
            DO UPDATE SET 
                total_views = video_analytics.total_views + 1,
                total_watch_time_seconds = video_analytics.total_watch_time_seconds + EXCLUDED.total_watch_time_seconds,
                average_completion_rate = (
                    (video_analytics.average_completion_rate * (video_analytics.total_views - 1) + EXCLUDED.average_completion_rate) 
                    / video_analytics.total_views
                ),
                updated_at = NOW()
        """)
        
        self.db.execute(query, {
            "video_id": progress.video_id,
            "codigo_tema": progress.codigo_tema,
            "watch_time": int(progress.watched_seconds),
            "completion_rate": progress.watched_percentage
        })
        
        self.db.commit()
    
    async def _update_plan_progress(self, progress: VideoProgressCreate):
        """Actualiza el progreso ponderado del plan de estudio"""
        
        # Obtener peso del video en la unidad
        weight_query = text("""
            SELECT video_weight FROM unit_content 
            WHERE unit_number = :unit_number AND codigo_tema = :codigo_tema AND content_type = 'video'
        """)
        
        weight_result = self.db.execute(weight_query, {
            "unit_number": progress.unit_number,
            "codigo_tema": progress.codigo_tema
        })
        
        video_weight = weight_result.fetchone()
        weight = video_weight.video_weight if video_weight else 0.33
        
        # Actualizar progreso del plan
        progress_query = text("""
            INSERT INTO plan_progress 
            (user_id, plan_id, unit_number, weighted_progress, is_completed)
            VALUES (:user_id, :plan_id, :unit_number, :weighted_progress, :is_completed)
            ON CONFLICT (user_id, plan_id, unit_number) 
            DO UPDATE SET 
                weighted_progress = GREATEST(plan_progress.weighted_progress, EXCLUDED.weighted_progress),
                is_completed = EXCLUDED.is_completed,
                completed_at = CASE WHEN EXCLUDED.is_completed THEN NOW() ELSE plan_progress.completed_at END,
                updated_at = NOW()
        """)
        
        weighted_progress = weight * (progress.watched_percentage / 100)
        is_completed = weighted_progress >= 0.8  # 80% para considerar completado
        
        self.db.execute(progress_query, {
            "user_id": progress.user_id,
            "plan_id": progress.plan_id,
            "unit_number": progress.unit_number,
            "weighted_progress": weighted_progress * 100,  # Convertir a porcentaje
            "is_completed": is_completed
        })
        
        self.db.commit()
    
    async def _award_xp_and_badges(self, progress: VideoProgressCreate) -> int:
        """Otorga XP y badges por completar video"""
        
        # XP base por completar video
        base_xp = 100
        
        # Bonus por velocidad de reproducción
        speed_bonus = 0
        if progress.speed_preference == "1.5":
            speed_bonus = 25
        elif progress.speed_preference == "2.0":
            speed_bonus = 50
        
        # Bonus por porcentaje de completitud
        completion_bonus = 0
        if progress.watched_percentage >= 95:
            completion_bonus = 50
        elif progress.watched_percentage >= 90:
            completion_bonus = 25
        
        total_xp = base_xp + speed_bonus + completion_bonus
        
        # Aquí podrías implementar lógica de badges
        # await self._check_and_award_badges(progress.user_id, progress.codigo_tema)
        
        return total_xp
    
    async def _cache_progress(self, progress: VideoProgressCreate):
        """Cachea el progreso para acceso rápido"""
        
        cache_key = f"video:{progress.user_id}:{progress.video_id}"
        cache_data = {
            "watched_seconds": progress.watched_seconds,
            "watched_percentage": progress.watched_percentage,
            "is_completed": progress.is_completed,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        await self.redis_client.setex(
            cache_key,
            300,  # 5 minutos TTL
            str(cache_data)
        )
    
    async def _generate_recommendations(self, progress: VideoProgressCreate) -> List[str]:
        """Genera recomendaciones basadas en el progreso"""
        
        recommendations = []
        
        # Si completó el video, recomendar el siguiente
        if progress.is_completed:
            next_video = await self._get_next_video_recommendation(progress)
            if next_video:
                recommendations.append(f"Próximo video recomendado: {next_video['title']}")
        
        # Si tuvo dificultades, recomendar refuerzo
        if progress.replay_count > 2:
            recommendations.append("Considera revisar conceptos básicos antes de continuar")
        
        return recommendations
    
    async def _get_next_video_recommendation(self, progress: VideoProgressCreate) -> Optional[Dict]:
        """Obtiene la siguiente recomendación de video"""
        
        query = text("""
            SELECT uc.content_id, uc.difficulty_level, uc.estimated_duration_minutes
            FROM unit_content uc
            WHERE uc.unit_number = :unit_number 
              AND uc.content_type = 'video'
              AND uc.codigo_tema != :current_tema
            ORDER BY uc.difficulty_level ASC, uc.estimated_duration_minutes ASC
            LIMIT 1
        """)
        
        result = self.db.execute(query, {
            "unit_number": progress.unit_number,
            "current_tema": progress.codigo_tema
        })
        
        row = result.fetchone()
        if row:
            return {
                "video_id": row.content_id,
                "title": f"Video {row.content_id}",
                "difficulty": row.difficulty_level,
                "duration": row.estimated_duration_minutes
            }
        return None
    
    async def _log_security_event(
        self, 
        user_id: UUID, 
        video_id: str, 
        alert_type: str, 
        severity: str,
        details: Dict[str, Any],
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Registra evento de seguridad"""
        
        security_event = SecurityEventCreate(
            user_id=user_id,
            video_id=video_id,
            alert_type=alert_type,
            severity=severity,
            details=details,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        query = text("""
            INSERT INTO security_events 
            (user_id, video_id, alert_type, severity, details, ip_address, user_agent)
            VALUES (:user_id, :video_id, :alert_type, :severity, :details, :ip_address, :user_agent)
        """)
        
        self.db.execute(query, {
            "user_id": security_event.user_id,
            "video_id": security_event.video_id,
            "alert_type": security_event.alert_type,
            "severity": security_event.severity,
            "details": security_event.details,
            "ip_address": security_event.ip_address,
            "user_agent": security_event.user_agent
        })
        
        self.db.commit()
        logger.warning(f"Security event logged: {alert_type} for user {user_id} on video {video_id}")
    
    async def get_user_video_stats(self, user_id: UUID) -> UserVideoStats:
        """Obtiene estadísticas completas de video del usuario"""
        
        # Estadísticas básicas
        basic_stats_query = text("""
            SELECT 
                COUNT(*) as total_videos,
                SUM(watched_seconds) as total_watch_time,
                AVG(watched_percentage) as avg_completion,
                SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) as completed_videos
            FROM video_tracking 
            WHERE user_id = :user_id
        """)
        
        basic_result = self.db.execute(basic_stats_query, {"user_id": user_id})
        basic_stats = basic_result.fetchone()
        
        # Temas favoritos
        favorite_topics_query = text("""
            SELECT codigo_tema, COUNT(*) as view_count
            FROM video_tracking 
            WHERE user_id = :user_id
            GROUP BY codigo_tema 
            ORDER BY view_count DESC 
            LIMIT 5
        """)
        
        topics_result = self.db.execute(favorite_topics_query, {"user_id": user_id})
        favorite_topics = [row.codigo_tema for row in topics_result]
        
        # Racha de aprendizaje (días consecutivos)
        streak_query = text("""
            SELECT COUNT(DISTINCT DATE(last_watched_at)) as streak_days
            FROM (
                SELECT last_watched_at,
                       DATE(last_watched_at) - ROW_NUMBER() OVER (ORDER BY DATE(last_watched_at)) as grp
                FROM video_tracking 
                WHERE user_id = :user_id
                ORDER BY last_watched_at DESC
            ) t
            GROUP BY grp
            ORDER BY streak_days DESC
            LIMIT 1
        """)
        
        streak_result = self.db.execute(streak_query, {"user_id": user_id})
        streak_row = streak_result.fetchone()
        learning_streak = streak_row.streak_days if streak_row else 0
        
        # XP total (simulado por ahora)
        total_xp = basic_stats.completed_videos * 100
        
        # Nivel basado en XP
        level = (total_xp // 1000) + 1
        next_level_xp = level * 1000
        
        return UserVideoStats(
            total_videos_watched=basic_stats.total_videos or 0,
            total_watch_time_hours=((basic_stats.total_watch_time or 0) / 3600),
            average_completion_rate=basic_stats.avg_completion or 0,
            favorite_topics=favorite_topics,
            learning_streak_days=learning_streak,
            xp_earned=total_xp,
            level=level,
            next_level_xp=next_level_xp
        )
    
    async def get_video_heatmap(self, video_id: str) -> VideoHeatmapData:
        """Genera mapa de calor de un video específico"""
        
        # Segmentos de 10 segundos
        heatmap_query = text("""
            SELECT 
                FLOOR(watched_seconds / 10) * 10 as segment_start,
                COUNT(*) as views,
                AVG(replay_count) as avg_replays,
                AVG(watched_percentage) as avg_completion
            FROM video_tracking
            WHERE video_id = :video_id
            GROUP BY FLOOR(watched_seconds / 10)
            ORDER BY segment_start
        """)
        
        result = self.db.execute(heatmap_query, {"video_id": video_id})
        segments = []
        
        for row in result:
            segments.append({
                "start_time": row.segment_start,
                "end_time": row.segment_start + 10,
                "views": row.views,
                "avg_replays": float(row.avg_replays or 0),
                "avg_completion": float(row.avg_completion or 0)
            })
        
        # Estadísticas generales del video
        stats_query = text("""
            SELECT 
                COUNT(*) as total_views,
                AVG(watched_percentage) as avg_completion,
                AVG(replay_count) as avg_replays
            FROM video_tracking
            WHERE video_id = :video_id
        """)
        
        stats_result = self.db.execute(stats_query, {"video_id": video_id})
        stats = stats_result.fetchone()
        
        # Identificar segmentos difíciles (más repeticiones)
        difficult_segments = [
            seg for seg in segments 
            if seg["avg_replays"] > 2.0
        ]
        
        return VideoHeatmapData(
            video_id=video_id,
            segments=segments,
            total_views=stats.total_views or 0,
            average_replay_rate=float(stats.avg_replays or 0),
            difficult_segments=difficult_segments
        )
    
    async def get_user_recommendations(self, user_id: UUID, limit: int = 5) -> List[Dict]:
        """Obtiene recomendaciones personalizadas para el usuario"""
        
        # Basado en temas favoritos y dificultad
        recommendations_query = text("""
            SELECT 
                uc.content_id as video_id,
                uc.codigo_tema,
                uc.difficulty_level,
                uc.estimated_duration_minutes,
                va.average_completion_rate,
                'Basado en tu progreso en ' || uc.codigo_tema as reason
            FROM unit_content uc
            LEFT JOIN video_analytics va ON uc.content_id = va.video_id
            WHERE uc.content_type = 'video'
              AND uc.codigo_tema IN (
                SELECT DISTINCT codigo_tema 
                FROM video_tracking 
                WHERE user_id = :user_id 
                  AND watched_percentage > 70
                LIMIT 3
              )
              AND uc.content_id NOT IN (
                SELECT video_id 
                FROM video_tracking 
                WHERE user_id = :user_id
              )
            ORDER BY uc.difficulty_level ASC, va.average_completion_rate DESC
            LIMIT :limit
        """)
        
        result = self.db.execute(recommendations_query, {
            "user_id": user_id,
            "limit": limit
        })
        
        recommendations = []
        for row in result:
            recommendations.append({
                "video_id": row.video_id,
                "codigo_tema": row.codigo_tema,
                "difficulty": row.difficulty_level,
                "duration": row.estimated_duration_minutes,
                "completion_rate": float(row.average_completion_rate or 0),
                "reason": row.reason
            })
        
        return recommendations

# =====================================================
# FUNCIONES DE UTILIDAD
# =====================================================

async def get_video_progress_service(db: Session = Depends(get_db)) -> VideoProgressService:
    """Dependency para obtener el servicio de video progress"""
    return VideoProgressService(db)

async def log_security_event(
    user_id: UUID,
    video_id: str,
    alert_type: str,
    severity: str = "MEDIUM",
    details: Dict[str, Any] = None,
    db: Session = Depends(get_db)
):
    """Función de utilidad para logging de eventos de seguridad"""
    service = VideoProgressService(db)
    await service._log_security_event(
        user_id, video_id, alert_type, severity, details or {}
    )


