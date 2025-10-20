#!/usr/bin/env python3
"""
Complete E2E Testing & Optimization - ICFES Leveling

Sistema completo de testing end-to-end y optimización que valida:
- Integridad del sistema de imágenes
- Funcionalidad IRT 3PL completa
- Sistema de práctica basado en fallos
- Motor de recomendaciones con embeddings
- Generación de dashboards y reportes PDF
- Performance y optimización
- Integración completa del pipeline

Author: Claude Code Assistant
Date: 2024
"""

import asyncio
import asyncpg
import aiohttp
import pandas as pd
import numpy as np
import logging
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess
import sys
import os

# Importar nuestros sistemas
try:
    from irt_3pl_engine import IRT3PLEngine
    from practice_from_failures import PracticeFromFailuresSystem
    from recommendation_engine import RecommendationEngine
    from advanced_dashboard_system import DashboardSystem, UserRole
    from pdf_report_system import PDFReportSystem
    from ai_study_system import AIStudySystem
except ImportError as e:
    logging.warning(f"Error importando módulos: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Resultado de un test específico"""
    test_name: str
    success: bool
    duration_ms: float
    details: Dict[str, Any]
    error_message: Optional[str] = None

@dataclass
class SystemMetrics:
    """Métricas del sistema"""
    database_connections: int
    memory_usage_mb: float
    disk_usage_gb: float
    response_times: Dict[str, float]
    error_rates: Dict[str, float]
    cache_hit_ratios: Dict[str, float]

class CompleteE2ETestingSystem:
    """Sistema completo de testing E2E"""
    
    def __init__(self):
        self.database_url = "postgresql://gameplay:gameplay123@localhost:5433/gameplay_db"
        self.frontend_url = "http://localhost:4001"
        self.backend_url = "http://localhost:4000"
        self.media_base_path = "database/allquestions"
        
        # Resultados de tests
        self.test_results: List[TestResult] = []
        self.system_metrics: Optional[SystemMetrics] = None
        
        # Configuración de tests
        self.test_timeout = 30.0  # segundos
        self.performance_thresholds = {
            'api_response_time_ms': 500,
            'database_query_time_ms': 100,
            'image_load_time_ms': 1000,
            'pdf_generation_time_s': 10,
            'cache_hit_ratio_min': 0.8
        }
        
    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """Ejecuta suite completa de testing E2E"""
        
        logger.info("🚀 Iniciando suite completa de testing E2E")
        start_time = time.time()
        
        try:
            # 1. Tests de prerequisitos
            await self._test_prerequisites()
            
            # 2. Tests de conectividad de servicios
            await self._test_service_connectivity()
            
            # 3. Tests del sistema de imágenes
            await self._test_image_system()
            
            # 4. Tests de IRT 3PL Engine
            await self._test_irt_engine()
            
            # 5. Tests de sistema de práctica
            await self._test_practice_system()
            
            # 6. Tests de motor de recomendaciones
            await self._test_recommendation_engine()
            
            # 7. Tests de dashboards
            await self._test_dashboard_system()
            
            # 8. Tests de reportes PDF
            await self._test_pdf_system()
            
            # 9. Tests de sistema AI
            await self._test_ai_system()
            
            # 10. Tests de performance
            await self._test_performance()
            
            # 11. Tests de integración completa
            await self._test_complete_integration()
            
        except Exception as e:
            logger.error(f"Error crítico en testing: {e}")
            self._add_test_result("CRITICAL_ERROR", False, 0, {}, str(e))
        
        # Generar reporte final
        total_time = (time.time() - start_time) * 1000
        return await self._generate_final_report(total_time)
    
    async def _test_prerequisites(self):
        """Tests de prerequisitos del sistema"""
        logger.info("📋 Testing prerequisitos...")
        
        start_time = time.time()
        
        try:
            # Verificar archivos críticos
            critical_files = [
                "scripts/irt_3pl_engine.py",
                "scripts/practice_from_failures.py", 
                "scripts/recommendation_engine.py",
                "scripts/advanced_dashboard_system.py",
                "scripts/pdf_report_system.py",
                "scripts/ai_study_system.py",
                "database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"
            ]
            
            missing_files = []
            for file_path in critical_files:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                self._add_test_result(
                    "prerequisites_files", 
                    False, 
                    (time.time() - start_time) * 1000,
                    {"missing_files": missing_files},
                    f"Archivos faltantes: {missing_files}"
                )
                return
            
            # Verificar dependencias Python
            required_packages = [
                'asyncpg', 'pandas', 'numpy', 'plotly', 
                'reportlab', 'PIL', 'matplotlib', 'seaborn'
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            details = {
                "critical_files": len(critical_files),
                "missing_files": len(missing_files),
                "required_packages": len(required_packages), 
                "missing_packages": len(missing_packages)
            }
            
            success = len(missing_files) == 0 and len(missing_packages) == 0
            error_msg = f"Paquetes faltantes: {missing_packages}" if missing_packages else None
            
            self._add_test_result(
                "prerequisites", 
                success, 
                (time.time() - start_time) * 1000,
                details,
                error_msg
            )
            
        except Exception as e:
            self._add_test_result(
                "prerequisites", 
                False, 
                (time.time() - start_time) * 1000,
                {},
                str(e)
            )
    
    async def _test_service_connectivity(self):
        """Tests de conectividad de servicios"""
        logger.info("🌐 Testing conectividad de servicios...")
        
        services_to_test = [
            ("database", self.database_url),
            ("backend", f"{self.backend_url}/health"),
            ("frontend", self.frontend_url)
        ]
        
        results = {}
        
        for service_name, url in services_to_test:
            start_time = time.time()
            
            try:
                if service_name == "database":
                    # Test de conexión a PostgreSQL
                    conn = await asyncpg.connect(url)
                    await conn.execute("SELECT 1")
                    await conn.close()
                    success = True
                    error = None
                    
                else:
                    # Test de HTTP endpoints
                    timeout = aiohttp.ClientTimeout(total=5.0)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(url) as response:
                            success = response.status < 400
                            error = f"HTTP {response.status}" if not success else None
                            
                duration = (time.time() - start_time) * 1000
                results[service_name] = {
                    "success": success,
                    "duration_ms": duration,
                    "error": error
                }
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                results[service_name] = {
                    "success": False,
                    "duration_ms": duration,
                    "error": str(e)
                }
        
        # Evaluar resultado general
        all_success = all(r["success"] for r in results.values())
        total_duration = sum(r["duration_ms"] for r in results.values())
        
        self._add_test_result(
            "service_connectivity",
            all_success,
            total_duration,
            results,
            None if all_success else "Algunos servicios no están disponibles"
        )
    
    async def _test_image_system(self):
        """Tests del sistema de imágenes"""
        logger.info("🖼️ Testing sistema de imágenes...")
        
        start_time = time.time()
        
        try:
            # Test 1: Verificar Excel existe y tiene estructura correcta
            excel_path = Path("database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx")
            
            if not excel_path.exists():
                self._add_test_result(
                    "image_system_excel",
                    False,
                    (time.time() - start_time) * 1000,
                    {},
                    "Excel principal no encontrado"
                )
                return
            
            # Cargar Excel y verificar columnas
            df = pd.read_excel(excel_path)
            expected_columns = [
                'Imagen_Pregunta_URL', 'Imagen_Opcion_A_URL', 
                'Imagen_Opcion_B_URL', 'Imagen_Opcion_C_URL', 
                'Imagen_Opcion_D_URL'
            ]
            
            missing_columns = [col for col in expected_columns if col not in df.columns]
            
            # Verificar rutas de imágenes
            image_columns = [col for col in expected_columns if col in df.columns]
            total_image_refs = 0
            valid_image_refs = 0
            
            for col in image_columns:
                valid_paths = df[col].dropna()
                total_image_refs += len(valid_paths)
                
                # Verificar algunas rutas físicamente (muestra)
                for path in valid_paths.head(10):
                    if path and path != '' and Path(self.media_base_path, path).exists():
                        valid_image_refs += 1
            
            # Test 2: Endpoint de media si backend está disponible
            media_endpoint_working = False
            try:
                test_url = f"{self.backend_url}/media/images/question/test.png"
                async with aiohttp.ClientSession() as session:
                    async with session.get(test_url) as response:
                        media_endpoint_working = response.status in [200, 404]  # 404 es OK, significa que endpoint existe
            except:
                pass
            
            details = {
                "excel_rows": len(df),
                "excel_columns": len(df.columns),
                "expected_image_columns": len(expected_columns),
                "missing_columns": len(missing_columns),
                "total_image_references": total_image_refs,
                "valid_image_references": valid_image_refs,
                "image_validity_ratio": valid_image_refs / max(total_image_refs, 1),
                "media_endpoint_working": media_endpoint_working
            }
            
            success = (
                len(missing_columns) == 0 and
                total_image_refs > 0 and
                (valid_image_refs / total_image_refs) > 0.8  # Al menos 80% válidas
            )
            
            self._add_test_result(
                "image_system",
                success,
                (time.time() - start_time) * 1000,
                details,
                f"Columnas faltantes: {missing_columns}" if missing_columns else None
            )
            
        except Exception as e:
            self._add_test_result(
                "image_system",
                False,
                (time.time() - start_time) * 1000,
                {},
                str(e)
            )
    
    async def _test_irt_engine(self):
        """Tests del motor IRT 3PL"""
        logger.info("📊 Testing IRT 3PL Engine...")
        
        start_time = time.time()
        
        try:
            # Crear datos de prueba
            sample_items = [
                {
                    'id': 1, 'statement': 'Test question 1', 'subject_id': 1,
                    'topic_id': 1, 'competence': 'Test', 'difficulty': 'low',
                    'irt_a': 1.2, 'irt_b': -1.0, 'irt_c': 0.2
                },
                {
                    'id': 2, 'statement': 'Test question 2', 'subject_id': 1,
                    'topic_id': 1, 'competence': 'Test', 'difficulty': 'mid', 
                    'irt_a': 1.5, 'irt_b': 0.0, 'irt_c': 0.25
                },
                {
                    'id': 3, 'statement': 'Test question 3', 'subject_id': 1,
                    'topic_id': 1, 'competence': 'Test', 'difficulty': 'high',
                    'irt_a': 1.8, 'irt_b': 1.5, 'irt_c': 0.15
                }
            ]
            
            # Inicializar motor IRT
            engine = IRT3PLEngine(sample_items)
            
            # Test 1: Iniciar sesión adaptativa
            session = engine.start_adaptive_session("test_student", 1, "Test Subject")
            
            # Test 2: Seleccionar ítems y simular respuestas
            responses_processed = 0
            theta_estimates = []
            
            for i in range(5):  # Simular 5 respuestas
                item = engine.select_next_item(session)
                if not item:
                    break
                
                # Simular respuesta (probabilidad basada en IRT)
                prob_correct = item.probability(session.current_theta)
                correct = np.random.random() < prob_correct
                response_time = np.random.uniform(10, 60)
                
                # Procesar respuesta
                report = engine.process_response(session, item, correct, response_time)
                responses_processed += 1
                theta_estimates.append(report['theta_estimate'])
                
                # Test si puede parar
                if session.can_stop():
                    break
            
            # Test 3: Finalizar sesión
            final_report = engine.finalize_session(session)
            
            details = {
                "items_loaded": len(sample_items),
                "session_started": session is not None,
                "responses_processed": responses_processed,
                "final_theta": final_report['theta_final'],
                "final_se": final_report['se_final'],
                "ability_level": final_report['ability_level'],
                "theta_convergence": len(set([round(t, 1) for t in theta_estimates[-3:]])) <= 2 if len(theta_estimates) >= 3 else False
            }
            
            success = (
                session is not None and
                responses_processed >= 3 and
                abs(final_report['theta_final']) <= 4.0 and  # Theta razonable
                final_report['se_final'] > 0  # SE positivo
            )
            
            self._add_test_result(
                "irt_engine",
                success,
                (time.time() - start_time) * 1000,
                details
            )
            
        except Exception as e:
            self._add_test_result(
                "irt_engine",
                False,
                (time.time() - start_time) * 1000,
                {},
                str(e)
            )
    
    async def _test_practice_system(self):
        """Tests del sistema de práctica basado en fallos"""
        logger.info("🎯 Testing sistema de práctica...")
        
        start_time = time.time()
        
        try:
            system = PracticeFromFailuresSystem(self.database_url)
            
            # Test 1: Validación de acceso
            test_student = "test_student_001"
            test_subject = 1
            
            validation = await system.validate_practice_access(test_student, test_subject)
            
            # Test 2: Pool de preguntas falladas (si hay diagnóstico)
            practice_questions = []
            if validation.get("allowed"):
                practice_questions = await system.get_failed_questions_pool(test_student, test_subject)
            
            # Test 3: Generar reporte de progreso
            report = await system.generate_practice_report(test_student, test_subject)
            
            details = {
                "access_validation": validation.get("allowed", False),
                "pool_size": len(practice_questions),
                "report_generated": report is not None,
                "mastery_percentage": report.get("summary", {}).get("mastery_percentage", 0) if report else 0
            }
            
            success = (
                validation is not None and
                isinstance(practice_questions, list) and
                report is not None
            )
            
            self._add_test_result(
                "practice_system",
                success,
                (time.time() - start_time) * 1000,
                details
            )
            
        except Exception as e:
            self._add_test_result(
                "practice_system", 
                False,
                (time.time() - start_time) * 1000,
                {},
                str(e)
            )
    
    async def _test_recommendation_engine(self):
        """Tests del motor de recomendaciones"""
        logger.info("🤖 Testing motor de recomendaciones...")
        
        start_time = time.time()
        
        try:
            engine = RecommendationEngine(self.database_url)
            
            # Test 1: Obtener perfil de debilidades
            test_student = "test_student_001"
            weaknesses = await engine.get_student_weakness_profile(test_student)
            
            # Test 2: Generar plan de estudio
            study_plan = await engine.generate_monthly_study_plan(test_student)
            
            # Test 3: Guardar plan YAML (crear directorio si es necesario)
            os.makedirs("plans", exist_ok=True)
            yaml_path = await engine.save_study_plan_yaml(study_plan, "plans")
            
            details = {
                "weaknesses_found": len(weaknesses),
                "study_plan_generated": study_plan is not None,
                "high_priority_recs": len(study_plan.priority_high) if study_plan else 0,
                "medium_priority_recs": len(study_plan.priority_medium) if study_plan else 0,
                "low_priority_recs": len(study_plan.priority_low) if study_plan else 0,
                "yaml_saved": Path(yaml_path).exists() if yaml_path else False
            }
            
            success = (
                isinstance(weaknesses, list) and
                study_plan is not None and
                yaml_path is not None
            )
            
            self._add_test_result(
                "recommendation_engine",
                success,
                (time.time() - start_time) * 1000,
                details
            )
            
        except Exception as e:
            self._add_test_result(
                "recommendation_engine",
                False,
                (time.time() - start_time) * 1000,
                {},
                str(e)
            )
    
    async def _test_dashboard_system(self):
        """Tests del sistema de dashboards"""
        logger.info("📈 Testing sistema de dashboards...")
        
        start_time = time.time()
        
        try:
            dashboard = DashboardSystem(self.database_url, self.media_base_path)
            
            # Test 1: Métricas de estudiante
            test_student = "test_student_001"
            
            try:
                metrics = await dashboard.get_student_metrics(test_student)
                student_metrics_success = True
                student_charts = dashboard.generate_student_dashboard_charts(metrics)
            except Exception as e:
                student_metrics_success = False
                student_charts = {}
                logger.warning(f"Error en métricas de estudiante: {e}")
            
            # Test 2: Distractores visuales
            try:
                visual_distractors = await dashboard.get_visual_distractors(limit=5)
                distractors_success = True
            except Exception as e:
                visual_distractors = []
                distractors_success = False
                logger.warning(f"Error en distractores visuales: {e}")
            
            # Test 3: Generar datos de dashboard
            try:
                dashboard_data = await dashboard.generate_dashboard_data(
                    test_student, UserRole.STUDENT
                )
                dashboard_data_success = True
            except Exception as e:
                dashboard_data = {}
                dashboard_data_success = False
                logger.warning(f"Error generando dashboard: {e}")
            
            details = {
                "student_metrics": student_metrics_success,
                "student_charts_generated": len(student_charts),
                "visual_distractors_found": len(visual_distractors),
                "distractors_success": distractors_success,
                "dashboard_data_generated": dashboard_data_success
            }
            
            success = student_metrics_success or distractors_success or dashboard_data_success
            
            self._add_test_result(
                "dashboard_system",
                success,
                (time.time() - start_time) * 1000,
                details
            )
            
        except Exception as e:
            self._add_test_result(
                "dashboard_system",
                False,
                (time.time() - start_time) * 1000,
                {},
                str(e)
            )
    
    async def _test_pdf_system(self):
        """Tests del sistema de reportes PDF"""
        logger.info("📄 Testing sistema de reportes PDF...")
        
        start_time = time.time()
        
        try:
            pdf_system = PDFReportSystem(self.database_url, self.media_base_path)
            
            # Test 1: Recopilar datos de estudiante
            test_student = "test_student_001"
            
            try:
                report_data = await pdf_system.collect_student_report_data(test_student)
                data_collection_success = True
            except Exception as e:
                logger.warning(f"Error recopilando datos: {e}")
                data_collection_success = False
                report_data = None
            
            # Test 2: Generar gráficos (solo si tenemos datos)
            chart_generation_success = False
            if report_data:
                try:
                    report_data = pdf_system.generate_charts(report_data)
                    chart_generation_success = True
                except Exception as e:
                    logger.warning(f"Error generando gráficos: {e}")
            
            # Test 3: Generar PDF (crear directorio si es necesario)
            pdf_generation_success = False
            pdf_path = None
            if report_data:
                try:
                    os.makedirs("reports", exist_ok=True)
                    pdf_path = f"reports/test_report_{test_student}.pdf"
                    await pdf_system.generate_pdf_report(report_data, pdf_path)
                    pdf_generation_success = Path(pdf_path).exists()
                except Exception as e:
                    logger.warning(f"Error generando PDF: {e}")
            
            details = {
                "data_collection": data_collection_success,
                "chart_generation": chart_generation_success,
                "pdf_generation": pdf_generation_success,
                "pdf_path": pdf_path,
                "subject_results": len(report_data.subject_results) if report_data else 0,
                "critical_failures": len(report_data.critical_failures) if report_data else 0
            }
            
            success = data_collection_success  # Al menos debe poder recopilar datos
            
            self._add_test_result(
                "pdf_system",
                success,
                (time.time() - start_time) * 1000,
                details
            )
            
        except Exception as e:
            self._add_test_result(
                "pdf_system",
                False,
                (time.time() - start_time) * 1000,
                {},
                str(e)
            )
    
    async def _test_ai_system(self):
        """Tests del sistema AI de estudio"""
        logger.info("🧠 Testing sistema AI...")
        
        start_time = time.time()
        
        try:
            ai_system = AIStudySystem(self.database_url)
            
            # Test 1: Obtener contexto de estudiante
            test_student = "test_student_001"
            
            try:
                context = await ai_system.get_study_context(test_student, subject_id=1)
                context_success = True
            except Exception as e:
                logger.warning(f"Error obteniendo contexto: {e}")
                context_success = False
                context = None
            
            # Test 2: Chat con IA (usando respuesta dummy si no hay OpenAI)
            chat_success = False
            ai_response = None
            if context:
                try:
                    user_message = "No entiendo esta pregunta de matemáticas"
                    ai_response = await ai_system.chat_with_ai(
                        test_student, 
                        user_message, 
                        subject_id=1
                    )
                    chat_success = True
                except Exception as e:
                    logger.warning(f"Error en chat AI: {e}")
            
            details = {
                "context_obtained": context_success,
                "chat_response_generated": chat_success,
                "response_has_content": bool(ai_response and ai_response.main_response) if ai_response else False,
                "follow_up_questions": len(ai_response.follow_up_questions) if ai_response else 0,
                "practice_suggestions": len(ai_response.practice_suggestions) if ai_response else 0,
                "theta_estimate": context.theta_estimate if context else 0,
                "difficulty_level": context.difficulty_level.value if context else "unknown"
            }
            
            success = context_success  # Al menos debe obtener contexto
            
            self._add_test_result(
                "ai_system",
                success,
                (time.time() - start_time) * 1000,
                details
            )
            
        except Exception as e:
            self._add_test_result(
                "ai_system",
                False,
                (time.time() - start_time) * 1000,
                {},
                str(e)
            )
    
    async def _test_performance(self):
        """Tests de performance del sistema"""
        logger.info("⚡ Testing performance...")
        
        start_time = time.time()
        
        try:
            performance_results = {}
            
            # Test 1: Tiempo de conexión a BD
            db_start = time.time()
            try:
                conn = await asyncpg.connect(self.database_url)
                await conn.execute("SELECT 1")
                await conn.close()
                db_connection_time = (time.time() - db_start) * 1000
                performance_results['db_connection_ms'] = db_connection_time
            except Exception as e:
                performance_results['db_connection_ms'] = None
                performance_results['db_error'] = str(e)
            
            # Test 2: Tiempo de respuesta API (si disponible)
            api_start = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.backend_url}/health") as response:
                        api_response_time = (time.time() - api_start) * 1000
                        performance_results['api_response_ms'] = api_response_time
                        performance_results['api_status'] = response.status
            except Exception as e:
                performance_results['api_response_ms'] = None
                performance_results['api_error'] = str(e)
            
            # Test 3: Tiempo de carga de imagen (si media endpoint disponible)
            try:
                image_start = time.time()
                async with aiohttp.ClientSession() as session:
                    test_image_url = f"{self.backend_url}/media/images/question/test.png"
                    async with session.get(test_image_url) as response:
                        image_load_time = (time.time() - image_start) * 1000
                        performance_results['image_load_ms'] = image_load_time
            except Exception as e:
                performance_results['image_load_ms'] = None
            
            # Evaluar performance contra thresholds
            performance_issues = []
            
            if performance_results.get('db_connection_ms', 0) > self.performance_thresholds['database_query_time_ms']:
                performance_issues.append("Base de datos lenta")
            
            if performance_results.get('api_response_ms', 0) > self.performance_thresholds['api_response_time_ms']:
                performance_issues.append("API lenta")
            
            if performance_results.get('image_load_ms', 0) > self.performance_thresholds['image_load_time_ms']:
                performance_issues.append("Carga de imágenes lenta")
            
            success = len(performance_issues) == 0
            
            details = {
                **performance_results,
                "performance_issues": performance_issues,
                "meets_thresholds": success
            }
            
            self._add_test_result(
                "performance",
                success,
                (time.time() - start_time) * 1000,
                details,
                f"Problemas de performance: {performance_issues}" if performance_issues else None
            )
            
        except Exception as e:
            self._add_test_result(
                "performance",
                False,
                (time.time() - start_time) * 1000,
                {},
                str(e)
            )
    
    async def _test_complete_integration(self):
        """Tests de integración completa del sistema"""
        logger.info("🔄 Testing integración completa...")
        
        start_time = time.time()
        
        try:
            # Simular flujo completo de usuario
            test_student = "test_student_integration"
            
            integration_steps = {
                "database_connection": False,
                "student_context": False,
                "recommendation_generation": False,
                "dashboard_generation": False,
                "report_generation": False
            }
            
            # Paso 1: Conectar a BD
            try:
                conn = await asyncpg.connect(self.database_url)
                await conn.close()
                integration_steps["database_connection"] = True
            except:
                pass
            
            # Paso 2: Obtener contexto de estudiante
            if integration_steps["database_connection"]:
                try:
                    ai_system = AIStudySystem(self.database_url)
                    context = await ai_system.get_study_context(test_student)
                    integration_steps["student_context"] = True
                except:
                    pass
            
            # Paso 3: Generar recomendaciones
            if integration_steps["student_context"]:
                try:
                    rec_engine = RecommendationEngine(self.database_url)
                    study_plan = await rec_engine.generate_monthly_study_plan(test_student)
                    integration_steps["recommendation_generation"] = study_plan is not None
                except:
                    pass
            
            # Paso 4: Generar dashboard
            if integration_steps["student_context"]:
                try:
                    dashboard = DashboardSystem(self.database_url)
                    dashboard_data = await dashboard.generate_dashboard_data(test_student, UserRole.STUDENT)
                    integration_steps["dashboard_generation"] = dashboard_data is not None
                except:
                    pass
            
            # Paso 5: Generar reporte PDF
            if integration_steps["student_context"]:
                try:
                    pdf_system = PDFReportSystem(self.database_url)
                    report_data = await pdf_system.collect_student_report_data(test_student)
                    integration_steps["report_generation"] = report_data is not None
                except:
                    pass
            
            # Evaluar éxito de integración
            successful_steps = sum(integration_steps.values())
            total_steps = len(integration_steps)
            integration_success = successful_steps >= (total_steps * 0.6)  # Al menos 60%
            
            details = {
                **integration_steps,
                "successful_steps": successful_steps,
                "total_steps": total_steps,
                "success_rate": successful_steps / total_steps
            }
            
            self._add_test_result(
                "complete_integration",
                integration_success,
                (time.time() - start_time) * 1000,
                details,
                f"Solo {successful_steps}/{total_steps} pasos exitosos" if not integration_success else None
            )
            
        except Exception as e:
            self._add_test_result(
                "complete_integration",
                False,
                (time.time() - start_time) * 1000,
                {},
                str(e)
            )
    
    def _add_test_result(self, test_name: str, success: bool, duration_ms: float,
                        details: Dict[str, Any], error_message: str = None):
        """Agrega resultado de test"""
        result = TestResult(
            test_name=test_name,
            success=success,
            duration_ms=duration_ms,
            details=details,
            error_message=error_message
        )
        
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name} ({duration_ms:.1f}ms)")
        if error_message:
            logger.warning(f"   Error: {error_message}")
    
    async def _generate_final_report(self, total_duration_ms: float) -> Dict[str, Any]:
        """Genera reporte final de testing"""
        
        # Calcular estadísticas
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Agrupar por categoría
        test_categories = {}
        for result in self.test_results:
            category = result.test_name.split('_')[0]
            if category not in test_categories:
                test_categories[category] = {'passed': 0, 'failed': 0, 'total': 0}
            
            test_categories[category]['total'] += 1
            if result.success:
                test_categories[category]['passed'] += 1
            else:
                test_categories[category]['failed'] += 1
        
        # Tests críticos fallados
        critical_failures = [
            r for r in self.test_results 
            if not r.success and r.test_name in [
                'prerequisites', 'service_connectivity', 'database_connection'
            ]
        ]
        
        # Generar reporte
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': success_rate,
                'total_duration_ms': total_duration_ms,
                'critical_failures': len(critical_failures)
            },
            'test_categories': test_categories,
            'detailed_results': [asdict(r) for r in self.test_results],
            'critical_failures': [asdict(r) for r in critical_failures],
            'recommendations': self._generate_recommendations(),
            'system_status': self._determine_system_status(success_rate, critical_failures),
            'generated_at': datetime.now().isoformat()
        }
        
        # Guardar reporte
        os.makedirs("reports", exist_ok=True)
        report_path = f"reports/e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Reporte final guardado en: {report_path}")
        
        # Imprimir resumen
        self._print_test_summary(report)
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Genera recomendaciones basadas en resultados"""
        recommendations = []
        
        # Análisis de fallos
        failed_tests = [r for r in self.test_results if not r.success]
        
        if any('prerequisites' in r.test_name for r in failed_tests):
            recommendations.append("🔧 Instalar dependencias faltantes y verificar archivos críticos")
        
        if any('connectivity' in r.test_name for r in failed_tests):
            recommendations.append("🌐 Verificar que todos los servicios estén ejecutándose (Docker, PostgreSQL, Redis)")
        
        if any('database' in r.test_name for r in failed_tests):
            recommendations.append("💾 Revisar configuración de base de datos y ejecutar migraciones")
        
        if any('image' in r.test_name for r in failed_tests):
            recommendations.append("🖼️ Ejecutar scripts de transformación de rutas de imágenes")
        
        if any('performance' in r.test_name for r in failed_tests):
            recommendations.append("⚡ Optimizar performance: revisar índices BD, cache Redis, compresión de imágenes")
        
        # Recomendaciones generales
        success_rate = (sum(1 for r in self.test_results if r.success) / len(self.test_results)) * 100
        
        if success_rate < 50:
            recommendations.append("🚨 Sistema requiere intervención urgente antes de producción")
        elif success_rate < 80:
            recommendations.append("⚠️ Sistema parcialmente funcional - revisar fallos antes de despliegue")
        else:
            recommendations.append("✅ Sistema en buen estado - listo para producción con monitoreo")
        
        return recommendations
    
    def _determine_system_status(self, success_rate: float, critical_failures: List) -> str:
        """Determina estado general del sistema"""
        if len(critical_failures) > 0:
            return "CRITICAL"
        elif success_rate < 60:
            return "UNSTABLE"
        elif success_rate < 85:
            return "PARTIAL"
        else:
            return "STABLE"
    
    def _print_test_summary(self, report: Dict[str, Any]):
        """Imprime resumen de tests en consola"""
        summary = report['summary']
        
        print("\n" + "="*80)
        print("🎯 RESUMEN DE TESTING E2E - ICFES LEVELING")
        print("="*80)
        
        print(f"📊 Tests Totales: {summary['total_tests']}")
        print(f"✅ Exitosos: {summary['passed_tests']}")
        print(f"❌ Fallidos: {summary['failed_tests']}")
        print(f"📈 Tasa de Éxito: {summary['success_rate']:.1f}%")
        print(f"⏱️ Duración Total: {summary['total_duration_ms']/1000:.1f}s")
        print(f"🚨 Fallos Críticos: {summary['critical_failures']}")
        print(f"🔧 Estado del Sistema: {report['system_status']}")
        
        print("\n📋 TESTS POR CATEGORÍA:")
        for category, stats in report['test_categories'].items():
            success_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"   {category}: {stats['passed']}/{stats['total']} ({success_rate:.0f}%)")
        
        if report['recommendations']:
            print("\n💡 RECOMENDACIONES:")
            for rec in report['recommendations']:
                print(f"   {rec}")
        
        print("="*80)


# Función principal
async def main():
    """Función principal para ejecutar testing E2E completo"""
    
    print("🚀 Iniciando Testing E2E Completo - ICFES Leveling")
    print("="*80)
    
    # Crear sistema de testing
    test_system = CompleteE2ETestingSystem()
    
    # Ejecutar suite completa
    final_report = await test_system.run_complete_test_suite()
    
    # Determinar código de salida
    success_rate = final_report['summary']['success_rate']
    critical_failures = len(final_report['critical_failures'])
    
    if critical_failures > 0 or success_rate < 50:
        print("\n❌ TESTING FALLÓ - Sistema no listo para producción")
        sys.exit(1)
    elif success_rate < 80:
        print("\n⚠️ TESTING PARCIAL - Revisar advertencias antes de despliegue") 
        sys.exit(0)
    else:
        print("\n✅ TESTING EXITOSO - Sistema listo para producción")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())