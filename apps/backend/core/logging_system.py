"""
Professional Logging System
Structured logging with multiple outputs and monitoring integration
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Union
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pythonjsonlogger import jsonlogger
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from contextvars import ContextVar

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)

class StructuredLogger:
    """Enhanced logger with structured output and context management"""
    
    def __init__(
        self,
        name: str,
        level: str = "INFO",
        log_dir: str = "/var/log/icfes-leveling",
        max_bytes: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 10,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_json: bool = True,
        enable_sentry: bool = True
    ):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.propagate = False
        
        # Clear existing handlers
        self.logger.handlers = []
        
        # Create log directory
        if enable_file and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Setup handlers
        if enable_console:
            self._setup_console_handler()
        
        if enable_file:
            self._setup_file_handler(log_dir, max_bytes, backup_count, enable_json)
        
        if enable_sentry and os.getenv("SENTRY_DSN"):
            self._setup_sentry()
    
    def _setup_console_handler(self):
        """Setup colored console output for development"""
        console_handler = logging.StreamHandler(sys.stdout)
        
        if os.getenv("NODE_ENV") == "development":
            # Colored output for development
            from colorlog import ColoredFormatter
            formatter = ColoredFormatter(
                "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        else:
            # JSON output for production
            formatter = CustomJsonFormatter()
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(
        self, 
        log_dir: str, 
        max_bytes: int, 
        backup_count: int,
        enable_json: bool
    ):
        """Setup rotating file handlers"""
        # Regular log file
        log_file = os.path.join(log_dir, f"{self.name}.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        
        if enable_json:
            file_handler.setFormatter(CustomJsonFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            )
        
        self.logger.addHandler(file_handler)
        
        # Error log file (errors and above)
        error_file = os.path.join(log_dir, f"{self.name}_errors.log")
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(CustomJsonFormatter())
        self.logger.addHandler(error_handler)
        
        # Daily rotating handler for audit logs
        audit_file = os.path.join(log_dir, f"{self.name}_audit.log")
        audit_handler = TimedRotatingFileHandler(
            audit_file,
            when='midnight',
            interval=1,
            backupCount=30
        )
        audit_handler.setFormatter(CustomJsonFormatter())
        self.logger.addHandler(audit_handler)
    
    def _setup_sentry(self):
        """Setup Sentry integration"""
        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
        
        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            integrations=[sentry_logging],
            traces_sample_rate=0.1,
            environment=os.getenv("ENVIRONMENT", "development")
        )
    
    def _add_context(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """Add request context to log entries"""
        context = {
            'timestamp': datetime.utcnow().isoformat(),
            'logger': self.name,
            'request_id': request_id_var.get(),
            'user_id': user_id_var.get(),
            'session_id': session_id_var.get(),
        }
        
        if extra:
            context.update(extra)
        
        return context
    
    def debug(self, message: str, **kwargs):
        """Debug level logging"""
        extra = self._add_context(kwargs)
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        """Info level logging"""
        extra = self._add_context(kwargs)
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Warning level logging"""
        extra = self._add_context(kwargs)
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, exc_info: bool = True, **kwargs):
        """Error level logging with exception info"""
        extra = self._add_context(kwargs)
        
        if exc_info and sys.exc_info()[0] is not None:
            extra['exception'] = traceback.format_exc()
        
        self.logger.error(message, exc_info=exc_info, extra=extra)
        
        # Send to Sentry
        if os.getenv("SENTRY_DSN"):
            sentry_sdk.capture_message(message, level="error")
    
    def critical(self, message: str, **kwargs):
        """Critical level logging"""
        extra = self._add_context(kwargs)
        self.logger.critical(message, extra=extra)
        
        # Send to Sentry immediately
        if os.getenv("SENTRY_DSN"):
            sentry_sdk.capture_message(message, level="fatal")
    
    def audit(self, action: str, **kwargs):
        """Audit logging for compliance"""
        audit_entry = {
            'audit': True,
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id_var.get(),
            'ip_address': kwargs.get('ip_address'),
            'user_agent': kwargs.get('user_agent'),
            'result': kwargs.get('result', 'success'),
            'metadata': kwargs.get('metadata', {})
        }
        
        self.logger.info(f"AUDIT: {action}", extra=audit_entry)
    
    def metric(self, name: str, value: float, unit: str = None, **tags):
        """Log metrics for monitoring"""
        metric_entry = {
            'metric': True,
            'metric_name': name,
            'metric_value': value,
            'metric_unit': unit,
            'tags': tags,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"METRIC: {name}={value}", extra=metric_entry)
    
    def performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        perf_entry = {
            'performance': True,
            'operation': operation,
            'duration_ms': duration * 1000,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if kwargs:
            perf_entry.update(kwargs)
        
        level = logging.INFO
        if duration > 1.0:  # Warn if operation takes > 1 second
            level = logging.WARNING
        elif duration > 5.0:  # Error if operation takes > 5 seconds
            level = logging.ERROR
        
        self.logger.log(
            level,
            f"PERFORMANCE: {operation} took {duration:.3f}s",
            extra=perf_entry
        )

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        
        # Add location info
        log_record['file'] = record.pathname
        log_record['line'] = record.lineno
        log_record['function'] = record.funcName
        
        # Add process info
        log_record['process'] = record.process
        log_record['thread'] = record.thread
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)

