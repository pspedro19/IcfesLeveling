from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import logging.config
import os
import asyncio
import sentry_sdk

from .core.config import settings, LOGGING_CONFIG

# Configure logging early so logger is available
os.makedirs("logs", exist_ok=True)
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.2,
        profiles_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
        release=settings.APP_VERSION,
    )
    logger.info("Sentry initialized for error tracking.")

from .core.database import engine, Base
from .middleware.guest_limits import GuestLimitsMiddleware
from .middleware.media_rate_limit import media_rate_limit_middleware
from .middleware.security import add_security_middleware
from .middleware.anti_gaming import get_anti_gaming
# Minimal core routes for testing
# ============================================
# ROUTERS - Organized by category
# ============================================

# ============================================
# TIER 1: ESSENTIAL (Authentication & Core)
# ============================================
from .routes import auth, questions, hearts, streak, mobile_api, sync, node_progress

# ============================================
# TIER 2: GAMIFICATION (Core game mechanics)
# ============================================
from .routes import economy, achievements, leaderboard, notifications, quests, answers, battles, practice

# ============================================
# TIER 3: DIAGNOSTIC SYSTEM
# ============================================
from .routes import diagnostic_public, diagnostic_two_phase
from .routes import monthly_reassessment, verified_image_diagnostic  # FIXED by Gemini

# ============================================
# TIER 4: STUDY PLANS & RECOMMENDATIONS
# ============================================
from .routes import (
    personality, recommendations,
    claude_study_plan_generator, integrated_study_plan_api,
    study_plans,  # FIXED: schema mismatch resolved
    quizzes,  # FIXED by Gemini: UserProfile.level
    spaced_repetition,  # SM-2 spaced repetition system
    personalized_study_plan_api
)
# NOTE: simple_recommendations, study_plans_simple, simple_study_plan_generator
# are deprecated - functionality consolidated into main routes

# ============================================
# TIER 4b: AI & INTELLIGENT FEATURES
# ============================================
from .routes import ai  # FIXED: sqlalchemy.func import added

# ============================================
# TIER 5: VIDEO & CONTENT
# ============================================
from .routes import videos, video_recommendations, youtube_api, icfes_catalog, intelligent_video_recommendations

# ============================================
# TIER 6: SOCIAL & COMPETITIVE
# ============================================
from .routes import guilds, leagues, store, boss_raid, bosses, premium_simple, dungeons

# ============================================
# TIER 7: AI & ASSETS
# ============================================
from .routes import ai_tips, images_api, dynamic_subjects, subjects_with_count, dynamic_images_api, image_required_questions, images

# ============================================
# TIER 8: ANALYTICS & DASHBOARD
# ============================================
from .routes import analytics_advanced, student_dashboard, mastery, advanced_stats
from .routes import users_cached, questions_cached, battles_cached


