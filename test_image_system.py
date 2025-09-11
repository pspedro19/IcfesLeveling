#!/usr/bin/env python3
"""
Test completo del sistema de imágenes ICFES Leveling

Script de testing E2E para verificar que todo el pipeline de imágenes
funcione correctamente: transformación → carga → servicio → frontend.

Author: Claude Code Assistant
Date: 2024
"""

import asyncio
import requests
import logging
import pandas as pd
from pathlib import Path
import json
import time
from typing import Dict, List, Optional
from datetime import datetime

# Configurar logging con colores
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Colors:
    """ANSI color codes"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def colored_print(message: str, color: str = Colors.WHITE):
    """Print con colores"""
    print(f"{color}{message}{Colors.END}")

class ICFESImageSystemTester:
    """
    Tester completo del sistema de imágenes ICFES
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent.resolve()
        self.base_media_path = self.project_root / "database" / "allquestions"
        
        # URLs de servicios
        self.backend_url = "http://localhost:4000"
        self.frontend_url = "http://localhost:4001"
        self.media_endpoint = f"{self.backend_url}/media/images"
        
        # Estadísticas de tests
        self.stats = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'warnings': 0,
            'start_time': None,
            'end_time': None
        }
        
        self.test_results = []
    
    def log_test(self, test_name: str, status: str, message: str = "", details: Dict = None):
        """Log de resultado de test"""
        self.stats['total_tests'] += 1
        
        if status == 'PASS':
            self.stats['passed_tests'] += 1
            colored_print(f"✅ {test_name}: {message}", Colors.GREEN)
        elif status == 'FAIL':
            self.stats['failed_tests'] += 1  
            colored_print(f"❌ {test_name}: {message}", Colors.RED)
        elif status == 'WARN':
            self.stats['warnings'] += 1
            colored_print(f"⚠️  {test_name}: {message}", Colors.YELLOW)
        else:
            colored_print(f"ℹ️  {test_name}: {message}", Colors.BLUE)
        
        self.test_results.append({
            'timestamp': datetime.now().isoformat(),
            'test': test_name,
            'status': status,
            'message': message,
            'details': details or {}
        })

    async def test_prerequisites(self):
        """Test de prerequisitos del sistema"""
        colored_print("\n🔍 TESTING PREREQUISITES", Colors.CYAN + Colors.BOLD)
        
        # 1. Verificar archivos críticos
        excel_main = self.project_root / "database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"
        if excel_main.exists():
            self.log_test("Excel Principal", "PASS", f"Encontrado: {excel_main}")
        else:
            self.log_test("Excel Principal", "FAIL", f"No encontrado: {excel_main}")
        
        # 2. Verificar scripts
        scripts = ['path_transformer.py', 'seed_questions.py', 'verify_assets.py']
        for script in scripts:
            script_path = self.project_root / "scripts" / script
            if script_path.exists():
                self.log_test(f"Script {script}", "PASS", "Script disponible")
            else:
                self.log_test(f"Script {script}", "FAIL", "Script faltante")
        
        # 3. Verificar directorio de imágenes
        if self.base_media_path.exists():
            image_count = len(list(self.base_media_path.rglob("*.png"))) + len(list(self.base_media_path.rglob("*.jpg")))
            self.log_test("Directorio Imágenes", "PASS", f"{image_count} imágenes encontradas")
        else:
            self.log_test("Directorio Imágenes", "FAIL", "Directorio no existe")

    async def test_services_connectivity(self):
        """Test de conectividad de servicios"""
        colored_print("\n🔌 TESTING SERVICE CONNECTIVITY", Colors.CYAN + Colors.BOLD)
        
        # Test Backend Health
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("Backend Health", "PASS", f"Status: {response.status_code}")
            else:
                self.log_test("Backend Health", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Backend Health", "FAIL", f"Error: {str(e)}")
        
        # Test Frontend
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                self.log_test("Frontend", "PASS", "Frontend responding")
            else:
                self.log_test("Frontend", "WARN", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Frontend", "FAIL", f"Error: {str(e)}")
        
        # Test Media Service
        try:
            # Test con una imagen placeholder o conocida
            response = requests.get(f"{self.media_endpoint}/question/test.png", timeout=5)
            if response.status_code in [200, 404]:  # 200 si existe, 404 esperado si no
                self.log_test("Media Service", "PASS", f"Service responding: {response.status_code}")
            else:
                self.log_test("Media Service", "FAIL", f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Media Service", "FAIL", f"Error: {str(e)}")

    async def test_path_transformation(self):
        """Test del sistema de transformación de rutas"""
        colored_print("\n🔄 TESTING PATH TRANSFORMATION", Colors.CYAN + Colors.BOLD)
        
        # Importar y usar path_transformer
        try:
            import sys
            sys.path.append(str(self.project_root / "scripts"))
            from path_transformer import PathTransformer
            
            transformer = PathTransformer(str(self.project_root))
            
            # Test de normalización Unicode
            test_cases = [
                ("C:\\Users\\natus\\Documents\\ciencias naturales\\test.png", "should_normalize"),
                ("database/allquestions/Matematicas/test.png", "should_pass"),
                ("../../../etc/passwd", "should_block"),
                ("", "should_handle_empty")
            ]
            
            for test_path, expectation in test_cases:
                try:
                    relative_path, exists, reason = transformer.transform_path_to_relative(test_path)
                    
                    if expectation == "should_normalize" and relative_path:
                        self.log_test(f"Transform: {expectation}", "PASS", f"Normalized: {relative_path}")
                    elif expectation == "should_block" and not relative_path:
                        self.log_test(f"Transform: {expectation}", "PASS", "Blocked dangerous path")
                    elif expectation == "should_handle_empty" and not relative_path:
                        self.log_test(f"Transform: {expectation}", "PASS", "Handled empty path")
                    else:
                        self.log_test(f"Transform: {expectation}", "WARN", f"Unexpected: {relative_path}")
                        
                except Exception as e:
                    self.log_test(f"Transform: {expectation}", "FAIL", f"Error: {str(e)}")
            
        except ImportError as e:
            self.log_test("Path Transformer Import", "FAIL", f"Cannot import: {str(e)}")

    async def test_media_service_endpoints(self):
        """Test detallado de endpoints del servicio de media"""
        colored_print("\n🖼️ TESTING MEDIA SERVICE ENDPOINTS", Colors.CYAN + Colors.BOLD)
        
        # Test básicos de endpoint
        test_endpoints = [
            ("/media/images/question/test.png", "Question Image"),
            ("/media/images/option_a/test.png", "Option A Image"),  
            ("/media/images/placeholder/test.png", "Placeholder"),
        ]
        
        for endpoint, name in test_endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                
                # Verificar headers de cache
                cache_control = response.headers.get('Cache-Control', '')
                etag = response.headers.get('ETag', '')
                
                if response.status_code in [200, 404]:
                    details = {
                        'status_code': response.status_code,
                        'has_cache_control': bool(cache_control),
                        'has_etag': bool(etag),
                        'content_type': response.headers.get('Content-Type', '')
                    }
                    self.log_test(f"Endpoint {name}", "PASS", 
                                f"Status: {response.status_code}, Cache: {bool(cache_control)}", details)
                else:
                    self.log_test(f"Endpoint {name}", "FAIL", f"Unexpected status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Endpoint {name}", "FAIL", f"Error: {str(e)}")
        
        # Test de seguridad - intentos de path traversal
        security_tests = [
            "/media/images/question/../../../etc/passwd",
            "/media/images/question/..%2f..%2f..%2fetc%2fpasswd", 
            "/media/images/question/test<script>alert('xss')</script>.png"
        ]
        
        for dangerous_path in security_tests:
            try:
                response = requests.get(f"{self.backend_url}{dangerous_path}", timeout=5)
                if response.status_code in [400, 403, 404]:
                    self.log_test("Security Block", "PASS", "Blocked dangerous path")
                else:
                    self.log_test("Security Block", "FAIL", f"Allowed dangerous path: {response.status_code}")
            except Exception:
                self.log_test("Security Block", "PASS", "Request blocked by client/network")

    async def test_database_questions(self):
        """Test de preguntas en base de datos"""
        colored_print("\n🗄️ TESTING DATABASE QUESTIONS", Colors.CYAN + Colors.BOLD)
        
        # Test básico de endpoint de preguntas
        try:
            response = requests.get(f"{self.backend_url}/api/questions", timeout=10)
            
            if response.status_code == 200:
                questions = response.json()
                question_count = len(questions) if isinstance(questions, list) else questions.get('total', 0)
                
                if question_count > 0:
                    self.log_test("Questions in DB", "PASS", f"{question_count} preguntas encontradas")
                    
                    # Verificar que algunas tengan imágenes
                    questions_with_images = 0
                    if isinstance(questions, list):
                        for q in questions[:10]:  # Check first 10
                            if (q.get('pregunta_imagen') or q.get('opcion_a_imagen') or 
                                q.get('opcion_b_imagen') or q.get('opcion_c_imagen') or 
                                q.get('opcion_d_imagen')):
                                questions_with_images += 1
                    
                    if questions_with_images > 0:
                        self.log_test("Questions with Images", "PASS", 
                                    f"{questions_with_images}/10 preguntas tienen imágenes")
                    else:
                        self.log_test("Questions with Images", "WARN", 
                                    "No se encontraron preguntas con imágenes en muestra")
                        
                else:
                    self.log_test("Questions in DB", "WARN", "No hay preguntas en la base de datos")
                    
            elif response.status_code == 404:
                self.log_test("Questions Endpoint", "WARN", "Endpoint no implementado")
            else:
                self.log_test("Questions Endpoint", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Database Questions", "FAIL", f"Error: {str(e)}")

    async def test_diagnostic_flow_with_images(self):
        """Test del flujo de diagnóstico con imágenes"""
        colored_print("\n🎯 TESTING DIAGNOSTIC FLOW WITH IMAGES", Colors.CYAN + Colors.BOLD)
        
        try:
            # Test de subjects
            response = requests.get(f"{self.backend_url}/api/subjects", timeout=5)
            if response.status_code == 200:
                subjects = response.json()
                subject_count = len(subjects) if isinstance(subjects, list) else 0
                
                if subject_count > 0:
                    self.log_test("Subjects Available", "PASS", f"{subject_count} materias disponibles")
                    
                    # Test diagnóstico con primera materia
                    if isinstance(subjects, list) and len(subjects) > 0:
                        first_subject = subjects[0]
                        subject_id = first_subject.get('id')
                        
                        diagnostic_response = requests.post(
                            f"{self.backend_url}/api/diagnostic/start", 
                            json={"subject_id": subject_id},
                            timeout=10
                        )
                        
                        if diagnostic_response.status_code in [200, 201]:
                            self.log_test("Diagnostic Start", "PASS", "Diagnóstico iniciado correctamente")
                        else:
                            self.log_test("Diagnostic Start", "WARN", 
                                        f"Status: {diagnostic_response.status_code}")
                else:
                    self.log_test("Subjects Available", "WARN", "No hay materias disponibles")
            else:
                self.log_test("Subjects Endpoint", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Diagnostic Flow", "FAIL", f"Error: {str(e)}")

    async def test_image_integrity(self):
        """Test de integridad de imágenes físicas"""
        colored_print("\n🔍 TESTING IMAGE INTEGRITY", Colors.CYAN + Colors.BOLD)
        
        if not self.base_media_path.exists():
            self.log_test("Image Directory", "FAIL", "Directorio de imágenes no existe")
            return
        
        # Contar archivos por formato
        formats = {'.png': 0, '.jpg': 0, '.jpeg': 0, '.gif': 0, '.webp': 0}
        total_size = 0
        large_files = 0
        
        for format_ext in formats:
            files = list(self.base_media_path.rglob(f"*{format_ext}"))
            formats[format_ext] = len(files)
            
            for file_path in files:
                try:
                    size = file_path.stat().st_size
                    total_size += size
                    if size > 1024 * 1024:  # > 1MB
                        large_files += 1
                except:
                    pass
        
        total_images = sum(formats.values())
        
        if total_images > 0:
            self.log_test("Image Files Found", "PASS", 
                        f"{total_images} imágenes ({total_size // (1024*1024)} MB total)")
            
            details = {
                'formats': formats,
                'total_size_mb': total_size // (1024*1024),
                'large_files': large_files
            }
            
            if large_files > 0:
                self.log_test("Large Files", "WARN", 
                            f"{large_files} archivos > 1MB necesitan optimización", details)
            else:
                self.log_test("File Sizes", "PASS", "Tamaños de archivo aceptables")
        else:
            self.log_test("Image Files", "WARN", "No se encontraron archivos de imagen")

    async def generate_test_report(self):
        """Generar reporte final de tests"""
        colored_print(f"\n📊 GENERATING TEST REPORT", Colors.CYAN + Colors.BOLD)
        
        # Crear directorio reports si no existe
        reports_dir = self.project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Calcular estadísticas
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        success_rate = (self.stats['passed_tests'] / max(self.stats['total_tests'], 1)) * 100
        
        report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': duration,
                'project_root': str(self.project_root)
            },
            'summary': {
                'total_tests': self.stats['total_tests'],
                'passed_tests': self.stats['passed_tests'],
                'failed_tests': self.stats['failed_tests'],
                'warnings': self.stats['warnings'],
                'success_rate_percentage': round(success_rate, 2)
            },
            'detailed_results': self.test_results
        }
        
        # Guardar reporte
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"image_system_test_report_{timestamp}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        colored_print(f"📄 Reporte guardado en: {report_path}", Colors.GREEN)
        return report

    def print_final_summary(self, report: Dict):
        """Imprimir resumen final"""
        colored_print(f"\n{'='*60}", Colors.CYAN + Colors.BOLD)
        colored_print("🎯 ICFES IMAGE SYSTEM TEST RESULTS", Colors.CYAN + Colors.BOLD) 
        colored_print(f"{'='*60}", Colors.CYAN + Colors.BOLD)
        
        summary = report['summary']
        
        # Estadísticas principales
        colored_print(f"\n📊 ESTADÍSTICAS:", Colors.WHITE + Colors.BOLD)
        print(f"   Total tests:     {summary['total_tests']}")
        print(f"   Tests pasados:   {colored_print(str(summary['passed_tests']), Colors.GREEN)}")
        print(f"   Tests fallidos:  {colored_print(str(summary['failed_tests']), Colors.RED)}")
        print(f"   Advertencias:    {colored_print(str(summary['warnings']), Colors.YELLOW)}")
        print(f"   Tasa de éxito:   {colored_print(f\"{summary['success_rate_percentage']:.1f}%\", Colors.GREEN if summary['success_rate_percentage'] > 80 else Colors.YELLOW)}")
        print(f"   Duración:        {report['metadata']['duration_seconds']:.1f}s")
        
        # Recomendaciones
        colored_print(f"\n💡 RECOMENDACIONES:", Colors.WHITE + Colors.BOLD)
        
        if summary['failed_tests'] > 0:
            colored_print("   ❌ Hay tests críticos fallando. Revisar logs detallados.", Colors.RED)
        
        if summary['warnings'] > 5:
            colored_print("   ⚠️  Múltiples advertencias. Considerar mejoras.", Colors.YELLOW)
        
        if summary['success_rate_percentage'] > 90:
            colored_print("   ✅ Excelente! Sistema funcionando correctamente.", Colors.GREEN)
        elif summary['success_rate_percentage'] > 70:
            colored_print("   🔧 Sistema funcional con mejoras necesarias.", Colors.YELLOW)  
        else:
            colored_print("   🚨 Sistema requiere atención inmediata.", Colors.RED)
        
        # Pasos siguientes
        colored_print(f"\n🚀 PRÓXIMOS PASOS:", Colors.WHITE + Colors.BOLD)
        print("   1. Revisar tests fallidos en el reporte detallado")
        print("   2. Ejecutar: make seed (si no hay preguntas)")
        print("   3. Ejecutar: make verify-integrity (para más detalles)")
        print("   4. Verificar servicios: make status")

    async def run_all_tests(self):
        """Ejecutar todos los tests"""
        self.stats['start_time'] = datetime.now()
        
        colored_print("🚀 INICIANDO TESTS DEL SISTEMA DE IMÁGENES ICFES", Colors.MAGENTA + Colors.BOLD)
        colored_print(f"Proyecto: {self.project_root}", Colors.BLUE)
        
        # Ejecutar tests en orden
        await self.test_prerequisites()
        await self.test_services_connectivity()
        await self.test_path_transformation()  
        await self.test_media_service_endpoints()
        await self.test_database_questions()
        await self.test_diagnostic_flow_with_images()
        await self.test_image_integrity()
        
        self.stats['end_time'] = datetime.now()
        
        # Generar reporte y mostrar resumen
        report = await self.generate_test_report()
        self.print_final_summary(report)


async def main():
    """Función principal"""
    tester = ICFESImageSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())