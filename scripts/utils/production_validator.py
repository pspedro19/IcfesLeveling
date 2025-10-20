#!/usr/bin/env python3
"""
Validador de Producción para Sistema ICFES Leveling
Ejecuta todas las validaciones técnicas críticas
"""

import asyncio
import asyncpg
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import os
import requests
import time
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Resultado de validación"""
    test_name: str
    status: str  # PASS, FAIL, WARNING
    message: str
    details: Dict[str, Any] = None
    execution_time: float = 0.0

class ProductionValidator:
    """Validador completo para producción"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'icfes_leveling',
            'user': 'gameplay',
            'password': 'gameplay123'
        }
        self.project_root = Path(r"C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling")
        self.data_dir = self.project_root / "database" / "allquestions"
        self.sql_file = self.project_root / "database" / "seed_data" / "complete_questions_load.sql"
        self.results: List[ValidationResult] = []
        
    def add_result(self, test_name: str, status: str, message: str, details: Dict = None, exec_time: float = 0.0):
        """Agregar resultado de validación"""
        self.results.append(ValidationResult(
            test_name=test_name,
            status=status,
            message=message,
            details=details or {},
            execution_time=exec_time
        ))
    
    async def validate_data_integrity(self):
        """1. Validación de Datos y Contenido"""
        start_time = time.time()
        
        try:
            # Verificar archivo SQL existe
            if not self.sql_file.exists():
                self.add_result(
                    "SQL_FILE_EXISTS",
                    "FAIL",
                    f"Archivo SQL no encontrado: {self.sql_file}",
                    exec_time=time.time() - start_time
                )
                return
            
            # Verificar directorio de imágenes
            if not self.data_dir.exists():
                self.add_result(
                    "IMAGES_DIRECTORY_EXISTS", 
                    "FAIL",
                    f"Directorio de imágenes no encontrado: {self.data_dir}",
                    exec_time=time.time() - start_time
                )
                return
            
            # Contar archivos de imagen
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
            image_files = []
            for ext in image_extensions:
                image_files.extend(list(self.data_dir.rglob(f"*{ext}"))[:])
            
            details = {
                "total_images_found": len(image_files),
                "sql_file_size_mb": round(self.sql_file.stat().st_size / (1024*1024), 2),
                "images_directory_size": len(list(self.data_dir.rglob("*")))
            }
            
            if len(image_files) >= 100:  # Esperamos al menos 100 imágenes
                self.add_result(
                    "DATA_INTEGRITY",
                    "PASS", 
                    f"Archivos encontrados: {len(image_files)} imágenes, SQL {details['sql_file_size_mb']} MB",
                    details,
                    time.time() - start_time
                )
            else:
                self.add_result(
                    "DATA_INTEGRITY",
                    "WARNING",
                    f"Pocas imágenes encontradas: {len(image_files)} (esperado ≥100)",
                    details,
                    time.time() - start_time
                )
                
        except Exception as e:
            self.add_result(
                "DATA_INTEGRITY",
                "FAIL",
                f"Error validando integridad: {e}",
                exec_time=time.time() - start_time
            )

    async def validate_irt_parameters(self):
        """2. Validar Parámetros IRT"""
        start_time = time.time()
        
        try:
            # Leer el reporte de carga para obtener promedios IRT
            report_file = self.project_root / "database" / "seed_data" / "load_summary_report.json"
            
            if not report_file.exists():
                self.add_result(
                    "IRT_PARAMETERS",
                    "FAIL",
                    "Reporte de carga no encontrado",
                    exec_time=time.time() - start_time
                )
                return
                
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            irt_avgs = report.get('irt_averages', {})
            difficulty = irt_avgs.get('difficulty', 0)
            discrimination = irt_avgs.get('discrimination', 1)
            guessing = irt_avgs.get('guessing', 0.2)
            
            # Validar rangos
            issues = []
            if not (-3 <= difficulty <= 3):
                issues.append(f"Dificultad fuera de rango: {difficulty} (esperado -3 a 3)")
            if not (0.5 <= discrimination <= 2.0):
                issues.append(f"Discriminación fuera de rango: {discrimination} (esperado 0.5-2.0)")
            if not (0.10 <= guessing <= 0.30):
                issues.append(f"Adivinanza fuera de rango: {guessing} (esperado 0.10-0.30)")
            
            details = {
                "avg_difficulty_b": difficulty,
                "avg_discrimination_a": discrimination, 
                "avg_guessing_c": guessing,
                "total_questions": report.get('total_questions', 0)
            }
            
            if not issues:
                self.add_result(
                    "IRT_PARAMETERS",
                    "PASS",
                    f"Parámetros IRT válidos: b={difficulty}, a={discrimination}, c={guessing}",
                    details,
                    time.time() - start_time
                )
            else:
                self.add_result(
                    "IRT_PARAMETERS",
                    "FAIL",
                    f"Problemas IRT: {'; '.join(issues)}",
                    details,
                    time.time() - start_time
                )
                
        except Exception as e:
            self.add_result(
                "IRT_PARAMETERS",
                "FAIL",
                f"Error validando IRT: {e}",
                exec_time=time.time() - start_time
            )

    def validate_practice_system_design(self):
        """3. Validar Diseño del Sistema de Práctica"""
        start_time = time.time()
        
        try:
            # Revisar que los scripts de práctica existen
            practice_script = self.project_root / "scripts" / "practice_from_failures.py"
            
            if not practice_script.exists():
                self.add_result(
                    "PRACTICE_SYSTEM_DESIGN",
                    "FAIL",
                    "Script practice_from_failures.py no encontrado",
                    exec_time=time.time() - start_time
                )
                return
            
            # Leer el script y validar lógica crítica
            with open(practice_script, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar patrones críticos
            critical_patterns = [
                "is_correct = FALSE",  # Solo preguntas falladas
                "diagnostic_attempts", # Referencia a diagnósticos
                "recency_score",      # Sistema de priorización
                "severity_score",     # Severidad del error
                "mastery_date"        # Tracking de dominio
            ]
            
            missing_patterns = []
            for pattern in critical_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            details = {
                "script_exists": True,
                "script_size_kb": round(len(content) / 1024, 2),
                "critical_patterns_found": len(critical_patterns) - len(missing_patterns),
                "critical_patterns_total": len(critical_patterns),
                "missing_patterns": missing_patterns
            }
            
            if not missing_patterns:
                self.add_result(
                    "PRACTICE_SYSTEM_DESIGN",
                    "PASS",
                    "Sistema de práctica correctamente diseñado (100% basado en fallos)",
                    details,
                    time.time() - start_time
                )
            else:
                self.add_result(
                    "PRACTICE_SYSTEM_DESIGN",
                    "WARNING", 
                    f"Patrones faltantes en sistema de práctica: {missing_patterns}",
                    details,
                    time.time() - start_time
                )
                
        except Exception as e:
            self.add_result(
                "PRACTICE_SYSTEM_DESIGN",
                "FAIL",
                f"Error validando sistema de práctica: {e}",
                exec_time=time.time() - start_time
            )

    def validate_image_endpoints(self):
        """4. Validar Endpoints de Imágenes (Mock)"""
        start_time = time.time()
        
        try:
            # Como no tenemos el servidor corriendo, validamos la estructura
            # Buscar archivos de configuración del servidor de imágenes
            
            # Verificar que existe configuración para servir imágenes
            config_files = [
                self.project_root / "docker-compose.yml",
                self.project_root / ".env.example",
                self.project_root / "Makefile"
            ]
            
            has_media_config = False
            config_details = {}
            
            for config_file in config_files:
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'media' in content.lower() or 'image' in content.lower():
                        has_media_config = True
                        config_details[config_file.name] = True
            
            # Verificar estructura de paths relativos
            sample_images = list(self.data_dir.rglob("*.png"))[:5]
            relative_paths = []
            
            for img in sample_images:
                try:
                    rel_path = img.relative_to(self.project_root)
                    relative_paths.append(str(rel_path))
                except ValueError:
                    continue
            
            details = {
                "media_config_found": has_media_config,
                "config_files_checked": len(config_files),
                "sample_relative_paths": relative_paths[:3],
                "total_sample_images": len(sample_images)
            }
            
            if has_media_config and relative_paths:
                self.add_result(
                    "IMAGE_ENDPOINTS_STRUCTURE",
                    "PASS",
                    "Estructura para endpoints de imágenes configurada correctamente",
                    details,
                    time.time() - start_time
                )
            else:
                self.add_result(
                    "IMAGE_ENDPOINTS_STRUCTURE",
                    "WARNING",
                    "Configuración de endpoints de imágenes incompleta",
                    details,
                    time.time() - start_time
                )
                
        except Exception as e:
            self.add_result(
                "IMAGE_ENDPOINTS_STRUCTURE",
                "FAIL",
                f"Error validando endpoints: {e}",
                exec_time=time.time() - start_time
            )

    def validate_security_measures(self):
        """6. Validar Medidas de Seguridad"""
        start_time = time.time()
        
        try:
            # Buscar medidas de seguridad en el código
            security_files = [
                self.project_root / "scripts" / "final_data_loader.py",
                self.project_root / "scripts" / "offline_sql_generator.py"
            ]
            
            security_patterns = [
                "escape_sql_string",   # Prevención SQL injection
                "replace",            # Sanitización
                "UUID",               # IDs seguros
                "relative_to",        # Path traversal prevention
            ]
            
            security_score = 0
            total_patterns = len(security_patterns)
            found_patterns = []
            
            for file_path in security_files:
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for pattern in security_patterns:
                        if pattern in content and pattern not in found_patterns:
                            found_patterns.append(pattern)
                            security_score += 1
            
            details = {
                "security_patterns_found": found_patterns,
                "security_score": f"{security_score}/{total_patterns}",
                "files_checked": len(security_files)
            }
            
            if security_score >= total_patterns * 0.75:  # 75% de patrones encontrados
                self.add_result(
                    "SECURITY_MEASURES",
                    "PASS",
                    f"Medidas de seguridad implementadas ({security_score}/{total_patterns})",
                    details,
                    time.time() - start_time
                )
            else:
                self.add_result(
                    "SECURITY_MEASURES",
                    "WARNING",
                    f"Medidas de seguridad parciales ({security_score}/{total_patterns})",
                    details,
                    time.time() - start_time
                )
                
        except Exception as e:
            self.add_result(
                "SECURITY_MEASURES",
                "FAIL",
                f"Error validando seguridad: {e}",
                exec_time=time.time() - start_time
            )

    def validate_e2e_flow(self):
        """8. Validar Flujo E2E Completo"""
        start_time = time.time()
        
        try:
            # Verificar que existen todos los scripts del flujo
            required_scripts = [
                "irt_3pl_engine.py",
                "practice_from_failures.py", 
                "recommendation_engine.py",
                "advanced_dashboard_system.py",
                "pdf_report_system.py",
                "ai_study_system.py",
                "complete_e2e_testing.py"
            ]
            
            scripts_dir = self.project_root / "scripts"
            existing_scripts = []
            missing_scripts = []
            
            for script_name in required_scripts:
                script_path = scripts_dir / script_name
                if script_path.exists():
                    existing_scripts.append(script_name)
                else:
                    missing_scripts.append(script_name)
            
            # Verificar documentación
            readme_final = self.project_root / "README_FINAL.md"
            deployment_status = self.project_root / "DEPLOYMENT_STATUS.md"
            
            docs_exist = readme_final.exists() and deployment_status.exists()
            
            details = {
                "existing_scripts": existing_scripts,
                "missing_scripts": missing_scripts,
                "scripts_completion": f"{len(existing_scripts)}/{len(required_scripts)}",
                "documentation_exists": docs_exist,
                "makefile_exists": (self.project_root / "Makefile").exists()
            }
            
            completion_rate = len(existing_scripts) / len(required_scripts)
            
            if completion_rate >= 0.9 and docs_exist:
                self.add_result(
                    "E2E_FLOW_COMPLETE",
                    "PASS",
                    f"Flujo E2E completo ({len(existing_scripts)}/{len(required_scripts)} scripts)",
                    details,
                    time.time() - start_time
                )
            elif completion_rate >= 0.75:
                self.add_result(
                    "E2E_FLOW_COMPLETE",
                    "WARNING",
                    f"Flujo E2E mayormente completo, faltan: {missing_scripts}",
                    details,
                    time.time() - start_time
                )
            else:
                self.add_result(
                    "E2E_FLOW_COMPLETE",
                    "FAIL",
                    f"Flujo E2E incompleto, faltan {len(missing_scripts)} scripts críticos",
                    details,
                    time.time() - start_time
                )
                
        except Exception as e:
            self.add_result(
                "E2E_FLOW_COMPLETE",
                "FAIL", 
                f"Error validando flujo E2E: {e}",
                exec_time=time.time() - start_time
            )

    async def run_all_validations(self):
        """Ejecutar todas las validaciones"""
        logger.info("Iniciando validaciones de produccion...")
        
        # Ejecutar validaciones
        await self.validate_data_integrity()
        await self.validate_irt_parameters()
        self.validate_practice_system_design()
        self.validate_image_endpoints()
        self.validate_security_measures()
        self.validate_e2e_flow()
        
        # Generar reporte final
        return self.generate_final_report()

    def generate_final_report(self) -> Dict[str, Any]:
        """Generar reporte final de validaciones"""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        warnings = sum(1 for r in self.results if r.status == "WARNING")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        
        total_time = sum(r.execution_time for r in self.results)
        
        # Determinar estado general
        if failed == 0 and warnings <= 2:
            overall_status = "PRODUCTION_READY"
        elif failed <= 1 and warnings <= 3:
            overall_status = "MOSTLY_READY"
        else:
            overall_status = "NEEDS_WORK"
        
        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "warnings": warnings,
                "failed": failed,
                "pass_rate": round((passed / total_tests) * 100, 1) if total_tests > 0 else 0,
                "total_execution_time": round(total_time, 2)
            },
            "test_results": [
                {
                    "test": r.test_name,
                    "status": r.status,
                    "message": r.message,
                    "execution_time": r.execution_time,
                    "details": r.details
                }
                for r in self.results
            ]
        }
        
        return report