class LoggerFactory:
    """Factory for creating loggers with consistent configuration"""
    
    _loggers: Dict[str, StructuredLogger] = {}
    
    @classmethod
    def get_logger(
        cls,
        name: str,
        level: str = None,
        **kwargs
    ) -> StructuredLogger:
        """Get or create a logger instance"""
        if name not in cls._loggers:
            level = level or os.getenv("LOG_LEVEL", "INFO")
            cls._loggers[name] = StructuredLogger(name, level, **kwargs)
        
        return cls._loggers[name]
    
    @classmethod
    def configure_all(cls, config: Dict[str, Any]):
        """Configure all loggers with global settings"""
        for logger_name, logger_config in config.items():
            cls.get_logger(logger_name, **logger_config)

# Middleware for request logging
class LoggingMiddleware:
    """FastAPI middleware for request/response logging"""
    
    def __init__(self, app, logger: StructuredLogger):
        self.app = app
        self.logger = logger
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Generate request ID
        import uuid
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Extract request info
        path = scope["path"]
        method = scope["method"]
        client = scope.get("client", ["unknown", None])
        
        # Log request
        start_time = datetime.utcnow()
        self.logger.info(
            f"Request started: {method} {path}",
            request_id=request_id,
            method=method,
            path=path,
            client_ip=client[0],
            user_agent=dict(scope.get("headers", {})).get(b"user-agent", b"").decode()
        )
        
        # Track response
        status_code = None
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(
                f"Request failed: {method} {path}",
                request_id=request_id,
                duration=duration,
                error=str(e)
            )
            raise
        finally:
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Log response
            log_level = "info"
            if status_code and status_code >= 400:
                log_level = "warning" if status_code < 500 else "error"
            
            getattr(self.logger, log_level)(
                f"Request completed: {method} {path}",
                request_id=request_id,
                method=method,
                path=path,
                status_code=status_code,
                duration=duration,
                client_ip=client[0]
            )
            
            # Log performance metric
            self.logger.performance(
                f"{method} {path}",
                duration,
                status_code=status_code
            )

# Decorators for function logging
def log_execution(logger: StructuredLogger = None):
    """Decorator to log function execution"""
    def decorator(func):
        import functools
        import inspect
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal logger
            if not logger:
                logger = LoggerFactory.get_logger(func.__module__)
            
            start_time = datetime.utcnow()
            logger.debug(f"Executing {func.__name__}", function=func.__name__)
            
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.debug(
                    f"Completed {func.__name__}",
                    function=func.__name__,
                    duration=duration
                )
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.error(
                    f"Failed {func.__name__}",
                    function=func.__name__,
                    duration=duration,
                    error=str(e)
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal logger
            if not logger:
                logger = LoggerFactory.get_logger(func.__module__)
            
            start_time = datetime.utcnow()
            logger.debug(f"Executing {func.__name__}", function=func.__name__)
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.debug(
                    f"Completed {func.__name__}",
                    function=func.__name__,
                    duration=duration
                )
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.error(
                    f"Failed {func.__name__}",
                    function=func.__name__,
                    duration=duration,
                    error=str(e)
                )
                raise
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Global logger instances
app_logger = LoggerFactory.get_logger("app")
api_logger = LoggerFactory.get_logger("api")
db_logger = LoggerFactory.get_logger("database")
auth_logger = LoggerFactory.get_logger("auth")
ai_logger = LoggerFactory.get_logger("ai")

# Export main components
__all__ = [
    'StructuredLogger',
    'LoggerFactory',
    'LoggingMiddleware',
    'log_execution',
    'app_logger',
    'api_logger',
    'db_logger',
    'auth_logger',
    'ai_logger',
    'request_id_var',
    'user_id_var',
    'session_id_var'
]