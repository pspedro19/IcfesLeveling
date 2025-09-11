#!/usr/bin/env python3
"""
SCRIPT MAESTRO - Actualización Completa de Base de Datos ICFES Leveling
Orquesta todos los componentes del sistema de actualización masiva.
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import subprocess

# Importar manejadores locales
from mass_image_update import DatabaseUpdateManager
from integrity_checker import DatabaseIntegrityChecker
from index_optimizer import DatabaseIndexOptimizer
from rollback_manager import DatabaseRollbackManager
from cache_manager import RedisCacheManager
from migration_manager import AlembicMigrationManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'master_update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MasterUpdateOrchestrator:
    """Orquestador maestro de actualizaciones de base de datos"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_config = config['database']
        self.redis_config = config.get('redis', {})
        self.correspondence_path = config.get('correspondence_table')
        
        # Inicializar manejadores
        self.update_manager = None
        self.integrity_checker = None
        self.index_optimizer = None
        self.rollback_manager = None
        self.cache_manager = None
        self.migration_manager = None
        
        # Resultados de cada fase
        self.phase_results = {}
        self.overall_success = True
        
    def initialize_managers(self):
        """Inicializar todos los manejadores"""
        logger.info("🔧 Inicializando manejadores del sistema...")
        
        try:
            self.update_manager = DatabaseUpdateManager(self.db_config, self.redis_config)
            self.integrity_checker = DatabaseIntegrityChecker(self.db_config)
            self.index_optimizer = DatabaseIndexOptimizer(self.db_config)
            self.rollback_manager = DatabaseRollbackManager(self.db_config)
            
            if self.redis_config:
                self.cache_manager = RedisCacheManager(self.redis_config)
            
            self.migration_manager = AlembicMigrationManager(self.db_config)
            
            logger.info("✅ Todos los manejadores inicializados correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando manejadores: {e}")
            raise

    async def execute_complete_update_process(self) -> bool:
        """Ejecutar proceso completo de actualización"""
        logger.info("🚀 INICIANDO PROCESO MAESTRO DE ACTUALIZACIÓN")
        logger.info("="*80)
        
        start_time = datetime.now()
        
        try:
            # FASE 0: Inicialización
            await self.phase_0_initialization()
            
            # FASE 1: Validaciones previas
            if not await self.phase_1_pre_validations():
                return False
            
            # FASE 2: Backup y preparación
            if not await self.phase_2_backup_preparation():
                return False
            
            # FASE 3: Migraciones de esquema (si es necesario)
            if not await self.phase_3_schema_migrations():
                return False
            
            # FASE 4: Actualización masiva de datos
            if not await self.phase_4_mass_data_update():
                return False
            
            # FASE 5: Optimización de índices
            if not await self.phase_5_index_optimization():
                return False
            
            # FASE 6: Validación de integridad
            if not await self.phase_6_integrity_validation():
                return False
            
            # FASE 7: Invalidación y optimización de cache
            if not await self.phase_7_cache_management():
                return False
            
            # FASE 8: Validación final y reporte
            await self.phase_8_final_validation()
            
            # Generar reporte final
            await self.generate_final_report(start_time)
            
            logger.info("🎉 PROCESO MAESTRO COMPLETADO EXITOSAMENTE")
            return self.overall_success
            
        except Exception as e:
            logger.error(f"❌ ERROR CRÍTICO EN PROCESO MAESTRO: {e}")
            await self.handle_critical_error(e)
            return False

    async def phase_0_initialization(self):
        """FASE 0: Inicialización del sistema"""
        logger.info("📋 FASE 0: Inicialización del sistema")
        
        phase_start = datetime.now()
        
        try:
            # Inicializar manejadores
            self.initialize_managers()
            
            # Verificar archivos necesarios
            if self.correspondence_path and not Path(self.correspondence_path).exists():
                raise FileNotFoundError(f"Tabla de correspondencia no encontrada: {self.correspondence_path}")
            
            # Crear directorios necesarios
            os.makedirs("database/reports", exist_ok=True)
            os.makedirs("database/backups", exist_ok=True)
            
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_0'] = {
                'success': True,
                'duration': duration,
                'description': 'Inicialización del sistema'
            }
            
            logger.info(f"✅ FASE 0 COMPLETADA ({duration:.2f}s)")
            
        except Exception as e:
            logger.error(f"❌ FASE 0 FALLÓ: {e}")
            self.overall_success = False
            raise

    async def phase_1_pre_validations(self) -> bool:
        """FASE 1: Validaciones previas"""
        logger.info("🔍 FASE 1: Validaciones previas")
        
        phase_start = datetime.now()
        
        try:
            # 1. Validar estructura de base de datos
            logger.info("🔍 Validando estructura de base de datos...")
            validation_result = self.update_manager.validate_database_structure()
            
            if not validation_result.success:
                logger.error(f"❌ Estructura de BD inválida: {validation_result.errors}")
                self.overall_success = False
                return False
            
            # 2. Verificar estado de migraciones
            logger.info("🔍 Verificando estado de migraciones...")
            migration_status = self.migration_manager.check_migration_status()
            
            if not migration_status['database_up_to_date']:
                logger.warning("⚠️ Base de datos no está actualizada - se aplicarán migraciones")
            
            # 3. Verificar integridad inicial
            logger.info("🔍 Verificando integridad inicial...")
            integrity_report = self.integrity_checker.run_complete_check()
            
            critical_errors = sum(1 for e in integrity_report.errors if e.severity == 'CRITICAL')
            if critical_errors > 0:
                logger.error(f"❌ {critical_errors} errores críticos de integridad encontrados")
                self.overall_success = False
                return False
            
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_1'] = {
                'success': True,
                'duration': duration,
                'validation_result': validation_result,
                'migration_status': migration_status,
                'integrity_errors': len(integrity_report.errors),
                'description': 'Validaciones previas'
            }
            
            logger.info(f"✅ FASE 1 COMPLETADA ({duration:.2f}s)")
            return True
            
        except Exception as e:
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_1'] = {
                'success': False,
                'duration': duration,
                'error': str(e),
                'description': 'Validaciones previas'
            }
            
            logger.error(f"❌ FASE 1 FALLÓ: {e}")
            self.overall_success = False
            return False

    async def phase_2_backup_preparation(self) -> bool:
        """FASE 2: Backup y preparación"""
        logger.info("💾 FASE 2: Backup y preparación")
        
        phase_start = datetime.now()
        
        try:
            # 1. Crear backup principal
            logger.info("💾 Creando backup principal...")
            backup_success = self.update_manager.create_database_backup()
            
            if not backup_success:
                logger.error("❌ No se pudo crear backup principal")
                self.overall_success = False
                return False
            
            # 2. Generar baseline de validación
            logger.info("📊 Generando baseline de validación...")
            baseline = self.rollback_manager.generate_validation_baseline()
            
            # 3. Crear script de rollback
            logger.info("🔙 Preparando script de rollback...")
            rollback_success = self.update_manager.create_rollback_script()
            
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_2'] = {
                'success': backup_success and rollback_success,
                'duration': duration,
                'backup_created': backup_success,
                'rollback_prepared': rollback_success,
                'baseline_metrics': len(baseline),
                'description': 'Backup y preparación'
            }
            
            logger.info(f"✅ FASE 2 COMPLETADA ({duration:.2f}s)")
            return backup_success and rollback_success
            
        except Exception as e:
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_2'] = {
                'success': False,
                'duration': duration,
                'error': str(e),
                'description': 'Backup y preparación'
            }
            
            logger.error(f"❌ FASE 2 FALLÓ: {e}")
            self.overall_success = False
            return False

    async def phase_3_schema_migrations(self) -> bool:
        """FASE 3: Migraciones de esquema"""
        logger.info("🔄 FASE 3: Migraciones de esquema")
        
        phase_start = datetime.now()
        
        try:
            # Verificar si hay migraciones pendientes
            status = self.migration_manager.check_migration_status()
            
            if status['database_up_to_date']:
                logger.info("ℹ️ Base de datos ya está actualizada")
                duration = (datetime.now() - phase_start).total_seconds()
                self.phase_results['phase_3'] = {
                    'success': True,
                    'duration': duration,
                    'migrations_applied': 0,
                    'already_up_to_date': True,
                    'description': 'Migraciones de esquema (omitidas)'
                }
                return True
            
            # Aplicar migraciones
            logger.info("🔄 Aplicando migraciones pendientes...")
            migration_result = self.migration_manager.upgrade_database('head')
            
            if not migration_result.success:
                logger.error(f"❌ Migraciones fallaron: {migration_result.errors}")
                self.overall_success = False
                return False
            
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_3'] = {
                'success': migration_result.success,
                'duration': duration,
                'migrations_applied': len(migration_result.migrations_applied),
                'from_revision': migration_result.from_revision,
                'to_revision': migration_result.to_revision,
                'migration_duration': migration_result.duration_seconds,
                'description': 'Migraciones de esquema'
            }
            
            logger.info(f"✅ FASE 3 COMPLETADA ({duration:.2f}s)")
            return True
            
        except Exception as e:
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_3'] = {
                'success': False,
                'duration': duration,
                'error': str(e),
                'description': 'Migraciones de esquema'
            }
            
            logger.error(f"❌ FASE 3 FALLÓ: {e}")
            self.overall_success = False
            return False

    async def phase_4_mass_data_update(self) -> bool:
        """FASE 4: Actualización masiva de datos"""
        logger.info("🔄 FASE 4: Actualización masiva de datos")
        
        phase_start = datetime.now()
        
        try:
            # 1. Cargar tabla de correspondencia
            if not self.correspondence_path:
                logger.warning("⚠️ No se especificó tabla de correspondencia - saltando actualización de imágenes")
                duration = (datetime.now() - phase_start).total_seconds()
                self.phase_results['phase_4'] = {
                    'success': True,
                    'duration': duration,
                    'skipped': True,
                    'description': 'Actualización masiva (omitida)'
                }
                return True
            
            logger.info("📋 Cargando tabla de correspondencia...")
            correspondence = self.update_manager.load_correspondence_table(self.correspondence_path)
            
            if not correspondence:
                logger.error("❌ No se pudo cargar tabla de correspondencia")
                self.overall_success = False
                return False
            
            # 2. Ejecutar actualización masiva
            logger.info("🔄 Ejecutando actualización masiva de imágenes...")
            update_result = self.update_manager.update_question_images(correspondence)
            
            if update_result.failed_records > 0:
                logger.warning(f"⚠️ {update_result.failed_records} actualizaciones fallaron")
            
            # 3. Actualizar campo requiere_imagen
            logger.info("🖼️ Actualizando campo requiere_imagen...")
            requiere_imagen_count = self.update_manager.update_requiere_imagen_field()
            
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_4'] = {
                'success': update_result.success,
                'duration': duration,
                'records_updated': update_result.updated_records,
                'records_failed': update_result.failed_records,
                'requiere_imagen_updated': requiere_imagen_count,
                'correspondence_entries': len(correspondence),
                'description': 'Actualización masiva de datos'
            }
            
            logger.info(f"✅ FASE 4 COMPLETADA ({duration:.2f}s)")
            return update_result.success
            
        except Exception as e:
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_4'] = {
                'success': False,
                'duration': duration,
                'error': str(e),
                'description': 'Actualización masiva de datos'
            }
            
            logger.error(f"❌ FASE 4 FALLÓ: {e}")
            self.overall_success = False
            return False

    async def phase_5_index_optimization(self) -> bool:
        """FASE 5: Optimización de índices"""
        logger.info("📊 FASE 5: Optimización de índices")
        
        phase_start = datetime.now()
        
        try:
            # Ejecutar optimización completa de índices
            logger.info("🔨 Optimizando índices...")
            optimization_report = self.index_optimizer.run_complete_optimization(priority_filter=2)
            
            success = optimization_report.indexes_failed == 0
            
            if optimization_report.indexes_failed > 0:
                logger.warning(f"⚠️ {optimization_report.indexes_failed} índices fallaron")
            
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_5'] = {
                'success': success,
                'duration': duration,
                'indexes_created': optimization_report.indexes_created,
                'indexes_existed': optimization_report.indexes_existed,
                'indexes_failed': optimization_report.indexes_failed,
                'optimization_duration': optimization_report.optimization_time_seconds,
                'performance_improvements': optimization_report.performance_improvements,
                'description': 'Optimización de índices'
            }
            
            logger.info(f"✅ FASE 5 COMPLETADA ({duration:.2f}s)")
            return success
            
        except Exception as e:
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_5'] = {
                'success': False,
                'duration': duration,
                'error': str(e),
                'description': 'Optimización de índices'
            }
            
            logger.error(f"❌ FASE 5 FALLÓ: {e}")
            self.overall_success = False
            return False

    async def phase_6_integrity_validation(self) -> bool:
        """FASE 6: Validación de integridad"""
        logger.info("🔗 FASE 6: Validación de integridad")
        
        phase_start = datetime.now()
        
        try:
            # Ejecutar verificación completa de integridad
            logger.info("🔍 Verificando integridad referencial...")
            integrity_report = self.integrity_checker.run_complete_check()
            
            critical_errors = sum(1 for e in integrity_report.errors if e.severity == 'CRITICAL')
            success = critical_errors == 0
            
            if critical_errors > 0:
                logger.error(f"❌ {critical_errors} errores críticos de integridad")
                self.overall_success = False
            
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_6'] = {
                'success': success,
                'duration': duration,
                'total_checks': integrity_report.total_checks,
                'passed_checks': integrity_report.passed_checks,
                'critical_errors': critical_errors,
                'warnings': integrity_report.warnings,
                'check_duration': integrity_report.performance_metrics.get('check_duration_seconds', 0),
                'description': 'Validación de integridad'
            }
            
            logger.info(f"✅ FASE 6 COMPLETADA ({duration:.2f}s)")
            return success
            
        except Exception as e:
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_6'] = {
                'success': False,
                'duration': duration,
                'error': str(e),
                'description': 'Validación de integridad'
            }
            
            logger.error(f"❌ FASE 6 FALLÓ: {e}")
            self.overall_success = False
            return False

    async def phase_7_cache_management(self) -> bool:
        """FASE 7: Gestión de cache"""
        logger.info("🧹 FASE 7: Gestión de cache")
        
        phase_start = datetime.now()
        
        try:
            if not self.cache_manager:
                logger.info("ℹ️ Redis no configurado - saltando gestión de cache")
                duration = (datetime.now() - phase_start).total_seconds()
                self.phase_results['phase_7'] = {
                    'success': True,
                    'duration': duration,
                    'skipped': True,
                    'description': 'Gestión de cache (omitida)'
                }
                return True
            
            # 1. Invalidación masiva de cache
            logger.info("🧹 Invalidando cache...")
            invalidation_report = self.cache_manager.mass_invalidate_after_db_update()
            
            # 2. Optimizar rendimiento de cache
            logger.info("🚀 Optimizando cache...")
            optimizations = self.cache_manager.optimize_cache_performance()
            
            # 3. Pre-cargar imágenes importantes (ejemplo básico)
            logger.info("⚡ Pre-cargando imágenes importantes...")
            sample_images = [
                {'path': '/mathimg/Math_1_1_Doc1.png', 'question_id': 'math_001', 'size_bytes': 45000}
            ]
            preloaded = await self.cache_manager.preload_important_images(sample_images, 'high')
            
            success = len(invalidation_report.errors) == 0
            
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_7'] = {
                'success': success,
                'duration': duration,
                'keys_invalidated': invalidation_report.keys_invalidated,
                'invalidation_errors': len(invalidation_report.errors),
                'preloaded_images': preloaded,
                'optimizations_applied': sum(1 for v in optimizations.values() if v),
                'description': 'Gestión de cache'
            }
            
            logger.info(f"✅ FASE 7 COMPLETADA ({duration:.2f}s)")
            return success
            
        except Exception as e:
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_7'] = {
                'success': False,
                'duration': duration,
                'error': str(e),
                'description': 'Gestión de cache'
            }
            
            logger.error(f"❌ FASE 7 FALLÓ: {e}")
            self.overall_success = False
            return False

    async def phase_8_final_validation(self):
        """FASE 8: Validación final"""
        logger.info("✅ FASE 8: Validación final")
        
        phase_start = datetime.now()
        
        try:
            # Validación final completa
            logger.info("🔍 Ejecutando validaciones finales...")
            
            # 1. Verificar estado de migraciones
            migration_status = self.migration_manager.check_migration_status()
            
            # 2. Verificar integridad una vez más
            integrity_brief = self.integrity_checker.check_foreign_keys()
            critical_fk_errors = sum(1 for e in integrity_brief if e.severity == 'CRITICAL')
            
            # 3. Verificar métricas de cache (si disponible)
            cache_healthy = True
            if self.cache_manager:
                cache_health = self.cache_manager.monitor_cache_health()
                cache_healthy = cache_health['status'] != 'critical'
            
            success = (migration_status['database_up_to_date'] and 
                      critical_fk_errors == 0 and 
                      cache_healthy)
            
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_8'] = {
                'success': success,
                'duration': duration,
                'migrations_up_to_date': migration_status['database_up_to_date'],
                'critical_fk_errors': critical_fk_errors,
                'cache_healthy': cache_healthy,
                'description': 'Validación final'
            }
            
            if not success:
                self.overall_success = False
            
            logger.info(f"✅ FASE 8 COMPLETADA ({duration:.2f}s)")
            
        except Exception as e:
            duration = (datetime.now() - phase_start).total_seconds()
            self.phase_results['phase_8'] = {
                'success': False,
                'duration': duration,
                'error': str(e),
                'description': 'Validación final'
            }
            
            logger.error(f"❌ FASE 8 FALLÓ: {e}")
            self.overall_success = False

    async def generate_final_report(self, start_time: datetime):
        """Generar reporte final completo"""
        logger.info("📊 Generando reporte final...")
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        final_report = {
            'execution_summary': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration_seconds': total_duration,
                'overall_success': self.overall_success,
                'database': self.db_config.get('database'),
                'correspondence_table': self.correspondence_path
            },
            'phase_results': self.phase_results,
            'phase_summary': {
                'total_phases': len(self.phase_results),
                'successful_phases': sum(1 for p in self.phase_results.values() if p['success']),
                'failed_phases': sum(1 for p in self.phase_results.values() if not p['success']),
                'total_phase_duration': sum(p['duration'] for p in self.phase_results.values())
            },
            'recommendations': self._generate_recommendations()
        }
        
        # Guardar reporte
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"database/reports/master_update_report_{timestamp}.json"
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📋 Reporte final guardado: {report_path}")
        
        # Mostrar resumen
        self._print_final_summary(final_report)

    def _generate_recommendations(self) -> List[str]:
        """Generar recomendaciones basadas en resultados"""
        recommendations = []
        
        if not self.overall_success:
            recommendations.append("Revisar logs detallados para identificar causas de fallas")
            recommendations.append("Considerar ejecutar rollback si es necesario")
        
        # Recomendaciones específicas por fase
        for phase, result in self.phase_results.items():
            if not result['success']:
                if 'integrity' in result['description'].lower():
                    recommendations.append("Ejecutar scripts de corrección de integridad")
                elif 'cache' in result['description'].lower():
                    recommendations.append("Revisar configuración de Redis")
                elif 'migration' in result['description'].lower():
                    recommendations.append("Verificar archivos de migración de Alembic")
        
        # Recomendaciones generales
        if self.overall_success:
            recommendations.extend([
                "Monitorear rendimiento de la aplicación después de los cambios",
                "Verificar funcionamiento de endpoints de media",
                "Considerar programar limpieza de backups antiguos"
            ])
        
        return recommendations

    def _print_final_summary(self, report: Dict[str, Any]):
        """Imprimir resumen final en consola"""
        summary = report['execution_summary']
        phase_summary = report['phase_summary']
        
        print("\n" + "="*80)
        print("REPORTE FINAL - ACTUALIZACIÓN MASIVA ICFES LEVELING")
        print("="*80)
        print(f"🕐 Inicio: {summary['start_time']}")
        print(f"🕐 Fin: {summary['end_time']}")
        print(f"⏱️ Duración total: {summary['total_duration_seconds']:.2f}s")
        print(f"🎯 Éxito general: {'✅ SÍ' if summary['overall_success'] else '❌ NO'}")
        print()
        print("RESUMEN POR FASES:")
        print(f"📊 Total de fases: {phase_summary['total_phases']}")
        print(f"✅ Fases exitosas: {phase_summary['successful_phases']}")
        print(f"❌ Fases fallidas: {phase_summary['failed_phases']}")
        print()
        
        # Detalles por fase
        for phase, result in self.phase_results.items():
            status_icon = "✅" if result['success'] else "❌"
            print(f"{status_icon} {result['description']}: {result['duration']:.2f}s")
        
        print()
        if report['recommendations']:
            print("💡 RECOMENDACIONES:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print("="*80)

    async def handle_critical_error(self, error: Exception):
        """Manejar errores críticos"""
        logger.error(f"🚨 MANEJO DE ERROR CRÍTICO: {error}")
        
        # Generar reporte de error
        error_report = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'phase_results': self.phase_results,
            'rollback_available': self.update_manager.backup_created if self.update_manager else False
        }
        
        error_report_path = f"database/reports/critical_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(error_report_path), exist_ok=True)
        
        with open(error_report_path, 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.error(f"📋 Reporte de error guardado: {error_report_path}")
        
        # Sugerir acciones de recuperación
        print("\n🚨 ERROR CRÍTICO DETECTADO")
        print("Acciones recomendadas:")
        print("1. Revisar el reporte de error detallado")
        print("2. Verificar logs del sistema")
        if error_report['rollback_available']:
            print("3. Considerar ejecutar rollback para restaurar estado anterior")
        print("4. Contactar al equipo de desarrollo si es necesario")


async def main():
    """Función principal del script maestro"""
    
    # Configuración del sistema
    config = {
        'database': {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'gameplay_db'),
            'user': os.getenv('DB_USER', 'gameplay'),
            'password': os.getenv('DB_PASSWORD', 'gameplay123')
        },
        'redis': {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': int(os.getenv('REDIS_DB', '0')),
            'decode_responses': True
        },
        'correspondence_table': os.getenv(
            'CORRESPONDENCE_TABLE', 
            r'C:\Users\PEDRO_PEREZ\tabla_correspondencia_imagenes.csv'
        )
    }
    
    logger.info("🚀 INICIANDO SCRIPT MAESTRO DE ACTUALIZACIÓN")
    logger.info(f"Base de datos: {config['database']['database']}")
    logger.info(f"Tabla de correspondencia: {config['correspondence_table']}")
    
    try:
        # Crear orquestador
        orchestrator = MasterUpdateOrchestrator(config)
        
        # Ejecutar proceso completo
        success = await orchestrator.execute_complete_update_process()
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ ERROR FATAL EN SCRIPT MAESTRO: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)