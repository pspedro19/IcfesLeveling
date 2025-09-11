#!/usr/bin/env python3
"""
PASO 7: Script de Actualización Masiva de Base de Datos con Rutas Normalizadas
Actualiza la tabla questions con rutas físicas reales usando tabla de correspondencia.
"""

import os
import sys
import csv
import json
import logging
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import time
import redis
from contextlib import contextmanager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'mass_update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class UpdateRecord:
    """Registro de actualización de imagen"""
    question_id: str
    old_path: str
    new_path: str
    field_name: str
    file_exists: bool
    file_size: int
    confidence: float
    timestamp: str

@dataclass
class ValidationResult:
    """Resultado de validación"""
    success: bool
    total_records: int
    updated_records: int
    failed_records: int
    errors: List[str]
    warnings: List[str]

class DatabaseUpdateManager:
    """Manejador principal de actualizaciones de base de datos"""
    
    def __init__(self, db_config: Dict[str, Any], redis_config: Optional[Dict[str, Any]] = None):
        self.db_config = db_config
        self.redis_config = redis_config or {}
        self.redis_client = None
        self.backup_created = False
        self.update_records: List[UpdateRecord] = []
        
        # Configuración de actualizacion
        self.IMAGE_FIELDS = [
            'pregunta_imagen',
            'opcion_a_imagen', 
            'opcion_b_imagen',
            'opcion_c_imagen',
            'opcion_d_imagen'
        ]
        
        # Configurar Redis si está disponible
        if self.redis_config:
            try:
                self.redis_client = redis.Redis(**self.redis_config)
                self.redis_client.ping()
                logger.info("✓ Conexión Redis establecida")
            except Exception as e:
                logger.warning(f"⚠ Redis no disponible: {e}")
                self.redis_client = None

    @contextmanager
    def get_db_connection(self):
        """Context manager para conexiones de base de datos"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error de conexión DB: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def create_database_backup(self) -> bool:
        """Crear backup de la tabla questions antes de modificaciones"""
        try:
            backup_name = f"questions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Crear tabla de backup
                cursor.execute(f"""
                    CREATE TABLE {backup_name} AS 
                    SELECT * FROM questions;
                """)
                
                # Verificar backup
                cursor.execute(f"SELECT COUNT(*) FROM {backup_name}")
                backup_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM questions")
                original_count = cursor.fetchone()[0]
                
                if backup_count == original_count:
                    conn.commit()
                    self.backup_created = True
                    logger.info(f"✓ Backup creado: {backup_name} ({backup_count} registros)")
                    
                    # Guardar nombre del backup para rollback
                    with open('database/backups/latest_backup.txt', 'w') as f:
                        f.write(backup_name)
                    
                    return True
                else:
                    conn.rollback()
                    logger.error(f"Error: Backup inconsistente ({backup_count} vs {original_count})")
                    return False
                    
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return False

    def load_correspondence_table(self, csv_path: str) -> Dict[str, Dict[str, Any]]:
        """Cargar tabla de correspondencia desde CSV"""
        correspondence = {}
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    question_id = row.get('pregunta_id', '').strip()
                    if question_id:
                        correspondence[question_id] = {
                            'original_path': row.get('ruta_csv_original', '').strip(),
                            'physical_path': row.get('ruta_fisica_real', '').strip(),
                            'file_exists': row.get('archivo_existe', 'False').lower() == 'true',
                            'file_size': int(row.get('tamaño_bytes', '0')),
                            'is_placeholder': row.get('es_placeholder', 'False').lower() == 'true',
                            'confidence': float(row.get('confianza_mapeo', '0.0')),
                            'notes': row.get('observaciones', '')
                        }
            
            logger.info(f"✓ Tabla de correspondencia cargada: {len(correspondence)} registros")
            return correspondence
            
        except Exception as e:
            logger.error(f"Error cargando correspondencia: {e}")
            return {}

    def validate_database_structure(self) -> ValidationResult:
        """Validar estructura de base de datos antes de actualización"""
        errors = []
        warnings = []
        
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar existencia de tabla questions
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'questions'
                    );
                """)
                
                if not cursor.fetchone()[0]:
                    errors.append("Tabla 'questions' no existe")
                
                # Verificar campos de imagen
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'questions' 
                    AND column_name IN %s;
                """, (tuple(self.IMAGE_FIELDS),))
                
                existing_fields = [row[0] for row in cursor.fetchall()]
                missing_fields = set(self.IMAGE_FIELDS) - set(existing_fields)
                
                if missing_fields:
                    warnings.append(f"Campos faltantes: {missing_fields}")
                
                # Verificar foreign keys
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'questions' 
                    AND constraint_type = 'FOREIGN KEY';
                """)
                
                fk_count = cursor.fetchone()[0]
                logger.info(f"Foreign keys encontradas: {fk_count}")
                
                # Contar registros totales
                cursor.execute("SELECT COUNT(*) FROM questions")
                total_records = cursor.fetchone()[0]
                
                return ValidationResult(
                    success=len(errors) == 0,
                    total_records=total_records,
                    updated_records=0,
                    failed_records=0,
                    errors=errors,
                    warnings=warnings
                )
                
        except Exception as e:
            logger.error(f"Error en validación: {e}")
            return ValidationResult(
                success=False,
                total_records=0,
                updated_records=0,
                failed_records=0,
                errors=[str(e)],
                warnings=[]
            )

    def update_question_images(self, correspondence: Dict[str, Dict[str, Any]]) -> ValidationResult:
        """Actualizar imágenes de preguntas usando correspondencia"""
        updated_records = 0
        failed_records = 0
        errors = []
        warnings = []
        
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener todas las preguntas que necesitan actualización
                cursor.execute("""
                    SELECT id, pregunta_imagen, opcion_a_imagen, opcion_b_imagen, 
                           opcion_c_imagen, opcion_d_imagen
                    FROM questions 
                    WHERE pregunta_imagen IS NOT NULL 
                       OR opcion_a_imagen IS NOT NULL
                       OR opcion_b_imagen IS NOT NULL
                       OR opcion_c_imagen IS NOT NULL
                       OR opcion_d_imagen IS NOT NULL;
                """)
                
                questions = cursor.fetchall()
                logger.info(f"Procesando {len(questions)} preguntas con imágenes")
                
                for question_row in questions:
                    question_id = str(question_row[0])
                    current_images = {
                        'pregunta_imagen': question_row[1],
                        'opcion_a_imagen': question_row[2],
                        'opcion_b_imagen': question_row[3],
                        'opcion_c_imagen': question_row[4],
                        'opcion_d_imagen': question_row[5]
                    }
                    
                    # Preparar actualizaciones
                    updates = {}
                    updated_fields = []
                    
                    for field_name, current_path in current_images.items():
                        if current_path and current_path.strip():
                            # Buscar correspondencia
                            mapped_data = self._find_correspondence(current_path, correspondence)
                            
                            if mapped_data and mapped_data['physical_path']:
                                new_path = mapped_data['physical_path']
                                updates[field_name] = new_path
                                updated_fields.append(field_name)
                                
                                # Registrar actualización
                                self.update_records.append(UpdateRecord(
                                    question_id=question_id,
                                    old_path=current_path,
                                    new_path=new_path,
                                    field_name=field_name,
                                    file_exists=mapped_data['file_exists'],
                                    file_size=mapped_data['file_size'],
                                    confidence=mapped_data['confidence'],
                                    timestamp=datetime.now().isoformat()
                                ))
                    
                    # Actualizar pregunta si hay cambios
                    if updates:
                        try:
                            # Construir query dinámico
                            set_clauses = [f"{field} = %s" for field in updates.keys()]
                            update_query = f"""
                                UPDATE questions 
                                SET {', '.join(set_clauses)}
                                WHERE id = %s
                            """
                            
                            cursor.execute(update_query, list(updates.values()) + [question_id])
                            updated_records += 1
                            
                            if updated_records % 100 == 0:
                                logger.info(f"Actualizadas {updated_records} preguntas...")
                            
                        except Exception as e:
                            failed_records += 1
                            error_msg = f"Error actualizando pregunta {question_id}: {e}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                
                # Commit todas las actualizaciones
                conn.commit()
                logger.info(f"✓ Actualizaciones completadas: {updated_records} exitosas, {failed_records} fallidas")
                
                return ValidationResult(
                    success=failed_records == 0,
                    total_records=len(questions),
                    updated_records=updated_records,
                    failed_records=failed_records,
                    errors=errors,
                    warnings=warnings
                )
                
        except Exception as e:
            logger.error(f"Error en actualización masiva: {e}")
            return ValidationResult(
                success=False,
                total_records=0,
                updated_records=0,
                failed_records=1,
                errors=[str(e)],
                warnings=[]
            )

    def _find_correspondence(self, current_path: str, correspondence: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Encontrar correspondencia para una ruta específica"""
        # Normalizar ruta actual
        normalized_path = current_path.strip().replace('\\', '/')
        
        # Buscar por coincidencia exacta en rutas originales
        for question_id, data in correspondence.items():
            if data['original_path'] == normalized_path:
                return data
        
        # Buscar por nombre de archivo
        current_filename = Path(normalized_path).name
        for question_id, data in correspondence.items():
            correspondence_filename = Path(data['original_path']).name
            if current_filename == correspondence_filename:
                return data
        
        return None

    def update_requiere_imagen_field(self) -> int:
        """Actualizar campo Requiere_Imagen basado en existencia real de archivos"""
        updated_count = 0
        
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Actualizar Requiere_Imagen = true donde hay imágenes válidas
                cursor.execute("""
                    UPDATE questions 
                    SET requiere_imagen = true
                    WHERE (pregunta_imagen IS NOT NULL AND pregunta_imagen != '')
                       OR (opcion_a_imagen IS NOT NULL AND opcion_a_imagen != '')
                       OR (opcion_b_imagen IS NOT NULL AND opcion_b_imagen != '')
                       OR (opcion_c_imagen IS NOT NULL AND opcion_c_imagen != '')
                       OR (opcion_d_imagen IS NOT NULL AND opcion_d_imagen != '');
                """)
                
                updated_count += cursor.rowcount
                
                # Actualizar Requiere_Imagen = false donde no hay imágenes
                cursor.execute("""
                    UPDATE questions 
                    SET requiere_imagen = false
                    WHERE (pregunta_imagen IS NULL OR pregunta_imagen = '')
                      AND (opcion_a_imagen IS NULL OR opcion_a_imagen = '')
                      AND (opcion_b_imagen IS NULL OR opcion_b_imagen = '')
                      AND (opcion_c_imagen IS NULL OR opcion_c_imagen = '')
                      AND (opcion_d_imagen IS NULL OR opcion_d_imagen = '');
                """)
                
                updated_count += cursor.rowcount
                conn.commit()
                
                logger.info(f"✓ Campo 'requiere_imagen' actualizado en {updated_count} registros")
                
        except Exception as e:
            logger.error(f"Error actualizando requiere_imagen: {e}")
        
        return updated_count

    def verify_referential_integrity(self) -> ValidationResult:
        """Verificar integridad referencial después de actualizaciones"""
        errors = []
        warnings = []
        
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar foreign keys de topics
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM questions q 
                    LEFT JOIN topics t ON q.topic_id = t.id 
                    WHERE q.topic_id IS NOT NULL AND t.id IS NULL;
                """)
                
                orphaned_topics = cursor.fetchone()[0]
                if orphaned_topics > 0:
                    errors.append(f"{orphaned_topics} preguntas con topic_id inválido")
                
                # Verificar foreign keys de subjects
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM questions q 
                    LEFT JOIN subjects s ON q.subject_id = s.id 
                    WHERE q.subject_id IS NOT NULL AND s.id IS NULL;
                """)
                
                orphaned_subjects = cursor.fetchone()[0]
                if orphaned_subjects > 0:
                    errors.append(f"{orphaned_subjects} preguntas con subject_id inválido")
                
                # Verificar unicidad de natural_key si existe
                cursor.execute("""
                    SELECT COUNT(*), COUNT(DISTINCT natural_key) 
                    FROM questions 
                    WHERE natural_key IS NOT NULL;
                """)
                
                result = cursor.fetchone()
                if result[0] != result[1]:
                    warnings.append("Duplicados encontrados en natural_key")
                
                # Contar registros totales después de actualización
                cursor.execute("SELECT COUNT(*) FROM questions")
                total_records = cursor.fetchone()[0]
                
                return ValidationResult(
                    success=len(errors) == 0,
                    total_records=total_records,
                    updated_records=0,
                    failed_records=0,
                    errors=errors,
                    warnings=warnings
                )
                
        except Exception as e:
            logger.error(f"Error en verificación de integridad: {e}")
            return ValidationResult(
                success=False,
                total_records=0,
                updated_records=0,
                failed_records=0,
                errors=[str(e)],
                warnings=[]
            )

    def create_optimized_indexes(self) -> bool:
        """Crear índices optimizados para búsquedas de imágenes"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                indexes_to_create = [
                    # Índice en imagen de pregunta para búsquedas rápidas
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_pregunta_imagen 
                       ON questions(pregunta_imagen) WHERE pregunta_imagen IS NOT NULL;""",
                    
                    # Índice compuesto para búsquedas por área y requerimiento de imagen
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_area_imagen 
                       ON questions(area_evaluada, requiere_imagen) 
                       WHERE requiere_imagen = true;""",
                    
                    # Índice en natural_key si existe
                    """CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_natural_key 
                       ON questions(natural_key) WHERE natural_key IS NOT NULL;""",
                    
                    # Índice para búsquedas de dificultad
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_difficulty 
                       ON questions(difficulty);""",
                    
                    # Índice compuesto para topic_id y subject_id
                    """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_topic_subject 
                       ON questions(topic_id, subject_id);"""
                ]
                
                created_indexes = 0
                for index_sql in indexes_to_create:
                    try:
                        cursor.execute(index_sql)
                        created_indexes += 1
                        conn.commit()
                        logger.info(f"✓ Índice creado: {index_sql.split('idx_')[1].split(' ')[0]}")
                    except Exception as e:
                        logger.warning(f"⚠ Error creando índice: {e}")
                        conn.rollback()
                
                logger.info(f"✓ {created_indexes}/{len(indexes_to_create)} índices creados exitosamente")
                return created_indexes > 0
                
        except Exception as e:
            logger.error(f"Error creando índices: {e}")
            return False

    def invalidate_cache(self) -> bool:
        """Invalidar cache Redis después de actualizaciones masivas"""
        if not self.redis_client:
            logger.info("Redis no disponible - saltando invalidación de cache")
            return True
        
        try:
            # Patrones de keys a invalidar
            patterns = [
                'img:*',  # Cache de imágenes
                'question:*',  # Cache de preguntas
                'media:*',  # Cache de media
                'questions_by_*'  # Queries cacheadas
            ]
            
            invalidated_keys = 0
            for pattern in patterns:
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis_client.delete(*keys)
                    invalidated_keys += deleted
                    logger.info(f"✓ Cache invalidado: {pattern} ({deleted} keys)")
            
            # Marcar timestamp de última invalidación
            self.redis_client.set('cache_invalidated_at', datetime.now().isoformat())
            
            logger.info(f"✓ Total de keys invalidadas: {invalidated_keys}")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidando cache: {e}")
            return False

    def preload_important_images(self) -> int:
        """Pre-cargar imágenes más importantes en cache"""
        if not self.redis_client:
            return 0
        
        preloaded_count = 0
        
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Seleccionar preguntas más importantes (por difficulty y usage)
                cursor.execute("""
                    SELECT id, pregunta_imagen, opcion_a_imagen, opcion_b_imagen, 
                           opcion_c_imagen, opcion_d_imagen, difficulty
                    FROM questions 
                    WHERE requiere_imagen = true 
                    ORDER BY difficulty ASC, created_at DESC 
                    LIMIT 50;
                """)
                
                important_questions = cursor.fetchall()
                
                for question in important_questions:
                    question_id = question[0]
                    images = question[1:6]  # Image fields
                    
                    for i, image_path in enumerate(images):
                        if image_path and image_path.strip():
                            try:
                                # Marcar imagen como importante en cache
                                cache_key = f"img:priority:{question_id}:{i}"
                                self.redis_client.set(
                                    cache_key, 
                                    json.dumps({
                                        'path': image_path,
                                        'preloaded_at': datetime.now().isoformat(),
                                        'priority': 'high'
                                    }),
                                    ex=3600  # 1 hour TTL
                                )
                                preloaded_count += 1
                            except Exception as e:
                                logger.warning(f"Error pre-cargando imagen {image_path}: {e}")
                
                logger.info(f"✓ {preloaded_count} imágenes importantes pre-cargadas")
                
        except Exception as e:
            logger.error(f"Error en pre-carga: {e}")
        
        return preloaded_count

    def generate_update_report(self) -> Dict[str, Any]:
        """Generar reporte completo de actualización"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'backup_created': self.backup_created,
            'total_update_records': len(self.update_records),
            'successful_updates': sum(1 for r in self.update_records if r.confidence > 0.5),
            'low_confidence_updates': sum(1 for r in self.update_records if r.confidence <= 0.5),
            'files_existing': sum(1 for r in self.update_records if r.file_exists),
            'files_missing': sum(1 for r in self.update_records if not r.file_exists),
            'update_records': [asdict(record) for record in self.update_records[-10:]]  # Últimos 10
        }
        
        # Guardar reporte
        report_path = f"database/reports/update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Reporte generado: {report_path}")
        return report

    def create_rollback_script(self) -> bool:
        """Crear script de rollback en caso de errores"""
        if not self.backup_created:
            logger.warning("No se puede crear rollback - backup no disponible")
            return False
        
        try:
            # Leer nombre del backup
            with open('database/backups/latest_backup.txt', 'r') as f:
                backup_table = f.read().strip()
            
            rollback_script = f"""-- SCRIPT DE ROLLBACK AUTOMÁTICO
-- Generado: {datetime.now().isoformat()}
-- Backup table: {backup_table}

BEGIN;

-- Restaurar datos desde backup
DELETE FROM questions;
INSERT INTO questions SELECT * FROM {backup_table};

-- Verificar restauración
DO $$
DECLARE
    original_count INTEGER;
    restored_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO original_count FROM {backup_table};
    SELECT COUNT(*) INTO restored_count FROM questions;
    
    IF original_count != restored_count THEN
        RAISE EXCEPTION 'Rollback falló: % vs % registros', original_count, restored_count;
    END IF;
    
    RAISE NOTICE 'Rollback exitoso: % registros restaurados', restored_count;
END $$;

COMMIT;

-- Eliminar tabla de backup después de rollback exitoso
-- DROP TABLE {backup_table};
"""
            
            rollback_path = f"database/scripts/rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            with open(rollback_path, 'w', encoding='utf-8') as f:
                f.write(rollback_script)
            
            logger.info(f"✓ Script de rollback creado: {rollback_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando rollback script: {e}")
            return False


