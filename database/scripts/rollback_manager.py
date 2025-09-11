#!/usr/bin/env python3
"""
Sistema de Validación y Rollback para Actualizaciones Masivas
Maneja backups, validaciones y rollback automático en caso de errores.
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
import shutil
import zipfile
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BackupInfo:
    """Información de un backup"""
    name: str
    table_name: str
    creation_time: str
    record_count: int
    size_bytes: int
    backup_type: str  # 'full', 'incremental', 'schema_only'
    status: str  # 'active', 'expired', 'corrupted'
    metadata: Dict[str, Any]

@dataclass
class ValidationRule:
    """Regla de validación"""
    name: str
    description: str
    sql_check: str
    severity: str  # 'critical', 'warning', 'info'
    expected_result: Any
    tolerance: Optional[float] = None

@dataclass
class RollbackPlan:
    """Plan de rollback"""
    backup_name: str
    target_table: str
    estimated_time_minutes: int
    steps: List[str]
    validation_checks: List[str]
    risk_level: str  # 'low', 'medium', 'high'

class DatabaseRollbackManager:
    """Manejador de validación y rollback de base de datos"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.backup_dir = "database/backups"
        self.validation_rules = self._define_validation_rules()
        
        # Crear directorio de backups
        os.makedirs(self.backup_dir, exist_ok=True)

    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return psycopg2.connect(**self.db_config)

    def _define_validation_rules(self) -> List[ValidationRule]:
        """Definir reglas de validación post-actualización"""
        rules = []
        
        # === REGLAS CRÍTICAS ===
        
        # 1. Validar integridad referencial
        rules.append(ValidationRule(
            name="foreign_key_integrity",
            description="Verificar que no hay foreign keys rotas",
            sql_check="""
                SELECT COUNT(*) FROM questions q 
                LEFT JOIN topics t ON q.topic_id = t.id 
                WHERE q.topic_id IS NOT NULL AND t.id IS NULL;
            """,
            severity="critical",
            expected_result=0
        ))
        
        # 2. Validar count total de registros
        rules.append(ValidationRule(
            name="record_count_stability",
            description="Verificar que el número de registros no cambió drásticamente",
            sql_check="SELECT COUNT(*) FROM questions;",
            severity="critical",
            expected_result=None,  # Se define dinámicamente
            tolerance=0.05  # 5% tolerancia
        ))
        
        # 3. Validar respuestas correctas válidas
        rules.append(ValidationRule(
            name="valid_correct_answers",
            description="Verificar respuestas_correcta válidas",
            sql_check="""
                SELECT COUNT(*) FROM questions 
                WHERE respuesta_correcta NOT IN ('a', 'b', 'c', 'd', 'A', 'B', 'C', 'D')
                AND respuesta_correcta IS NOT NULL;
            """,
            severity="critical",
            expected_result=0
        ))
        
        # === REGLAS DE ADVERTENCIA ===
        
        # 4. Validar consistencia de requiere_imagen
        rules.append(ValidationRule(
            name="requiere_imagen_consistency",
            description="Verificar consistencia del campo requiere_imagen",
            sql_check="""
                SELECT COUNT(*) FROM questions 
                WHERE requiere_imagen = true 
                AND (pregunta_imagen IS NULL OR pregunta_imagen = '')
                AND (opcion_a_imagen IS NULL OR opcion_a_imagen = '')
                AND (opcion_b_imagen IS NULL OR opcion_b_imagen = '')
                AND (opcion_c_imagen IS NULL OR opcion_c_imagen = '')
                AND (opcion_d_imagen IS NULL OR opcion_d_imagen = '');
            """,
            severity="warning",
            expected_result=0,
            tolerance=0.1  # 10% tolerancia para advertencias
        ))
        
        # 5. Validar paths de imagen válidos
        rules.append(ValidationRule(
            name="valid_image_paths",
            description="Verificar que las rutas de imagen son válidas",
            sql_check="""
                SELECT COUNT(*) FROM questions 
                WHERE (pregunta_imagen LIKE '%<%' OR pregunta_imagen LIKE '%>%')
                OR (opcion_a_imagen LIKE '%<%' OR opcion_a_imagen LIKE '%>%')
                OR (opcion_b_imagen LIKE '%<%' OR opcion_b_imagen LIKE '%>%')
                OR (opcion_c_imagen LIKE '%<%' OR opcion_c_imagen LIKE '%>%')
                OR (opcion_d_imagen LIKE '%<%' OR opcion_d_imagen LIKE '%>%');
            """,
            severity="warning",
            expected_result=0
        ))
        
        # === REGLAS INFORMATIVAS ===
        
        # 6. Contar preguntas con imágenes
        rules.append(ValidationRule(
            name="questions_with_images",
            description="Contar preguntas que tienen imágenes",
            sql_check="""
                SELECT COUNT(*) FROM questions 
                WHERE requiere_imagen = true;
            """,
            severity="info",
            expected_result=None
        ))
        
        return rules

    def create_backup(self, table_name: str, backup_type: str = 'full') -> Optional[BackupInfo]:
        """Crear backup de tabla"""
        logger.info(f"💾 Creando backup {backup_type} de tabla {table_name}...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{table_name}_backup_{timestamp}"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Crear tabla de backup
                if backup_type == 'full':
                    cursor.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name};")
                elif backup_type == 'schema_only':
                    cursor.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name} WHERE false;")
                
                # Obtener información del backup
                cursor.execute(f"SELECT COUNT(*) FROM {backup_name};")
                record_count = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT pg_total_relation_size('{backup_name}');")
                size_bytes = cursor.fetchone()[0]
                
                conn.commit()
                
                # Crear info de backup
                backup_info = BackupInfo(
                    name=backup_name,
                    table_name=table_name,
                    creation_time=datetime.now().isoformat(),
                    record_count=record_count,
                    size_bytes=size_bytes,
                    backup_type=backup_type,
                    status='active',
                    metadata={
                        'database': self.db_config.get('database'),
                        'user': self.db_config.get('user')
                    }
                )
                
                # Guardar metadata del backup
                self._save_backup_metadata(backup_info)
                
                logger.info(f"✅ Backup creado: {backup_name} ({record_count} registros, {size_bytes} bytes)")
                return backup_info
                
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
            return None

    def _save_backup_metadata(self, backup_info: BackupInfo):
        """Guardar metadata de backup"""
        metadata_file = Path(self.backup_dir) / f"{backup_info.name}_metadata.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(backup_info), f, indent=2, ensure_ascii=False, default=str)

    def load_backup_metadata(self, backup_name: str) -> Optional[BackupInfo]:
        """Cargar metadata de backup"""
        metadata_file = Path(self.backup_dir) / f"{backup_name}_metadata.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return BackupInfo(**data)
        except Exception as e:
            logger.error(f"Error cargando metadata de backup {backup_name}: {e}")
            return None

    def list_available_backups(self, table_name: str = None) -> List[BackupInfo]:
        """Listar backups disponibles"""
        backups = []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Buscar tablas de backup en la base de datos
                cursor.execute("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename LIKE '%_backup_%'
                    ORDER BY tablename DESC;
                """)
                
                backup_tables = cursor.fetchall()
                
                for (backup_name,) in backup_tables:
                    # Filtrar por tabla si se especifica
                    if table_name and not backup_name.startswith(f"{table_name}_backup_"):
                        continue
                    
                    # Cargar metadata si existe
                    backup_info = self.load_backup_metadata(backup_name)
                    if backup_info:
                        backups.append(backup_info)
                    else:
                        # Crear metadata básica si no existe
                        cursor.execute(f"SELECT COUNT(*) FROM {backup_name};")
                        record_count = cursor.fetchone()[0]
                        
                        # Intentar extraer información del nombre
                        parts = backup_name.split('_')
                        original_table = parts[0] if parts else 'unknown'
                        
                        backup_info = BackupInfo(
                            name=backup_name,
                            table_name=original_table,
                            creation_time=datetime.now().isoformat(),  # Aproximado
                            record_count=record_count,
                            size_bytes=0,
                            backup_type='unknown',
                            status='active',
                            metadata={}
                        )
                        backups.append(backup_info)
                
        except Exception as e:
            logger.error(f"Error listando backups: {e}")
        
        return backups

    def validate_post_update(self, baseline_values: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[Dict[str, Any]]]:
        """Ejecutar validaciones post-actualización"""
        logger.info("🔍 Ejecutando validaciones post-actualización...")
        
        validation_results = []
        all_passed = True
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for rule in self.validation_rules:
                    try:
                        logger.debug(f"Ejecutando validación: {rule.name}")
                        cursor.execute(rule.sql_check)
                        actual_result = cursor.fetchone()[0]
                        
                        # Determinar si la validación pasó
                        passed = True
                        message = ""
                        
                        if rule.expected_result is not None:
                            if rule.tolerance is not None:
                                # Validación con tolerancia
                                if isinstance(actual_result, (int, float)) and isinstance(rule.expected_result, (int, float)):
                                    diff_percent = abs(actual_result - rule.expected_result) / max(rule.expected_result, 1)
                                    passed = diff_percent <= rule.tolerance
                                    message = f"Diferencia: {diff_percent:.2%} (tolerancia: {rule.tolerance:.2%})"
                                else:
                                    passed = actual_result == rule.expected_result
                            else:
                                # Validación exacta
                                passed = actual_result == rule.expected_result
                        
                        # Usar baseline si está disponible
                        elif baseline_values and rule.name in baseline_values:
                            baseline_value = baseline_values[rule.name]
                            if rule.tolerance:
                                diff_percent = abs(actual_result - baseline_value) / max(baseline_value, 1)
                                passed = diff_percent <= rule.tolerance
                                message = f"Baseline: {baseline_value}, Actual: {actual_result}, Diff: {diff_percent:.2%}"
                            else:
                                passed = actual_result == baseline_value
                                message = f"Baseline: {baseline_value}, Actual: {actual_result}"
                        
                        # Registrar resultado
                        result = {
                            'rule_name': rule.name,
                            'description': rule.description,
                            'severity': rule.severity,
                            'expected': rule.expected_result or baseline_values.get(rule.name) if baseline_values else None,
                            'actual': actual_result,
                            'passed': passed,
                            'message': message
                        }
                        
                        validation_results.append(result)
                        
                        # Determinar si el resultado afecta el éxito general
                        if not passed and rule.severity == 'critical':
                            all_passed = False
                            logger.error(f"❌ Validación crítica falló: {rule.name} - {message}")
                        elif not passed and rule.severity == 'warning':
                            logger.warning(f"⚠️ Validación con advertencia: {rule.name} - {message}")
                        else:
                            logger.info(f"✅ Validación pasó: {rule.name}")
                    
                    except Exception as e:
                        logger.error(f"❌ Error ejecutando validación {rule.name}: {e}")
                        validation_results.append({
                            'rule_name': rule.name,
                            'description': rule.description,
                            'severity': rule.severity,
                            'expected': rule.expected_result,
                            'actual': None,
                            'passed': False,
                            'message': f"Error de ejecución: {str(e)}"
                        })
                        if rule.severity == 'critical':
                            all_passed = False
                
                logger.info(f"✅ Validaciones completadas: {len(validation_results)} ejecutadas")
                
        except Exception as e:
            logger.error(f"❌ Error general en validación: {e}")
            all_passed = False
        
        return all_passed, validation_results

    def create_rollback_plan(self, backup_name: str, target_table: str) -> RollbackPlan:
        """Crear plan de rollback"""
        logger.info(f"📋 Creando plan de rollback para {target_table} desde {backup_name}...")
        
        # Calcular tiempo estimado basado en tamaño
        backup_info = self.load_backup_metadata(backup_name)
        estimated_minutes = max(1, (backup_info.record_count // 10000) if backup_info else 5)
        
        # Definir pasos del rollback
        steps = [
            f"1. Verificar existencia de backup {backup_name}",
            f"2. Crear backup de seguridad de {target_table} actual",
            f"3. Truncar tabla {target_table}",
            f"4. Insertar datos desde {backup_name}",
            f"5. Verificar integridad de datos restaurados",
            f"6. Actualizar estadísticas de tabla",
            f"7. Ejecutar validaciones post-rollback"
        ]
        
        # Definir validaciones
        validation_checks = [
            f"COUNT(*) de {target_table} == COUNT(*) de {backup_name}",
            "Verificar foreign keys intactas",
            "Verificar constraints de tabla",
            "Verificar índices funcionales"
        ]
        
        # Determinar nivel de riesgo
        risk_level = "low"
        if backup_info and backup_info.record_count > 100000:
            risk_level = "medium"
        if backup_info and backup_info.record_count > 1000000:
            risk_level = "high"
        
        return RollbackPlan(
            backup_name=backup_name,
            target_table=target_table,
            estimated_time_minutes=estimated_minutes,
            steps=steps,
            validation_checks=validation_checks,
            risk_level=risk_level
        )

    def execute_rollback(self, rollback_plan: RollbackPlan, force: bool = False) -> bool:
        """Ejecutar rollback según el plan"""
        if not force and rollback_plan.risk_level == 'high':
            logger.warning("⚠️ Rollback de alto riesgo detectado. Use force=True para continuar.")
            return False
        
        logger.info(f"🔄 Ejecutando rollback: {rollback_plan.target_table} ← {rollback_plan.backup_name}")
        logger.info(f"⏱️ Tiempo estimado: {rollback_plan.estimated_time_minutes} minutos")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Paso 1: Verificar backup existe
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{rollback_plan.backup_name}'
                    );
                """)
                
                if not cursor.fetchone()[0]:
                    logger.error(f"❌ Backup {rollback_plan.backup_name} no existe")
                    return False
                
                # Paso 2: Crear backup de seguridad de tabla actual
                safety_backup = self.create_backup(rollback_plan.target_table, 'full')
                if not safety_backup:
                    logger.error("❌ No se pudo crear backup de seguridad")
                    return False
                
                logger.info(f"✅ Backup de seguridad creado: {safety_backup.name}")
                
                # Paso 3: Obtener count de backup para validación
                cursor.execute(f"SELECT COUNT(*) FROM {rollback_plan.backup_name};")
                backup_count = cursor.fetchone()[0]
                
                # Paso 4: Ejecutar rollback
                logger.info(f"🔄 Restaurando {backup_count} registros...")
                
                # Truncar tabla actual
                cursor.execute(f"TRUNCATE TABLE {rollback_plan.target_table} RESTART IDENTITY CASCADE;")
                
                # Insertar datos desde backup
                cursor.execute(f"""
                    INSERT INTO {rollback_plan.target_table} 
                    SELECT * FROM {rollback_plan.backup_name};
                """)
                
                # Paso 5: Verificar restauración
                cursor.execute(f"SELECT COUNT(*) FROM {rollback_plan.target_table};")
                restored_count = cursor.fetchone()[0]
                
                if restored_count != backup_count:
                    logger.error(f"❌ Error en restauración: {restored_count} vs {backup_count} registros")
                    conn.rollback()
                    return False
                
                # Paso 6: Actualizar estadísticas
                cursor.execute(f"ANALYZE {rollback_plan.target_table};")
                
                # Commit todas las operaciones
                conn.commit()
                
                logger.info(f"✅ Rollback completado exitosamente: {restored_count} registros restaurados")
                
                # Paso 7: Ejecutar validaciones post-rollback
                passed, validation_results = self.validate_post_update()
                
                if not passed:
                    logger.error("❌ Validaciones post-rollback fallaron")
                    # Aquí podrías decidir hacer otro rollback al safety_backup
                    return False
                
                logger.info("✅ Validaciones post-rollback exitosas")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando rollback: {e}")
            return False

    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """Limpiar backups antiguos"""
        logger.info(f"🧹 Limpiando backups con más de {retention_days} días...")
        
        cleaned_count = 0
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        try:
            backups = self.list_available_backups()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for backup in backups:
                    try:
                        creation_date = datetime.fromisoformat(backup.creation_time.replace('Z', '+00:00'))
                        
                        if creation_date < cutoff_date:
                            logger.info(f"🗑️ Eliminando backup antiguo: {backup.name}")
                            
                            # Eliminar tabla de backup
                            cursor.execute(f"DROP TABLE IF EXISTS {backup.name};")
                            
                            # Eliminar metadata
                            metadata_file = Path(self.backup_dir) / f"{backup.name}_metadata.json"
                            if metadata_file.exists():
                                metadata_file.unlink()
                            
                            cleaned_count += 1
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error limpiando backup {backup.name}: {e}")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Error general limpiando backups: {e}")
        
        logger.info(f"✅ {cleaned_count} backups antiguos eliminados")
        return cleaned_count

    def generate_validation_baseline(self) -> Dict[str, Any]:
        """Generar valores baseline para validaciones futuras"""
        logger.info("📊 Generando baseline de validación...")
        
        baseline = {}
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for rule in self.validation_rules:
                    if rule.severity == 'info' or rule.expected_result is None:
                        try:
                            cursor.execute(rule.sql_check)
                            baseline[rule.name] = cursor.fetchone()[0]
                        except Exception as e:
                            logger.warning(f"⚠️ Error obteniendo baseline para {rule.name}: {e}")
                
            # Guardar baseline
            baseline_file = Path(self.backup_dir) / f"validation_baseline_{datetime.now().strftime('%Y%m%d')}.json"
            with open(baseline_file, 'w', encoding='utf-8') as f:
                json.dump(baseline, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"✅ Baseline guardado: {baseline_file}")
            
        except Exception as e:
            logger.error(f"❌ Error generando baseline: {e}")
        
        return baseline


