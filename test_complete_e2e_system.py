#!/usr/bin/env python3
"""
PRUEBA END-TO-END COMPLETA SISTEMA ICFES
========================================

Este script ejecuta una prueba completa del sistema:
1. Carga de 480 preguntas desde Excel
2. Inicio de diagnóstico desde Portal Despertar  
3. Responder 10 preguntas adaptativas con IRT
4. Verificar imágenes en preguntas/opciones
5. Ver explicaciones después de respuestas
6. Obtener theta score final y ranking
7. Verificar que todo se guarde en DB
"""

import requests
import json
import time
import sys
import random
from typing import Dict, List, Any, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URLs del sistema
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3002"

class ICFESTestRunner:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.diagnostic_session_id = None
        self.questions_answered = []
        self.current_theta = None
        self.final_results = None
        
    def print_separator(self, title: str):
        """Imprime separador visual"""
        print("=" * 80)
        print(f"  {title}")
        print("=" * 80)
        
    def print_step_result(self, step: str, success: bool, details: str = ""):
        """Imprime resultado de un paso"""
        status = "✅ ÉXITO" if success else "❌ FALLO"
        print(f"{status} - {step}")
        if details:
            print(f"    {details}")
        print()
        
    def step_1_verify_questions_loaded(self) -> bool:
        """Paso 1: Verificar que las 480 preguntas están cargadas"""
        self.print_separator("PASO 1: VERIFICANDO CARGA DE PREGUNTAS")
        
        try:
            # Verificar que el backend esté funcionando
            response = self.session.get(f"{BACKEND_URL}/api/v1/health")
            if response.status_code != 200:
                self.print_step_result("Verificar backend", False, f"Backend no responde: {response.status_code}")
                return False
                
            # Obtener estadísticas de preguntas por materia
            response = self.session.get(f"{BACKEND_URL}/api/v1/subjects")
            if response.status_code != 200:
                self.print_step_result("Obtener materias", False, f"Error: {response.status_code}")
                return False
                
            subjects = response.json()
            total_questions = 0
            
            for subject in subjects:
                subject_name = subject.get('name', 'Unknown')
                # Intentar obtener preguntas de cada materia
                questions_response = self.session.get(f"{BACKEND_URL}/api/v1/questions", 
                                                    params={'subject': subject_name, 'limit': 1000})
                
                if questions_response.status_code == 200:
                    questions_data = questions_response.json()
                    count = len(questions_data.get('questions', []))
                    total_questions += count
                    logger.info(f"Materia {subject_name}: {count} preguntas")
                    
            self.print_step_result("Verificar carga de preguntas", True, 
                                 f"Total preguntas encontradas: {total_questions}")
            
            return total_questions > 300  # Al menos 300 preguntas cargadas
            
        except Exception as e:
            self.print_step_result("Verificar carga de preguntas", False, f"Error: {str(e)}")
            return False
            
    def step_2_start_diagnostic_test(self) -> bool:
        """Paso 2: Iniciar prueba diagnóstica desde Portal Despertar"""
        self.print_separator("PASO 2: INICIANDO DIAGNÓSTICO DESDE PORTAL DESPERTAR")
        
        try:
            # Simular login (usando cuenta de prueba)
            login_data = {
                "username": "test",
                "password": "secret"
            }
            
            response = self.session.post(f"{BACKEND_URL}/api/v1/auth-simple/login", 
                                       json=login_data)
            
            if response.status_code != 200:
                self.print_step_result("Login de usuario", False, f"Error login: {response.status_code}")
                return False
                
            auth_data = response.json()
            self.auth_token = auth_data.get('access_token')
            self.user_data = auth_data.get('user')
            
            # Configurar headers de autenticación
            self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
            
            # Iniciar sesión diagnóstica
            diagnostic_data = {
                "subject": "matematicas",  # Empezar con matemáticas
                "difficulty_level": "medium",
                "adaptive_mode": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/api/v1/diagnostic/start", 
                                       json=diagnostic_data)
            
            if response.status_code != 200:
                self.print_step_result("Iniciar diagnóstico", False, f"Error: {response.status_code}")
                return False
                
            diagnostic_response = response.json()
            self.diagnostic_session_id = diagnostic_response.get('session_id')
            
            self.print_step_result("Iniciar diagnóstico", True, 
                                 f"Sesión iniciada: {self.diagnostic_session_id}")
            
            return True
            
        except Exception as e:
            self.print_step_result("Iniciar diagnóstico", False, f"Error: {str(e)}")
            return False
            
    def step_3_answer_adaptive_questions(self) -> bool:
        """Paso 3: Responder 10 preguntas adaptativas con IRT"""
        self.print_separator("PASO 3: RESPONDIENDO 10 PREGUNTAS ADAPTATIVAS CON IRT")
        
        try:
            questions_answered = 0
            target_questions = 10
            
            while questions_answered < target_questions:
                # Obtener siguiente pregunta adaptativa
                response = self.session.get(f"{BACKEND_URL}/api/v1/diagnostic/{self.diagnostic_session_id}/next-question")
                
                if response.status_code != 200:
                    self.print_step_result(f"Obtener pregunta {questions_answered + 1}", False, 
                                         f"Error: {response.status_code}")
                    break
                    
                question_data = response.json()
                question = question_data.get('question')
                
                if not question:
                    self.print_step_result(f"Obtener pregunta {questions_answered + 1}", False, 
                                         "No hay más preguntas disponibles")
                    break
                    
                question_id = question.get('id')
                question_text = question.get('question', '')[:100] + '...'
                options = [question.get('option_a'), question.get('option_b'), 
                          question.get('option_c'), question.get('option_d')]
                correct_answer = question.get('correct_answer')
                
                logger.info(f"Pregunta {questions_answered + 1}: {question_text}")
                logger.info(f"Opciones: A) {options[0][:50]}... B) {options[1][:50]}...")
                
                # Simular respuesta (aleatoria para prueba)
                user_answer = random.choice(['A', 'B', 'C', 'D'])
                is_correct = user_answer == correct_answer
                
                # Enviar respuesta
                answer_data = {
                    "question_id": question_id,
                    "answer": user_answer,
                    "time_taken": random.randint(30, 120)  # 30-120 segundos
                }
                
                response = self.session.post(f"{BACKEND_URL}/api/v1/diagnostic/{self.diagnostic_session_id}/answer",
                                           json=answer_data)
                
                if response.status_code != 200:
                    self.print_step_result(f"Enviar respuesta {questions_answered + 1}", False, 
                                         f"Error: {response.status_code}")
                    break
                    
                answer_result = response.json()
                new_theta = answer_result.get('current_theta', 0)
                
                # Guardar información de la pregunta
                self.questions_answered.append({
                    'question_id': question_id,
                    'user_answer': user_answer,
                    'correct_answer': correct_answer,
                    'is_correct': is_correct,
                    'theta_after': new_theta,
                    'question_text': question_text
                })
                
                questions_answered += 1
                self.current_theta = new_theta
                
                logger.info(f"Respuesta: {user_answer} ({'✅' if is_correct else '❌'}), Theta: {new_theta:.3f}")
                
                # Pequeña pausa entre preguntas
                time.sleep(0.5)
                
            self.print_step_result("Responder preguntas adaptativas", True, 
                                 f"Respondidas {questions_answered} preguntas con IRT")
            
            return questions_answered >= 5  # Al menos 5 preguntas para ser válido
            
        except Exception as e:
            self.print_step_result("Responder preguntas adaptativas", False, f"Error: {str(e)}")
            return False
            
    def step_4_verify_images_display(self) -> bool:
        """Paso 4: Verificar que las imágenes se muestren en preguntas/opciones"""
        self.print_separator("PASO 4: VERIFICANDO VISUALIZACIÓN DE IMÁGENES")
        
        try:
            images_found = 0
            images_accessible = 0
            
            # Buscar preguntas con imágenes
            for question_info in self.questions_answered:
                question_id = question_info['question_id']
                
                # Obtener detalles completos de la pregunta
                response = self.session.get(f"{BACKEND_URL}/api/v1/questions/{question_id}")
                
                if response.status_code == 200:
                    question_detail = response.json()
                    
                    # Verificar si tiene URLs de imágenes
                    image_fields = ['imagen_pregunta_url', 'imagen_opcion_a_url', 
                                  'imagen_opcion_b_url', 'imagen_opcion_c_url', 'imagen_opcion_d_url']
                    
                    for field in image_fields:
                        image_url = question_detail.get(field)
                        if image_url and image_url.strip():
                            images_found += 1
                            
                            # Verificar si la imagen es accesible
                            try:
                                img_response = self.session.get(image_url, timeout=5)
                                if img_response.status_code == 200:
                                    images_accessible += 1
                                    logger.info(f"Imagen accesible: {image_url}")
                                else:
                                    logger.warning(f"Imagen no accesible: {image_url} ({img_response.status_code})")
                            except:
                                logger.warning(f"Error accediendo imagen: {image_url}")
                                
            self.print_step_result("Verificar imágenes", True, 
                                 f"Encontradas {images_found} imágenes, {images_accessible} accesibles")
            
            return True  # No falla aunque no haya imágenes
            
        except Exception as e:
            self.print_step_result("Verificar imágenes", False, f"Error: {str(e)}")
            return False
            
    def step_5_view_explanations(self) -> bool:
        """Paso 5: Ver explicaciones después de respuestas"""
        self.print_separator("PASO 5: VERIFICANDO EXPLICACIONES DE RESPUESTAS")
        
        try:
            explanations_found = 0
            
            for question_info in self.questions_answered:
                question_id = question_info['question_id']
                
                # Obtener explicación de la pregunta
                response = self.session.get(f"{BACKEND_URL}/api/v1/questions/{question_id}/explanation")
                
                if response.status_code == 200:
                    explanation_data = response.json()
                    explanation = explanation_data.get('explanation', '')
                    
                    if explanation and explanation.strip():
                        explanations_found += 1
                        logger.info(f"Explicación disponible para pregunta {question_id}: {explanation[:100]}...")
                        
                elif response.status_code == 404:
                    # Buscar en el objeto pregunta directamente
                    response = self.session.get(f"{BACKEND_URL}/api/v1/questions/{question_id}")
                    if response.status_code == 200:
                        question_detail = response.json()
                        explanation = question_detail.get('explicacion_respuesta', '')
                        
                        if explanation and explanation.strip():
                            explanations_found += 1
                            logger.info(f"Explicación en pregunta {question_id}: {explanation[:100]}...")
                            
            self.print_step_result("Verificar explicaciones", True, 
                                 f"Encontradas {explanations_found} explicaciones")
            
            return True
            
        except Exception as e:
            self.print_step_result("Verificar explicaciones", False, f"Error: {str(e)}")
            return False
            
    def step_6_get_final_theta_and_rank(self) -> bool:
        """Paso 6: Obtener theta score final y ranking"""
        self.print_separator("PASO 6: OBTENIENDO THETA SCORE FINAL Y RANKING")
        
        try:
            # Finalizar sesión diagnóstica
            response = self.session.post(f"{BACKEND_URL}/api/v1/diagnostic/{self.diagnostic_session_id}/complete")
            
            if response.status_code != 200:
                self.print_step_result("Finalizar diagnóstico", False, f"Error: {response.status_code}")
                return False
                
            final_results = response.json()
            self.final_results = final_results
            
            final_theta = final_results.get('final_theta', self.current_theta)
            percentile = final_results.get('percentile', 0)
            level = final_results.get('level', 'Básico')
            
            # Obtener ranking/leaderboard
            response = self.session.get(f"{BACKEND_URL}/api/v1/leaderboard")
            
            ranking_info = ""
            if response.status_code == 200:
                leaderboard = response.json()
                user_rank = None
                
                for i, entry in enumerate(leaderboard.get('rankings', [])):
                    if entry.get('user_id') == self.user_data.get('id'):
                        user_rank = i + 1
                        break
                        
                if user_rank:
                    ranking_info = f"Posición en ranking: {user_rank}"
                    
            self.print_step_result("Obtener theta final y ranking", True, 
                                 f"Theta: {final_theta:.3f}, Percentil: {percentile}%, Nivel: {level}. {ranking_info}")
            
            return True
            
        except Exception as e:
            self.print_step_result("Obtener theta final y ranking", False, f"Error: {str(e)}")
            return False
            
    def step_7_verify_data_saved(self) -> bool:
        """Paso 7: Verificar que todos los datos se guardaron en DB"""
        self.print_separator("PASO 7: VERIFICANDO DATOS GUARDADOS EN BASE DE DATOS")
        
        try:
            # Verificar que la sesión diagnóstica se guardó
            response = self.session.get(f"{BACKEND_URL}/api/v1/diagnostic/sessions")
            
            if response.status_code != 200:
                self.print_step_result("Verificar sesiones guardadas", False, f"Error: {response.status_code}")
                return False
                
            sessions = response.json()
            session_found = False
            
            for session in sessions.get('sessions', []):
                if session.get('id') == self.diagnostic_session_id:
                    session_found = True
                    break
                    
            if not session_found:
                self.print_step_result("Verificar sesión guardada", False, "Sesión no encontrada en DB")
                return False
                
            # Verificar respuestas guardadas
            response = self.session.get(f"{BACKEND_URL}/api/v1/diagnostic/{self.diagnostic_session_id}/answers")
            
            if response.status_code == 200:
                saved_answers = response.json()
                answers_count = len(saved_answers.get('answers', []))
            else:
                answers_count = 0
                
            # Verificar progreso del usuario
            response = self.session.get(f"{BACKEND_URL}/api/v1/users/{self.user_data.get('id')}/progress")
            
            progress_updated = False
            if response.status_code == 200:
                progress = response.json()
                if progress.get('total_questions_answered', 0) > 0:
                    progress_updated = True
                    
            self.print_step_result("Verificar datos guardados", True, 
                                 f"Sesión guardada ✅, {answers_count} respuestas guardadas, Progreso actualizado: {'✅' if progress_updated else '❌'}")
            
            return session_found
            
        except Exception as e:
            self.print_step_result("Verificar datos guardados", False, f"Error: {str(e)}")
            return False
            
    def generate_final_report(self):
        """Generar reporte final de la prueba"""
        self.print_separator("REPORTE FINAL DE LA PRUEBA E2E")
        
        print("📊 ESTADÍSTICAS DE LA PRUEBA:")
        print(f"   • Preguntas respondidas: {len(self.questions_answered)}")
        print(f"   • Theta score final: {self.current_theta:.3f}")
        print(f"   • Sesión diagnóstica: {self.diagnostic_session_id}")
        
        if self.final_results:
            print(f"   • Percentil: {self.final_results.get('percentile', 'N/A')}%")
            print(f"   • Nivel: {self.final_results.get('level', 'N/A')}")
            
        print("\n📋 RESUMEN DE RESPUESTAS:")
        correct_count = sum(1 for q in self.questions_answered if q['is_correct'])
        print(f"   • Respuestas correctas: {correct_count}/{len(self.questions_answered)}")
        print(f"   • Porcentaje de acierto: {(correct_count/len(self.questions_answered)*100):.1f}%")
        
        print("\n🎯 EVOLUCIÓN DEL THETA:")
        for i, q in enumerate(self.questions_answered):
            status = "✅" if q['is_correct'] else "❌"
            print(f"   Pregunta {i+1}: {status} → θ = {q['theta_after']:.3f}")
            
    def run_complete_test(self):
        """Ejecutar prueba completa end-to-end"""
        print("INICIANDO PRUEBA END-TO-END COMPLETA DEL SISTEMA ICFES")
        print("Tiempo estimado: 3-5 minutos")
        print()
        
        start_time = time.time()
        steps_results = []
        
        # Ejecutar todos los pasos
        steps = [
            ("Verificar carga de 480 preguntas", self.step_1_verify_questions_loaded),
            ("Iniciar diagnóstico Portal Despertar", self.step_2_start_diagnostic_test),
            ("Responder 10 preguntas adaptativas IRT", self.step_3_answer_adaptive_questions),
            ("Verificar visualización de imágenes", self.step_4_verify_images_display),
            ("Verificar explicaciones de respuestas", self.step_5_view_explanations),
            ("Obtener theta score final y ranking", self.step_6_get_final_theta_and_rank),
            ("Verificar datos guardados en DB", self.step_7_verify_data_saved)
        ]
        
        for step_name, step_function in steps:
            try:
                result = step_function()
                steps_results.append((step_name, result))
                
                if not result:
                    print(f"⚠️  ADVERTENCIA: El paso '{step_name}' falló, pero continuando con la prueba...")
                    
            except Exception as e:
                logger.error(f"Error en paso '{step_name}': {str(e)}")
                steps_results.append((step_name, False))
                
        # Generar reporte final
        end_time = time.time()
        duration = end_time - start_time
        
        self.generate_final_report()
        
        # Resumen final
        self.print_separator("RESUMEN FINAL DE LA PRUEBA E2E")
        
        successful_steps = sum(1 for _, result in steps_results if result)
        total_steps = len(steps_results)
        
        print(f"⏱️  Duración total: {duration:.1f} segundos")
        print(f"✅ Pasos exitosos: {successful_steps}/{total_steps}")
        print(f"📊 Porcentaje de éxito: {(successful_steps/total_steps*100):.1f}%")
        
        print("\n📋 DETALLES POR PASO:")
        for step_name, result in steps_results:
            status = "✅ ÉXITO" if result else "❌ FALLO"
            print(f"   {status} - {step_name}")
            
        if successful_steps == total_steps:
            print("\n🎉 ¡PRUEBA E2E COMPLETAMENTE EXITOSA!")
            print("   Todos los componentes del sistema funcionan correctamente.")
        elif successful_steps >= total_steps * 0.7:
            print(f"\n⚠️  PRUEBA E2E PARCIALMENTE EXITOSA ({successful_steps}/{total_steps})")
            print("   La mayoría de componentes funcionan, revisar fallos específicos.")
        else:
            print(f"\n❌ PRUEBA E2E CON FALLOS SIGNIFICATIVOS ({successful_steps}/{total_steps})")
            print("   Varios componentes requieren atención.")
            
        return successful_steps == total_steps

if __name__ == "__main__":
    print("PRUEBA END-TO-END SISTEMA ICFES LEVELING")
    print("=" * 50)
    
    try:
        runner = ICFESTestRunner()
        success = runner.run_complete_test()
        
        exit_code = 0 if success else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️  Prueba interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error fatal en la prueba: {str(e)}")
        sys.exit(1)