#!/usr/bin/env python3
"""
Validador de Performance para Sistema ICFES Leveling
Tests de rendimiento, concurrencia y métricas críticas
"""

import time
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceValidator:
    """Validador de performance del sistema"""
    
    def __init__(self):
        self.project_root = Path(r"C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling")
        self.results = []
        self.thresholds = {
            "sql_generation_time": 2.0,      # seconds
            "image_processing_time": 0.1,    # per image
            "script_execution_time": 10.0,   # seconds
            "memory_usage_mb": 512,           # MB
            "file_read_time": 0.05           # seconds
        }

    def add_result(self, test_name: str, status: str, message: str, details: Dict = None, exec_time: float = 0.0):
        """Agregar resultado de validación"""
        self.results.append({
            "test": test_name,
            "status": status,
            "message": message,
            "execution_time": exec_time,
            "details": details or {}
        })

    def test_sql_generation_performance(self):
        """Test: Performance de generación SQL"""
        start_time = time.time()
        
        try:
            # Ejecutar generador SQL y medir tiempo
            cmd = ["python", str(self.project_root / "scripts" / "offline_sql_generator.py")]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                # Verificar que se generó el archivo
                sql_file = self.project_root / "database" / "seed_data" / "complete_questions_load.sql"
                file_size_mb = sql_file.stat().st_size / (1024*1024) if sql_file.exists() else 0
                
                details = {
                    "execution_time": round(execution_time, 2),
                    "threshold": self.thresholds["sql_generation_time"],
                    "file_generated": sql_file.exists(),
                    "file_size_mb": round(file_size_mb, 2),
                    "within_threshold": execution_time <= self.thresholds["sql_generation_time"]
                }
                
                if execution_time <= self.thresholds["sql_generation_time"]:
                    self.add_result(
                        "SQL_GENERATION_PERFORMANCE",
                        "PASS",
                        f"Generación SQL rápida: {execution_time:.2f}s (< {self.thresholds['sql_generation_time']}s)",
                        details,
                        execution_time
                    )
                else:
                    self.add_result(
                        "SQL_GENERATION_PERFORMANCE",
                        "WARNING",
                        f"Generación SQL lenta: {execution_time:.2f}s (> {self.thresholds['sql_generation_time']}s)",
                        details,
                        execution_time
                    )
            else:
                self.add_result(
                    "SQL_GENERATION_PERFORMANCE",
                    "FAIL",
                    f"Error en generación SQL: {result.stderr[:200]}",
                    {"execution_time": execution_time, "error": result.stderr},
                    execution_time
                )
                
        except subprocess.TimeoutExpired:
            self.add_result(
                "SQL_GENERATION_PERFORMANCE",
                "FAIL",
                "Timeout en generación SQL (>30s)",
                {"timeout": True},
                30.0
            )
        except Exception as e:
            self.add_result(
                "SQL_GENERATION_PERFORMANCE",
                "FAIL",
                f"Error ejecutando generación: {e}",
                exec_time=time.time() - start_time
            )

    def test_file_io_performance(self):
        """Test: Performance de I/O de archivos"""
        start_time = time.time()
        
        try:
            # Test de lectura de Excel
            excel_file = self.project_root / "database" / "allquestions" / "ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"
            
            if not excel_file.exists():
                self.add_result(
                    "FILE_IO_PERFORMANCE",
                    "FAIL",
                    "Archivo Excel no encontrado para test I/O",
                    exec_time=time.time() - start_time
                )
                return
            
            # Medir tiempo de lectura del Excel
            excel_start = time.time()
            
            try:
                import pandas as pd
                df = pd.read_excel(excel_file)
                excel_time = time.time() - excel_start
                
                # Test de lectura de múltiples imágenes
                images_dir = self.project_root / "database" / "allquestions"
                image_files = list(images_dir.rglob("*.png"))[:10]  # Primeras 10 imágenes
                
                image_times = []
                for img_file in image_files:
                    img_start = time.time()
                    with open(img_file, 'rb') as f:
                        f.read()
                    image_times.append(time.time() - img_start)
                
                avg_image_time = sum(image_times) / len(image_times) if image_times else 0
                
                details = {
                    "excel_read_time": round(excel_time, 3),
                    "excel_rows": len(df),
                    "images_tested": len(image_files),
                    "avg_image_read_time": round(avg_image_time, 4),
                    "image_threshold": self.thresholds["image_processing_time"],
                    "excel_within_threshold": excel_time <= 5.0,  # 5s threshold for Excel
                    "images_within_threshold": avg_image_time <= self.thresholds["image_processing_time"]
                }
                
                total_time = time.time() - start_time
                
                if excel_time <= 5.0 and avg_image_time <= self.thresholds["image_processing_time"]:
                    self.add_result(
                        "FILE_IO_PERFORMANCE",
                        "PASS",
                        f"I/O eficiente: Excel {excel_time:.2f}s, Imágenes avg {avg_image_time:.4f}s",
                        details,
                        total_time
                    )
                else:
                    self.add_result(
                        "FILE_IO_PERFORMANCE",
                        "WARNING",
                        f"I/O lento: Excel {excel_time:.2f}s, Imágenes {avg_image_time:.4f}s",
                        details,
                        total_time
                    )
                    
            except ImportError:
                self.add_result(
                    "FILE_IO_PERFORMANCE",
                    "WARNING",
                    "pandas no disponible para test Excel I/O",
                    exec_time=time.time() - start_time
                )
                
        except Exception as e:
            self.add_result(
                "FILE_IO_PERFORMANCE",
                "FAIL",
                f"Error en test I/O: {e}",
                exec_time=time.time() - start_time
            )

    def test_script_execution_performance(self):
        """Test: Performance de ejecución de scripts críticos"""
        start_time = time.time()
        
        critical_scripts = [
            "production_validator.py",
            "validate_sql_logic.py",
            "complete_e2e_testing.py"
        ]
        
        script_results = {}
        
        for script_name in critical_scripts:
            script_path = self.project_root / "scripts" / script_name
            
            if not script_path.exists():
                script_results[script_name] = {
                    "exists": False,
                    "execution_time": None,
                    "success": False
                }
                continue
            
            # Medir tiempo de ejecución
            script_start = time.time()
            
            try:
                # Para scripts de validación, ejecutar con timeout
                if "validate" in script_name or "testing" in script_name:
                    timeout = 20  # 20 segundos timeout
                else:
                    timeout = 10  # 10 segundos timeout
                
                cmd = ["python", str(script_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                
                execution_time = time.time() - script_start
                
                script_results[script_name] = {
                    "exists": True,
                    "execution_time": round(execution_time, 2),
                    "success": result.returncode == 0,
                    "within_threshold": execution_time <= self.thresholds["script_execution_time"],
                    "output_lines": len(result.stdout.split('\n')) if result.stdout else 0
                }
                
            except subprocess.TimeoutExpired:
                script_results[script_name] = {
                    "exists": True,
                    "execution_time": timeout,
                    "success": False,
                    "timeout": True
                }
            except Exception as e:
                script_results[script_name] = {
                    "exists": True,
                    "execution_time": None,
                    "success": False,
                    "error": str(e)
                }
        
        # Evaluar resultados
        successful_scripts = sum(1 for r in script_results.values() if r.get("success", False))
        fast_scripts = sum(1 for r in script_results.values() if r.get("within_threshold", False))
        
        total_time = time.time() - start_time
        
        details = {
            "scripts_tested": len(critical_scripts),
            "successful_executions": successful_scripts,
            "fast_executions": fast_scripts,
            "script_details": script_results
        }
        
        if successful_scripts >= len(critical_scripts) * 0.8 and fast_scripts >= len(critical_scripts) * 0.6:
            self.add_result(
                "SCRIPT_EXECUTION_PERFORMANCE",
                "PASS",
                f"Scripts eficientes: {successful_scripts}/{len(critical_scripts)} exitosos, {fast_scripts} rápidos",
                details,
                total_time
            )
        elif successful_scripts >= len(critical_scripts) * 0.6:
            self.add_result(
                "SCRIPT_EXECUTION_PERFORMANCE",
                "WARNING",
                f"Scripts parcialmente eficientes: {successful_scripts}/{len(critical_scripts)} exitosos",
                details,
                total_time
            )
        else:
            self.add_result(
                "SCRIPT_EXECUTION_PERFORMANCE",
                "FAIL",
                f"Scripts lentos: solo {successful_scripts}/{len(critical_scripts)} exitosos",
                details,
                total_time
            )

    def test_concurrent_file_access(self):
        """Test: Acceso concurrente a archivos"""
        start_time = time.time()
        
        try:
            # Simular acceso concurrente a imágenes
            images_dir = self.project_root / "database" / "allquestions"
            image_files = list(images_dir.rglob("*.png"))[:20]  # Primeras 20 imágenes
            
            if len(image_files) < 5:
                self.add_result(
                    "CONCURRENT_FILE_ACCESS",
                    "WARNING",
                    f"Pocas imágenes para test concurrente: {len(image_files)}",
                    exec_time=time.time() - start_time
                )
                return
            
            def read_file(file_path):
                """Leer archivo y retornar tiempo"""
                read_start = time.time()
                try:
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    return {
                        "success": True,
                        "time": time.time() - read_start,
                        "size": len(data)
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "time": time.time() - read_start,
                        "error": str(e)
                    }
            
            # Test con 5 threads concurrentes
            concurrent_start = time.time()
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(read_file, img) for img in image_files[:10]]
                results = [f.result() for f in futures]
            
            concurrent_time = time.time() - concurrent_start
            
            successful_reads = sum(1 for r in results if r["success"])
            avg_read_time = sum(r["time"] for r in results if r["success"]) / successful_reads if successful_reads > 0 else 0
            total_size_mb = sum(r.get("size", 0) for r in results) / (1024*1024)
            
            details = {
                "concurrent_execution_time": round(concurrent_time, 2),
                "files_processed": len(results),
                "successful_reads": successful_reads,
                "avg_read_time": round(avg_read_time, 4),
                "total_size_mb": round(total_size_mb, 2),
                "throughput_mb_per_sec": round(total_size_mb / concurrent_time, 2) if concurrent_time > 0 else 0
            }
            
            if successful_reads >= len(results) * 0.9 and avg_read_time <= 0.1:
                self.add_result(
                    "CONCURRENT_FILE_ACCESS",
                    "PASS",
                    f"Acceso concurrente eficiente: {successful_reads}/{len(results)} exitosos, {details['throughput_mb_per_sec']} MB/s",
                    details,
                    time.time() - start_time
                )
            else:
                self.add_result(
                    "CONCURRENT_FILE_ACCESS",
                    "WARNING",
                    f"Acceso concurrente lento: {successful_reads}/{len(results)}, avg {avg_read_time:.4f}s",
                    details,
                    time.time() - start_time
                )
                
        except Exception as e:
            self.add_result(
                "CONCURRENT_FILE_ACCESS",
                "FAIL",
                f"Error en test concurrente: {e}",
                exec_time=time.time() - start_time
            )

    def test_memory_efficiency(self):
        """Test: Eficiencia de memoria"""
        start_time = time.time()
        
        try:
            import psutil
            process = psutil.Process()
            
            # Memoria inicial
            initial_memory = process.memory_info().rss / (1024*1024)  # MB
            
            # Simular operación memory-intensive (leer múltiples archivos grandes)
            memory_test_start = time.time()
            
            # Leer Excel grande
            excel_file = self.project_root / "database" / "allquestions" / "ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"
            
            if excel_file.exists():
                try:
                    import pandas as pd
                    df = pd.read_excel(excel_file)
                    # Procesamiento básico
                    df_memory = df.memory_usage(deep=True).sum() / (1024*1024)
                    
                    # Memoria después de carga
                    peak_memory = process.memory_info().rss / (1024*1024)
                    
                    # Limpiar
                    del df
                    
                    # Memoria final
                    final_memory = process.memory_info().rss / (1024*1024)
                    
                    details = {
                        "initial_memory_mb": round(initial_memory, 2),
                        "peak_memory_mb": round(peak_memory, 2),
                        "final_memory_mb": round(final_memory, 2),
                        "memory_increase_mb": round(peak_memory - initial_memory, 2),
                        "dataframe_memory_mb": round(df_memory, 2),
                        "memory_threshold_mb": self.thresholds["memory_usage_mb"],
                        "within_threshold": peak_memory <= self.thresholds["memory_usage_mb"],
                        "memory_cleaned": final_memory < peak_memory * 0.9
                    }
                    
                    if peak_memory <= self.thresholds["memory_usage_mb"]:
                        self.add_result(
                            "MEMORY_EFFICIENCY",
                            "PASS",
                            f"Memoria eficiente: peak {peak_memory:.1f}MB (< {self.thresholds['memory_usage_mb']}MB)",
                            details,
                            time.time() - start_time
                        )
                    else:
                        self.add_result(
                            "MEMORY_EFFICIENCY",
                            "WARNING",
                            f"Uso de memoria alto: peak {peak_memory:.1f}MB (> {self.thresholds['memory_usage_mb']}MB)",
                            details,
                            time.time() - start_time
                        )
                        
                except ImportError:
                    self.add_result(
                        "MEMORY_EFFICIENCY",
                        "WARNING",
                        "pandas no disponible para test de memoria",
                        exec_time=time.time() - start_time
                    )
            else:
                self.add_result(
                    "MEMORY_EFFICIENCY",
                    "WARNING",
                    "Excel no encontrado para test de memoria",
                    exec_time=time.time() - start_time
                )
                
        except ImportError:
            self.add_result(
                "MEMORY_EFFICIENCY",
                "WARNING",
                "psutil no disponible para test de memoria",
                exec_time=time.time() - start_time
            )
        except Exception as e:
            self.add_result(
                "MEMORY_EFFICIENCY",
                "FAIL",
                f"Error en test de memoria: {e}",
                exec_time=time.time() - start_time
            )

    def run_all_performance_tests(self):
        """Ejecutar todos los tests de performance"""
        logger.info("Iniciando tests de performance...")
        
        self.test_sql_generation_performance()
        self.test_file_io_performance()
        self.test_script_execution_performance()
        self.test_concurrent_file_access()
        self.test_memory_efficiency()
        
        return self.generate_performance_report()

    def generate_performance_report(self):
        """Generar reporte de performance"""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        warnings = sum(1 for r in self.results if r["status"] == "WARNING")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        
        total_execution_time = sum(r["execution_time"] for r in self.results)
        
        return {
            "total_tests": total_tests,
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "pass_rate": round((passed / total_tests) * 100, 1) if total_tests > 0 else 0,
            "total_execution_time": round(total_execution_time, 2),
            "results": self.results
        }

def main():
    """Función principal"""
    validator = PerformanceValidator()
    report = validator.run_all_performance_tests()
    
    print("\n" + "="*60)
    print("VALIDACION DE PERFORMANCE")
    print("="*60)
    
    print(f"Tests Totales: {report['total_tests']}")
    print(f"Pasaron: {report['passed']}")
    print(f"Advertencias: {report['warnings']}")
    print(f"Fallaron: {report['failed']}")
    print(f"Tasa de Exito: {report['pass_rate']}%")
    print(f"Tiempo Total: {report['total_execution_time']}s")
    
    print("\nRESULTADOS DETALLADOS:")
    for result in report["results"]:
        status_symbol = {"PASS": "[OK]", "WARNING": "[WARN]", "FAIL": "[FAIL]"}[result["status"]]
        exec_time = f" ({result['execution_time']:.2f}s)" if result["execution_time"] > 0 else ""
        print(f"{status_symbol} {result['test']}: {result['message']}{exec_time}")
    
    if report["failed"] == 0:
        print("\nPERFORMANCE: VALIDADA CORRECTAMENTE")
        return 0
    else:
        print(f"\nPERFORMANCE: {report['failed']} validaciones fallaron")
        return 1

if __name__ == "__main__":
    exit(main())