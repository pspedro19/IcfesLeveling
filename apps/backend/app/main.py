from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.trustedhost import TrustedHostMiddleware  # Comentado temporalmente
from fastapi.responses import JSONResponse
# from fastapi.staticfiles import StaticFiles  # Comentado temporalmente
from contextlib import asynccontextmanager
import logging
import logging.config
import os

from .core.config import settings, LOGGING_CONFIG
from .core.database import engine, Base
# from .middleware.guest_limits import GuestLimitsMiddleware  # Comentado temporalmente
from .routes import auth, auth_simple, questions, battles, ai, leaderboard, quests, personality, diagnostic, diagnostic_public, diagnostic_simple, study_plans, videos, video_recommendations, quizzes, bosses, analytics, monthly_reassessment, premium_simple as premium, guilds, achievements, store, analytics_advanced, questions_cached, users_cached, battles_cached, ai_tips, recommendations, admin, video_tracking, exercise_tracking, rank_reevaluation, advanced_health, video_progress_api, yml_plans
from .routes.icfes import recommendations as icfes_recommendations
from .routes import icfes_catalog

# Configurar logging
os.makedirs("logs", exist_ok=True)
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

def _ensure_question_columns() -> None:
    """Ensure new multimedia columns exist on questions table (idempotent)."""
    try:
        from sqlalchemy import text
        ddl_statements = [
            "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS pregunta_texto TEXT",
            "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS pregunta_imagen VARCHAR(500)",
            "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_a_texto TEXT",
            "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_a_imagen VARCHAR(500)",
            "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_b_texto TEXT",
            "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_b_imagen VARCHAR(500)",
            "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_c_texto TEXT",
            "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_c_imagen VARCHAR(500)",
            "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_d_texto TEXT",
            "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS opcion_d_imagen VARCHAR(500)",
            "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS respuesta_correcta VARCHAR(1)"
        ]
        with engine.begin() as conn:
            for ddl in ddl_statements:
                conn.execute(text(ddl))
        logger.info("Question table columns verified/created successfully")
    except Exception as e:
        logger.error(f"Failed verifying question columns: {e}")

def _ensure_diagnostic_test_columns() -> None:
    """Ensure all required columns exist on diagnostic_tests table (idempotent)."""
    try:
        from sqlalchemy import text
        ddl_statements = [
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS reassessment_type VARCHAR(50)",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS original_test_id UUID REFERENCES diagnostic_tests(id)",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS is_monthly_reassessment BOOLEAN DEFAULT FALSE",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS days_since_initial INTEGER",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS comparison_with_initial JSONB",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS plan_regenerated BOOLEAN DEFAULT FALSE",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS new_goals_generated BOOLEAN DEFAULT FALSE",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS notification_sent BOOLEAN DEFAULT FALSE",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS questions_answered INTEGER DEFAULT 0",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS time_spent_seconds INTEGER DEFAULT 0",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS score_percentage DECIMAL(5,2) DEFAULT 0.00",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS score_by_topic JSONB DEFAULT '{}'",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'in_progress'",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS started_at TIMESTAMP",
            "ALTER TABLE IF EXISTS diagnostic_tests ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP"
        ]
        with engine.begin() as conn:
            for ddl in ddl_statements:
                conn.execute(text(ddl))
        logger.info("Diagnostic test table columns verified/created successfully")
    except Exception as e:
        logger.error(f"Failed verifying diagnostic test columns: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ICFES LEVELING API...")
    
    # Crear tablas si no existen
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    
    # Configurar monitores del sistema
    try:
        from .monitoring.schema_guard import setup_schema_guard
        from .monitoring.system_health import setup_system_health_monitor
        from .routes.advanced_health import set_monitors
        
        # Inicializar monitores
        schema_guard = setup_schema_guard(app, engine)
        system_health_monitor = setup_system_health_monitor(app, engine)
        
        # Configurar monitores en los endpoints
        set_monitors(schema_guard, system_health_monitor)
        
        logger.info("✅ Monitores del sistema configurados exitosamente")
        logger.info("   - Schema Guard: Protegiendo integridad de BD")
        logger.info("   - System Health Monitor: Monitoreando salud del sistema")
        
    except Exception as e:
        logger.error(f"Error configurando monitores: {e}")
        logger.warning("⚠️ Sistema funcionará sin monitoreo avanzado")
    
    # Asegurar columnas necesarias e importar preguntas desde Excel si está habilitado por env
    try:
        logger.info("🔧 Iniciando configuración automática del sistema...")
        
        # Paso 1: Asegurar estructura de base de datos
        logger.info("📊 Verificando estructura de base de datos...")
        _ensure_question_columns()
        _ensure_diagnostic_test_columns()
        logger.info("✅ Estructura de base de datos verificada")
        
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
                        import time
                        time.sleep(2 ** attempt)  # Backoff exponencial
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
            catalog_csv_path = os.getenv("ICFES_CATALOG_CSV_PATH", "/app/01_icfes_topics_catalog.csv")
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
                            'host': 'postgres',
                            'port': '5432',
                            'database': 'gameplay_db',
                            'user': 'gameplay',
                            'password': 'gameplay123'
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
                            import time
                            time.sleep(2 ** attempt)  # Backoff exponencial
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

