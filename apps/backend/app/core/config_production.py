"""Production-ready configuration with security best practices"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from functools import lru_cache

class ProductionSettings(BaseSettings):
    """Production configuration with enhanced security"""
    
    # Environment
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    APP_NAME: str = "ICFES LEVELING API"
    APP_VERSION: str = "1.0.0"
    
    # Security - NO DEFAULT VALUES FOR PRODUCTION
    JWT_SECRET: str
    SECRET_KEY: str  
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database - SSL REQUIRED
    DATABASE_URL: str
    DB_SSL_MODE: str = "require"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True
    
    # Redis - AUTH REQUIRED
    REDIS_URL: str
    REDIS_PASSWORD: str
    REDIS_SSL: bool = True
    REDIS_SSL_CERT_REQS: str = "required"
    REDIS_CACHE_TTL: int = 3600
    
    # ClickHouse
    CLICKHOUSE_URL: str
    CLICKHOUSE_DATABASE: str = "icfes_analytics"
    CLICKHOUSE_SSL: bool = True
    
    # External APIs - REQUIRED
    OPENAI_API_KEY: str
    YOUTUBE_API_KEY: Optional[str] = None
    
    # CORS - STRICT PRODUCTION DOMAINS
    ALLOWED_ORIGINS: List[str] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # SSL/TLS
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None
    FORCE_HTTPS: bool = True
    
    # Security Headers
    SECURE_HEADERS_ENABLED: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    CSP_POLICY: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 100
    RATE_LIMIT_STORAGE: str = "redis"
    
    # File Upload Security
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    UPLOAD_VIRUS_SCAN: bool = True
    UPLOAD_PATH: str = "/app/uploads"
    
    # Logging & Monitoring
    LOG_LEVEL: str = "WARNING"
    LOG_FORMAT: str = "json"
    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    
    # Performance
    MAX_WORKERS: int = 4
    WORKER_TIMEOUT: int = 30
    KEEP_ALIVE: int = 2
    MAX_REQUESTS: int = 1000
    MAX_REQUESTS_JITTER: int = 100
    
    # Session Security
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "strict"
    SESSION_COOKIE_MAX_AGE: int = 3600
    
    # Game Settings - PRODUCTION VALUES
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
    AI_RATE_LIMIT_PER_HOUR: int = 100
    
    # Backup & Recovery
    BACKUP_ENABLED: bool = True
    BACKUP_ENCRYPTION_KEY: str
    BACKUP_S3_BUCKET: str
    BACKUP_SCHEDULE: str = "0 2 * * *"  # Daily at 2 AM
    BACKUP_RETENTION_DAYS: int = 30
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    
    # Health Checks
    HEALTH_CHECK_INTERVAL: int = 30
    HEALTH_CHECK_TIMEOUT: int = 10
    HEALTH_CHECK_RETRIES: int = 3
    
    # Admin Security
    ADMIN_IPS: List[str] = []  # Restrict admin access to specific IPs
    ADMIN_2FA_REQUIRED: bool = True
    
    class Config:
        env_file = ".env.production"
        case_sensitive = True
        validate_assignment = True

@lru_cache()
def get_production_settings() -> ProductionSettings:
    """Get cached production settings"""
    return ProductionSettings()

# Enhanced logging configuration for production
PRODUCTION_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d"
        },
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": "WARNING"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/icfes/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
            "level": "WARNING"
        },
        "security": {
            "class": "logging.handlers.RotatingFileHandler", 
            "filename": "/var/log/icfes/security.log",
            "maxBytes": 10485760,
            "backupCount": 10,
            "formatter": "json",
            "level": "INFO"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False
        },
        "security": {
            "handlers": ["security"],
            "level": "INFO", 
            "propagate": False
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False
        },
        "sqlalchemy": {
            "handlers": ["file"],
            "level": "ERROR",
            "propagate": False
        }
    }
}