def main():
    """Función principal de actualización masiva"""
    
    # Configuración de base de datos
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'gameplay_db'),
        'user': os.getenv('DB_USER', 'gameplay'),
        'password': os.getenv('DB_PASSWORD', 'gameplay123')
    }
    
    # Configuración de Redis
    redis_config = {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', '6379')),
        'db': int(os.getenv('REDIS_DB', '0')),
        'decode_responses': True
    }
    
    # Ruta de la tabla de correspondencia
    correspondence_path = os.getenv(
        'CORRESPONDENCE_TABLE', 
        r'C:\Users\PEDRO_PEREZ\tabla_correspondencia_imagenes.csv'
    )
    
    logger.info("=== INICIO DE ACTUALIZACIÓN MASIVA DE BASE DE DATOS ===")
    logger.info(f"Tabla de correspondencia: {correspondence_path}")
    
    # Inicializar manejador
    update_manager = DatabaseUpdateManager(db_config, redis_config)
    
    try:
        # PASO 1: Validar estructura de base de datos
        logger.info("🔍 Validando estructura de base de datos...")
        validation = update_manager.validate_database_structure()
        if not validation.success:
            logger.error(f"❌ Validación fallida: {validation.errors}")
            return False
        
        logger.info(f"✓ Base de datos válida ({validation.total_records} registros)")
        
        # PASO 2: Crear backup
        logger.info("💾 Creando backup de seguridad...")
        if not update_manager.create_database_backup():
            logger.error("❌ Error creando backup - abortando actualización")
            return False
        
        # PASO 3: Cargar tabla de correspondencia
        logger.info("📋 Cargando tabla de correspondencia...")
        correspondence = update_manager.load_correspondence_table(correspondence_path)
        if not correspondence:
            logger.error("❌ Error cargando correspondencia - abortando")
            return False
        
        # PASO 4: Actualizar imágenes de preguntas
        logger.info("🔄 Ejecutando actualización masiva...")
        update_result = update_manager.update_question_images(correspondence)
        
        if update_result.failed_records > 0:
            logger.warning(f"⚠ {update_result.failed_records} actualizaciones fallaron")
        
        # PASO 5: Actualizar campo Requiere_Imagen
        logger.info("🖼️ Actualizando campo requiere_imagen...")
        updated_requiere_imagen = update_manager.update_requiere_imagen_field()
        
        # PASO 6: Verificar integridad referencial
        logger.info("🔗 Verificando integridad referencial...")
        integrity_check = update_manager.verify_referential_integrity()
        
        if not integrity_check.success:
            logger.error(f"❌ Problemas de integridad: {integrity_check.errors}")
            logger.warning("Considere ejecutar rollback si es necesario")
        
        # PASO 7: Crear índices optimizados
        logger.info("📊 Creando índices optimizados...")
        indexes_created = update_manager.create_optimized_indexes()
        
        # PASO 8: Invalidar cache
        logger.info("🧹 Invalidando cache...")
        cache_invalidated = update_manager.invalidate_cache()
        
        # PASO 9: Pre-cargar imágenes importantes
        logger.info("⚡ Pre-cargando imágenes importantes...")
        preloaded_count = update_manager.preload_important_images()
        
        # PASO 10: Crear script de rollback
        logger.info("🔙 Creando script de rollback...")
        rollback_created = update_manager.create_rollback_script()
        
        # PASO 11: Generar reporte final
        logger.info("📊 Generando reporte final...")
        final_report = update_manager.generate_update_report()
        
        # Resumen final
        logger.info("=== RESUMEN DE ACTUALIZACIÓN ===")
        logger.info(f"✓ Registros actualizados: {update_result.updated_records}")
        logger.info(f"✓ Registros fallidos: {update_result.failed_records}")
        logger.info(f"✓ Campo requiere_imagen: {updated_requiere_imagen} actualizaciones")
        logger.info(f"✓ Índices creados: {indexes_created}")
        logger.info(f"✓ Cache invalidado: {cache_invalidated}")
        logger.info(f"✓ Imágenes pre-cargadas: {preloaded_count}")
        logger.info(f"✓ Script de rollback: {rollback_created}")
        
        if update_result.success and integrity_check.success:
            logger.info("🎉 ACTUALIZACIÓN MASIVA COMPLETADA EXITOSAMENTE")
            return True
        else:
            logger.warning("⚠ ACTUALIZACIÓN COMPLETADA CON ADVERTENCIAS")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR CRÍTICO: {e}")
        logger.error("Considere ejecutar rollback para restaurar estado anterior")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)