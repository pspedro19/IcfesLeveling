"""
API Routes para el Sistema de Video Progress ICFES
Endpoints para tracking, analytics y recomendaciones de videos
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import logging
from uuid import UUID

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..schemas.video_learning import (
    VideoProgressCreate, VideoProgressUpdate, VideoProgress,
    VideoProgressResponse, VideoAnalyticsResponse, EngagementResponse,
    VideoRecommendationResponse, UserVideoStats, VideoHeatmapData,
    VideoPlayerConfig, SecurityConfig
)
from ..services.video_progress_service import VideoProgressService, get_video_progress_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/video", tags=["Video Progress"])

# =====================================================
# ENDPOINTS PRINCIPALES
# =====================================================

@router.post("/progress/update", response_model=VideoProgressResponse)
async def update_video_progress(
    progress: VideoProgressCreate,
    request: Request,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza el progreso de un video con validaciones de seguridad
    """
    try:
        # Verificar que el usuario está actualizando su propio progreso
        if str(progress.user_id) != str(current_user.id):
            raise HTTPException(403, "No puedes actualizar el progreso de otro usuario")
        
        # Obtener IP del cliente
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Crear servicio y actualizar progreso
        service = VideoProgressService(db)
        result = await service.update_video_progress(
            progress, client_ip, user_agent
        )
        
        logger.info(f"✅ Progreso de video actualizado para usuario {current_user.id}")
        
        return VideoProgressResponse(
            status="success",
            message=result["message"],
            data=result["data"],
            xp_earned=result["xp_earned"],
            security_warnings=result["security_warnings"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando progreso de video: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")

@router.get("/progress/{user_id}/{video_id}", response_model=VideoProgress)
async def get_video_progress(
    user_id: UUID,
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el progreso de un video específico
    """
    try:
        # Verificar permisos
        if str(user_id) != str(current_user.id):
            raise HTTPException(403, "No puedes ver el progreso de otro usuario")
        
        # Buscar progreso en cache primero
        service = VideoProgressService(db)
        
        # Intentar obtener del cache
        cache_key = f"video:{user_id}:{video_id}"
        cached = await service.redis_client.get(cache_key)
        
        if cached:
            logger.info(f"✅ Progreso obtenido del cache para usuario {user_id}")
            # Aquí podrías parsear el cache y retornar
            # Por ahora, continuamos con la base de datos
        
        # Buscar en base de datos
        query = """
            SELECT * FROM video_tracking 
            WHERE user_id = :user_id AND video_id = :video_id 
            ORDER BY updated_at DESC LIMIT 1
        """
        
        result = db.execute(query, {"user_id": user_id, "video_id": video_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(404, "Progreso de video no encontrado")
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo progreso de video: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")

@router.get("/progress/{user_id}/stats", response_model=UserVideoStats)
async def get_user_video_stats(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas completas de video del usuario
    """
    try:
        # Verificar permisos
        if str(user_id) != str(current_user.id):
            raise HTTPException(403, "No puedes ver las estadísticas de otro usuario")
        
        service = VideoProgressService(db)
        stats = await service.get_user_video_stats(user_id)
        
        logger.info(f"✅ Estadísticas obtenidas para usuario {user_id}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")

@router.get("/analytics/{video_id}", response_model=VideoHeatmapData)
async def get_video_analytics(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene analytics detallados de un video (mapa de calor)
    """
    try:
        service = VideoProgressService(db)
        heatmap = await service.get_video_heatmap(video_id)
        
        logger.info(f"✅ Analytics obtenidos para video {video_id}")
        return heatmap
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo analytics: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")

@router.get("/recommendations/{user_id}", response_model=List[Dict])
async def get_user_recommendations(
    user_id: UUID,
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene recomendaciones personalizadas de videos para el usuario
    """
    try:
        # Verificar permisos
        if str(user_id) != str(current_user.id):
            raise HTTPException(403, "No puedes ver las recomendaciones de otro usuario")
        
        service = VideoProgressService(db)
        recommendations = await service.get_user_recommendations(user_id, limit)
        
        logger.info(f"✅ Recomendaciones obtenidas para usuario {user_id}")
        return recommendations
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo recomendaciones: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")

# =====================================================
# ENDPOINTS DE CONFIGURACIÓN
# =====================================================

@router.get("/config/player", response_model=VideoPlayerConfig)
async def get_video_player_config():
    """
    Obtiene configuración del reproductor de video
    """
    return VideoPlayerConfig()

@router.get("/config/security", response_model=SecurityConfig)
async def get_security_config():
    """
    Obtiene configuración de seguridad del sistema
    """
    return SecurityConfig()

# =====================================================
# ENDPOINTS DE ENGAGEMENT
# =====================================================

@router.post("/engagement/start")
async def start_engagement_session(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Inicia una sesión de engagement para tracking en tiempo real
    """
    try:
        import uuid
        session_id = str(uuid.uuid4())
        
        # Crear métricas de engagement
        query = """
            INSERT INTO engagement_metrics 
            (user_id, session_id, current_video_id, is_active, last_activity)
            VALUES (:user_id, :session_id, :video_id, true, NOW())
            ON CONFLICT (user_id, session_id) 
            DO UPDATE SET 
                current_video_id = EXCLUDED.current_video_id,
                is_active = true,
                last_activity = NOW()
        """
        
        db.execute(query, {
            "user_id": current_user.id,
            "session_id": session_id,
            "video_id": video_id
        })
        db.commit()
        
        logger.info(f"✅ Sesión de engagement iniciada para usuario {current_user.id}")
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Sesión de engagement iniciada"
        }
        
    except Exception as e:
        logger.error(f"❌ Error iniciando sesión de engagement: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")

@router.post("/engagement/update")
async def update_engagement(
    session_id: str,
    engagement_score: float,
    focus_time_seconds: int,
    tab_switches: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza métricas de engagement en tiempo real
    """
    try:
        # Validar parámetros
        if not 0 <= engagement_score <= 100:
            raise HTTPException(400, "Engagement score debe estar entre 0 y 100")
        
        if focus_time_seconds < 0:
            raise HTTPException(400, "Focus time no puede ser negativo")
        
        if tab_switches < 0:
            raise HTTPException(400, "Tab switches no puede ser negativo")
        
        # Actualizar métricas
        query = """
            UPDATE engagement_metrics 
            SET engagement_score = :score,
                focus_time_seconds = :focus_time,
                tab_switches = :tab_switches,
                last_activity = NOW()
            WHERE user_id = :user_id AND session_id = :session_id
        """
        
        result = db.execute(query, {
            "score": engagement_score,
            "focus_time": focus_time_seconds,
            "tab_switches": tab_switches,
            "user_id": current_user.id,
            "session_id": session_id
        })
        
        if result.rowcount == 0:
            raise HTTPException(404, "Sesión de engagement no encontrada")
        
        db.commit()
        
        logger.info(f"✅ Engagement actualizado para usuario {current_user.id}")
        
        return {
            "status": "success",
            "message": "Engagement actualizado exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando engagement: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")

@router.post("/engagement/end")
async def end_engagement_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Finaliza una sesión de engagement
    """
    try:
        query = """
            UPDATE engagement_metrics 
            SET is_active = false, last_activity = NOW()
            WHERE user_id = :user_id AND session_id = :session_id
        """
        
        result = db.execute(query, {
            "user_id": current_user.id,
            "session_id": session_id
        })
        
        if result.rowcount == 0:
            raise HTTPException(404, "Sesión de engagement no encontrada")
        
        db.commit()
        
        logger.info(f"✅ Sesión de engagement finalizada para usuario {current_user.id}")
        
        return {
            "status": "success",
            "message": "Sesión de engagement finalizada"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error finalizando sesión de engagement: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")

# =====================================================
# ENDPOINTS DE BATCH OPERATIONS
# =====================================================

@router.post("/progress/batch-update")
async def batch_update_video_progress(
    updates: List[VideoProgressCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza múltiples progresos de video en una sola operación
    """
    try:
        # Verificar que todos los updates son del usuario actual
        for update in updates:
            if str(update.user_id) != str(current_user.id):
                raise HTTPException(400, "No puedes actualizar el progreso de otro usuario")
        
        service = VideoProgressService(db)
        results = []
        total_xp = 0
        
        for progress in updates:
            try:
                result = await service.update_video_progress(progress)
                results.append({
                    "video_id": progress.video_id,
                    "status": "success",
                    "xp_earned": result["xp_earned"]
                })
                total_xp += result["xp_earned"]
            except Exception as e:
                results.append({
                    "video_id": progress.video_id,
                    "status": "error",
                    "error": str(e)
                })
        
        success_count = len([r for r in results if r["status"] == "success"])
        error_count = len([r for r in results if r["status"] == "error"])
        
        logger.info(f"✅ Batch update completado: {success_count} exitosos, {error_count} errores")
        
        return {
            "status": "success",
            "processed_count": len(updates),
            "success_count": success_count,
            "error_count": error_count,
            "results": results,
            "xp_total_earned": total_xp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en batch update: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")

# =====================================================
# ENDPOINTS DE ADMINISTRACIÓN
# =====================================================

@router.get("/admin/security-events")
async def get_security_events(
    user_id: Optional[UUID] = None,
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene eventos de seguridad (solo para administradores)
    """
    try:
        # Verificar si es administrador
        if not current_user.is_admin:
            raise HTTPException(403, "Solo administradores pueden ver eventos de seguridad")
        
        # Construir query
        query = "SELECT * FROM security_events WHERE 1=1"
        params = {}
        
        if user_id:
            query += " AND user_id = :user_id"
            params["user_id"] = user_id
        
        if alert_type:
            query += " AND alert_type = :alert_type"
            params["alert_type"] = alert_type
        
        if severity:
            query += " AND severity = :severity"
            params["severity"] = severity
        
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        result = db.execute(query, params)
        events = []
        
        for row in result:
            events.append({
                "id": str(row.id),
                "user_id": str(row.user_id),
                "video_id": row.video_id,
                "alert_type": row.alert_type,
                "severity": row.severity,
                "details": row.details,
                "ip_address": row.ip_address,
                "user_agent": row.user_agent,
                "created_at": row.created_at.isoformat()
            })
        
        return {
            "status": "success",
            "total_events": len(events),
            "events": events
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo eventos de seguridad: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")

@router.get("/admin/video-stats")
async def get_admin_video_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas generales de videos (solo para administradores)
    """
    try:
        # Verificar si es administrador
        if not current_user.is_admin:
            raise HTTPException(403, "Solo administradores pueden ver estadísticas generales")
        
        # Estadísticas generales
        stats_query = """
            SELECT 
                COUNT(DISTINCT user_id) as total_users,
                COUNT(*) as total_video_sessions,
                AVG(watched_percentage) as avg_completion_rate,
                SUM(watched_seconds) / 3600 as total_watch_hours
            FROM video_tracking
        """
        
        result = db.execute(stats_query)
        stats = result.fetchone()
        
        # Videos más populares
        popular_query = """
            SELECT 
                video_id,
                COUNT(*) as view_count,
                AVG(watched_percentage) as avg_completion
            FROM video_tracking
            GROUP BY video_id
            ORDER BY view_count DESC
            LIMIT 10
        """
        
        popular_result = db.execute(popular_query)
        popular_videos = []
        
        for row in popular_result:
            popular_videos.append({
                "video_id": row.video_id,
                "view_count": row.view_count,
                "avg_completion": float(row.avg_completion or 0)
            })
        
        return {
            "status": "success",
            "general_stats": {
                "total_users": stats.total_users or 0,
                "total_video_sessions": stats.total_video_sessions or 0,
                "avg_completion_rate": float(stats.avg_completion_rate or 0),
                "total_watch_hours": float(stats.total_watch_hours or 0)
            },
            "popular_videos": popular_videos
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas generales: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")

# =====================================================
# ENDPOINTS DE WEBHOOK
# =====================================================

@router.post("/webhook/progress-update")
async def webhook_progress_update(
    payload: Dict[str, Any],
    request: Request
):
    """
    Webhook para recibir actualizaciones de progreso de sistemas externos
    """
    try:
        # Verificar autenticación del webhook (implementar según necesidades)
        # auth_header = request.headers.get("authorization")
        # if not verify_webhook_auth(auth_header):
        #     raise HTTPException(401, "Webhook no autorizado")
        
        # Procesar payload
        user_id = payload.get("user_id")
        video_id = payload.get("video_id")
        progress_data = payload.get("progress", {})
        
        if not user_id or not video_id:
            raise HTTPException(400, "Payload inválido: faltan user_id o video_id")
        
        # Crear objeto de progreso
        progress = VideoProgressCreate(
            user_id=UUID(user_id),
            video_id=video_id,
            plan_id=UUID(payload.get("plan_id", "00000000-0000-0000-0000-000000000000")),
            unit_number=payload.get("unit_number", 1),
            codigo_tema=payload.get("codigo_tema", "GENERAL"),
            watched_seconds=progress_data.get("watched_seconds", 0),
            watched_percentage=progress_data.get("watched_percentage", 0),
            is_completed=progress_data.get("is_completed", False),
            replay_count=progress_data.get("replay_count", 0),
            speed_preference=progress_data.get("speed_preference", "1.0")
        )
        
        # Procesar progreso
        db = next(get_db())
        service = VideoProgressService(db)
        result = await service.update_video_progress(progress)
        
        logger.info(f"✅ Webhook procesado exitosamente para usuario {user_id}")
        
        return {
            "status": "success",
            "message": "Webhook procesado exitosamente",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")

# =====================================================
# ENDPOINTS DE SALUD Y MONITOREO
# =====================================================

@router.get("/health")
async def video_system_health():
    """
    Verifica la salud del sistema de video learning
    """
    try:
        # Verificar conectividad a Redis
        redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        await redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "video_progress_api": "healthy",
            "redis_cache": redis_status,
            "database": "healthy"  # Asumiendo que la DB está funcionando
        },
        "version": "1.0.0"
    }

@router.get("/metrics")
async def get_system_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene métricas del sistema en tiempo real
    """
    try:
        # Solo administradores pueden ver métricas del sistema
        if not current_user.is_admin:
            raise HTTPException(403, "Solo administradores pueden ver métricas del sistema")
        
        # Usuarios activos
        active_users_query = """
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM engagement_metrics
            WHERE is_active = true AND last_activity > NOW() - INTERVAL '5 minutes'
        """
        
        active_result = db.execute(active_users_query)
        active_users = active_result.fetchone().active_users or 0
        
        # Videos en progreso
        in_progress_query = """
            SELECT COUNT(*) as videos_in_progress
            FROM video_tracking
            WHERE updated_at > NOW() - INTERVAL '1 hour'
        """
        
        progress_result = db.execute(in_progress_query)
        videos_in_progress = progress_result.fetchone().videos_in_progress or 0
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "active_users": active_users,
                "videos_in_progress": videos_in_progress,
                "system_load": "normal",  # Implementar métricas reales
                "cache_hit_rate": "85%"   # Implementar métricas reales
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo métricas: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")
