from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    model_config = ConfigDict(extra='allow', env_file='.env')
    # Database
    DATABASE_URL: str = "postgresql://gameplay:gameplay123@postgres:5432/gameplay_db"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 100
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_CONNECTION_TIMEOUT: int = 10
    REDIS_RETRY_ON_TIMEOUT: bool = True
    
    # JWT
    JWT_SECRET: str = "your-super-secret-jwt-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # WOMPI Payment Gateway (Colombia)
    WOMPI_PUBLIC_KEY: str = os.getenv("WOMPI_PUBLIC_KEY", "pub_test_XXXXXXXXX")
    WOMPI_PRIVATE_KEY: str = os.getenv("WOMPI_PRIVATE_KEY", "prv_test_XXXXXXXXX")
    WOMPI_EVENT_SECRET: str = os.getenv("WOMPI_EVENT_SECRET", "test_events_XXXXXXXXX")
    
    # CORS - Updated to include Wompi domains
    CORS_ORIGINS: list = [
        "http://localhost:4001",  # Frontend principal
        "http://127.0.0.1:4001",
        "http://localhost:4000",  # Backend expuesto
        "http://127.0.0.1:4000",
        "http://localhost:4002",  # WebSocket expuesto
        "http://127.0.0.1:4002",
        "http://localhost:8002",  # AI Service
        "http://127.0.0.1:8002",
        "https://checkout.wompi.co",  # Wompi production checkout
        "https://checkout-test.wompi.co",  # Wompi test checkout
    ]
    
    # App
    APP_NAME: str = "ICFES LEVELING API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:4001"
    PORT: int = 4000
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024 # 10MB
    ALLOWED_EXTENSIONS: list = [".jpg", ".jpeg", ".png", ".gif"]
    
    # Game Settings
    MAX_LEVEL: int = 100
    BASE_HP: int = 100
    BASE_MP: int = 50
    BASE_POWER: int = 10
    BASE_WISDOM: int = 10
    BASE_SPEED: int = 10
    
    # Battle Settings
    BATTLE_TIMEOUT_SECONDS: int = 30
    MAX_COMBO_COUNT: int = 10
    
    # AI Settings
    AI_CACHE_TTL_DAYS: int = 30
    AI_MAX_TOKENS: int = 500
    
    # Analytics
    CLICKHOUSE_URL: str = "clickhouse://default:clickhouse123@clickhouse:9000/gameplay_analytics"
    CLICKHOUSE_DATABASE: str = "gameplay_analytics"
    
    # Media Cache Settings
    MEDIA_CACHE_TTL: int = 3600  # 1 hour default
    MEDIA_CACHE_PREFIX: str = "img"
    MEDIA_CACHE_COMPRESSION: bool = True
    MEDIA_CACHE_COMPRESSION_LEVEL: int = 6
    MEDIA_CACHE_MAX_SIZE: int = 50 * 1024 * 1024  # 50MB per cached item
    
    # Media Performance Settings
    MEDIA_RESIZE_ENABLED: bool = True
    MEDIA_LAZY_LOADING: bool = True
    MEDIA_PREFETCH_ENABLED: bool = True
    MEDIA_PREFETCH_LIMIT: int = 10
    
    # Media Metrics Settings
    MEDIA_METRICS_RETENTION_DAYS: int = 30
    MEDIA_METRICS_TOP_LIMIT: int = 10
    MEDIA_ALERT_CACHE_MISS_THRESHOLD: float = 0.8  # 80% miss rate
    
    # Background Tasks Settings
    BACKGROUND_TASK_INTERVAL: int = 300  # 5 minutes
    CACHE_INVALIDATION_CHECK_INTERVAL: int = 60  # 1 minute
    

settings = Settings()

# Configuración de logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/app.log",
            "formatter": "detailed",
            "level": "DEBUG"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        },
        "sqlalchemy": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False
        }
    }
}