# Logging already configured above imports

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events."""
    # Asegurar columnas necesarias e importar preguntas desde Excel si está habilitado por env
    try:
        logger.info("🔧 Iniciando configuración automática del sistema...")
        
        # Paso 1: Asegurar estructura de base de datos
        logger.info("📊 Verificando estructura de base de datos...")
        # _ensure_question_columns() # REMOVED - Logic moved to Alembic
        # _ensure_diagnostic_test_columns() # REMOVED - Logic moved to Alembic
        
        # Paso 1.5: CRÍTICO - Asegurar tablas avanzadas para 95% completitud
        # _ensure_advanced_learning_tables()
        
        logger.info("✅ Estructura de base de datos verificada (incluyendo sistema avanzado)")
        
        # Paso 2: Importar preguntas desde Excel
        auto_import = os.getenv("AUTO_IMPORT_QUESTIONS", "false").lower() in ("1", "true", "yes")
        excel_path = os.getenv("QUESTIONS_EXCEL_PATH")
        clear_existing = os.getenv("IMPORT_CLEAR_EXISTING", "false").lower() in ("1", "true", "yes")
        
        if auto_import and excel_path and os.path.exists(excel_path):
            logger.info(f"📚 AUTO_IMPORT_QUESTIONS enabled. Importing from: {excel_path} (clear={clear_existing})")
            
            # Reintentos para importación de preguntas
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    from .core.database import get_db
                    from .import_icfes_excel import ICFESExcelImporter
                    from .models.question import Question

                    db = next(get_db())
                    if clear_existing:
                        logger.info("🧹 Clearing existing questions...")
                        db.query(Question).delete()
                        db.commit()

                    importer = ICFESExcelImporter(db)
                    result = importer.import_excel(excel_path, validate_only=False)
                    logger.info(f"✅ Imported {result['imported_questions']} questions. Errors: {len(result['errors'])}")
                    
                    # Log first few errors for diagnostics
                    if result.get('errors'):
                        logger.warning(f"⚠️ First few import errors:")
                        for err in result.get('errors', [])[:5]:
                            logger.warning(f"  - {err}")
                    
                    break  # Éxito, salir del bucle
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ Import attempt {attempt + 1} failed: {e}. Retrying...")
                        await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                    else:
                        logger.error(f"❌ All import attempts failed: {e}")
                        raise
        else:
            if auto_import and not excel_path:
                logger.warning("⚠️ AUTO_IMPORT_QUESTIONS is true but QUESTIONS_EXCEL_PATH is not set")
            elif auto_import and excel_path and not os.path.exists(excel_path):
                logger.warning(f"⚠️ QUESTIONS_EXCEL_PATH does not exist: {excel_path}")
        
        # Paso 3: Cargar catálogo de temas ICFES
        logger.info("📖 Cargando catálogo de temas ICFES...")
        try:
            catalog_csv_path = os.getenv("ICFES_CATALOG_CSV_PATH", "/app/database/catalogs/icfes_topics.csv")
            if os.path.exists(catalog_csv_path):
                logger.info(f"📁 Loading ICFES topics catalog from: {catalog_csv_path}")
                
                # Reintentos para catálogo ICFES
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        from .scripts.load_icfes_catalog import ICFESCatalogLoader
                        from .core.database import get_db
                        
                        db = next(get_db())
                        loader = ICFESCatalogLoader({
                            'host': os.getenv('DB_HOST', 'postgres'),
                            'port': os.getenv('DB_PORT', '5432'),
                            'database': os.getenv('DB_NAME', 'gameplay_db'),
                            'user': os.getenv('DB_USER', 'gameplay'),
                            'password': os.getenv('DB_PASSWORD', '')
                        })
                        loader.run(catalog_csv_path)
                        logger.info("✅ ICFES topics catalog loaded successfully")
                        
                        # Cargar YouTube links después del catálogo ICFES
                        try:
                            from .scripts.load_youtube_links import YouTubeLinksLoader
                            youtube_loader = YouTubeLinksLoader()
                            await youtube_loader.load_youtube_links()
                            logger.info("✅ YouTube links catalog loaded successfully")
                        except Exception as e:
                            logger.warning(f"⚠️ YouTube links loading failed: {e}")
                            logger.warning("⚠️ Video recommendations will work with limited content")
                        
                        break  # Éxito, salir del bucle
                        
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"⚠️ ICFES catalog attempt {attempt + 1} failed: {e}. Retrying...")
                            await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                        else:
                            logger.error(f"❌ All ICFES catalog attempts failed: {e}")
                            logger.warning("⚠️ ICFES system will work without topics catalog")
            else:
                logger.warning(f"⚠️ ICFES catalog CSV not found at: {catalog_csv_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load ICFES topics catalog: {e}")
            logger.warning("⚠️ ICFES system will work without topics catalog")
        
        logger.info("🎉 Configuración automática del sistema completada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Auto-import on startup failed: {e}")
        logger.error("⚠️ El sistema puede no funcionar correctamente")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ICFES LEVELING API...")
    
    # Stop media cache background service
    try:
        from .services.media_background_service import media_background_service
        await media_background_service.stop_background_service()
        logger.info("✅ Media cache background service stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping media cache background service: {e}")
    
    # Cleanup optimization service resources
    try:
        from .services.media_optimization_service import media_optimization_service
        media_optimization_service.cleanup()
        logger.info("✅ Media optimization service cleaned up")
    except Exception as e:
        logger.error(f"❌ Error cleaning up media optimization service: {e}")

# Crear aplicación FastAPI
app = FastAPI(
    title="ICFES LEVELING API",
    description="API para el sistema de gamificación educativa ICFES Leveling",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Configurar CORS con configuración optimizada para desarrollo
# In development, allow all origins for Flutter web debugging
if settings.ENVIRONMENT == "development" or settings.DEBUG:
    ALLOWED_ORIGINS = ["*"]
else:
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:4001,http://127.0.0.1:4001,http://localhost:4000,http://127.0.0.1:4000,http://localhost:4002,http://127.0.0.1:4002,http://localhost:8002,http://127.0.0.1:8002").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True if ALLOWED_ORIGINS != ["*"] else False,  # Cannot use credentials with wildcard origin
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware for secure session management
import secrets
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('SESSION_SECRET', secrets.token_urlsafe(32)),
    max_age=7200,  # 2 hours
    https_only=(settings.ENVIRONMENT == "production"),  # True in production, False in development
    same_site='lax'
)

# Media rate limiting middleware
app.middleware("http")(media_rate_limit_middleware)

# Media cache middleware (cache reads work; cache writes silently skip streaming responses)
from .middleware.media_cache_middleware import setup_media_cache_middleware
setup_media_cache_middleware(app)

# Global OPTIONS handler for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle OPTIONS requests for CORS preflight"""
    return {"message": "OK"}

