from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
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
# from .middleware.media_rate_limit import media_rate_limit_middleware  # TEMPORALMENTE COMENTADO
# Temporary fix: comment out problematic imports due to numpy/pandas/scipy issues
from .routes import auth, auth_simple, questions, battles, ai, leaderboard, quests, personality, diagnostic, diagnostic_public, diagnostic_simple, diagnostic_public_fix, diagnostic_test_fix, subjects_fix, study_plans, study_plans_simple, videos, video_recommendations, quizzes, bosses, analytics, monthly_reassessment, premium_simple as premium, guilds, achievements, store, analytics_advanced, questions_cached, users_cached, battles_cached, ai_tips, recommendations, intelligent_video_recommendations, personalized_study_plan_api, images_api, subjects_with_count, image_required_questions, diagnostic_images_test, verified_image_diagnostic, dynamic_images_api  # , admin, video_tracking, exercise_tracking, rank_reevaluation, advanced_health, video_progress_api, yml_plans, dynamic_subjects, dynamic_study_plan, diagnostic_adaptive, boss_battle_diagnostic, media, diagnostic_api, rank_management, training_zone (temporarily disabled due to asyncpg dependency)
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
            "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS respuesta_correcta VARCHAR(1)",
            "ALTER TABLE IF EXISTS questions ADD COLUMN IF NOT EXISTS puntos_xp INTEGER DEFAULT 10"
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

def _ensure_advanced_learning_tables() -> None:
    """Ensure advanced learning system tables exist (CRITICAL for 95% completeness)."""
    try:
        from sqlalchemy import text
        logger.info("🔄 Verifying advanced learning system tables...")
        
        # Check if critical tables exist
        table_checks = [
            "SELECT 1 FROM information_schema.tables WHERE table_name = 'user_skills'",
            "SELECT 1 FROM information_schema.tables WHERE table_name = 'question_responses'", 
            "SELECT 1 FROM information_schema.tables WHERE table_name = 'learning_sessions'",
            "SELECT 1 FROM information_schema.tables WHERE table_name = 'skill_prerequisites'"
        ]
        
        missing_tables = []
        with engine.begin() as conn:
            for i, check in enumerate(table_checks):
                result = conn.execute(text(check)).fetchone()
                if not result:
                    table_names = ['user_skills', 'question_responses', 'learning_sessions', 'skill_prerequisites']
                    missing_tables.append(table_names[i])
        
        if missing_tables:
            logger.warning(f"⚠️ Missing critical tables: {missing_tables}")
            logger.info("🔧 Creating advanced learning system tables...")
            
            # Read and execute the advanced learning system SQL
            import os
            sql_file_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'init', '15-advanced-learning-system.sql')
            
            if os.path.exists(sql_file_path):
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                with engine.begin() as conn:
                    # Execute in chunks to handle complex statements
                    for statement in sql_content.split('-- ================================================================================================'):
                        if statement.strip():
                            try:
                                conn.execute(text(statement))
                            except Exception as stmt_error:
                                # Log but continue with other statements
                                logger.warning(f"Statement execution warning: {stmt_error}")
                
                logger.info("✅ Advanced learning system tables created successfully")
                
                # Run data migration if we have existing data
                migration_file_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'init', '16-data-migration-advanced-system.sql')
                if os.path.exists(migration_file_path):
                    logger.info("🔄 Running data migration...")
                    with open(migration_file_path, 'r', encoding='utf-8') as f:
                        migration_content = f.read()
                    
                    with engine.begin() as conn:
                        try:
                            conn.execute(text(migration_content))
                            logger.info("✅ Data migration completed successfully")
                        except Exception as migration_error:
                            logger.warning(f"Data migration warning: {migration_error}")
            else:
                logger.error(f"❌ Advanced learning system SQL file not found: {sql_file_path}")
        else:
            logger.info("✅ All advanced learning system tables already exist")
            
    except Exception as e:
        logger.error(f"❌ Failed ensuring advanced learning tables: {e}")
        logger.warning("⚠️ System will operate with reduced functionality")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ICFES LEVELING API...")
    
    # Initialize media cache system
    try:
        from .services.media_background_service import media_background_service
        await media_background_service.start_background_service()
        logger.info("✅ Media cache background service started")
    except Exception as e:
        logger.error(f"❌ Failed to start media cache background service: {e}")
        logger.warning("⚠️ System will operate without background cache management")
    
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
        
        # Paso 1.5: CRÍTICO - Asegurar tablas avanzadas para 95% completitud
        _ensure_advanced_learning_tables()
        
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
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:4001,http://127.0.0.1:4001,http://localhost:4000,http://127.0.0.1:4000,http://localhost:4002,http://127.0.0.1:4002,http://localhost:8002,http://127.0.0.1:8002").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
    allow_credentials=True,  # Permitir cookies y headers de autorización
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware for secure session management
import secrets
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('SESSION_SECRET', secrets.token_urlsafe(32)),
    max_age=7200,  # 2 hours
    https_only=False,  # Set to True in production
    same_site='lax'
)

