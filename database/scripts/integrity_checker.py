#!/usr/bin/env python3
"""
Sistema de Verificación de Integridad Referencial para ICFES Leveling
Valida constraints, foreign keys, y consistencia de datos después de actualizaciones masivas.
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class IntegrityError:
    """Representa un error de integridad"""
    severity: str  # 'CRITICAL', 'WARNING', 'INFO'
    category: str  # 'FOREIGN_KEY', 'CONSTRAINT', 'DATA_CONSISTENCY', 'INDEX'
    table_name: str
    description: str
    affected_records: int
    sql_query: Optional[str] = None
    suggested_fix: Optional[str] = None

@dataclass
class IntegrityReport:
    """Reporte completo de integridad"""
    timestamp: str
    database_name: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    critical_errors: int
    warnings: int
    info_messages: int
    errors: List[IntegrityError]
    performance_metrics: Dict[str, Any]

class DatabaseIntegrityChecker:
    """Verificador de integridad referencial y consistencia de datos"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.errors: List[IntegrityError] = []
        self.performance_metrics = {}
        
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return psycopg2.connect(**self.db_config)

    def check_foreign_keys(self) -> List[IntegrityError]:
        """Verificar todas las foreign keys de la tabla questions"""
        logger.info("🔗 Verificando foreign keys...")
        errors = []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Verificar topic_id
                cursor.execute("""
                    SELECT COUNT(*) as orphaned_count
                    FROM questions q 
                    LEFT JOIN topics t ON q.topic_id = t.id 
                    WHERE q.topic_id IS NOT NULL AND t.id IS NULL;
                """)
                
                orphaned_topics = cursor.fetchone()[0]
                if orphaned_topics > 0:
                    errors.append(IntegrityError(
                        severity='CRITICAL',
                        category='FOREIGN_KEY',
                        table_name='questions',
                        description=f'{orphaned_topics} preguntas con topic_id inválido',
                        affected_records=orphaned_topics,
                        sql_query="""SELECT id, topic_id FROM questions q 
                                   WHERE NOT EXISTS (SELECT 1 FROM topics t WHERE t.id = q.topic_id)
                                   AND topic_id IS NOT NULL;""",
                        suggested_fix="Eliminar registros huérfanos o crear topics faltantes"
                    ))
                
                # 2. Verificar subject_id
                cursor.execute("""
                    SELECT COUNT(*) as orphaned_count
                    FROM questions q 
                    LEFT JOIN subjects s ON q.subject_id = s.id 
                    WHERE q.subject_id IS NOT NULL AND s.id IS NULL;
                """)
                
                orphaned_subjects = cursor.fetchone()[0]
                if orphaned_subjects > 0:
                    errors.append(IntegrityError(
                        severity='CRITICAL',
                        category='FOREIGN_KEY',
                        table_name='questions',
                        description=f'{orphaned_subjects} preguntas con subject_id inválido',
                        affected_records=orphaned_subjects,
                        sql_query="""SELECT id, subject_id FROM questions q 
                                   WHERE NOT EXISTS (SELECT 1 FROM subjects s WHERE s.id = q.subject_id)
                                   AND subject_id IS NOT NULL;""",
                        suggested_fix="Eliminar registros huérfanos o crear subjects faltantes"
                    ))
                
                # 3. Verificar integridad de relaciones cascade
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM battle_answers ba
                    LEFT JOIN questions q ON ba.question_id = q.id 
                    WHERE q.id IS NULL;
                """)
                
                orphaned_battle_answers = cursor.fetchone()[0]
                if orphaned_battle_answers > 0:
                    errors.append(IntegrityError(
                        severity='WARNING',
                        category='FOREIGN_KEY',
                        table_name='battle_answers',
                        description=f'{orphaned_battle_answers} respuestas de batalla huérfanas',
                        affected_records=orphaned_battle_answers,
                        suggested_fix="Limpiar respuestas huérfanas con cascada"
                    ))
                
                logger.info(f"✓ Verificación FK completada: {len(errors)} errores encontrados")
                
        except Exception as e:
            logger.error(f"Error verificando foreign keys: {e}")
            errors.append(IntegrityError(
                severity='CRITICAL',
                category='FOREIGN_KEY',
                table_name='questions',
                description=f'Error de conexión o consulta: {str(e)}',
                affected_records=0,
                suggested_fix="Verificar conexión a base de datos y permisos"
            ))
        
        return errors

    def check_constraints(self) -> List[IntegrityError]:
        """Verificar constraints de tabla y datos"""
        logger.info("🛡️ Verificando constraints...")
        errors = []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Verificar constraint de respuesta_correcta
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM questions 
                    WHERE respuesta_correcta NOT IN ('a', 'b', 'c', 'd', 'A', 'B', 'C', 'D')
                    AND respuesta_correcta IS NOT NULL;
                """)
                
                invalid_answers = cursor.fetchone()[0]
                if invalid_answers > 0:
                    errors.append(IntegrityError(
                        severity='CRITICAL',
                        category='CONSTRAINT',
                        table_name='questions',
                        description=f'{invalid_answers} preguntas con respuesta_correcta inválida',
                        affected_records=invalid_answers,
                        sql_query="SELECT id, respuesta_correcta FROM questions WHERE respuesta_correcta NOT IN ('a', 'b', 'c', 'd', 'A', 'B', 'C', 'D');",
                        suggested_fix="Corregir valores de respuesta_correcta a a, b, c, o d"
                    ))
                
                # 2. Verificar constraint de difficulty
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM questions 
                    WHERE difficulty < 1 OR difficulty > 10;
                """)
                
                invalid_difficulty = cursor.fetchone()[0]
                if invalid_difficulty > 0:
                    errors.append(IntegrityError(
                        severity='WARNING',
                        category='CONSTRAINT',
                        table_name='questions',
                        description=f'{invalid_difficulty} preguntas con difficulty fuera del rango 1-10',
                        affected_records=invalid_difficulty,
                        sql_query="SELECT id, difficulty FROM questions WHERE difficulty < 1 OR difficulty > 10;",
                        suggested_fix="Ajustar difficulty a valores entre 1 y 10"
                    ))
                
                # 3. Verificar que preguntas tengan contenido
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM questions 
                    WHERE (pregunta_texto IS NULL OR pregunta_texto = '') 
                    AND (pregunta_imagen IS NULL OR pregunta_imagen = '')
                    AND (question_text IS NULL OR question_text = '');
                """)
                
                empty_questions = cursor.fetchone()[0]
                if empty_questions > 0:
                    errors.append(IntegrityError(
                        severity='CRITICAL',
                        category='CONSTRAINT',
                        table_name='questions',
                        description=f'{empty_questions} preguntas sin contenido (texto o imagen)',
                        affected_records=empty_questions,
                        suggested_fix="Agregar contenido a preguntas vacías o eliminar registros"
                    ))
                
                # 4. Verificar constraint NOT NULL en campos críticos
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM questions 
                    WHERE id IS NULL OR topic_id IS NULL OR subject_id IS NULL;
                """)
                
                null_critical = cursor.fetchone()[0]
                if null_critical > 0:
                    errors.append(IntegrityError(
                        severity='CRITICAL',
                        category='CONSTRAINT',
                        table_name='questions',
                        description=f'{null_critical} preguntas con campos críticos NULL',
                        affected_records=null_critical,
                        suggested_fix="Completar campos obligatorios o eliminar registros inválidos"
                    ))
                
        except Exception as e:
            logger.error(f"Error verificando constraints: {e}")
            errors.append(IntegrityError(
                severity='CRITICAL',
                category='CONSTRAINT',
                table_name='questions',
                description=f'Error verificando constraints: {str(e)}',
                affected_records=0
            ))
        
        return errors

    def check_data_consistency(self) -> List[IntegrityError]:
        """Verificar consistencia de datos"""
        logger.info("📊 Verificando consistencia de datos...")
        errors = []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Verificar consistencia de campo requiere_imagen
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM questions 
                    WHERE requiere_imagen = true 
                    AND (pregunta_imagen IS NULL OR pregunta_imagen = '')
                    AND (opcion_a_imagen IS NULL OR opcion_a_imagen = '')
                    AND (opcion_b_imagen IS NULL OR opcion_b_imagen = '')
                    AND (opcion_c_imagen IS NULL OR opcion_c_imagen = '')
                    AND (opcion_d_imagen IS NULL OR opcion_d_imagen = '');
                """)
                
                inconsistent_requiere_imagen = cursor.fetchone()[0]
                if inconsistent_requiere_imagen > 0:
                    errors.append(IntegrityError(
                        severity='WARNING',
                        category='DATA_CONSISTENCY',
                        table_name='questions',
                        description=f'{inconsistent_requiere_imagen} preguntas marcadas como requiere_imagen=true sin imágenes',
                        affected_records=inconsistent_requiere_imagen,
                        suggested_fix="Actualizar campo requiere_imagen basado en existencia real de imágenes"
                    ))
                
                # 2. Verificar rutas de imagen válidas
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM questions 
                    WHERE (pregunta_imagen LIKE '%http://%' OR pregunta_imagen LIKE '%https://%')
                    OR (opcion_a_imagen LIKE '%http://%' OR opcion_a_imagen LIKE '%https://%')
                    OR (opcion_b_imagen LIKE '%http://%' OR opcion_b_imagen LIKE '%https://%')
                    OR (opcion_c_imagen LIKE '%http://%' OR opcion_c_imagen LIKE '%https://%')
                    OR (opcion_d_imagen LIKE '%http://%' OR opcion_d_imagen LIKE '%https://%');
                """)
                
                url_images = cursor.fetchone()[0]
                if url_images > 0:
                    errors.append(IntegrityError(
                        severity='INFO',
                        category='DATA_CONSISTENCY',
                        table_name='questions',
                        description=f'{url_images} preguntas con URLs de imagen (no rutas locales)',
                        affected_records=url_images,
                        suggested_fix="Verificar si estas URLs deben ser convertidas a rutas locales"
                    ))
                
                # 3. Verificar duplicados por natural_key
                cursor.execute("""
                    SELECT natural_key, COUNT(*) 
                    FROM questions 
                    WHERE natural_key IS NOT NULL 
                    GROUP BY natural_key 
                    HAVING COUNT(*) > 1;
                """)
                
                duplicates = cursor.fetchall()
                if duplicates:
                    total_duplicates = sum(count - 1 for _, count in duplicates)
                    errors.append(IntegrityError(
                        severity='WARNING',
                        category='DATA_CONSISTENCY',
                        table_name='questions',
                        description=f'{total_duplicates} preguntas duplicadas por natural_key',
                        affected_records=total_duplicates,
                        sql_query="SELECT natural_key, COUNT(*) FROM questions GROUP BY natural_key HAVING COUNT(*) > 1;",
                        suggested_fix="Eliminar duplicados manteniendo el registro más reciente"
                    ))
                
                # 4. Verificar opciones de respuesta válidas
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM questions q
                    WHERE respuesta_correcta = 'a' 
                    AND (opcion_a_texto IS NULL OR opcion_a_texto = '') 
                    AND (opcion_a_imagen IS NULL OR opcion_a_imagen = '')
                    UNION ALL
                    SELECT COUNT(*) 
                    FROM questions q
                    WHERE respuesta_correcta = 'b' 
                    AND (opcion_b_texto IS NULL OR opcion_b_texto = '') 
                    AND (opcion_b_imagen IS NULL OR opcion_b_imagen = '')
                    UNION ALL
                    SELECT COUNT(*) 
                    FROM questions q
                    WHERE respuesta_correcta = 'c' 
                    AND (opcion_c_texto IS NULL OR opcion_c_texto = '') 
                    AND (opcion_c_imagen IS NULL OR opcion_c_imagen = '')
                    UNION ALL
                    SELECT COUNT(*) 
                    FROM questions q
                    WHERE respuesta_correcta = 'd' 
                    AND (opcion_d_texto IS NULL OR opcion_d_texto = '') 
                    AND (opcion_d_imagen IS NULL OR opcion_d_imagen = '');
                """)
                
                invalid_correct_options = sum(row[0] for row in cursor.fetchall())
                if invalid_correct_options > 0:
                    errors.append(IntegrityError(
                        severity='CRITICAL',
                        category='DATA_CONSISTENCY',
                        table_name='questions',
                        description=f'{invalid_correct_options} preguntas donde la respuesta correcta no tiene contenido',
                        affected_records=invalid_correct_options,
                        suggested_fix="Corregir respuesta_correcta o agregar contenido a la opción correcta"
                    ))
                
        except Exception as e:
            logger.error(f"Error verificando consistencia: {e}")
            errors.append(IntegrityError(
                severity='CRITICAL',
                category='DATA_CONSISTENCY',
                table_name='questions',
                description=f'Error verificando consistencia: {str(e)}',
                affected_records=0
            ))
        
        return errors

    def check_indexes_performance(self) -> List[IntegrityError]:
        """Verificar existencia y rendimiento de índices"""
        logger.info("📈 Verificando índices y rendimiento...")
        errors = []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Verificar índices recomendados
                recommended_indexes = [
                    ('idx_questions_pregunta_imagen', 'pregunta_imagen'),
                    ('idx_questions_area_imagen', 'area_evaluada, requiere_imagen'),
                    ('idx_questions_natural_key', 'natural_key'),
                    ('idx_questions_difficulty', 'difficulty'),
                    ('idx_questions_topic_subject', 'topic_id, subject_id')
                ]
                
                cursor.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'questions';
                """)
                
                existing_indexes = {row[0] for row in cursor.fetchall()}
                
                for index_name, columns in recommended_indexes:
                    if index_name not in existing_indexes:
                        errors.append(IntegrityError(
                            severity='WARNING',
                            category='INDEX',
                            table_name='questions',
                            description=f'Índice recomendado faltante: {index_name} en ({columns})',
                            affected_records=0,
                            suggested_fix=f"Crear índice: CREATE INDEX {index_name} ON questions({columns});"
                        ))
                
                # 2. Verificar estadísticas de tabla
                cursor.execute("""
                    SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del,
                           n_dead_tup, last_vacuum, last_autovacuum, last_analyze, last_autoanalyze
                    FROM pg_stat_user_tables 
                    WHERE tablename = 'questions';
                """)
                
                stats = cursor.fetchone()
                if stats:
                    dead_tuples = stats[5] or 0
                    total_tuples = (stats[2] or 0) + (stats[3] or 0)
                    
                    if total_tuples > 0 and dead_tuples / total_tuples > 0.2:
                        errors.append(IntegrityError(
                            severity='WARNING',
                            category='INDEX',
                            table_name='questions',
                            description=f'Tabla necesita VACUUM: {dead_tuples} tuplas muertas de {total_tuples}',
                            affected_records=dead_tuples,
                            suggested_fix="Ejecutar VACUUM ANALYZE questions;"
                        ))
                
                # 3. Verificar tamaño de tabla y consultas lentas
                cursor.execute("""
                    SELECT pg_size_pretty(pg_total_relation_size('questions')) as table_size,
                           pg_size_pretty(pg_relation_size('questions')) as data_size;
                """)
                
                sizes = cursor.fetchone()
                logger.info(f"Tamaño tabla questions: {sizes[0]} (datos: {sizes[1]})")
                
        except Exception as e:
            logger.error(f"Error verificando índices: {e}")
            errors.append(IntegrityError(
                severity='WARNING',
                category='INDEX',
                table_name='questions',
                description=f'Error verificando índices: {str(e)}',
                affected_records=0
            ))
        
        return errors

    def check_database_health(self) -> Dict[str, Any]:
        """Verificar salud general de la base de datos"""
        logger.info("🏥 Verificando salud general de la base de datos...")
        health_metrics = {}
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Estadísticas generales
                cursor.execute("SELECT COUNT(*) FROM questions;")
                health_metrics['total_questions'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM questions WHERE requiere_imagen = true;")
                health_metrics['questions_with_images'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT topic_id) FROM questions;")
                health_metrics['unique_topics'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT subject_id) FROM questions;")
                health_metrics['unique_subjects'] = cursor.fetchone()[0]
                
                # Distribución por dificultad
                cursor.execute("""
                    SELECT difficulty, COUNT(*) 
                    FROM questions 
                    GROUP BY difficulty 
                    ORDER BY difficulty;
                """)
                health_metrics['difficulty_distribution'] = dict(cursor.fetchall())
                
                # Preguntas actualizadas recientemente
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM questions 
                    WHERE created_at >= NOW() - INTERVAL '24 hours';
                """)
                health_metrics['questions_last_24h'] = cursor.fetchone()[0]
                
                logger.info(f"✓ Métricas de salud recopiladas: {len(health_metrics)} indicadores")
                
        except Exception as e:
            logger.error(f"Error verificando salud de BD: {e}")
            health_metrics['error'] = str(e)
        
        return health_metrics

    def generate_fix_scripts(self, errors: List[IntegrityError]) -> str:
        """Generar scripts SQL para corregir errores encontrados"""
        fix_script = f"""-- SCRIPT DE CORRECCIÓN DE INTEGRIDAD
-- Generado: {datetime.now().isoformat()}
-- Errores encontrados: {len(errors)}

BEGIN;

"""
        
        for error in errors:
            if error.severity == 'CRITICAL' and error.suggested_fix:
                fix_script += f"""
-- {error.category}: {error.description}
-- Registros afectados: {error.affected_records}
-- {error.suggested_fix}

"""
                
                if error.sql_query and 'DELETE' not in error.sql_query.upper():
                    fix_script += f"-- Query diagnóstica:\n-- {error.sql_query}\n\n"
        
        fix_script += """
-- Verificar cambios antes de commit
-- ROLLBACK; -- Descomentar si algo sale mal
-- COMMIT;   -- Descomentar cuando esté seguro
"""
        
        return fix_script

    def run_complete_check(self) -> IntegrityReport:
        """Ejecutar verificación completa de integridad"""
        logger.info("🔍 Iniciando verificación completa de integridad...")
        start_time = datetime.now()
        
        all_errors = []
        checks_performed = 0
        
        # Ejecutar todas las verificaciones
        try:
            # 1. Foreign Keys
            fk_errors = self.check_foreign_keys()
            all_errors.extend(fk_errors)
            checks_performed += 1
            
            # 2. Constraints  
            constraint_errors = self.check_constraints()
            all_errors.extend(constraint_errors)
            checks_performed += 1
            
            # 3. Data Consistency
            consistency_errors = self.check_data_consistency()
            all_errors.extend(consistency_errors)
            checks_performed += 1
            
            # 4. Indexes Performance
            index_errors = self.check_indexes_performance()
            all_errors.extend(index_errors)
            checks_performed += 1
            
            # 5. Database Health
            health_metrics = self.check_database_health()
            checks_performed += 1
            
        except Exception as e:
            logger.error(f"Error durante verificación: {e}")
            all_errors.append(IntegrityError(
                severity='CRITICAL',
                category='SYSTEM',
                table_name='N/A',
                description=f'Error del sistema: {str(e)}',
                affected_records=0
            ))
        
        # Clasificar errores
        critical_errors = sum(1 for e in all_errors if e.severity == 'CRITICAL')
        warnings = sum(1 for e in all_errors if e.severity == 'WARNING')
        info_messages = sum(1 for e in all_errors if e.severity == 'INFO')
        
        # Métricas de rendimiento
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        performance_metrics = {
            'check_duration_seconds': duration,
            'checks_performed': checks_performed,
            'database_health': health_metrics if 'health_metrics' in locals() else {}
        }
        
        # Crear reporte
        report = IntegrityReport(
            timestamp=start_time.isoformat(),
            database_name=self.db_config.get('database', 'unknown'),
            total_checks=checks_performed,
            passed_checks=checks_performed - len([e for e in all_errors if e.severity == 'CRITICAL']),
            failed_checks=len([e for e in all_errors if e.severity == 'CRITICAL']),
            critical_errors=critical_errors,
            warnings=warnings,
            info_messages=info_messages,
            errors=all_errors,
            performance_metrics=performance_metrics
        )
        
        logger.info(f"✅ Verificación completada en {duration:.2f}s")
        logger.info(f"📊 Resumen: {critical_errors} críticos, {warnings} advertencias, {info_messages} info")
        
        return report

    def save_report(self, report: IntegrityReport, output_path: str = None) -> str:
        """Guardar reporte de integridad"""
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"database/reports/integrity_report_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convertir a diccionario para JSON
        report_dict = asdict(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📋 Reporte guardado: {output_path}")
        
        # Generar también script de corrección
        if report.errors:
            fix_script_path = output_path.replace('.json', '_fixes.sql')
            fix_script = self.generate_fix_scripts(report.errors)
            
            with open(fix_script_path, 'w', encoding='utf-8') as f:
                f.write(fix_script)
            
            logger.info(f"🔧 Script de corrección: {fix_script_path}")
        
        return output_path


def main():
    """Función principal del verificador de integridad"""
    
    # Configuración de base de datos
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'gameplay_db'),
        'user': os.getenv('DB_USER', 'gameplay'),
        'password': os.getenv('DB_PASSWORD', 'gameplay123')
    }
    
    logger.info("=== VERIFICADOR DE INTEGRIDAD REFERENCIAL ===")
    
    try:
        # Inicializar verificador
        checker = DatabaseIntegrityChecker(db_config)
        
        # Ejecutar verificación completa
        report = checker.run_complete_check()
        
        # Guardar reporte
        report_path = checker.save_report(report)
        
        # Mostrar resumen
        print("\n" + "="*60)
        print("RESUMEN DE INTEGRIDAD REFERENCIAL")
        print("="*60)
        print(f"✓ Verificaciones realizadas: {report.total_checks}")
        print(f"✓ Verificaciones exitosas: {report.passed_checks}")
        print(f"❌ Verificaciones fallidas: {report.failed_checks}")
        print(f"🚨 Errores críticos: {report.critical_errors}")
        print(f"⚠️ Advertencias: {report.warnings}")
        print(f"ℹ️ Información: {report.info_messages}")
        print(f"📋 Reporte guardado: {report_path}")
        
        # Mostrar errores críticos
        if report.critical_errors > 0:
            print("\n🚨 ERRORES CRÍTICOS ENCONTRADOS:")
            for error in report.errors:
                if error.severity == 'CRITICAL':
                    print(f"  • {error.description} ({error.affected_records} registros)")
        
        # Mostrar advertencias importantes
        if report.warnings > 0:
            print("\n⚠️ ADVERTENCIAS IMPORTANTES:")
            for error in report.errors:
                if error.severity == 'WARNING':
                    print(f"  • {error.description} ({error.affected_records} registros)")
        
        print("="*60)
        
        # Código de salida basado en errores críticos
        return 0 if report.critical_errors == 0 else 1
        
    except Exception as e:
        logger.error(f"❌ Error fatal en verificación: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)