# TrustedHost middleware (production only)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Guest mode limits middleware
app.add_middleware(GuestLimitsMiddleware)

# Security middleware (headers, request logging)
add_security_middleware(app)

# Static files (create directory if it doesn't exist)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Exception handler global mejorado
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# ============================================
# REGISTER ROUTERS (CLEANED UP)
# ============================================

# TIER 1: ESSENTIAL (Authentication & Core)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")
app.include_router(mobile_api.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")
app.include_router(node_progress.router, prefix="/api/v1")

# TIER 2: GAMIFICATION (Core game mechanics)
app.include_router(hearts.router, prefix="/api/v1")
app.include_router(streak.router, prefix="/api/v1")
app.include_router(economy.router, prefix="/api/v1")
app.include_router(answers.router, prefix="/api/v1")
app.include_router(battles.router, prefix="/api/v1")
app.include_router(practice.router, prefix="/api/v1")
app.include_router(achievements.router, prefix="/api/v1")
app.include_router(quests.router, prefix="/api/v1")
app.include_router(mastery.router, prefix="/api/v1") 

# TIER 3: DIAGNOSTIC SYSTEM
app.include_router(diagnostic_two_phase.router, prefix="/api/v1")
app.include_router(diagnostic_public.router, prefix="/api/v1")
app.include_router(monthly_reassessment.router, prefix="/api/v1")
app.include_router(verified_image_diagnostic.router, prefix="/api/v1")
app.include_router(quizzes.router, prefix="/api/v1")

# TIER 4: STUDY PLANS & RECOMMENDATIONS
app.include_router(study_plans.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(personality.router, prefix="/api/v1")
app.include_router(claude_study_plan_generator.router, prefix="/api/v1")
app.include_router(integrated_study_plan_api.router, prefix="/api/v1")
app.include_router(spaced_repetition.router, prefix="/api/v1")  # SM-2 spaced repetition
app.include_router(personalized_study_plan_api.router)  # Self-contained prefix /api/v1/...

# TIER 5: VIDEO & CONTENT
app.include_router(videos.router, prefix="/api/v1")
app.include_router(video_recommendations.router, prefix="/api/v1")
app.include_router(youtube_api.router, prefix="/api/v1")
app.include_router(icfes_catalog.router, prefix="/api/v1")
app.include_router(intelligent_video_recommendations.router)  # Self-contained prefix /api/v1/...

# TIER 6: SOCIAL & COMPETITIVE
app.include_router(guilds.router, prefix="/api/v1")
app.include_router(leagues.router, prefix="/api/v1")
app.include_router(leaderboard.router, prefix="/api/v1")
app.include_router(store.router, prefix="/api/v1")
app.include_router(boss_raid.router, prefix="/api/v1")
app.include_router(bosses.router, prefix="/api/v1")
app.include_router(premium_simple.router, prefix="/api/v1")
app.include_router(dungeons.router, prefix="/api/v1")  # Solo Leveling-style dungeon gates

# TIER 7: AI & ASSETS
app.include_router(ai.router, prefix="/api/v1")
app.include_router(ai_tips.router, prefix="/api/v1")
app.include_router(images_api.router)
app.include_router(dynamic_subjects.router, prefix="/api/v1")
app.include_router(images.router, prefix="/api/v1/images", tags=["images"]) # Serve static images

# TIER 8: ANALYTICS & DASHBOARD
app.include_router(analytics_advanced.router, prefix="/api/v1")
app.include_router(student_dashboard.router)
app.include_router(advanced_stats.router, prefix="/api/v1")  # Heatmap, National Comparison, Skill Tree, Triggers

# TIER 9: CACHED/OPTIMIZED ENDPOINTS
app.include_router(users_cached.router, prefix="/api/v1")
app.include_router(questions_cached.router, prefix="/api/v1")
app.include_router(battles_cached.router, prefix="/api/v1")

# TIER 10: PUSH NOTIFICATIONS
app.include_router(notifications.router, prefix="/api/v1")


# Rutas de health check
@app.get("/")
async def root():
    return {
        "message": "ICFES LEVELING API",
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        from sqlalchemy import text
        from datetime import datetime
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

@app.get("/api/v1/health")
async def api_health_check():
    """API health check endpoint"""
    from datetime import datetime
    return {
        "status": "healthy",
        "api_version": "v1",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    try:
        import time
        from datetime import datetime
        import psutil

        process = psutil.Process()
        memory_info = process.memory_info()

        lines = []
        lines.append(f"# HELP process_resident_memory_bytes Resident memory size in bytes")
        lines.append(f"# TYPE process_resident_memory_bytes gauge")
        lines.append(f"process_resident_memory_bytes {memory_info.rss}")
        lines.append(f"# HELP process_cpu_percent CPU usage percentage")
        lines.append(f"# TYPE process_cpu_percent gauge")
        lines.append(f"process_cpu_percent {process.cpu_percent()}")
        lines.append(f"# HELP process_open_fds Number of open file descriptors")
        lines.append(f"# TYPE process_open_fds gauge")
        try:
            lines.append(f"process_open_fds {process.num_fds()}")
        except AttributeError:
            lines.append(f"process_open_fds {len(process.open_files())}")
        lines.append(f"# HELP process_uptime_seconds Process uptime in seconds")
        lines.append(f"# TYPE process_uptime_seconds gauge")
        lines.append(f"process_uptime_seconds {time.time() - process.create_time()}")

        from fastapi.responses import PlainTextResponse
        return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain")
    except ImportError:
        return {"error": "psutil not installed", "status": "metrics_unavailable"}
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return {"error": str(e)}

# Analytics endpoint
@app.post("/api/v1/analytics/track")
async def track_user_event(request: Request, event: dict):
    """Track user events for analytics and improvement"""
    try:
        import json
        from datetime import datetime
        
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'session_id': request.session.get('session_id', 'anonymous'),
            'event_type': event.get('type'),
            'event_data': event.get('data', {}),
            'user_agent': request.headers.get('user-agent', ''),
            'ip_address': request.client.host if request.client else 'unknown'
        }
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Simple file logging (can upgrade to database later)
        with open('logs/analytics.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(event_data, ensure_ascii=False) + '\n')
            
        return {"status": "tracked", "event_type": event.get('type')}
    except Exception as e:
        logger.error(f"Analytics tracking error: {e}")
        return {"status": "error", "message": str(e)}

# Session management endpoints
@app.post("/api/v1/session/store")
async def store_session_data(request: Request, data: dict):
    """Store data securely in server session"""
    try:
        from datetime import datetime
        data_type = data.get('type')
        data_content = data.get('content', {})
        
        if data_type == 'diagnostic_results':
            request.session['diagnostic_results'] = {
                'score': data_content.get('score'),
                'percentage': data_content.get('percentage'),
                'subject_id': data_content.get('subject_id'),
                'total_questions': data_content.get('total_questions'),
                'weaknesses': data_content.get('weaknesses', []),
                'timestamp': datetime.now().isoformat()
            }
        
        return {"status": "stored", "type": data_type}
    except Exception as e:
        logger.error(f"Session storage error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/v1/session/get/{data_type}")
async def get_session_data(request: Request, data_type: str):
    """Get data from secure server session"""
    try:
        data = request.session.get(data_type)
        if not data:
            raise HTTPException(status_code=404, detail=f"No {data_type} found in session")
        return {"status": "found", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cleanup endpoint
@app.post("/api/v1/cleanup")
async def cleanup_old_sessions():
    """Cleanup old sessions and temporary data"""
    logger.info("Cleaning up old sessions...")
    # Implementar lógica de limpieza
    return "Old sessions cleaned"

# Configuración de Celery (para tareas en segundo plano)
# Import the scheduled tasks celery app which includes all task configurations
from .tasks.scheduled import celery_app as scheduled_celery_app

# Re-export the celery app from scheduled tasks (includes beat schedule)
celery_app = scheduled_celery_app

# Legacy tasks - kept for backward compatibility
@celery_app.task(name="app.main.generate_daily_quests")
def generate_daily_quests():
    """Generar quests diarios para todos los usuarios"""
    logger.info("Generating daily quests...")
    # Implementar lógica de generación de quests
    return "Daily quests generated"

@celery_app.task(name="app.main.update_leaderboard")
def update_leaderboard():
    """Actualizar leaderboard global"""
    logger.info("Updating global leaderboard...")
    # Implementar lógica de actualización de leaderboard
    return "Leaderboard updated"

@celery_app.task(name="app.main.cleanup_old_sessions_task")
def cleanup_old_sessions_task():
    """Limpiar sesiones antiguas"""
    logger.info("Cleaning up old sessions...")
    # Implementar lógica de limpieza
    return "Old sessions cleaned"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=4000,  # ✅ ALINEADO: Puerto 4000 para consistencia con Docker
        reload=True
    )
