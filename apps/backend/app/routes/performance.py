#!/usr/bin/env python3
"""
Performance Monitoring API Routes
Provides real-time performance metrics and monitoring capabilities
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging

from app.services.advanced_performance_monitor import performance_monitor
from app.core.database import get_db
from app.core.cache_manager import cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/performance",
    tags=["performance"],
    responses={404: {"description": "Not found"}}
)

@router.get("/dashboard")
async def get_performance_dashboard():
    """Get comprehensive performance dashboard data"""
    try:
        dashboard_data = performance_monitor.get_performance_dashboard_data()
        return JSONResponse(content={
            "status": "success",
            "data": dashboard_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting performance dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance dashboard")

@router.get("/metrics/current")
async def get_current_metrics():
    """Get current system metrics"""
    try:
        current_metrics = await performance_monitor.collect_metrics()
        return JSONResponse(content={
            "status": "success",
            "data": {
                "timestamp": current_metrics.timestamp,
                "cpu_usage": current_metrics.cpu_usage,
                "memory_usage": current_metrics.memory_usage,
                "memory_available_gb": current_metrics.memory_available,
                "disk_io": {
                    "read_kb_per_sec": current_metrics.disk_io_read,
                    "write_kb_per_sec": current_metrics.disk_io_write
                },
                "network_io": {
                    "sent_kb_per_sec": current_metrics.network_sent,
                    "received_kb_per_sec": current_metrics.network_received
                },
                "database_connections": current_metrics.database_connections,
                "cache_hit_rate": current_metrics.cache_hit_rate,
                "response_time_avg": current_metrics.response_time_avg,
                "active_sessions": current_metrics.active_sessions
            }
        })
    except Exception as e:
        logger.error(f"Error getting current metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get current metrics")

@router.get("/metrics/history")
async def get_metrics_history(
    hours: Optional[int] = 1,
    limit: Optional[int] = 100
):
    """Get historical metrics for specified time period"""
    try:
        if hours > 24:
            hours = 24  # Limit to 24 hours
        
        start_time = datetime.now() - timedelta(hours=hours)
        end_time = datetime.now()
        
        metrics = performance_monitor.get_metrics_for_timerange(
            start_time.timestamp(),
            end_time.timestamp()
        )
        
        # Limit results
        if limit and len(metrics) > limit:
            # Sample evenly across time range
            step = len(metrics) // limit
            metrics = metrics[::step][:limit]
        
        # Convert to API format
        history_data = []
        for metric in metrics:
            history_data.append({
                "timestamp": metric.timestamp,
                "cpu_usage": metric.cpu_usage,
                "memory_usage": metric.memory_usage,
                "response_time_avg": metric.response_time_avg,
                "cache_hit_rate": metric.cache_hit_rate,
                "database_connections": metric.database_connections
            })
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "period_hours": hours,
                "total_points": len(history_data),
                "metrics": history_data
            }
        })
    except Exception as e:
        logger.error(f"Error getting metrics history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics history")

@router.get("/alerts")
async def get_active_alerts():
    """Get current active performance alerts"""
    try:
        alerts = []
        for alert in performance_monitor.active_alerts:
            alerts.append({
                "type": alert[0],
                "severity": alert[1],
                "message": alert[2],
                "timestamp": datetime.now().isoformat()  # Active alerts don't have exact timestamps
            })
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "active_alerts": alerts,
                "total_alerts": len(alerts)
            }
        })
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active alerts")

@router.get("/recommendations")
async def get_performance_recommendations():
    """Get performance optimization recommendations"""
    try:
        recommendations = performance_monitor.generate_recommendations()
        
        # Categorize recommendations
        categorized = {
            "HIGH": [r for r in recommendations if r.get("priority") == "HIGH"],
            "MEDIUM": [r for r in recommendations if r.get("priority") == "MEDIUM"],
            "LOW": [r for r in recommendations if r.get("priority") == "LOW"]
        }
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "recommendations": recommendations,
                "by_priority": categorized,
                "total_recommendations": len(recommendations)
            }
        })
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

@router.get("/database/health")
async def get_database_health():
    """Get detailed database health and performance metrics"""
    try:
        from app.core.database import check_database_health
        
        db_health = check_database_health()
        
        # Add query performance stats
        slow_queries = []
        for query_hash, times in performance_monitor.query_performance_stats.items():
            if times:
                import statistics
                avg_time = statistics.mean(times)
                if avg_time > 0.5:  # Queries taking more than 500ms
                    slow_queries.append({
                        "query_hash": query_hash,
                        "avg_execution_time": avg_time,
                        "executions": len(times),
                        "max_time": max(times),
                        "min_time": min(times)
                    })
        
        slow_queries.sort(key=lambda x: x["avg_execution_time"], reverse=True)
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "connection_health": db_health,
                "slow_queries": slow_queries[:20],  # Top 20 slow queries
                "total_queries_tracked": len(performance_monitor.query_performance_stats)
            }
        })
    except Exception as e:
        logger.error(f"Error getting database health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get database health")

@router.get("/cache/stats")
async def get_cache_performance():
    """Get cache performance statistics"""
    try:
        cache_stats = cache_manager.get_cache_stats()
        
        return JSONResponse(content={
            "status": "success",
            "data": cache_stats
        })
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache statistics")

@router.post("/monitoring/start")
async def start_monitoring(
    background_tasks: BackgroundTasks,
    interval: Optional[float] = 30.0
):
    """Start performance monitoring"""
    try:
        if performance_monitor.is_monitoring:
            return JSONResponse(content={
                "status": "info",
                "message": "Performance monitoring is already running"
            })
        
        # Start monitoring in background
        background_tasks.add_task(performance_monitor.start_monitoring, interval)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Performance monitoring started with {interval}s interval"
        })
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to start monitoring")

@router.post("/monitoring/stop")
async def stop_monitoring():
    """Stop performance monitoring"""
    try:
        performance_monitor.stop_monitoring()
        
        return JSONResponse(content={
            "status": "success",
            "message": "Performance monitoring stopped"
        })
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop monitoring")

@router.get("/monitoring/status")
async def get_monitoring_status():
    """Get performance monitoring status"""
    try:
        return JSONResponse(content={
            "status": "success",
            "data": {
                "is_monitoring": performance_monitor.is_monitoring,
                "metrics_collected": len(performance_monitor.metrics_history),
                "active_alerts": len(performance_monitor.active_alerts),
                "response_times_tracked": len(performance_monitor.response_times),
                "queries_tracked": len(performance_monitor.query_performance_stats)
            }
        })
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring status")

@router.get("/system/resources")
async def get_system_resources():
    """Get detailed system resource information"""
    try:
        import psutil
        
        # CPU information
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            "cpu_percent_per_core": psutil.cpu_percent(percpu=True)
        }
        
        # Memory information
        memory = psutil.virtual_memory()
        memory_info = {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_gb": memory.used / (1024**3),
            "percentage": memory.percent
        }
        
        # Disk information
        disk = psutil.disk_usage('/')
        disk_info = {
            "total_gb": disk.total / (1024**3),
            "used_gb": disk.used / (1024**3),
            "free_gb": disk.free / (1024**3),
            "percentage": (disk.used / disk.total) * 100
        }
        
        # Network information
        network_io = psutil.net_io_counters()
        network_info = {
            "bytes_sent_mb": network_io.bytes_sent / (1024**2),
            "bytes_received_mb": network_io.bytes_recv / (1024**2),
            "packets_sent": network_io.packets_sent,
            "packets_received": network_io.packets_recv
        }
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": network_info,
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Error getting system resources: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system resources")

@router.post("/export/metrics")
async def export_metrics(
    background_tasks: BackgroundTasks,
    format: str = "json"
):
    """Export performance metrics to file"""
    try:
        if format not in ["json"]:
            raise HTTPException(status_code=400, detail="Unsupported format. Only 'json' is supported")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_metrics_{timestamp}.{format}"
        filepath = f"/tmp/{filename}"
        
        # Export in background
        background_tasks.add_task(performance_monitor.export_metrics_to_json, filepath)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Metrics export started. File will be saved as {filename}",
            "filepath": filepath
        })
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to export metrics")

@router.get("/health")
async def performance_health_check():
    """Health check for performance monitoring system"""
    try:
        current_time = datetime.now()
        
        # Check if monitoring is active
        monitoring_healthy = performance_monitor.is_monitoring
        
        # Check if we have recent metrics
        recent_metrics = len(performance_monitor.metrics_history) > 0
        
        # Check system resources
        import psutil
        cpu_ok = psutil.cpu_percent() < 90
        memory_ok = psutil.virtual_memory().percent < 95
        
        overall_health = all([monitoring_healthy, recent_metrics, cpu_ok, memory_ok])
        
        return JSONResponse(
            status_code=200 if overall_health else 503,
            content={
                "status": "healthy" if overall_health else "unhealthy",
                "checks": {
                    "monitoring_active": monitoring_healthy,
                    "recent_metrics": recent_metrics,
                    "cpu_healthy": cpu_ok,
                    "memory_healthy": memory_ok
                },
                "timestamp": current_time.isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error in performance health check: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )