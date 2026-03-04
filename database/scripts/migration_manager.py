#!/usr/bin/env python3
"""
Manejador de Migraciones Alembic para ICFES Leveling
Sistema completo de gestión de migraciones de base de datos.
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
import psycopg2
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MigrationInfo:
    """Información de migración"""
    revision: str
    description: str
    branch_labels: Optional[str]
    depends_on: Optional[str]
    is_head: bool
    is_current: bool

@dataclass
class MigrationResult:
    """Resultado de migración"""
    success: bool
    from_revision: str
    to_revision: str
    migrations_applied: List[str]
    duration_seconds: float
    errors: List[str]
    warnings: List[str]

class AlembicMigrationManager:
    """Manejador de migraciones Alembic"""
    
    def __init__(self, db_config: Dict[str, Any], alembic_dir: str = "database/migrations"):
        self.db_config = db_config
        self.alembic_dir = Path(alembic_dir)
        self.alembic_ini = self.alembic_dir / "alembic.ini"
        
        # Verificar configuración
        self._verify_setup()

    def _verify_setup(self):
        """Verificar que Alembic está configurado correctamente"""
        if not self.alembic_ini.exists():
            raise FileNotFoundError(f"Archivo alembic.ini no encontrado en {self.alembic_ini}")
        
        env_py = self.alembic_dir / "env.py"
        if not env_py.exists():
            raise FileNotFoundError(f"Archivo env.py no encontrado en {env_py}")
        
        versions_dir = self.alembic_dir / "versions"
        if not versions_dir.exists():
            versions_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Directorio de versiones creado: {versions_dir}")

    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return psycopg2.connect(**self.db_config)

    def _run_alembic_command(self, command: List[str], capture_output: bool = True) -> Tuple[bool, str, str]:
        """Ejecutar comando de Alembic"""
        try:
            # Configurar variables de entorno
            env = os.environ.copy()
            
            # Construir URL de base de datos
            db_url = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            env['DATABASE_URL'] = db_url
            
            # Comando completo
            full_command = ['alembic', '-c', str(self.alembic_ini)] + command
            
            logger.info(f"🔧 Ejecutando: {' '.join(full_command)}")
            
            result = subprocess.run(
                full_command,
                capture_output=capture_output,
                text=True,
                env=env,
                cwd=self.alembic_dir.parent
            )
            
            return result.returncode == 0, result.stdout, result.stderr
            
        except Exception as e:
            logger.error(f"Error ejecutando comando Alembic: {e}")
            return False, "", str(e)

    def get_current_revision(self) -> Optional[str]:
        """Obtener revisión actual de la base de datos"""
        try:
            success, stdout, stderr = self._run_alembic_command(['current'])
            if success and stdout:
                # Extraer revision ID del output
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line and not line.startswith('INFO'):
                        return line.strip().split()[0]
            return None
        except Exception as e:
            logger.error(f"Error obteniendo revisión actual: {e}")
            return None

    def get_migration_history(self) -> List[MigrationInfo]:
        """Obtener historial de migraciones"""
        migrations = []
        
        try:
            # Obtener información de todas las migraciones
            success, stdout, stderr = self._run_alembic_command(['history', '--verbose'])
            
            if success and stdout:
                current_revision = self.get_current_revision()
                
                # Parsear output de history
                migration_blocks = stdout.split('\n\n')
                
                for block in migration_blocks:
                    if '->' in block and 'Rev:' in block:
                        lines = block.strip().split('\n')
                        
                        # Extraer información de la migración
                        revision = ""
                        description = ""
                        branch_labels = None
                        depends_on = None
                        
                        for line in lines:
                            line = line.strip()
                            if line.startswith('Rev:'):
                                revision = line.split('Rev:')[1].strip().split()[0]
                            elif line.startswith('Parent:'):
                                depends_on = line.split('Parent:')[1].strip()
                                if depends_on == '<base>':
                                    depends_on = None
                            elif line.startswith('Branch labels:'):
                                branch_labels = line.split('Branch labels:')[1].strip()
                                if branch_labels in ['none', '']:
                                    branch_labels = None
                            elif '->' in line and 'Rev:' not in line:
                                # Esta es probablemente la descripción
                                description = line.split('->')[-1].strip()
                        
                        if revision:
                            migrations.append(MigrationInfo(
                                revision=revision,
                                description=description,
                                branch_labels=branch_labels,
                                depends_on=depends_on,
                                is_head=False,  # Se actualiza después
                                is_current=(revision == current_revision)
                            ))
            
            # Identificar heads
            success, stdout, stderr = self._run_alembic_command(['heads'])
            if success and stdout:
                head_revisions = []
                for line in stdout.strip().split('\n'):
                    if line and not line.startswith('INFO'):
                        head_revisions.append(line.strip().split()[0])
                
                # Marcar heads
                for migration in migrations:
                    if migration.revision in head_revisions:
                        migration.is_head = True
            
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
        
        return migrations

    def check_migration_status(self) -> Dict[str, Any]:
        """Verificar estado de migraciones"""
        status = {
            'current_revision': self.get_current_revision(),
            'pending_migrations': [],
            'applied_migrations': [],
            'head_revision': None,
            'database_up_to_date': False
        }
        
        try:
            # Obtener head revision
            success, stdout, stderr = self._run_alembic_command(['heads'])
            if success and stdout:
                for line in stdout.strip().split('\n'):
                    if line and not line.startswith('INFO'):
                        status['head_revision'] = line.strip().split()[0]
                        break
            
            # Verificar si hay migraciones pendientes
            success, stdout, stderr = self._run_alembic_command(['check'])
            status['database_up_to_date'] = success
            
            # Si no está actualizada, obtener migraciones pendientes
            if not success:
                # Obtener migraciones que faltan por aplicar
                success, stdout, stderr = self._run_alembic_command(['show', 'head'])
                if success and 'Rev:' in stdout:
                    # Aquí podrías parsear las migraciones pendientes
                    # Por simplicidad, solo marcamos que hay pendientes
                    status['pending_migrations'] = ['pending']
            
            # Obtener historial aplicado
            history = self.get_migration_history()
            status['applied_migrations'] = [m.revision for m in history if m.is_current or self._is_applied(m.revision)]
            
        except Exception as e:
            logger.error(f"Error verificando estado: {e}")
            status['error'] = str(e)
        
        return status

    def _is_applied(self, revision: str) -> bool:
        """Verificar si una revisión está aplicada"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM alembic_version WHERE version_num = %s;",
                    (revision,)
                )
                return cursor.fetchone() is not None
        except Exception:
            return False

    def upgrade_database(self, revision: str = "head") -> MigrationResult:
        """Ejecutar upgrade de base de datos"""
        logger.info(f"🚀 Iniciando upgrade a revisión: {revision}")
        
        start_time = datetime.now()
        current_revision = self.get_current_revision()
        
        try:
            success, stdout, stderr = self._run_alembic_command(['upgrade', revision])
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Obtener nueva revisión
            new_revision = self.get_current_revision()
            
            # Parsear migraciones aplicadas del output
            migrations_applied = []
            errors = []
            warnings = []
            
            if stdout:
                for line in stdout.split('\n'):
                    if 'Running upgrade' in line:
                        # Extraer información de migración aplicada
                        parts = line.split('->')
                        if len(parts) == 2:
                            migrations_applied.append(parts[1].strip())
                    elif 'WARNING' in line:
                        warnings.append(line)
            
            if stderr:
                errors.extend(stderr.split('\n'))
            
            result = MigrationResult(
                success=success,
                from_revision=current_revision or 'None',
                to_revision=new_revision or revision,
                migrations_applied=migrations_applied,
                duration_seconds=duration,
                errors=errors,
                warnings=warnings
            )
            
            if success:
                logger.info(f"✅ Upgrade exitoso: {current_revision} -> {new_revision}")
            else:
                logger.error(f"❌ Upgrade falló: {stderr}")
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return MigrationResult(
                success=False,
                from_revision=current_revision or 'None',
                to_revision=revision,
                migrations_applied=[],
                duration_seconds=duration,
                errors=[str(e)],
                warnings=[]
            )

    def downgrade_database(self, revision: str) -> MigrationResult:
        """Ejecutar downgrade de base de datos"""
        logger.info(f"⬇️ Iniciando downgrade a revisión: {revision}")
        
        start_time = datetime.now()
        current_revision = self.get_current_revision()
        
        try:
            success, stdout, stderr = self._run_alembic_command(['downgrade', revision])
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            new_revision = self.get_current_revision()
            
            # Parsear output similar al upgrade
            migrations_applied = []
            errors = []
            warnings = []
            
            if stdout:
                for line in stdout.split('\n'):
                    if 'Running downgrade' in line:
                        migrations_applied.append(line)
                    elif 'WARNING' in line:
                        warnings.append(line)
            
            if stderr:
                errors.extend(stderr.split('\n'))
            
            result = MigrationResult(
                success=success,
                from_revision=current_revision or 'None',
                to_revision=new_revision or revision,
                migrations_applied=migrations_applied,
                duration_seconds=duration,
                errors=errors,
                warnings=warnings
            )
            
            if success:
                logger.info(f"✅ Downgrade exitoso: {current_revision} -> {new_revision}")
            else:
                logger.error(f"❌ Downgrade falló: {stderr}")
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return MigrationResult(
                success=False,
                from_revision=current_revision or 'None',
                to_revision=revision,
                migrations_applied=[],
                duration_seconds=duration,
                errors=[str(e)],
                warnings=[]
            )

    def create_migration(self, message: str, autogenerate: bool = True) -> Tuple[bool, str]:
        """Crear nueva migración"""
        logger.info(f"📝 Creando migración: {message}")
        
        command = ['revision']
        if autogenerate:
            command.append('--autogenerate')
        command.extend(['-m', message])
        
        try:
            success, stdout, stderr = self._run_alembic_command(command)
            
            if success:
                # Extraer nombre del archivo creado
                for line in stdout.split('\n'):
                    if 'Generating' in line and '.py' in line:
                        logger.info(f"✅ Migración creada: {line}")
                        return True, line
                return True, "Migración creada exitosamente"
            else:
                logger.error(f"❌ Error creando migración: {stderr}")
                return False, stderr
                
        except Exception as e:
            logger.error(f"Error creando migración: {e}")
            return False, str(e)

    def validate_migrations(self) -> Dict[str, Any]:
        """Validar integridad de migraciones"""
        logger.info("🔍 Validando integridad de migraciones")
        
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'migration_count': 0,
            'orphaned_migrations': []
        }
        
        try:
            # Verificar que no hay migraciones huérfanas
            success, stdout, stderr = self._run_alembic_command(['check'])
            if not success:
                validation['valid'] = False
                validation['errors'].append("Migraciones inconsistentes detectadas")
                validation['errors'].append(stderr)
            
            # Contar migraciones
            history = self.get_migration_history()
            validation['migration_count'] = len(history)
            
            # Verificar archivos de migración huérfanos
            versions_dir = self.alembic_dir / "versions"
            if versions_dir.exists():
                migration_files = list(versions_dir.glob("*.py"))
                if len(migration_files) != len(history):
                    validation['warnings'].append(
                        f"Discrepancia: {len(migration_files)} archivos vs {len(history)} en historial"
                    )
            
            logger.info(f"✅ Validación completada: {validation['migration_count']} migraciones")
            
        except Exception as e:
            validation['valid'] = False
            validation['errors'].append(str(e))
        
        return validation

    def generate_migration_report(self) -> Dict[str, Any]:
        """Generar reporte completo de migraciones"""
        logger.info("📊 Generando reporte de migraciones")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'database': self.db_config.get('database'),
            'status': self.check_migration_status(),
            'history': [asdict(m) for m in self.get_migration_history()],
            'validation': self.validate_migrations()
        }
        
        return report

    def save_migration_report(self, report: Dict[str, Any]) -> str:
        """Guardar reporte de migraciones"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"database/reports/migration_report_{timestamp}.json"
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📋 Reporte guardado: {report_path}")
        return report_path


def main():
    """Función principal del manejador de migraciones"""
    
    # Configuración de base de datos
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'gameplay_db'),
        'user': os.getenv('DB_USER', 'gameplay'),
        'password': os.getenv('DB_PASSWORD', 'gameplay123')
    }
    
    action = sys.argv[1] if len(sys.argv) > 1 else 'status'
    
    logger.info("=== MANEJADOR DE MIGRACIONES ALEMBIC ===")
    logger.info(f"Acción: {action}")
    
    try:
        manager = AlembicMigrationManager(db_config)
        
        if action == 'status':
            # Mostrar estado actual
            status = manager.check_migration_status()
            
            print("\n" + "="*60)
            print("ESTADO DE MIGRACIONES")
            print("="*60)
            print(f"📍 Revisión actual: {status['current_revision'] or 'None'}")
            print(f"🎯 Revisión head: {status['head_revision'] or 'None'}")
            print(f"✅ Base de datos actualizada: {status['database_up_to_date']}")
            print(f"📊 Migraciones aplicadas: {len(status['applied_migrations'])}")
            print(f"⏳ Migraciones pendientes: {len(status['pending_migrations'])}")
            
            return 0
            
        elif action == 'upgrade':
            revision = sys.argv[2] if len(sys.argv) > 2 else 'head'
            result = manager.upgrade_database(revision)
            
            print(f"{'✅' if result.success else '❌'} Upgrade: {result.from_revision} -> {result.to_revision}")
            print(f"⏱️ Duración: {result.duration_seconds:.2f}s")
            print(f"📊 Migraciones aplicadas: {len(result.migrations_applied)}")
            
            if result.errors:
                print("❌ Errores:")
                for error in result.errors[:3]:
                    print(f"  • {error}")
            
            return 0 if result.success else 1
            
        elif action == 'downgrade':
            if len(sys.argv) < 3:
                print("Uso: python migration_manager.py downgrade <revision>")
                return 1
            
            revision = sys.argv[2]
            result = manager.downgrade_database(revision)
            
            print(f"{'✅' if result.success else '❌'} Downgrade: {result.from_revision} -> {result.to_revision}")
            print(f"⏱️ Duración: {result.duration_seconds:.2f}s")
            
            return 0 if result.success else 1
            
        elif action == 'create':
            if len(sys.argv) < 3:
                print("Uso: python migration_manager.py create '<mensaje>'")
                return 1
            
            message = sys.argv[2]
            autogenerate = '--autogenerate' in sys.argv or '-a' in sys.argv
            
            success, output = manager.create_migration(message, autogenerate)
            print(f"{'✅' if success else '❌'} {output}")
            
            return 0 if success else 1
            
        elif action == 'history':
            # Mostrar historial
            history = manager.get_migration_history()
            
            print("\n" + "="*60)
            print("HISTORIAL DE MIGRACIONES")
            print("="*60)
            
            for migration in history:
                status_icons = []
                if migration.is_current:
                    status_icons.append("📍")
                if migration.is_head:
                    status_icons.append("🎯")
                
                print(f"{''.join(status_icons)} {migration.revision}")
                print(f"   {migration.description}")
                if migration.depends_on:
                    print(f"   Depende de: {migration.depends_on}")
                print()
            
            return 0
            
        elif action == 'validate':
            # Validar migraciones
            validation = manager.validate_migrations()
            
            print(f"{'✅' if validation['valid'] else '❌'} Validación: {'EXITOSA' if validation['valid'] else 'FALLIDA'}")
            print(f"📊 Migraciones: {validation['migration_count']}")
            
            if validation['errors']:
                print("❌ Errores:")
                for error in validation['errors']:
                    print(f"  • {error}")
            
            if validation['warnings']:
                print("⚠️ Advertencias:")
                for warning in validation['warnings']:
                    print(f"  • {warning}")
            
            return 0 if validation['valid'] else 1
            
        elif action == 'report':
            # Generar reporte completo
            report = manager.generate_migration_report()
            report_path = manager.save_migration_report(report)
            
            print(f"📋 Reporte generado: {report_path}")
            
            # Mostrar resumen
            status = report['status']
            print(f"📍 Estado actual: {status['current_revision'] or 'None'}")
            print(f"📊 Total migraciones: {len(report['history'])}")
            print(f"✅ Válido: {report['validation']['valid']}")
            
            return 0
            
        else:
            print("Acciones disponibles: status, upgrade, downgrade, create, history, validate, report")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)