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

        # Procesar respuestas
        correct_answers = 0
        total_time = 0
        topic_scores = {}
        topic_counts = {}

        for answer_data in answers:
            question = self.db.query(Question).filter(Question.id == answer_data["question_id"]).first()
            if not question:
                continue

            # Verificar si la respuesta es correcta
            is_correct = answer_data["user_answer"] == question.correct_answer
            if is_correct:
                correct_answers += 1

            # Acumular tiempo
            total_time += answer_data.get("response_time_ms", 0)

            # Acumular puntajes por tema
            topic_name = question.topic.name if question.topic else "general"
            if topic_name not in topic_scores:
                topic_scores[topic_name] = 0
                topic_counts[topic_name] = 0
            
            topic_scores[topic_name] += 1 if is_correct else 0
            topic_counts[topic_name] += 1

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

        # Determinar fortalezas y debilidades
        strengths = [topic for topic, score in score_by_topic.items() if score >= 70]
        weaknesses = [topic for topic, score in score_by_topic.items() if score < 50]

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

        if overall_score < 50:
            recommendations.append("Necesitas reforzar los conceptos básicos de la materia")
            recommendations.append("Considera revisar el material desde el principio")
        elif overall_score < 70:
            recommendations.append("Tienes una base sólida, pero hay áreas de mejora")
            recommendations.append("Enfócate en los temas identificados como débiles")

        for weakness in weaknesses:
            if "álgebra" in weakness.lower():
                recommendations.append("Practica más ejercicios de álgebra y ecuaciones")
            elif "geometría" in weakness.lower():
                recommendations.append("Refuerza conceptos de geometría y fórmulas")
            elif "comprensión" in weakness.lower():
                recommendations.append("Mejora tus habilidades de comprensión lectora")
            elif "gramática" in weakness.lower():
                recommendations.append("Revisa las reglas gramaticales básicas")

        if not recommendations:
            recommendations.append("¡Excelente trabajo! Mantén tu nivel de estudio")

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