# Crear aplicación FastAPI
app = FastAPI(
    title="ICFES LEVELING API",
    description="API para el sistema de gamificación educativa ICFES Leveling",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Configurar CORS con configuración optimizada para desarrollo
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:4001,http://127.0.0.1:4001,http://localhost:4000,http://127.0.0.1:4000,http://localhost:4002,http://127.0.0.1:4002,http://localhost:8002,http://127.0.0.1:8002").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
    allow_credentials=True,  # Permitir cookies y headers de autorización
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global OPTIONS handler for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle OPTIONS requests for CORS preflight"""
    return {"message": "OK"}

# Configurar TrustedHost (comentado temporalmente)
# if settings.ENVIRONMENT == "production":
#     app.add_middleware(
#         TrustedHostMiddleware,
#         allowed_hosts=settings.ALLOWED_HOSTS
#     )

# Agregar middleware de límites para guest mode (comentado temporalmente)
# app.add_middleware(GuestLimitsMiddleware)

# Configurar archivos estáticos (comentado temporalmente)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Exception handler global mejorado
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Incluir routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(auth_simple.router, prefix="/api/v1")  # Ruta simple para testing
app.include_router(questions.router, prefix="/api/v1")
app.include_router(battles.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(leaderboard.router, prefix="/api/v1")
app.include_router(quests.router, prefix="/api/v1")
app.include_router(personality.router, prefix="/api/v1")
app.include_router(diagnostic.router, prefix="/api/v1")
# Alias para compatibilidad con clientes que usan 'agnostic' por error tipográfico
app.include_router(diagnostic.router, prefix="/api/v1/agnostic")
app.include_router(diagnostic_public.router)  # Sin prefijo /api/v1 para acceso directo
app.include_router(diagnostic_simple.router)  # Ruta simple para testing
app.include_router(study_plans.router, prefix="/api/v1")
app.include_router(videos.router, prefix="/api/v1")
app.include_router(video_recommendations.router, prefix="/api/v1/video-recommendations")
app.include_router(quizzes.router, prefix="/api/v1")
app.include_router(bosses.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(analytics.router)  # Ruta adicional para compatibilidad con frontend (/analytics/events)
app.include_router(analytics_advanced.router, prefix="/api/v1")
app.include_router(questions_cached.router, prefix="/api/v1")
app.include_router(users_cached.router, prefix="/api/v1")
app.include_router(battles_cached.router, prefix="/api/v1")
app.include_router(ai_tips.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(monthly_reassessment.router, prefix="/api/v1")
app.include_router(premium.router, prefix="/api/v1")
app.include_router(guilds.router, prefix="/api/v1")
app.include_router(achievements.router, prefix="/api/v1")
app.include_router(store.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(video_tracking.router, prefix="/api/v1")
app.include_router(exercise_tracking.router, prefix="/api/v1")
app.include_router(rank_reevaluation.router, prefix="/api/v1")
app.include_router(icfes_recommendations.router, prefix="/api/v1")  # Rutas ICFES
app.include_router(icfes_catalog.router, prefix="/api/v1")  # Catálogo ICFES
app.include_router(yml_plans.router)  # Rutas YML personalizadas
app.include_router(video_progress_api.router)  # Sistema de Video Progress
app.include_router(advanced_health.router)  # Endpoints de salud avanzada

# Importar y registrar el nuevo router de YouTube API
from .routes import youtube_api
app.include_router(youtube_api.router)

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
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2024-01-01T00:00:00Z"
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
    return {
        "status": "healthy",
        "api_version": "v1",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Cleanup endpoint
@app.post("/api/v1/cleanup")
async def cleanup_old_sessions():
    """Cleanup old sessions and temporary data"""
    logger.info("Cleaning up old sessions...")
    # Implementar lógica de limpieza
    return "Old sessions cleaned"

# Configuración de Celery (para tareas en segundo plano)
from celery import Celery

celery_app = Celery(
    "icfes_leveling",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Tareas de Celery
@celery_app.task
def generate_daily_quests():
    """Generar quests diarios para todos los usuarios"""
    logger.info("Generating daily quests...")
    # Implementar lógica de generación de quests
    return "Daily quests generated"

@celery_app.task
def update_leaderboard():
    """Actualizar leaderboard global"""
    logger.info("Updating global leaderboard...")
    # Implementar lógica de actualización de leaderboard
    return "Leaderboard updated"

@celery_app.task
def cleanup_old_sessions():
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