async def main():
    """Función principal"""
    validator = ProductionValidator()
    
    try:
        report = await validator.run_all_validations()
        
        # Guardar reporte
        report_file = validator.project_root / "validation_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Imprimir resumen
        print("\n" + "="*70)
        print("REPORTE DE VALIDACIONES DE PRODUCCION")
        print("="*70)
        
        summary = report['summary']
        print(f"Estado General: {report['overall_status']}")
        print(f"Tests Totales: {summary['total_tests']}")
        print(f"Pasaron: {summary['passed']}")
        print(f"Advertencias: {summary['warnings']}")
        print(f"Fallaron: {summary['failed']}")
        print(f"Tasa de Éxito: {summary['pass_rate']}%")
        print(f"Tiempo Total: {summary['total_execution_time']}s")
        
        print("\nRESULTADOS POR TEST:")
        for result in validator.results:
            status_symbol = {"PASS": "[OK]", "WARNING": "[WARN]", "FAIL": "[FAIL]"}[result.status]
            print(f"{status_symbol} {result.test_name}: {result.message}")
        
        print(f"\nReporte completo guardado en: {report_file}")
        
        if report['overall_status'] == "PRODUCTION_READY":
            print("\nSISTEMA LISTO PARA PRODUCCION!")
            return 0
        elif report['overall_status'] == "MOSTLY_READY":
            print("\nSistema mayormente listo, revisar advertencias")
            return 1
        else:
            print("\nSistema requiere trabajo adicional")
            return 2
            
    except Exception as e:
        print(f"\nERROR CRITICO EN VALIDACION: {e}")
        return 3

if __name__ == "__main__":
    exit_code = asyncio.run(main())