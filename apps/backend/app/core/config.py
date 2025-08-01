from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://gameplay:gameplay123@postgres:5432/gameplay_db"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # JWT
    JWT_SECRET: str = "your-super-secret-jwt-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://frontend:3000"]
    
    # App
    APP_NAME: str = "ICFES LEVELING API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
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
    CLICKHOUSE_URL: str = "http://clickhouse:9000"
    CLICKHOUSE_DATABASE: str = "gameplay_analytics"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instancia global de configuración
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