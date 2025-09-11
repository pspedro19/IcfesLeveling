#!/usr/bin/env python3
"""
Optimizador de Índices para Sistema ICFES Leveling
Crea índices optimizados para búsquedas de imágenes y consultas de rendimiento.
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class IndexDefinition:
    """Definición de un índice"""
    name: str
    table: str
    columns: str
    index_type: str = 'btree'
    unique: bool = False
    concurrent: bool = True
    where_clause: Optional[str] = None
    description: str = ""
    priority: int = 1  # 1=alta, 2=media, 3=baja

@dataclass
class IndexStatus:
    """Estado de un índice"""
    name: str
    exists: bool
    size: str
    usage_stats: Optional[Dict[str, Any]] = None
    creation_time: Optional[str] = None
    last_used: Optional[str] = None

@dataclass
class OptimizationReport:
    """Reporte de optimización de índices"""
    timestamp: str
    database_name: str
    total_indexes_defined: int
    indexes_created: int
    indexes_existed: int
    indexes_failed: int
    optimization_time_seconds: float
    index_definitions: List[IndexDefinition]
    index_statuses: List[IndexStatus]
    performance_improvements: Dict[str, Any]

class DatabaseIndexOptimizer:
    """Optimizador de índices para base de datos"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.index_definitions = self._define_optimized_indexes()
        
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return psycopg2.connect(**self.db_config)

    def _define_optimized_indexes(self) -> List[IndexDefinition]:
        """Definir todos los índices optimizados necesarios"""
        indexes = []
        
        # === ÍNDICES DE ALTA PRIORIDAD ===
        
        # 1. Índice para búsquedas de imágenes de pregunta
        indexes.append(IndexDefinition(
            name="idx_questions_pregunta_imagen",
            table="questions",
            columns="pregunta_imagen",
            where_clause="pregunta_imagen IS NOT NULL",
            description="Optimiza búsquedas de imágenes de pregunta",
            priority=1
        ))
        
        # 2. Índice compuesto para área evaluada y requiere imagen
        indexes.append(IndexDefinition(
            name="idx_questions_area_imagen",
            table="questions", 
            columns="area_evaluada, requiere_imagen",
            where_clause="requiere_imagen = true",
            description="Optimiza filtros por área con imágenes",
            priority=1
        ))
        
        # 3. Índice único en natural_key
        indexes.append(IndexDefinition(
            name="idx_questions_natural_key",
            table="questions",
            columns="natural_key",
            unique=True,
            where_clause="natural_key IS NOT NULL",
            description="Garantiza unicidad de natural_key",
            priority=1
        ))
        
        # 4. Índice compuesto topic_id y subject_id para joins
        indexes.append(IndexDefinition(
            name="idx_questions_topic_subject",
            table="questions",
            columns="topic_id, subject_id", 
            description="Optimiza joins con topics y subjects",
            priority=1
        ))
        
        # === ÍNDICES DE PRIORIDAD MEDIA ===
        
        # 5. Índice en difficulty para filtros de dificultad
        indexes.append(IndexDefinition(
            name="idx_questions_difficulty",
            table="questions",
            columns="difficulty",
            description="Optimiza filtros por dificultad",
            priority=2
        ))
        
        # 6. Índice compuesto para respuesta correcta y dificultad
        indexes.append(IndexDefinition(
            name="idx_questions_answer_difficulty",
            table="questions",
            columns="respuesta_correcta, difficulty",
            description="Optimiza análisis de respuestas por dificultad",
            priority=2
        ))
        
        # 7. Índice en created_at para consultas temporales
        indexes.append(IndexDefinition(
            name="idx_questions_created_at",
            table="questions", 
            columns="created_at",
            description="Optimiza consultas por fecha de creación",
            priority=2
        ))
        
        # 8. Índice parcial en preguntas con explicación
        indexes.append(IndexDefinition(
            name="idx_questions_with_explanation",
            table="questions",
            columns="id, explanation",
            where_clause="explanation IS NOT NULL AND explanation != ''",
            description="Optimiza búsqueda de preguntas con explicación",
            priority=2
        ))
        
        # === ÍNDICES ESPECIALIZADOS PARA IMÁGENES ===
        
        # 9. Índice compuesto para todas las imágenes de opciones
        indexes.append(IndexDefinition(
            name="idx_questions_opciones_imagenes",
            table="questions",
            columns="opcion_a_imagen, opcion_b_imagen, opcion_c_imagen, opcion_d_imagen",
            where_clause="(opcion_a_imagen IS NOT NULL OR opcion_b_imagen IS NOT NULL OR opcion_c_imagen IS NOT NULL OR opcion_d_imagen IS NOT NULL)",
            description="Optimiza búsquedas de imágenes en opciones",
            priority=2
        ))
        
        # 10. Índice GIN para búsqueda full-text en pregunta_texto
        indexes.append(IndexDefinition(
            name="idx_questions_pregunta_texto_gin",
            table="questions",
            columns="to_tsvector('spanish', pregunta_texto)",
            index_type="gin",
            where_clause="pregunta_texto IS NOT NULL",
            description="Habilita búsqueda full-text en texto de pregunta",
            priority=2
        ))
        
        # === ÍNDICES DE BAJA PRIORIDAD (RENDIMIENTO) ===
        
        # 11. Índice en question_type para filtros de tipo
        indexes.append(IndexDefinition(
            name="idx_questions_type",
            table="questions",
            columns="question_type",
            description="Optimiza filtros por tipo de pregunta",
            priority=3
        ))
        
        # 12. Índice compuesto para power_stats
        indexes.append(IndexDefinition(
            name="idx_questions_power_stats",
            table="questions",
            columns="((power_stats->>'discrimination_index')::float), ((power_stats->>'success_rate')::float)",
            where_clause="power_stats IS NOT NULL",
            description="Optimiza consultas de estadísticas de rendimiento",
            priority=3
        ))
        
        # === ÍNDICES PARA TABLAS RELACIONADAS ===
        
        # 13. Índice en battle_answers.question_id
        indexes.append(IndexDefinition(
            name="idx_battle_answers_question_id",
            table="battle_answers",
            columns="question_id",
            description="Optimiza joins con preguntas en batallas",
            priority=2
        ))
        
        # 14. Índice compuesto en ai_explanations
        indexes.append(IndexDefinition(
            name="idx_ai_explanations_question_created",
            table="ai_explanations",
            columns="question_id, created_at",
            description="Optimiza búsqueda de explicaciones por pregunta",
            priority=3
        ))
        
        return indexes

    def check_existing_indexes(self) -> Dict[str, IndexStatus]:
        """Verificar qué índices ya existen"""
        logger.info("🔍 Verificando índices existentes...")
        existing_indexes = {}
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener información de índices existentes
                cursor.execute("""
                    SELECT 
                        i.indexname,
                        pg_size_pretty(pg_relation_size(i.indexname::regclass)) as size,
                        i.indexdef,
                        s.idx_scan,
                        s.idx_tup_read,
                        s.idx_tup_fetch,
                        t.n_tup_ins,
                        t.n_tup_upd,
                        t.n_tup_del
                    FROM pg_indexes i
                    LEFT JOIN pg_stat_user_indexes s ON i.indexname = s.indexname
                    LEFT JOIN pg_stat_user_tables t ON i.tablename = t.relname
                    WHERE i.schemaname = 'public'
                    ORDER BY i.tablename, i.indexname;
                """)
                
                for row in cursor.fetchall():
                    index_name = row[0]
                    existing_indexes[index_name] = IndexStatus(
                        name=index_name,
                        exists=True,
                        size=row[1],
                        usage_stats={
                            'scans': row[3] or 0,
                            'tuples_read': row[4] or 0,
                            'tuples_fetched': row[5] or 0,
                            'table_inserts': row[6] or 0,
                            'table_updates': row[7] or 0,
                            'table_deletes': row[8] or 0
                        }
                    )
                
                logger.info(f"✓ Encontrados {len(existing_indexes)} índices existentes")
                
        except Exception as e:
            logger.error(f"Error verificando índices existentes: {e}")
        
        return existing_indexes

    def analyze_query_performance(self) -> Dict[str, Any]:
        """Analizar rendimiento de consultas antes de optimización"""
        logger.info("📊 Analizando rendimiento de consultas...")
        performance_metrics = {}
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Test queries representativas
                test_queries = [
                    {
                        'name': 'busqueda_imagen_pregunta',
                        'query': "SELECT id FROM questions WHERE pregunta_imagen LIKE '/mathimg/%' LIMIT 10;",
                        'description': 'Búsqueda de preguntas con imagen'
                    },
                    {
                        'name': 'filtro_area_imagen',
                        'query': "SELECT COUNT(*) FROM questions WHERE area_evaluada = 'Matemáticas' AND requiere_imagen = true;",
                        'description': 'Filtro por área con imágenes'
                    },
                    {
                        'name': 'join_topic_subject',
                        'query': """SELECT q.id FROM questions q 
                                   JOIN topics t ON q.topic_id = t.id 
                                   JOIN subjects s ON q.subject_id = s.id LIMIT 10;""",
                        'description': 'Join con topics y subjects'
                    },
                    {
                        'name': 'filtro_dificultad',
                        'query': "SELECT COUNT(*) FROM questions WHERE difficulty BETWEEN 3 AND 7;",
                        'description': 'Filtro por rango de dificultad'
                    }
                ]
                
                for test in test_queries:
                    try:
                        # Ejecutar EXPLAIN ANALYZE
                        start_time = time.time()
                        cursor.execute(f"EXPLAIN ANALYZE {test['query']}")
                        execution_plan = cursor.fetchall()
                        end_time = time.time()
                        
                        # Extraer métricas del plan
                        execution_time = (end_time - start_time) * 1000  # ms
                        plan_text = '\n'.join([row[0] for row in execution_plan])
                        
                        performance_metrics[test['name']] = {
                            'description': test['description'],
                            'execution_time_ms': execution_time,
                            'execution_plan': plan_text,
                            'uses_index': 'Index Scan' in plan_text or 'Index Cond' in plan_text
                        }
                        
                    except Exception as e:
                        logger.warning(f"Error analizando query {test['name']}: {e}")
                        performance_metrics[test['name']] = {
                            'description': test['description'],
                            'error': str(e)
                        }
                
                logger.info(f"✓ {len(performance_metrics)} consultas analizadas")
                
        except Exception as e:
            logger.error(f"Error analizando rendimiento: {e}")
        
        return performance_metrics

    def create_indexes(self, priority_filter: int = 3) -> Tuple[int, int, int]:
        """Crear índices según prioridad"""
        logger.info(f"🔨 Creando índices con prioridad <= {priority_filter}...")
        
        created = 0
        existed = 0
        failed = 0
        
        # Verificar índices existentes
        existing_indexes = self.check_existing_indexes()
        
        # Filtrar índices por prioridad
        indexes_to_create = [idx for idx in self.index_definitions if idx.priority <= priority_filter]
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for index_def in indexes_to_create:
                    try:
                        # Verificar si el índice ya existe
                        if index_def.name in existing_indexes:
                            logger.info(f"⏭️ Índice ya existe: {index_def.name}")
                            existed += 1
                            continue
                        
                        # Construir comando CREATE INDEX
                        create_cmd = self._build_create_index_command(index_def)
                        
                        logger.info(f"🔨 Creando índice: {index_def.name}...")
                        logger.debug(f"SQL: {create_cmd}")
                        
                        start_time = time.time()
                        cursor.execute(create_cmd)
                        conn.commit()
                        end_time = time.time()
                        
                        creation_time = end_time - start_time
                        logger.info(f"✅ Índice creado exitosamente: {index_def.name} ({creation_time:.2f}s)")
                        created += 1
                        
                    except psycopg2.Error as e:
                        logger.error(f"❌ Error creando índice {index_def.name}: {e}")
                        conn.rollback()  # Rollback en caso de error
                        failed += 1
                    except Exception as e:
                        logger.error(f"❌ Error inesperado creando índice {index_def.name}: {e}")
                        conn.rollback()
                        failed += 1
                
        except Exception as e:
            logger.error(f"Error general creando índices: {e}")
        
        logger.info(f"✅ Creación de índices completada: {created} creados, {existed} existían, {failed} fallaron")
        return created, existed, failed

    def _build_create_index_command(self, index_def: IndexDefinition) -> str:
        """Construir comando CREATE INDEX"""
        cmd_parts = ["CREATE"]
        
        # Agregar UNIQUE si es necesario
        if index_def.unique:
            cmd_parts.append("UNIQUE")
        
        # Agregar INDEX
        cmd_parts.append("INDEX")
        
        # Agregar CONCURRENTLY si está habilitado
        if index_def.concurrent:
            cmd_parts.append("CONCURRENTLY")
        
        # Agregar IF NOT EXISTS
        cmd_parts.append("IF NOT EXISTS")
        
        # Nombre del índice
        cmd_parts.append(index_def.name)
        
        # Tabla
        cmd_parts.append(f"ON {index_def.table}")
        
        # Tipo de índice (si no es btree por defecto)
        if index_def.index_type != 'btree':
            cmd_parts.append(f"USING {index_def.index_type}")
        
        # Columnas
        cmd_parts.append(f"({index_def.columns})")
        
        # WHERE clause si existe
        if index_def.where_clause:
            cmd_parts.append(f"WHERE {index_def.where_clause}")
        
        return " ".join(cmd_parts) + ";"

    def update_table_statistics(self) -> bool:
        """Actualizar estadísticas de tabla para mejor planificación de consultas"""
        logger.info("📈 Actualizando estadísticas de tabla...")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Actualizar estadísticas de tabla principal
                cursor.execute("ANALYZE questions;")
                
                # Actualizar estadísticas de tablas relacionadas
                related_tables = ['topics', 'subjects', 'battle_answers', 'ai_explanations']
                
                for table in related_tables:
                    try:
                        cursor.execute(f"ANALYZE {table};")
                        logger.info(f"✓ Estadísticas actualizadas: {table}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error actualizando estadísticas de {table}: {e}")
                
                conn.commit()
                logger.info("✅ Estadísticas de tabla actualizadas")
                return True
                
        except Exception as e:
            logger.error(f"Error actualizando estadísticas: {e}")
            return False

    def vacuum_analyze_tables(self) -> bool:
        """Ejecutar VACUUM y ANALYZE en tablas principales"""
        logger.info("🧹 Ejecutando VACUUM ANALYZE...")
        
        try:
            # VACUUM requiere autocommit
            with self.get_connection() as conn:
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                cursor = conn.cursor()
                
                # VACUUM ANALYZE en tabla principal
                cursor.execute("VACUUM ANALYZE questions;")
                logger.info("✓ VACUUM ANALYZE completado: questions")
                
                # VACUUM en tablas relacionadas importantes
                related_tables = ['battle_answers', 'ai_explanations', 'quiz_answers']
                
                for table in related_tables:
                    try:
                        cursor.execute(f"VACUUM ANALYZE {table};")
                        logger.info(f"✓ VACUUM ANALYZE completado: {table}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error en VACUUM {table}: {e}")
                
                logger.info("✅ VACUUM ANALYZE completado")
                return True
                
        except Exception as e:
            logger.error(f"Error ejecutando VACUUM: {e}")
            return False

    def benchmark_after_optimization(self) -> Dict[str, Any]:
        """Hacer benchmark después de la optimización"""
        logger.info("🏁 Ejecutando benchmark post-optimización...")
        
        # Usar las mismas consultas que el análisis inicial
        return self.analyze_query_performance()

    def generate_optimization_report(self, 
                                   created: int, 
                                   existed: int, 
                                   failed: int,
                                   optimization_time: float,
                                   before_performance: Dict[str, Any],
                                   after_performance: Dict[str, Any]) -> OptimizationReport:
        """Generar reporte completo de optimización"""
        
        # Calcular mejoras de rendimiento
        performance_improvements = {}
        
        for query_name in before_performance:
            if query_name in after_performance:
                before_time = before_performance[query_name].get('execution_time_ms', 0)
                after_time = after_performance[query_name].get('execution_time_ms', 0)
                
                if before_time > 0 and after_time > 0:
                    improvement = ((before_time - after_time) / before_time) * 100
                    performance_improvements[query_name] = {
                        'before_ms': before_time,
                        'after_ms': after_time,
                        'improvement_percent': round(improvement, 2),
                        'uses_index_after': after_performance[query_name].get('uses_index', False)
                    }
        
        # Obtener estados finales de índices
        final_index_statuses = list(self.check_existing_indexes().values())
        
        return OptimizationReport(
            timestamp=datetime.now().isoformat(),
            database_name=self.db_config.get('database', 'unknown'),
            total_indexes_defined=len(self.index_definitions),
            indexes_created=created,
            indexes_existed=existed,
            indexes_failed=failed,
            optimization_time_seconds=optimization_time,
            index_definitions=self.index_definitions,
            index_statuses=final_index_statuses,
            performance_improvements=performance_improvements
        )

    def run_complete_optimization(self, priority_filter: int = 2) -> OptimizationReport:
        """Ejecutar optimización completa de índices"""
        logger.info("🚀 Iniciando optimización completa de índices...")
        start_time = datetime.now()
        
        try:
            # 1. Análisis inicial de rendimiento
            logger.info("📊 Analizando rendimiento inicial...")
            before_performance = self.analyze_query_performance()
            
            # 2. Actualizar estadísticas antes de crear índices
            self.update_table_statistics()
            
            # 3. Crear índices optimizados
            created, existed, failed = self.create_indexes(priority_filter)
            
            # 4. Ejecutar VACUUM ANALYZE después de crear índices
            self.vacuum_analyze_tables()
            
            # 5. Análisis final de rendimiento
            logger.info("📊 Analizando rendimiento post-optimización...")
            after_performance = self.benchmark_after_optimization()
            
            # 6. Calcular tiempo total
            end_time = datetime.now()
            optimization_time = (end_time - start_time).total_seconds()
            
            # 7. Generar reporte
            report = self.generate_optimization_report(
                created, existed, failed, optimization_time,
                before_performance, after_performance
            )
            
            logger.info(f"🎉 Optimización completada en {optimization_time:.2f}s")
            return report
            
        except Exception as e:
            logger.error(f"❌ Error durante optimización: {e}")
            
            # Reporte de error
            end_time = datetime.now()
            optimization_time = (end_time - start_time).total_seconds()
            
            return OptimizationReport(
                timestamp=start_time.isoformat(),
                database_name=self.db_config.get('database', 'unknown'),
                total_indexes_defined=len(self.index_definitions),
                indexes_created=0,
                indexes_existed=0,
                indexes_failed=len(self.index_definitions),
                optimization_time_seconds=optimization_time,
                index_definitions=self.index_definitions,
                index_statuses=[],
                performance_improvements={}
            )

    def save_report(self, report: OptimizationReport, output_path: str = None) -> str:
        """Guardar reporte de optimización"""
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"database/reports/index_optimization_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convertir a diccionario para JSON
        report_dict = asdict(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📋 Reporte de optimización guardado: {output_path}")
        return output_path


def main():
    """Función principal del optimizador de índices"""
    
    # Configuración de base de datos
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'gameplay_db'),
        'user': os.getenv('DB_USER', 'gameplay'),
        'password': os.getenv('DB_PASSWORD', 'gameplay123')
    }
    
    # Filtro de prioridad (1=alta, 2=media, 3=baja)
    priority_filter = int(os.getenv('INDEX_PRIORITY', '2'))
    
    logger.info("=== OPTIMIZADOR DE ÍNDICES ICFES LEVELING ===")
    logger.info(f"Prioridad máxima: {priority_filter} (1=alta, 2=media, 3=baja)")
    
    try:
        # Inicializar optimizador
        optimizer = DatabaseIndexOptimizer(db_config)
        
        # Ejecutar optimización completa
        report = optimizer.run_complete_optimization(priority_filter)
        
        # Guardar reporte
        report_path = optimizer.save_report(report)
        
        # Mostrar resumen
        print("\n" + "="*60)
        print("RESUMEN DE OPTIMIZACIÓN DE ÍNDICES")
        print("="*60)
        print(f"⏱️ Tiempo total: {report.optimization_time_seconds:.2f}s")
        print(f"📊 Índices definidos: {report.total_indexes_defined}")
        print(f"✅ Índices creados: {report.indexes_created}")
        print(f"⏭️ Índices existentes: {report.indexes_existed}")
        print(f"❌ Índices fallidos: {report.indexes_failed}")
        print(f"📋 Reporte guardado: {report_path}")
        
        # Mostrar mejoras de rendimiento
        if report.performance_improvements:
            print("\n🚀 MEJORAS DE RENDIMIENTO:")
            for query_name, improvement in report.performance_improvements.items():
                if improvement['improvement_percent'] > 0:
                    print(f"  • {query_name}: {improvement['improvement_percent']:.1f}% más rápido")
                    print(f"    {improvement['before_ms']:.2f}ms → {improvement['after_ms']:.2f}ms")
        
        print("="*60)
        
        # Código de salida basado en éxito
        return 0 if report.indexes_failed == 0 else 1
        
    except Exception as e:
        logger.error(f"❌ Error fatal en optimización: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)