from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Optional, Any
from datetime import datetime
import random
import uuid
import logging

from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.question import Question, Topic
from ..models.subject import Subject
from ..models.user import User
from ..schemas.diagnostic_test import (
    DiagnosticTestCreate, 
    DiagnosticTestSubmit, 
    DiagnosticTestAnalysis,
    DIAGNOSTIC_TEST_CONFIGS
)
from .diagnostic_analytics_service import DiagnosticAnalyticsService

class DiagnosticService:
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def create_diagnostic_test(self, user_id: str, subject_id: str, test_type: str = "real_icfes") -> DiagnosticTest:
        """Crear un nuevo test diagnóstico"""
        # Validate that the subject exists
        subject = self.db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise ValueError(f"Subject with ID {subject_id} does not exist")
        
        diagnostic_test = DiagnosticTest(
            user_id=user_id,
            subject_id=subject_id,
            test_type=test_type,
            status="in_progress",
            started_at=datetime.utcnow()
        )
        self.db.add(diagnostic_test)
        self.db.commit()
        self.db.refresh(diagnostic_test)
        return diagnostic_test

    def get_diagnostic_questions(self, subject_id: str, limit: int = None) -> List[Question]:
        """Obtener preguntas para el test diagnóstico"""
        query = self.db.query(Question).filter(Question.subject_id == subject_id)
        
        if limit:
            query = query.limit(limit)
        
        questions = query.all()
        
        # Mezclar las preguntas para aleatorizar el orden
        random.shuffle(questions)
        return questions

    def get_diagnostic_test_config(self, subject_name: str) -> Dict[str, Any]:
        """Obtener configuración del test por materia"""
        subject_name_lower = subject_name.lower()
        return DIAGNOSTIC_TEST_CONFIGS.get(subject_name_lower, {
            "total_questions": 45,
            "time_limit_minutes": 90,
            "topics": []
        })

    def submit_diagnostic_test(self, test_id: str, answers: List[Dict]) -> DiagnosticTestAnalysis:
        """Procesar respuestas del test diagnóstico y generar análisis"""
        # Obtener el test
        test = self.db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
        if not test:
            raise ValueError("Test diagnóstico no encontrado")

        # Procesar respuestas con análisis detallado
        correct_answers = 0
        total_time = 0
        topic_scores = {}
        topic_counts = {}
        difficulty_analysis = {"easy": {"correct": 0, "total": 0}, "medium": {"correct": 0, "total": 0}, "hard": {"correct": 0, "total": 0}}
        response_time_analysis = {"fast": 0, "normal": 0, "slow": 0}
        topic_difficulty_analysis = {}

        for answer_data in answers:
            question = self.db.query(Question).filter(Question.id == answer_data["question_id"]).first()
            if not question:
                continue

            # Verificar si la respuesta es correcta
            is_correct = answer_data["user_answer"] == question.correct_answer
            if is_correct:
                correct_answers += 1

            # Acumular tiempo
            response_time = answer_data.get("response_time_ms", 0)
            total_time += response_time

            # Análisis de tiempo de respuesta
            if response_time < 30000:  # Menos de 30 segundos
                response_time_analysis["fast"] += 1
            elif response_time < 90000:  # Entre 30-90 segundos
                response_time_analysis["normal"] += 1
            else:  # Más de 90 segundos
                response_time_analysis["slow"] += 1

            # Acumular puntajes por tema
            topic_name = question.topic.name if question.topic else "general"
            if topic_name not in topic_scores:
                topic_scores[topic_name] = 0
                topic_counts[topic_name] = 0
                topic_difficulty_analysis[topic_name] = {"easy": {"correct": 0, "total": 0}, "medium": {"correct": 0, "total": 0}, "hard": {"correct": 0, "total": 0}}
            
            topic_scores[topic_name] += 1 if is_correct else 0
            topic_counts[topic_name] += 1

            # Análisis por dificultad
            difficulty_level = "easy" if question.difficulty <= 3 else "medium" if question.difficulty <= 6 else "hard"
            difficulty_analysis[difficulty_level]["total"] += 1
            topic_difficulty_analysis[topic_name][difficulty_level]["total"] += 1
            
            if is_correct:
                difficulty_analysis[difficulty_level]["correct"] += 1
                topic_difficulty_analysis[topic_name][difficulty_level]["correct"] += 1
            
            # Análisis adicional por tags si están disponibles
            if question.tags and not is_correct:
                # Agregar análisis de tags para preguntas incorrectas
                for tag in question.tags:
                    if tag and len(tag.strip()) > 0:
                        tag_name = tag.strip().lower()
                        # Identificar patrones de error por tipo de pregunta
                        if any(concept in tag_name for concept in ['aplicacion', 'procedimiento', 'calculo']):
                            if "Aplicación práctica - Dificultad en procedimientos" not in weaknesses:
                                pass  # Se agregará en el análisis final si es necesario

            # Guardar respuesta
            # Clamp response time to valid 32-bit signed int range to avoid DB overflow
            raw_rt = int(answer_data.get("response_time_ms", 0) or 0)
            if raw_rt < 0:
                raw_rt = 0
            if raw_rt > 2_147_483_647:
                raw_rt = 2_147_483_647

            test_answer = DiagnosticTestAnswer(
                diagnostic_test_id=test_id,
                question_id=answer_data["question_id"],
                user_answer=answer_data["user_answer"],
                is_correct=is_correct,
                response_time_ms=raw_rt,
                topic_id=question.topic_id
            )
            self.db.add(test_answer)

        # Calcular porcentajes por tema
        score_by_topic = {}
        for topic_name in topic_scores:
            if topic_counts[topic_name] > 0:
                score_by_topic[topic_name] = (topic_scores[topic_name] / topic_counts[topic_name]) * 100

        # Determinar fortalezas y debilidades con análisis detallado
        strengths = []
        weaknesses = []
        
        # Análisis de fortalezas basado en múltiples criterios
        for topic_name, score in score_by_topic.items():
            topic_data = topic_difficulty_analysis.get(topic_name, {})
            
            # Fortaleza: buen rendimiento general y en preguntas difíciles
            if score >= 70:
                hard_performance = 0
                if topic_data.get("hard", {}).get("total", 0) > 0:
                    hard_performance = (topic_data["hard"]["correct"] / topic_data["hard"]["total"]) * 100
                
                if hard_performance >= 50 or score >= 80:
                    strength_detail = f"{topic_name} - Dominio sólido"
                    if hard_performance >= 60:
                        strength_detail += " (excelente en preguntas avanzadas)"
                    elif score >= 90:
                        strength_detail += " (rendimiento excepcional)"
                    strengths.append(strength_detail)
            
            # Debilidad: bajo rendimiento o dificultades específicas
            elif score < 50:
                weakness_detail = f"{topic_name} - Requiere refuerzo"
                
                # Análisis específico de la debilidad
                easy_performance = 0
                medium_performance = 0
                if topic_data.get("easy", {}).get("total", 0) > 0:
                    easy_performance = (topic_data["easy"]["correct"] / topic_data["easy"]["total"]) * 100
                if topic_data.get("medium", {}).get("total", 0) > 0:
                    medium_performance = (topic_data["medium"]["correct"] / topic_data["medium"]["total"]) * 100
                
                if easy_performance < 50:
                    weakness_detail += " (conceptos básicos)"
                elif medium_performance < 40:
                    weakness_detail += " (aplicación intermedia)"
                else:
                    weakness_detail += " (preguntas complejas)"
                
                weaknesses.append(weakness_detail)
        
        # Análisis adicional de fortalezas por velocidad y dificultad
        total_questions = len(answers)
        if total_questions > 0:
            easy_accuracy = (difficulty_analysis["easy"]["correct"] / difficulty_analysis["easy"]["total"] * 100) if difficulty_analysis["easy"]["total"] > 0 else 0
            medium_accuracy = (difficulty_analysis["medium"]["correct"] / difficulty_analysis["medium"]["total"] * 100) if difficulty_analysis["medium"]["total"] > 0 else 0
            hard_accuracy = (difficulty_analysis["hard"]["correct"] / difficulty_analysis["hard"]["total"] * 100) if difficulty_analysis["hard"]["total"] > 0 else 0
            
            # Fortaleza en velocidad de respuesta
            fast_percentage = (response_time_analysis["fast"] / total_questions) * 100
            if fast_percentage >= 60 and correct_answers >= total_questions * 0.6:
                strengths.append("Velocidad de respuesta - Procesamiento ágil y preciso")
            
            # Fortaleza en preguntas difíciles
            if hard_accuracy >= 60 and difficulty_analysis["hard"]["total"] >= 3:
                strengths.append("Resolución avanzada - Manejo eficaz de preguntas complejas")
            
            # Debilidad en gestión del tiempo
            slow_percentage = (response_time_analysis["slow"] / total_questions) * 100
            if slow_percentage >= 40:
                weaknesses.append("Gestión del tiempo - Necesita optimizar velocidad de respuesta")
            
            # Debilidad en conceptos básicos
            if easy_accuracy < 60 and difficulty_analysis["easy"]["total"] >= 3:
                weaknesses.append("Fundamentos básicos - Requiere reforzar conceptos elementales")

        # Actualizar test
        test.questions_answered = len(answers)
        test.correct_answers = correct_answers
        test.time_spent_seconds = total_time // 1000  # Convertir de ms a segundos
        test.score_percentage = (correct_answers / len(answers)) * 100 if answers else 0
        test.strengths = strengths
        test.weaknesses = weaknesses
        test.score_by_topic = score_by_topic
        test.status = "completed"
        test.completed_at = datetime.utcnow()

        self.db.commit()

        # Crear análisis detallado con el nuevo servicio (no bloquear guardado si falla)
        try:
            analytics_service = DiagnosticAnalyticsService(self.db)
            detailed_analytics = analytics_service.create_detailed_analysis(test_id)
        except Exception:
            detailed_analytics = None

        # Generar análisis básico para mantener compatibilidad
        analysis = DiagnosticTestAnalysis(
            subject=test.subject.name,
            score=correct_answers,
            total_questions=len(answers),
            percentage=test.score_percentage,
            time_spent_minutes=test.time_spent_seconds / 60,
            strengths=strengths,
            weaknesses=weaknesses,
            score_by_topic=score_by_topic,
            recommendations=self._generate_recommendations(weaknesses, test.score_percentage)
        )

        return analysis

    def _generate_recommendations(self, weaknesses: List[str], overall_score: float) -> List[str]:
        """Generar recomendaciones basadas en debilidades y puntaje general"""
        recommendations = []

        # Recomendaciones generales según el rendimiento
        if overall_score < 30:
            recommendations.append("📚 Prioridad: Reforzar fundamentos básicos con ejercicios simples y teoría")
            recommendations.append("⏰ Dedica 2-3 horas diarias a revisar conceptos elementales")
        elif overall_score < 50:
            recommendations.append("📖 Necesitas reforzar los conceptos básicos de la materia")
            recommendations.append("🎯 Enfócate en dominar los temas fundamentales antes de avanzar")
        elif overall_score < 70:
            recommendations.append("💪 Tienes una base sólida, continúa practicando temas específicos")
            recommendations.append("🔍 Identifica y trabaja en las áreas identificadas como débiles")
        elif overall_score < 85:
            recommendations.append("🌟 Buen rendimiento, perfecciona las áreas de oportunidad")
            recommendations.append("📈 Enfócate en preguntas de mayor dificultad para alcanzar la excelencia")

        # Recomendaciones específicas por tipo de debilidad
        for weakness in weaknesses:
            weakness_lower = weakness.lower()
            
            # Análisis por temas específicos
            if any(term in weakness_lower for term in ["álgebra", "ecuaciones", "funciones"]):
                recommendations.append("🧮 Álgebra: Practica resolución de ecuaciones paso a paso y gráficas de funciones")
            elif any(term in weakness_lower for term in ["geometría", "figuras", "área", "volumen"]):
                recommendations.append("📐 Geometría: Refuerza fórmulas de área, perímetro y volumen con ejercicios visuales")
            elif any(term in weakness_lower for term in ["estadística", "probabilidad", "datos"]):
                recommendations.append("📊 Estadística: Practica interpretación de gráficos y cálculo de probabilidades")
            elif any(term in weakness_lower for term in ["cálculo", "derivadas", "integrales"]):
                recommendations.append("∫ Cálculo: Repasa reglas de derivación e integración con ejercicios graduales")
            
            # Análisis por tipo de dificultad
            if "conceptos básicos" in weakness_lower:
                recommendations.append("🔤 Fundamentos: Dedica tiempo extra a repasar definiciones y teorías básicas")
            elif "aplicación intermedia" in weakness_lower:
                recommendations.append("⚙️ Aplicación: Practica problemas de nivel intermedio y casos prácticos")
            elif "preguntas complejas" in weakness_lower:
                recommendations.append("🧩 Complejidad: Resuelve problemas avanzados y analiza múltiples pasos de solución")
            
            # Análisis por velocidad
            if "gestión del tiempo" in weakness_lower:
                recommendations.append("⏱️ Tiempo: Practica con cronómetro para mejorar tu velocidad de respuesta")
            elif "velocidad" in weakness_lower:
                recommendations.append("🏃 Agilidad: Entrena con ejercicios de respuesta rápida y técnicas de eliminación")

        # Recomendaciones de estudio específicas
        if len(weaknesses) >= 3:
            recommendations.append("📅 Plan intensivo: Crea un cronograma de estudio que cubra todas las áreas débiles")
        elif len(weaknesses) == 0 and overall_score >= 85:
            recommendations.append("🏆 ¡Excelente trabajo! Mantén tu nivel con práctica regular")
            recommendations.append("🎯 Enfócate en simulacros completos para mantener tu rendimiento")

        # Siempre agregar una recomendación motivacional
        if overall_score < 50:
            recommendations.append("💪 Recuerda: cada mejora cuenta, mantén la constancia en tu estudio")
        else:
            recommendations.append("🌟 ¡Vas por buen camino! La práctica constante te llevará al éxito")

        return recommendations

    def get_user_diagnostic_tests(self, user_id: str) -> List[DiagnosticTest]:
        """Obtener todos los tests diagnósticos de un usuario"""
        # Limpiar tests existentes que no tienen started_at
        self._cleanup_legacy_tests()
        
        return self.db.query(DiagnosticTest).filter(
            DiagnosticTest.user_id == user_id
        ).order_by(DiagnosticTest.created_at.desc()).all()
    
    def _cleanup_legacy_tests(self):
        """Limpiar tests existentes que no tienen campos requeridos"""
        try:
            from datetime import datetime
            
            # Actualizar tests que no tienen started_at
            legacy_tests = self.db.query(DiagnosticTest).filter(
                DiagnosticTest.started_at.is_(None)
            ).all()
            
            for test in legacy_tests:
                test.started_at = test.created_at or datetime.utcnow()
                test.reassessment_type = test.reassessment_type or 'initial'
                test.status = test.status or 'in_progress'
            
            if legacy_tests:
                self.db.commit()
                self.logger.info(f"Cleaned up {len(legacy_tests)} legacy diagnostic tests")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up legacy tests: {e}")
            self.db.rollback()

    def get_diagnostic_test_by_id(self, test_id: str) -> Optional[DiagnosticTest]:
        """Obtener un test diagnóstico específico"""
        return self.db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()

    def get_diagnostic_test_answers(self, test_id: str) -> List[DiagnosticTestAnswer]:
        """Obtener todas las respuestas de un test diagnóstico"""
        return self.db.query(DiagnosticTestAnswer).filter(
            DiagnosticTestAnswer.diagnostic_test_id == test_id
        ).all()

    def get_subject_stats(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """Obtener estadísticas de tests diagnósticos por materia"""
        tests = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.subject_id == subject_id,
                DiagnosticTest.status == "completed"
            )
        ).all()

        if not tests:
            return {
                "total_tests": 0,
                "average_score": 0,
                "best_score": 0,
                "total_time_minutes": 0
            }

        total_tests = len(tests)
        average_score = sum(test.score_percentage for test in tests) / total_tests
        best_score = max(test.score_percentage for test in tests)
        total_time_minutes = sum(test.time_spent_seconds for test in tests) / 60

        return {
            "total_tests": total_tests,
            "average_score": round(average_score, 2),
            "best_score": round(best_score, 2),
            "total_time_minutes": round(total_time_minutes, 2)
        } 