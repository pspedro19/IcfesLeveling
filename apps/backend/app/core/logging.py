import logging
import sys
from datetime import datetime
from pathlib import Path
import json
import os
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                'filename', 'module', 'lineno', 'funcName', 'created', 
                'msecs', 'relativeCreated', 'thread', 'threadName', 
                'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 
                'stack_info'
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)

class ContextFilter(logging.Filter):
    """Add contextual information to log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add service name
        record.service = "icfes-backend"
        
        # Add environment
        record.environment = os.getenv("ENVIRONMENT", "development")
        
        # Add request ID if available (would be set by middleware)
        record.request_id = getattr(record, 'request_id', None)
        
        return True

def setup_logging():
    """Setup application logging configuration"""
    
    # Get log level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler for development
    if os.getenv("ENVIRONMENT", "development") == "development":
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler for all environments
    file_handler = logging.FileHandler("logs/app.log")
    file_handler.setLevel(getattr(logging, log_level))
    
    # Use JSON formatting in production
    if os.getenv("ENVIRONMENT") == "production":
        json_formatter = JSONFormatter()
        file_handler.setFormatter(json_formatter)
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
    
    # Add context filter
    context_filter = ContextFilter()
    file_handler.addFilter(context_filter)
    
    root_logger.addHandler(file_handler)
    
    # Error file handler for errors and above
    error_handler = logging.FileHandler("logs/error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter() if os.getenv("ENVIRONMENT") == "production" else file_formatter)
    error_handler.addFilter(context_filter)
    root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    
    # Silence verbose third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Application logger
    app_logger = logging.getLogger("icfes.app")
    app_logger.setLevel(logging.INFO)
    
    # Database logger
    db_logger = logging.getLogger("icfes.database")
    db_logger.setLevel(logging.INFO)
    
    # Security logger for auth events
    security_logger = logging.getLogger("icfes.security")
    security_logger.setLevel(logging.INFO)
    
    # Performance logger
    performance_logger = logging.getLogger("icfes.performance")
    performance_logger.setLevel(logging.INFO)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(f"icfes.{name}")

# Performance logging utilities
def log_performance(operation: str, duration: float, **kwargs):
    """Log performance metrics"""
    logger = get_logger("performance")
    logger.info(
        f"Performance: {operation}",
        extra={
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            "metric_type": "performance",
            **kwargs
        }
    )

def log_user_action(user_id: int, action: str, **kwargs):
    """Log user actions for analytics"""
    logger = get_logger("user_action")
    logger.info(
        f"User action: {action}",
        extra={
            "user_id": user_id,
            "action": action,
            "metric_type": "user_action",
            **kwargs
        }
    )

def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "info"):
    """Log security events"""
    logger = get_logger("security")
    
    log_method = getattr(logger, severity.lower(), logger.info)
    log_method(
        f"Security event: {event_type}",
        extra={
            "event_type": event_type,
            "metric_type": "security",
            **details
        }
    )

def log_database_query(query: str, duration: float, **kwargs):
    """Log database query performance"""
    logger = get_logger("database")
    logger.debug(
        f"Database query executed",
        extra={
            "query": query[:200] + "..." if len(query) > 200 else query,
            "duration_ms": round(duration * 1000, 2),
            "metric_type": "database_query",
            **kwargs
        }
    )

# Request logging middleware helper
def log_request(method: str, path: str, status_code: int, duration: float, **kwargs):
    """Log HTTP requests"""
    logger = get_logger("api")
    
    level = logging.ERROR if status_code >= 500 else logging.WARNING if status_code >= 400 else logging.INFO
    
    logger.log(
        level,
        f"{method} {path} - {status_code}",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2),
            "metric_type": "http_request",
            **kwargs
        }
    )

# Initialize logging when module is imported
logger = setup_logging()