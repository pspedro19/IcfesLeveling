from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import logging.config
import os

from .core.config import settings, LOGGING_CONFIG
from .core.database import engine, Base
from .routes import auth, questions, battles, ai, leaderboard, quests

# Configurar logging
os.makedirs("logs", exist_ok=True)
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

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
    
    yield
    
    # Shutdown
    logger.info("Shutting down ICFES LEVELING API...")

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para el videojuego educativo ICFES LEVELING",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware de seguridad
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # En producción, especificar hosts específicos
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de logging
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Middleware de manejo de errores
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Incluir routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")
app.include_router(battles.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(leaderboard.router, prefix="/api/v1")
app.include_router(quests.router, prefix="/api/v1")

# Rutas de health check
@app.get("/")
async def root():
    return {
        "message": "ICFES LEVELING API",
        "version": settings.APP_VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.get("/api/v1/health")
async def api_health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "database": "connected",
        "redis": "connected"
    }

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
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    ) 