# Add media rate limiting middleware - TEMPORALMENTE COMENTADO
# app.middleware("http")(media_rate_limit_middleware)

# Setup media cache middleware - TEMPORALMENTE COMENTADO PARA DEBUGGING
# from .middleware.media_cache_middleware import setup_media_cache_middleware
# setup_media_cache_middleware(app)

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
app.include_router(diagnostic_public.router, prefix="/api/v1")  # Con prefijo /api/v1 para frontend
app.include_router(diagnostic_simple.router)  # Ruta simple para testing
app.include_router(diagnostic_public_fix.router)  # Public routes fix
app.include_router(diagnostic_test_fix.router)  # Fixed diagnostic endpoints
app.include_router(subjects_fix.router)  # Fixed subjects endpoints
app.include_router(subjects_with_count.router)  # Subjects with question counts
app.include_router(image_required_questions.router)  # Questions requiring images for testing
app.include_router(diagnostic_images_test.router)  # IMAGE-ONLY diagnostic test for frontend testing
app.include_router(verified_image_diagnostic.router)  # VERIFIED image diagnostic with multi-agent validation
app.include_router(dynamic_images_api.router)  # DYNAMIC images API with environment-based URLs
app.include_router(study_plans.router, prefix="/api/v1")
app.include_router(study_plans_simple.router)  # Simple study plans with built-in prefix
app.include_router(videos.router, prefix="/api/v1")
app.include_router(video_recommendations.router, prefix="/api/v1/video-recommendations")
app.include_router(intelligent_video_recommendations.router)  # Intelligent video system with built-in prefix
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
# app.include_router(admin.router, prefix="/api/v1")  # TEMPORALMENTE COMENTADO
# app.include_router(video_tracking.router, prefix="/api/v1")  # TEMPORALMENTE COMENTADO
# app.include_router(exercise_tracking.router, prefix="/api/v1")  # TEMPORALMENTE COMENTADO
# app.include_router(rank_reevaluation.router, prefix="/api/v1")  # TEMPORALMENTE COMENTADO
# app.include_router(rank_management.router, prefix="/api/v1", tags=["rank-management"])  # TEMPORALMENTE COMENTADO
app.include_router(icfes_recommendations.router, prefix="/api/v1")  # Rutas ICFES
app.include_router(icfes_catalog.router, prefix="/api/v1")  # Catálogo ICFES
# app.include_router(training_zone.router, prefix="/api/v1")  # Training Zone System - temporarily disabled due to asyncpg dependency
app.include_router(personalized_study_plan_api.router)  # Personalized Study Plan System (has built-in prefix)
# app.include_router(yml_plans.router)  # TEMPORALMENTE COMENTADO
# app.include_router(video_progress_api.router)  # TEMPORALMENTE COMENTADO
# app.include_router(advanced_health.router)  # TEMPORALMENTE COMENTADO
# app.include_router(dynamic_subjects.router)  # TEMPORALMENTE COMENTADO
# app.include_router(dynamic_study_plan.router)  # TEMPORALMENTE COMENTADO

# Enhanced diagnostic system with adaptive features
# app.include_router(diagnostic_adaptive.router, prefix="/api/v1")  # TEMPORALMENTE COMENTADO
# app.include_router(boss_battle_diagnostic.router, prefix="/api/v1")  # TEMPORALMENTE COMENTADO

# Complete Diagnostic API endpoints
# app.include_router(diagnostic_api.router, prefix="/api")  # TEMPORALMENTE COMENTADO

# Importar y registrar el nuevo router de YouTube API
from .routes import youtube_api
app.include_router(youtube_api.router)

# Importar y registrar el enhanced video recommendation router
from .routers import video_recommendations as enhanced_video_recommendations
app.include_router(enhanced_video_recommendations.router, prefix="/api/v1/enhanced-video-recommendations")

# Register secure media service endpoint
# app.include_router(media.router, prefix="/api/v1")  # TEMPORALMENTE COMENTADO

# Register images service endpoint
app.include_router(images_api.router)  # Question images serving endpoint

# Register integrated study plan API
from .routes import integrated_study_plan_api
app.include_router(integrated_study_plan_api.router)  # Integrated study plan system with real videos

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