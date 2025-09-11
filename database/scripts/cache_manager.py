#!/usr/bin/env python3
"""
Sistema de Gestión de Cache Redis para ICFES Leveling
Maneja invalidación de cache, pre-carga de imágenes y integración con actualizaciones de BD.
"""

import os
import sys
import json
import logging
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
import time
import asyncio
import aioredis
from pathlib import Path
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class CacheMetrics:
    """Métricas de cache"""
    total_keys: int
    hit_rate: float
    miss_rate: float
    memory_usage_mb: float
    expired_keys: int
    invalid_keys: int
    last_update: str

@dataclass
class ImageCacheEntry:
    """Entrada de cache de imagen"""
    path: str
    size_bytes: int
    last_accessed: str
    access_count: int
    priority: str  # 'high', 'medium', 'low'
    compressed: bool
    cache_key: str

@dataclass
class CacheInvalidationReport:
    """Reporte de invalidación de cache"""
    timestamp: str
    invalidation_type: str  # 'mass', 'selective', 'pattern'
    patterns_invalidated: List[str]
    keys_invalidated: int
    preload_completed: int
    errors: List[str]
    duration_seconds: float

class RedisCacheManager:
    """Manejador de cache Redis para el sistema ICFES"""
    
    def __init__(self, redis_config: Dict[str, Any]):
        self.redis_config = redis_config
        self.redis_client = None
        self.async_client = None
        
        # Configuración de cache
        self.CACHE_PREFIXES = {
            'images': 'img',
            'questions': 'q',
            'media': 'media',
            'queries': 'query',
            'sessions': 'session',
            'metadata': 'meta'
        }
        
        self.DEFAULT_TTL = {
            'images': 3600,      # 1 hora
            'questions': 1800,   # 30 minutos  
            'media': 7200,       # 2 horas
            'queries': 900,      # 15 minutos
            'sessions': 86400,   # 24 horas
            'metadata': 3600     # 1 hora
        }
        
        self._connect()

    def _connect(self):
        """Establecer conexión con Redis"""
        try:
            self.redis_client = redis.Redis(**self.redis_config)
            self.redis_client.ping()
            logger.info("✅ Conexión Redis establecida")
        except Exception as e:
            logger.error(f"❌ Error conectando a Redis: {e}")
            self.redis_client = None

    async def _connect_async(self):
        """Establecer conexión asíncrona con Redis"""
        try:
            redis_url = f"redis://{self.redis_config.get('host', 'localhost')}:{self.redis_config.get('port', 6379)}"
            self.async_client = await aioredis.from_url(redis_url, decode_responses=True)
            await self.async_client.ping()
            logger.info("✅ Conexión Redis asíncrona establecida")
        except Exception as e:
            logger.error(f"❌ Error conectando async a Redis: {e}")
            self.async_client = None

    def get_cache_metrics(self) -> Optional[CacheMetrics]:
        """Obtener métricas de cache"""
        if not self.redis_client:
            return None
        
        try:
            info = self.redis_client.info()
            
            # Obtener estadísticas
            total_keys = info.get('db0', {}).get('keys', 0) if isinstance(info.get('db0'), dict) else 0
            
            # Calcular métricas de memoria
            used_memory = info.get('used_memory', 0)
            memory_mb = used_memory / (1024 * 1024)
            
            # Obtener estadísticas de hit/miss (si están disponibles)
            hit_rate = 0.0
            miss_rate = 0.0
            
            keyspace_hits = info.get('keyspace_hits', 0)
            keyspace_misses = info.get('keyspace_misses', 0)
            total_operations = keyspace_hits + keyspace_misses
            
            if total_operations > 0:
                hit_rate = keyspace_hits / total_operations
                miss_rate = keyspace_misses / total_operations
            
            # Contar keys expiradas
            expired_keys = info.get('expired_keys', 0)
            
            return CacheMetrics(
                total_keys=total_keys,
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                memory_usage_mb=memory_mb,
                expired_keys=expired_keys,
                invalid_keys=0,  # Se calcula por separado
                last_update=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas de cache: {e}")
            return None

    def invalidate_cache_patterns(self, patterns: List[str]) -> CacheInvalidationReport:
        """Invalidar cache por patrones"""
        logger.info(f"🧹 Invalidando cache por patrones: {patterns}")
        
        start_time = time.time()
        invalidated_keys = 0
        errors = []
        
        try:
            if not self.redis_client:
                errors.append("Cliente Redis no disponible")
                return self._create_error_report('pattern', patterns, errors, start_time)
            
            for pattern in patterns:
                try:
                    # Buscar keys que coincidan con el patrón
                    keys = self.redis_client.keys(pattern)
                    
                    if keys:
                        # Eliminar keys en lotes para mejor rendimiento
                        batch_size = 1000
                        for i in range(0, len(keys), batch_size):
                            batch = keys[i:i + batch_size]
                            deleted = self.redis_client.delete(*batch)
                            invalidated_keys += deleted
                    
                    logger.info(f"✅ Patrón {pattern}: {len(keys)} keys encontradas")
                    
                except Exception as e:
                    error_msg = f"Error invalidando patrón {pattern}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            duration = time.time() - start_time
            
            return CacheInvalidationReport(
                timestamp=datetime.now().isoformat(),
                invalidation_type='pattern',
                patterns_invalidated=patterns,
                keys_invalidated=invalidated_keys,
                preload_completed=0,
                errors=errors,
                duration_seconds=duration
            )
            
        except Exception as e:
            error_msg = f"Error general invalidando cache: {e}"
            errors.append(error_msg)
            logger.error(error_msg)
            return self._create_error_report('pattern', patterns, errors, start_time)

    def mass_invalidate_after_db_update(self) -> CacheInvalidationReport:
        """Invalidación masiva después de actualizaciones de BD"""
        logger.info("🚨 Ejecutando invalidación masiva post-actualización BD")
        
        # Patrones críticos que deben invalidarse después de actualizaciones de BD
        critical_patterns = [
            f"{self.CACHE_PREFIXES['images']}:*",      # Cache de imágenes
            f"{self.CACHE_PREFIXES['questions']}:*",   # Cache de preguntas
            f"{self.CACHE_PREFIXES['media']}:*",       # Cache de media
            f"{self.CACHE_PREFIXES['queries']}:*",     # Cache de queries
            "questions_by_*",                          # Queries cacheadas específicas
            "image_validation_*",                      # Cache de validación de imágenes
            "question_count_*",                        # Cache de conteos
            "search_results_*"                         # Cache de búsquedas
        ]
        
        return self.invalidate_cache_patterns(critical_patterns)

    def selective_invalidate_images(self, image_paths: List[str]) -> int:
        """Invalidación selectiva de imágenes específicas"""
        logger.info(f"🎯 Invalidación selectiva de {len(image_paths)} imágenes")
        
        invalidated = 0
        
        if not self.redis_client:
            return invalidated
        
        try:
            for image_path in image_paths:
                # Generar claves de cache posibles para esta imagen
                cache_keys = self._generate_image_cache_keys(image_path)
                
                for key in cache_keys:
                    if self.redis_client.delete(key):
                        invalidated += 1
            
            logger.info(f"✅ {invalidated} entradas de imagen invalidadas")
            
        except Exception as e:
            logger.error(f"Error en invalidación selectiva: {e}")
        
        return invalidated

    def _generate_image_cache_keys(self, image_path: str) -> List[str]:
        """Generar posibles claves de cache para una imagen"""
        keys = []
        
        # Normalizar ruta
        normalized_path = image_path.replace('\\', '/').strip()
        
        # Hash de la ruta para key consistente
        path_hash = hashlib.md5(normalized_path.encode()).hexdigest()[:16]
        
        # Generar diferentes formatos de key
        keys.extend([
            f"{self.CACHE_PREFIXES['images']}:{path_hash}",
            f"{self.CACHE_PREFIXES['images']}:{normalized_path}",
            f"{self.CACHE_PREFIXES['media']}:{path_hash}",
            f"{self.CACHE_PREFIXES['media']}:{normalized_path}",
            f"img_cache_{path_hash}",
            f"media_{path_hash}"
        ])
        
        return keys

    async def preload_important_images(self, image_data: List[Dict[str, Any]], 
                                     priority: str = 'high') -> int:
        """Pre-cargar imágenes importantes de forma asíncrona"""
        logger.info(f"⚡ Pre-cargando {len(image_data)} imágenes importantes")
        
        if not self.async_client:
            await self._connect_async()
            
        if not self.async_client:
            logger.error("No se pudo establecer conexión asíncrona")
            return 0
        
        preloaded = 0
        
        try:
            tasks = []
            
            for img_data in image_data:
                task = self._preload_single_image(img_data, priority)
                tasks.append(task)
            
            # Ejecutar en lotes para no sobrecargar
            batch_size = 10
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                results = await asyncio.gather(*batch, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.warning(f"Error pre-cargando imagen: {result}")
                    elif result:
                        preloaded += 1
                
                # Pequeña pausa entre lotes
                await asyncio.sleep(0.1)
            
            logger.info(f"✅ {preloaded} imágenes pre-cargadas exitosamente")
            
        except Exception as e:
            logger.error(f"Error en pre-carga masiva: {e}")
        
        return preloaded

    async def _preload_single_image(self, img_data: Dict[str, Any], priority: str) -> bool:
        """Pre-cargar una sola imagen"""
        try:
            image_path = img_data.get('path', '')
            question_id = img_data.get('question_id', '')
            
            if not image_path:
                return False
            
            # Generar cache key
            path_hash = hashlib.md5(image_path.encode()).hexdigest()[:16]
            cache_key = f"{self.CACHE_PREFIXES['images']}:priority:{question_id}:{path_hash}"
            
            # Crear entrada de cache
            cache_entry = ImageCacheEntry(
                path=image_path,
                size_bytes=img_data.get('size_bytes', 0),
                last_accessed=datetime.now().isoformat(),
                access_count=0,
                priority=priority,
                compressed=False,
                cache_key=cache_key
            )
            
            # Guardar en cache con TTL extendido para imágenes importantes
            ttl = self.DEFAULT_TTL['images'] * 2 if priority == 'high' else self.DEFAULT_TTL['images']
            
            await self.async_client.set(
                cache_key,
                json.dumps(asdict(cache_entry)),
                ex=ttl
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error pre-cargando imagen {img_data}: {e}")
            return False

    def set_cache_expiration_policies(self) -> bool:
        """Configurar políticas de expiración de cache"""
        logger.info("⚙️ Configurando políticas de expiración de cache")
        
        if not self.redis_client:
            return False
        
        try:
            # Configurar maxmemory policy para LRU
            self.redis_client.config_set('maxmemory-policy', 'allkeys-lru')
            
            # Configurar límite de memoria (opcional)
            # self.redis_client.config_set('maxmemory', '500mb')
            
            # Configurar lazy expiration
            self.redis_client.config_set('hz', '100')  # Frecuencia de limpieza
            
            logger.info("✅ Políticas de expiración configuradas")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando políticas: {e}")
            return False

    def optimize_cache_performance(self) -> Dict[str, Any]:
        """Optimizar rendimiento del cache"""
        logger.info("🚀 Optimizando rendimiento de cache")
        
        optimizations = {
            'memory_cleaned': 0,
            'expired_keys_cleaned': 0,
            'fragmentation_reduced': False,
            'policies_updated': False
        }
        
        if not self.redis_client:
            return optimizations
        
        try:
            # 1. Limpiar keys expiradas manualmente
            info = self.redis_client.info()
            expired_before = info.get('expired_keys', 0)
            
            # Forzar limpieza de keys expiradas
            self.redis_client.debug_object('expire')  # Trigger expiration
            
            info_after = self.redis_client.info()
            expired_after = info_after.get('expired_keys', 0)
            optimizations['expired_keys_cleaned'] = expired_after - expired_before
            
            # 2. Ejecutar MEMORY PURGE si está disponible
            try:
                self.redis_client.memory_purge()
                optimizations['memory_cleaned'] = 1
            except:
                pass  # Comando no disponible en todas las versiones
            
            # 3. Actualizar políticas
            optimizations['policies_updated'] = self.set_cache_expiration_policies()
            
            # 4. Obtener estadísticas de fragmentación
            mem_fragmentation_ratio = info.get('mem_fragmentation_ratio', 0)
            if mem_fragmentation_ratio > 1.5:
                logger.warning(f"Alta fragmentación de memoria: {mem_fragmentation_ratio}")
            
            logger.info("✅ Optimización de cache completada")
            
        except Exception as e:
            logger.error(f"Error optimizando cache: {e}")
        
        return optimizations

    def create_cache_warming_schedule(self) -> Dict[str, Any]:
        """Crear schedule para warming de cache"""
        logger.info("📅 Creando schedule de warming de cache")
        
        schedule = {
            'daily_warm_time': '06:00',  # 6 AM
            'warm_patterns': [
                'most_accessed_questions',
                'high_priority_images', 
                'recent_user_queries'
            ],
            'batch_size': 50,
            'max_duration_minutes': 30
        }
        
        # Guardar schedule en cache para referencia
        if self.redis_client:
            try:
                self.redis_client.set(
                    'cache_warming_schedule',
                    json.dumps(schedule),
                    ex=86400  # 24 horas
                )
                logger.info("✅ Schedule de warming guardado")
            except Exception as e:
                logger.error(f"Error guardando schedule: {e}")
        
        return schedule

    def monitor_cache_health(self) -> Dict[str, Any]:
        """Monitorear salud del cache"""
        logger.info("🏥 Monitoreando salud del cache")
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'metrics': None,
            'alerts': [],
            'recommendations': []
        }
        
        try:
            # Obtener métricas
            metrics = self.get_cache_metrics()
            health_report['metrics'] = asdict(metrics) if metrics else None
            
            if metrics:
                # Evaluar salud basada en métricas
                
                # 1. Verificar hit rate
                if metrics.hit_rate < 0.5:  # Menos de 50% hit rate
                    health_report['alerts'].append("Baja tasa de hit en cache (< 50%)")
                    health_report['recommendations'].append("Considerar pre-carga de datos más frecuentes")
                    health_report['status'] = 'warning'
                
                # 2. Verificar uso de memoria
                if metrics.memory_usage_mb > 800:  # Más de 800MB
                    health_report['alerts'].append(f"Alto uso de memoria: {metrics.memory_usage_mb:.1f}MB")
                    health_report['recommendations'].append("Ejecutar limpieza de cache")
                    health_report['status'] = 'warning'
                
                # 3. Verificar keys expiradas
                if metrics.expired_keys > 10000:
                    health_report['alerts'].append(f"Muchas keys expiradas: {metrics.expired_keys}")
                    health_report['recommendations'].append("Ajustar TTL o limpiar keys expiradas")
                
                # 4. Estado crítico
                if metrics.hit_rate < 0.2 or metrics.memory_usage_mb > 1000:
                    health_report['status'] = 'critical'
            
        except Exception as e:
            health_report['status'] = 'error'
            health_report['alerts'].append(f"Error monitoreando salud: {e}")
        
        return health_report

    def _create_error_report(self, invalidation_type: str, patterns: List[str], 
                           errors: List[str], start_time: float) -> CacheInvalidationReport:
        """Crear reporte de error"""
        return CacheInvalidationReport(
            timestamp=datetime.now().isoformat(),
            invalidation_type=invalidation_type,
            patterns_invalidated=patterns,
            keys_invalidated=0,
            preload_completed=0,
            errors=errors,
            duration_seconds=time.time() - start_time
        )

    def save_cache_report(self, report: Any, report_type: str) -> str:
        """Guardar reporte de cache"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"database/reports/cache_{report_type}_{timestamp}.json"
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            if hasattr(report, '__dict__'):
                json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)
            else:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📋 Reporte de cache guardado: {report_path}")
        return report_path


async def main():
    """Función principal del manejador de cache"""
    
    # Configuración de Redis
    redis_config = {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', '6379')),
        'db': int(os.getenv('REDIS_DB', '0')),
        'decode_responses': True,
        'socket_timeout': 5,
        'socket_connect_timeout': 5
    }
    
    action = sys.argv[1] if len(sys.argv) > 1 else 'health'
    
    logger.info("=== GESTOR DE CACHE REDIS ICFES LEVELING ===")
    logger.info(f"Acción: {action}")
    
    try:
        manager = RedisCacheManager(redis_config)
        
        if action == 'invalidate':
            # Invalidación masiva después de actualización de BD
            report = manager.mass_invalidate_after_db_update()
            manager.save_cache_report(report, 'invalidation')
            
            print(f"✅ Cache invalidado: {report.keys_invalidated} keys")
            print(f"⏱️ Duración: {report.duration_seconds:.2f}s")
            
            if report.errors:
                print(f"❌ Errores: {len(report.errors)}")
                for error in report.errors[:3]:  # Mostrar solo los primeros 3
                    print(f"  • {error}")
            
            return 0 if not report.errors else 1
            
        elif action == 'preload':
            # Pre-carga de imágenes importantes (ejemplo)
            sample_images = [
                {'path': '/mathimg/Math_1_1_Doc1.png', 'question_id': 'math_001', 'size_bytes': 45000},
                {'path': '/mathimg/Math_2_1_Doc1.png', 'question_id': 'math_002', 'size_bytes': 38000},
                {'path': '/mathimg/Math_3_1_Doc1.png', 'question_id': 'math_003', 'size_bytes': 42000}
            ]
            
            preloaded = await manager.preload_important_images(sample_images, 'high')
            print(f"✅ {preloaded} imágenes pre-cargadas")
            return 0
            
        elif action == 'optimize':
            # Optimizar rendimiento de cache
            optimizations = manager.optimize_cache_performance()
            manager.save_cache_report(optimizations, 'optimization')
            
            print("✅ Optimizaciones aplicadas:")
            for key, value in optimizations.items():
                print(f"  • {key}: {value}")
            
            return 0
            
        elif action == 'health':
            # Monitorear salud del cache
            health = manager.monitor_cache_health()
            manager.save_cache_report(health, 'health')
            
            print("\n" + "="*60)
            print("SALUD DEL CACHE REDIS")
            print("="*60)
            print(f"🏥 Estado: {health['status'].upper()}")
            
            if health['metrics']:
                metrics = health['metrics']
                print(f"📊 Keys totales: {metrics['total_keys']}")
                print(f"🎯 Hit rate: {metrics['hit_rate']:.1%}")
                print(f"💾 Memoria: {metrics['memory_usage_mb']:.1f}MB")
                print(f"⏰ Keys expiradas: {metrics['expired_keys']}")
            
            if health['alerts']:
                print(f"\n🚨 ALERTAS ({len(health['alerts'])}):")
                for alert in health['alerts']:
                    print(f"  • {alert}")
            
            if health['recommendations']:
                print(f"\n💡 RECOMENDACIONES ({len(health['recommendations'])}):")
                for rec in health['recommendations']:
                    print(f"  • {rec}")
            
            return 0 if health['status'] != 'critical' else 1
            
        elif action == 'metrics':
            # Mostrar métricas detalladas
            metrics = manager.get_cache_metrics()
            if metrics:
                manager.save_cache_report(asdict(metrics), 'metrics')
                print(json.dumps(asdict(metrics), indent=2, default=str))
            else:
                print("❌ No se pudieron obtener métricas")
                return 1
            
            return 0
            
        elif action == 'schedule':
            # Crear schedule de warming
            schedule = manager.create_cache_warming_schedule()
            manager.save_cache_report(schedule, 'warming_schedule')
            
            print("📅 Schedule de warming de cache creado:")
            print(json.dumps(schedule, indent=2))
            return 0
            
        else:
            print("Acciones disponibles: invalidate, preload, optimize, health, metrics, schedule")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)