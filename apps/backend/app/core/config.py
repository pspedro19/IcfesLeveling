from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator
from typing import Optional
import os

class Settings(BaseSettings):
    model_config = ConfigDict(extra='allow', env_file='.env')
    # Database - REQUIRED: Must be set via environment variable
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Database connection components (for scripts that need individual params)
    DB_HOST: str = os.getenv("DB_HOST", "postgres")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "gameplay_db")
    DB_USER: str = os.getenv("DB_USER", "gameplay")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    @field_validator('DATABASE_URL')
    @classmethod
    def database_url_must_be_set(cls, v: str) -> str:
        if not v or v == "":
            raise ValueError('DATABASE_URL environment variable is required and must be set')
        return v

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 100
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_CONNECTION_TIMEOUT: int = 10
    REDIS_RETRY_ON_TIMEOUT: bool = True

    # JWT - REQUIRED: Must be set via environment variable
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator('JWT_SECRET')
    @classmethod
    def jwt_secret_must_be_set(cls, v: str) -> str:
        if not v or v == "":
            raise ValueError('JWT_SECRET environment variable is required and must be set')
        if len(v) < 32:
            raise ValueError('JWT_SECRET must be at least 32 characters long for security')
        return v
    
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
    
    # Firebase Admin SDK (Push Notifications)
    FIREBASE_CREDENTIALS_PATH: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_PATH", None)
    GOOGLE_APPLICATION_CREDENTIALS_JSON: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON", None)

    # Sentry for error tracking
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    
    # App
    APP_NAME: str = "ICFES LEVELING API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:4001"
    PORT: int = 4000
    DEFAULT_TIMEZONE: str = "America/Bogota"
    
    # Security - REQUIRED: Must be set via environment variable
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")

    @field_validator('SECRET_KEY')
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if not v or v == "":
            raise ValueError('SECRET_KEY environment variable is required and must be set')
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long for security')
        return v
    
    # Trusted Hosts (production only)
    ALLOWED_HOSTS: list = ["api.icfesleveling.com", "localhost", "127.0.0.1"]

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
    
    # Analytics - ClickHouse credentials via environment variables
    CLICKHOUSE_HOST: str = os.getenv("CLICKHOUSE_HOST", "clickhouse")
    CLICKHOUSE_PORT: int = int(os.getenv("CLICKHOUSE_PORT", "9000"))
    CLICKHOUSE_USER: str = os.getenv("CLICKHOUSE_USER", "default")
    CLICKHOUSE_PASSWORD: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    CLICKHOUSE_DATABASE: str = os.getenv("CLICKHOUSE_DATABASE", "gameplay_analytics")
    
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
    

import logging
    

import json
    

from datetime import datetime
    


    

# ... (rest of the file until LOGGING_CONFIG)
    


    

settings = Settings()
    


    

# Structured JSON Logging
    

class JsonFormatter(logging.Formatter):
    

    def format(self, record):
    

        log_record = {
    

            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
    

            "level": record.levelname,
    

            "message": record.getMessage(),
    

            "logger": record.name,
    

        }
    

        if record.exc_info:
    

            log_record['exc_info'] = self.formatException(record.exc_info)
    

        
    

        # Add extra fields if they exist
    

        extra_fields = record.__dict__.get('extra', {})
    

        if extra_fields:
    

            log_record.update(extra_fields)
    

            
    

        return json.dumps(log_record)
    


    

# Configuración de logging
    

LOGGING_CONFIG = {
    

    "version": 1,
    

    "disable_existing_loggers": False,
    

    "formatters": {
    

        "json": {
    

            "()": JsonFormatter,
    

        },
    

        "default": {
    

            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    

        }
    

    },
    

    "handlers": {
    

        "console": {
    

            "class": "logging.StreamHandler",
    

            "formatter": "json",
    

            "level": "INFO"
    

        },
    

        "file": {

            "class": "logging.handlers.RotatingFileHandler",

            "filename": "logs/app.log",

            "formatter": "json",

            "level": "DEBUG",

            "maxBytes": 10485760,

            "backupCount": 5,

            "encoding": "utf-8"

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
    
