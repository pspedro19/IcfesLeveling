#!/usr/bin/env python3
"""
System Health Monitor - Monitoreo completo de la salud del sistema ICFES
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psutil
import docker
from sqlalchemy import create_engine, text
import redis

logger = logging.getLogger(__name__)

class SystemHealthMonitor:
    """Monitor de salud del sistema completo"""
    
    def __init__(self, db_engine, redis_client=None):
        self.db_engine = db_engine
        self.redis_client = redis_client
        self.docker_client = docker.from_env()
        self.last_check = time.time()
        self.check_interval = 60  # 1 minuto
        self.health_history = []
        self.max_history = 100
        
    async def start_monitoring(self):
        """Iniciar monitoreo continuo del sistema"""
        logger.info("🏥 System Health Monitor iniciado - Monitoreando cada minuto")
        
        while True:
            try:
                health_status = await self.check_system_health()
                self._store_health_status(health_status)
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error en System Health Monitor: {e}")
                await asyncio.sleep(30)  # Esperar 30 segundos en caso de error
    
    async def check_system_health(self) -> Dict:
        """Verificar salud completa del sistema"""
        logger.info("🔍 Verificando salud del sistema...")
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": {},
            "database": {},
            "system": {},
            "performance": {}
        }
        
        # Verificar servicios Docker
        services_health = await self._check_docker_services()
        health_status["services"] = services_health
        
        # Verificar base de datos
        db_health = await self._check_database_health()
        health_status["database"] = db_health
        
        # Verificar sistema operativo
        system_health = await self._check_system_health()
        health_status["system"] = system_health
        
        # Verificar rendimiento
        performance_health = await self._check_performance_health()
        health_status["performance"] = performance_health
        
        # Determinar estado general
        health_status["overall_status"] = self._determine_overall_status(health_status)
        
        return health_status
    
    async def _check_docker_services(self) -> Dict:
        """Verificar salud de los servicios Docker"""
        services_health = {}
        
        try:
            containers = self.docker_client.containers.list()
            
            for container in containers:
                container_name = container.name
                container_status = container.status
                container_health = container.attrs.get('State', {}).get('Health', {}).get('Status', 'unknown')
                
                services_health[container_name] = {
                    "status": container_status,
                    "health": container_health,
                    "uptime": self._get_container_uptime(container),
                    "memory_usage": self._get_container_memory_usage(container),
                    "cpu_usage": self._get_container_cpu_usage(container)
                }
                
        except Exception as e:
            logger.error(f"Error verificando servicios Docker: {e}")
            services_health["error"] = str(e)
        
        return services_health
    
    async def _check_database_health(self) -> Dict:
        """Verificar salud de la base de datos"""
        db_health = {}
        
        try:
            # Verificar conexión
            with self.db_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                db_health["connection"] = "healthy"
                
                # Verificar tablas críticas
                result = conn.execute(text("""
                    SELECT COUNT(*) as table_count 
                    FROM information_schema.tables 
                    WHERE table_name IN (
                        'users', 'subjects', 'topics', 'questions',
                        'diagnostic_tests', 'diagnostic_test_answers'
                    )
                """))
                table_count = result.fetchone()[0]
                db_health["critical_tables"] = f"{table_count}/6"
                
                # Verificar foreign keys
                result = conn.execute(text("""
                    SELECT COUNT(*) as fk_count 
                    FROM information_schema.table_constraints 
                    WHERE constraint_type = 'FOREIGN KEY'
                """))
                fk_count = result.fetchone()[0]
                db_health["foreign_keys"] = fk_count
                
        except Exception as e:
            logger.error(f"Error verificando BD: {e}")
            db_health["connection"] = "error"
            db_health["error"] = str(e)
        
        return db_health
    
    async def _check_system_health(self) -> Dict:
        """Verificar salud del sistema operativo"""
        system_health = {}
        
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            system_health["cpu_usage"] = f"{cpu_percent}%"
            
            # Memoria
            memory = psutil.virtual_memory()
            system_health["memory_usage"] = f"{memory.percent}%"
            system_health["memory_available"] = f"{memory.available // (1024**3)} GB"
            
            # Disco
            disk = psutil.disk_usage('/')
            system_health["disk_usage"] = f"{disk.percent}%"
            system_health["disk_available"] = f"{disk.free // (1024**3)} GB"
            
            # Red
            network = psutil.net_io_counters()
            system_health["network_bytes_sent"] = f"{network.bytes_sent // (1024**2)} MB"
            system_health["network_bytes_recv"] = f"{network.bytes_recv // (1024**2)} MB"
            
        except Exception as e:
            logger.error(f"Error verificando sistema: {e}")
            system_health["error"] = str(e)
        
        return system_health
    
    async def _check_performance_health(self) -> Dict:
        """Verificar métricas de rendimiento"""
        performance_health = {}
        
        try:
            # Tiempo de respuesta de la BD
            start_time = time.time()
            with self.db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_response_time = (time.time() - start_time) * 1000
            performance_health["db_response_time_ms"] = round(db_response_time, 2)
            
            # Verificar Redis si está disponible
            if self.redis_client:
                start_time = time.time()
                self.redis_client.ping()
                redis_response_time = (time.time() - start_time) * 1000
                performance_health["redis_response_time_ms"] = round(redis_response_time, 2)
            
            # Métricas de Docker
            containers = self.docker_client.containers.list()
            total_memory = 0
            total_cpu = 0
            
            for container in containers:
                try:
                    stats = container.stats(stream=False)
                    memory_usage = stats['memory_stats']['usage']
                    total_memory += memory_usage
                    
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                    cpu_percent = (cpu_delta / system_delta) * 100 if system_delta > 0 else 0
                    total_cpu += cpu_percent
                    
                except Exception:
                    continue
            
            performance_health["total_docker_memory_mb"] = round(total_memory / (1024**2), 2)
            performance_health["total_docker_cpu_percent"] = round(total_cpu, 2)
            
        except Exception as e:
            logger.error(f"Error verificando rendimiento: {e}")
            performance_health["error"] = str(e)
        
        return performance_health
    
    def _determine_overall_status(self, health_status: Dict) -> str:
        """Determinar estado general del sistema"""
        # Verificar servicios críticos
        critical_services = ['icfes_backend', 'icfes_postgres']
        services_down = 0
        
        for service in critical_services:
            if service in health_status["services"]:
                service_status = health_status["services"][service]["status"]
                if service_status != "running":
                    services_down += 1
        
        # Verificar base de datos
        db_healthy = health_status["database"].get("connection") == "healthy"
        
        # Verificar sistema
        cpu_usage = float(health_status["system"].get("cpu_usage", "0%").replace("%", ""))
        memory_usage = float(health_status["system"].get("memory_usage", "0%").replace("%", ""))
        
        # Determinar estado
        if services_down > 0 or not db_healthy:
            return "critical"
        elif cpu_usage > 90 or memory_usage > 90:
            return "warning"
        else:
            return "healthy"
    
    def _store_health_status(self, health_status: Dict):
        """Almacenar historial de salud"""
        self.health_history.append(health_status)
        
        # Mantener solo los últimos registros
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)
    
    def _get_container_uptime(self, container) -> str:
        """Obtener tiempo de actividad del contenedor"""
        try:
            started_at = container.attrs['State']['StartedAt']
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            uptime = datetime.now(start_time.tzinfo) - start_time
            return str(uptime).split('.')[0]  # Sin microsegundos
        except:
            return "unknown"
    
    def _get_container_memory_usage(self, container) -> str:
        """Obtener uso de memoria del contenedor"""
        try:
            stats = container.stats(stream=False)
            memory_usage = stats['memory_stats']['usage']
            return f"{memory_usage // (1024**2)} MB"
        except:
            return "unknown"
    
    def _get_container_cpu_usage(self, container) -> str:
        """Obtener uso de CPU del contenedor"""
        try:
            stats = container.stats(stream=False)
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * 100 if system_delta > 0 else 0
            return f"{cpu_percent:.1f}%"
        except:
            return "unknown"
    
    def get_current_health(self) -> Dict:
        """Obtener estado de salud actual"""
        if self.health_history:
            return self.health_history[-1]
        return {"overall_status": "unknown"}
    
    def get_health_history(self, hours: int = 24) -> List[Dict]:
        """Obtener historial de salud de las últimas N horas"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_history = []
        for status in self.health_history:
            status_time = datetime.fromisoformat(status["timestamp"])
            if status_time >= cutoff_time:
                filtered_history.append(status)
        
        return filtered_history
    
    def get_health_summary(self) -> Dict:
        """Obtener resumen de salud del sistema"""
        if not self.health_history:
            return {"status": "unknown", "message": "No hay datos de salud disponibles"}
        
        # Calcular estadísticas
        total_checks = len(self.health_history)
        healthy_checks = sum(1 for status in self.health_history if status["overall_status"] == "healthy")
        warning_checks = sum(1 for status in self.health_history if status["overall_status"] == "warning")
        critical_checks = sum(1 for status in self.health_history if status["overall_status"] == "critical")
        
        uptime_percentage = (healthy_checks / total_checks) * 100 if total_checks > 0 else 0
        
        return {
            "status": self.health_history[-1]["overall_status"],
            "uptime_percentage": round(uptime_percentage, 2),
            "total_checks": total_checks,
            "healthy_checks": healthy_checks,
            "warning_checks": warning_checks,
            "critical_checks": critical_checks,
            "last_check": self.health_history[-1]["timestamp"] if self.health_history else None
        }

# Función de configuración
def setup_system_health_monitor(app, db_engine, redis_client=None):
    """Configurar System Health Monitor en la aplicación"""
    monitor = SystemHealthMonitor(db_engine, redis_client)
    
    @app.on_event("startup")
    async def start_system_health_monitor():
        asyncio.create_task(monitor.start_monitoring())
    
    return monitor
