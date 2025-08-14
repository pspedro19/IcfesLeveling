from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
import psutil
import os
from datetime import datetime
from typing import Dict, Any
from .core.database import get_db
from .core.redis_cache import cache
import redis

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "icfes-backend",
        "version": os.getenv("APP_VERSION", "1.0.0")
    }

@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with all dependencies"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "icfes-backend",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "checks": {}
    }
    
    overall_healthy = True
    
    # Database health check
    try:
        start_time = time.time()
        db.execute(text("SELECT 1"))
        db_response_time = (time.time() - start_time) * 1000
        
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_response_time, 2)
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Redis health check
    try:
        start_time = time.time()
        cache.redis_client.ping()
        redis_response_time = (time.time() - start_time) * 1000
        
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "response_time_ms": round(redis_response_time, 2)
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        # Redis is not critical, don't mark overall as unhealthy
    
    # System resources check
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status["checks"]["system"] = {
            "status": "healthy",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2)
        }
        
        # Check if resources are critically low
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 95:
            health_status["checks"]["system"]["status"] = "warning"
            health_status["checks"]["system"]["message"] = "High resource usage detected"
        
    except Exception as e:
        health_status["checks"]["system"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        # System checks are not critical for app functionality
    
    # Application-specific checks
    try:
        # Check if we can query users table (basic app functionality)
        start_time = time.time()
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        app_response_time = (time.time() - start_time) * 1000
        
        health_status["checks"]["application"] = {
            "status": "healthy",
            "user_count": user_count,
            "response_time_ms": round(app_response_time, 2)
        }
    except Exception as e:
        health_status["checks"]["application"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # External services check (if any)
    health_status["checks"]["external_services"] = {
        "status": "healthy",
        "message": "No external dependencies configured"
    }
    
    # Update overall status
    if not overall_healthy:
        health_status["status"] = "unhealthy"
    
    # Return appropriate HTTP status
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe endpoint"""
    
    try:
        # Check if database is accessible
        db.execute(text("SELECT 1"))
        
        # Check if essential tables exist
        tables_check = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'subjects', 'questions')
        """)).scalar()
        
        if tables_check < 3:
            raise HTTPException(
                status_code=503, 
                detail="Essential database tables not found"
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    
    try:
        # Basic process health check
        current_time = time.time()
        
        # Check if the process is responsive
        response_time = time.time() - current_time
        
        if response_time > 5.0:  # If it takes more than 5 seconds, something is wrong
            raise HTTPException(
                status_code=503,
                detail="Process is not responsive"
            )
        
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "process_id": os.getpid(),
            "uptime_seconds": time.time() - psutil.Process().create_time()
        }
        
    except psutil.Error:
        # If we can't get process info, but we're responding, we're still alive
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "process_id": os.getpid()
        }

@router.get("/metrics")
async def metrics_endpoint(db: Session = Depends(get_db)):
    """Prometheus-style metrics endpoint"""
    
    try:
        # Database metrics
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        question_count = db.execute(text("SELECT COUNT(*) FROM questions")).scalar()
        
        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        # Redis metrics
        redis_info = {}
        try:
            redis_info = cache.redis_client.info()
        except:
            pass
        
        metrics = {
            "database_users_total": user_count,
            "database_questions_total": question_count,
            "system_cpu_percent": cpu_percent,
            "system_memory_percent": memory.percent,
            "system_memory_available_bytes": memory.available,
            "redis_connected_clients": redis_info.get("connected_clients", 0),
            "redis_used_memory_bytes": redis_info.get("used_memory", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error collecting metrics: {str(e)}"
        )