def main():
    """Función principal del manejador de rollback"""
    
    # Configuración de base de datos
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'gameplay_db'),
        'user': os.getenv('DB_USER', 'gameplay'),
        'password': os.getenv('DB_PASSWORD', 'gameplay123')
    }
    
    action = sys.argv[1] if len(sys.argv) > 1 else 'validate'
    
    logger.info("=== SISTEMA DE VALIDACIÓN Y ROLLBACK ===")
    logger.info(f"Acción: {action}")
    
    try:
        manager = DatabaseRollbackManager(db_config)
        
        if action == 'backup':
            table_name = sys.argv[2] if len(sys.argv) > 2 else 'questions'
            backup_info = manager.create_backup(table_name)
            if backup_info:
                print(f"✅ Backup creado: {backup_info.name}")
                return 0
            else:
                print("❌ Error creando backup")
                return 1
                
        elif action == 'validate':
            baseline_file = sys.argv[2] if len(sys.argv) > 2 else None
            baseline = {}
            
            if baseline_file and Path(baseline_file).exists():
                with open(baseline_file, 'r') as f:
                    baseline = json.load(f)
                logger.info(f"📊 Usando baseline: {baseline_file}")
            
            passed, results = manager.validate_post_update(baseline)
            
            print("\n" + "="*60)
            print("RESULTADOS DE VALIDACIÓN")
            print("="*60)
            
            critical_failed = sum(1 for r in results if not r['passed'] and r['severity'] == 'critical')
            warnings = sum(1 for r in results if not r['passed'] and r['severity'] == 'warning')
            
            print(f"✅ Validaciones exitosas: {sum(1 for r in results if r['passed'])}")
            print(f"❌ Fallas críticas: {critical_failed}")
            print(f"⚠️ Advertencias: {warnings}")
            
            if critical_failed > 0:
                print("\n🚨 FALLAS CRÍTICAS:")
                for result in results:
                    if not result['passed'] and result['severity'] == 'critical':
                        print(f"  • {result['rule_name']}: {result['message']}")
            
            return 0 if passed else 1
            
        elif action == 'rollback':
            if len(sys.argv) < 4:
                print("Uso: python rollback_manager.py rollback <backup_name> <target_table>")
                return 1
            
            backup_name = sys.argv[2]
            target_table = sys.argv[3]
            force = '--force' in sys.argv
            
            plan = manager.create_rollback_plan(backup_name, target_table)
            success = manager.execute_rollback(plan, force)
            
            return 0 if success else 1
            
        elif action == 'list':
            table_filter = sys.argv[2] if len(sys.argv) > 2 else None
            backups = manager.list_available_backups(table_filter)
            
            print("\n" + "="*60)
            print("BACKUPS DISPONIBLES")
            print("="*60)
            
            for backup in backups:
                print(f"📦 {backup.name}")
                print(f"   Tabla: {backup.table_name}")
                print(f"   Fecha: {backup.creation_time}")
                print(f"   Registros: {backup.record_count}")
                print(f"   Tamaño: {backup.size_bytes} bytes")
                print()
            
            return 0
            
        elif action == 'cleanup':
            retention_days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            cleaned = manager.cleanup_old_backups(retention_days)
            print(f"✅ {cleaned} backups antiguos eliminados")
            return 0
            
        elif action == 'baseline':
            baseline = manager.generate_validation_baseline()
            print(f"✅ Baseline generado con {len(baseline)} métricas")
            return 0
            
        else:
            print("Acciones disponibles: backup, validate, rollback, list, cleanup, baseline")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)