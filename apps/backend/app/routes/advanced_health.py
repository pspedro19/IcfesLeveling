#!/usr/bin/env python3
"""
Advanced Health Endpoints - Endpoints de salud avanzada del sistema ICFES
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
import logging

from ..core.database import get_db
from ..monitoring.schema_guard import SchemaGuard
from ..monitoring.system_health import SystemHealthMonitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["Advanced Health"])

# Variables globales para los monitores
schema_guard: SchemaGuard = None
system_health_monitor: SystemHealthMonitor = None

def set_monitors(sg: SchemaGuard, shm: SystemHealthMonitor):
    """Configurar los monitores desde main.py"""
    global schema_guard, system_health_monitor
    schema_guard = sg
    system_health_monitor = shm

@router.get("/advanced")
async def get_advanced_health():
    """Obtener estado de salud avanzado del sistema"""
    try:
        if not schema_guard or not system_health_monitor:
            raise HTTPException(status_code=503, detail="Monitores no configurados")
        
        # Obtener estado del Schema Guard
        schema_status = schema_guard.get_health_status()
        
        # Obtener estado del System Health Monitor
        system_status = system_health_monitor.get_current_health()
        system_summary = system_health_monitor.get_health_summary()
        
        # Combinar información
        advanced_health = {
            "timestamp": system_status.get("timestamp"),
            "overall_status": system_status.get("overall_status"),
            "schema_guard": schema_status,
            "system_health": system_status,
            "system_summary": system_summary,
            "recommendations": _generate_recommendations(schema_status, system_status)
        }
        
        return advanced_health
        
    except Exception as e:
        logger.error(f"Error obteniendo salud avanzada: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/schema")
async def get_schema_health():
    """Obtener estado de salud del esquema de base de datos"""
    try:
        if not schema_guard:
            raise HTTPException(status_code=503, detail="Schema Guard no configurado")
        
        return schema_guard.get_health_status()
        
    except Exception as e:
        logger.error(f"Error obteniendo salud del esquema: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/system")
async def get_system_health():
    """Obtener estado de salud del sistema operativo y servicios"""
    try:
        if not system_health_monitor:
            raise HTTPException(status_code=503, detail="System Health Monitor no configurado")
        
        return {
            "current": system_health_monitor.get_current_health(),
            "summary": system_health_monitor.get_health_summary(),
            "history_24h": system_health_monitor.get_health_history(24)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo salud del sistema: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/schema/force-check")
async def force_schema_check():
    """Forzar verificación inmediata del esquema"""
    try:
        if not schema_guard:
            raise HTTPException(status_code=503, detail="Schema Guard no configurado")
        
        await schema_guard.force_check()
        return {"message": "Verificación del esquema iniciada", "status": "success"}
        
    except Exception as e:
        logger.error(f"Error forzando verificación del esquema: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/services")
async def get_services_health():
    """Obtener estado de salud de todos los servicios"""
    try:
        if not system_health_monitor:
            raise HTTPException(status_code=503, detail="System Health Monitor no configurado")
        
        current_health = system_health_monitor.get_current_health()
        services = current_health.get("services", {})
        
        # Analizar estado de servicios críticos
        critical_services = ['icfes_backend', 'icfes_postgres', 'icfes_frontend', 'icfes_redis']
        service_analysis = {}
        
        for service_name in critical_services:
            if service_name in services:
                service_info = services[service_name]
                service_analysis[service_name] = {
                    "status": service_info.get("status"),
                    "health": service_info.get("health"),
                    "uptime": service_info.get("uptime"),
                    "memory_usage": service_info.get("memory_usage"),
                    "cpu_usage": service_info.get("cpu_usage"),
                    "is_healthy": service_info.get("status") == "running" and service_info.get("health") == "healthy"
                }
            else:
                service_analysis[service_name] = {
                    "status": "not_found",
                    "health": "unknown",
                    "uptime": "unknown",
                    "memory_usage": "unknown",
                    "cpu_usage": "unknown",
                    "is_healthy": False
                }
        
        return {
            "services": service_analysis,
            "overall_services_health": _calculate_services_health(service_analysis)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo salud de servicios: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/database")
async def get_database_health():
    """Obtener estado de salud detallado de la base de datos"""
    try:
        if not system_health_monitor:
            raise HTTPException(status_code=503, detail="System Health Monitor no configurado")
        
        current_health = system_health_monitor.get_current_health()
        db_health = current_health.get("database", {})
        
        # Información adicional de la BD
        db_info = {
            "connection": db_health.get("connection"),
            "critical_tables": db_health.get("critical_tables"),
            "foreign_keys": db_health.get("foreign_keys"),
            "performance": {
                "response_time_ms": current_health.get("performance", {}).get("db_response_time_ms")
            }
        }
        
        # Determinar estado de la BD
        if db_info["connection"] == "healthy":
            db_info["status"] = "healthy"
            db_info["message"] = "Base de datos funcionando correctamente"
        else:
            db_info["status"] = "error"
            db_info["message"] = "Problemas de conexión con la base de datos"
        
        return db_info
        
    except Exception as e:
        logger.error(f"Error obteniendo salud de la BD: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

def _generate_recommendations(schema_status: Dict, system_status: Dict) -> List[str]:
    """Generar recomendaciones basadas en el estado del sistema"""
    recommendations = []
    
    # Recomendaciones del Schema Guard
    if schema_status.get("status") == "warning":
        recommendations.append("🔧 Verificar integridad del esquema de base de datos")
    
    if schema_status.get("issues_count", 0) > 0:
        recommendations.append(f"🚨 {schema_status['issues_count']} problemas de esquema detectados - Ejecutar reparación")
    
    # Recomendaciones del sistema
    if system_status.get("overall_status") == "critical":
        recommendations.append("🚨 Estado crítico del sistema - Revisar servicios inmediatamente")
    
    if system_status.get("overall_status") == "warning":
        recommendations.append("⚠️ Estado de advertencia - Monitorear recursos del sistema")
    
    # Verificar servicios específicos
    services = system_status.get("services", {})
    if "icfes_backend" in services and services["icfes_backend"]["status"] != "running":
        recommendations.append("🔧 Backend no está ejecutándose - Reiniciar servicio")
    
    if "icfes_postgres" in services and services["icfes_postgres"]["status"] != "running":
        recommendations.append("🔧 Base de datos no está ejecutándose - Verificar contenedor")
    
    # Si no hay problemas, mostrar mensaje positivo
    if not recommendations:
        recommendations.append("✅ Sistema funcionando correctamente - No se requieren acciones")
    
    return recommendations

def _calculate_services_health(service_analysis: Dict) -> str:
    """Calcular estado general de salud de los servicios"""
    total_services = len(service_analysis)
    healthy_services = sum(1 for service in service_analysis.values() if service.get("is_healthy", False))
    
    health_percentage = (healthy_services / total_services) * 100 if total_services > 0 else 0
    
    if health_percentage >= 90:
        return "excellent"
    elif health_percentage >= 75:
        return "good"
    elif health_percentage >= 50:
        return "fair"
    else:
        return "poor"
