from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import random
import math

from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.question import Question, Topic
from ..models.subject import Subject
from ..models.user import User
from ..models.study_plan import StudyPlan
from ..schemas.diagnostic_test import (
    MonthlyReassessmentRequest,
    ReassessmentComparison,
    ReassessmentNotification
)

class MonthlyReassessmentService:
    def __init__(self, db: Session):
        self.db = db

    def check_monthly_reassessment_eligibility(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """Verificar si el usuario es elegible para una reevaluación mensual"""
        # Buscar el test diagnóstico inicial más reciente
        initial_test = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.subject_id == subject_id,
                DiagnosticTest.reassessment_type == "initial",
                DiagnosticTest.status == "completed"
            )
        ).order_by(DiagnosticTest.created_at.desc()).first()

        if not initial_test:
            return {
                "eligible": False,
                "reason": "No se encontró test diagnóstico inicial",
                "days_since_initial": None
            }

        # Calcular días desde el test inicial
        days_since_initial = (datetime.utcnow() - initial_test.created_at).days

        # Verificar si han pasado al menos 30 días
        if days_since_initial < 30:
            return {
                "eligible": False,
                "reason": f"Faltan {30 - days_since_initial} días para la reevaluación mensual",
                "days_since_initial": days_since_initial
            }

        # Verificar si ya existe una reevaluación mensual reciente (últimos 7 días)
        recent_reassessment = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.subject_id == subject_id,
                DiagnosticTest.is_monthly_reassessment == True,
                DiagnosticTest.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).first()

        if recent_reassessment:
            return {
                "eligible": False,
                "reason": "Ya se realizó una reevaluación mensual recientemente",
                "days_since_initial": days_since_initial
            }

        return {
            "eligible": True,
            "initial_test_id": str(initial_test.id),
            "days_since_initial": days_since_initial,
            "initial_score": float(initial_test.score_percentage)
        }

    def create_monthly_reassessment(self, user_id: str, subject_id: str) -> DiagnosticTest:
        """Crear una reevaluación mensual (test corto con 20% de preguntas originales)"""
        # Verificar elegibilidad
        eligibility = self.check_monthly_reassessment_eligibility(user_id, subject_id)
        if not eligibility["eligible"]:
            raise ValueError(eligibility["reason"])

        # Obtener el test inicial
        initial_test = self.db.query(DiagnosticTest).filter(
            DiagnosticTest.id == eligibility["initial_test_id"]
        ).first()

        # Calcular número de preguntas (20% del test original)
        original_questions_count = initial_test.questions_answered
        reassessment_questions_count = max(6, int(original_questions_count * 0.2))

        # Crear el test de reevaluación
        reassessment_test = DiagnosticTest(
            user_id=user_id,
            subject_id=subject_id,
            test_type="monthly_reassessment",
            reassessment_type="monthly",
            original_test_id=initial_test.id,
            is_monthly_reassessment=True,
            days_since_initial=eligibility["days_since_initial"],
            status="in_progress"
        )

        self.db.add(reassessment_test)
        self.db.commit()
        self.db.refresh(reassessment_test)

        return reassessment_test

    def get_reassessment_questions(self, test_id: str, subject_id: str, question_count: int) -> List[Question]:
        """Obtener preguntas para la reevaluación mensual (dificultad alta)"""
        # Obtener preguntas de alta dificultad (7-10)
        questions = self.db.query(Question).filter(
            and_(
                Question.subject_id == subject_id,
                Question.difficulty >= 7
            )
        ).all()

        if len(questions) < question_count:
            # Si no hay suficientes preguntas de alta dificultad, incluir de dificultad media
            medium_questions = self.db.query(Question).filter(
                and_(
                    Question.subject_id == subject_id,
                    Question.difficulty >= 5,
                    Question.difficulty < 7
                )
            ).all()
            questions.extend(medium_questions)

        # Mezclar y seleccionar el número requerido
        random.shuffle(questions)
        return questions[:question_count]

    def submit_monthly_reassessment(self, test_id: str, answers: List[Dict]) -> Dict[str, Any]:
        """Procesar respuestas de la reevaluación mensual y generar comparación"""
        # Obtener el test de reevaluación
        reassessment_test = self.db.query(DiagnosticTest).filter(
            DiagnosticTest.id == test_id
        ).first()

        if not reassessment_test:
            raise ValueError("Test de reevaluación no encontrado")

        # Obtener el test inicial para comparación
        initial_test = self.db.query(DiagnosticTest).filter(
            DiagnosticTest.id == reassessment_test.original_test_id
        ).first()

        # Procesar respuestas (similar al diagnostic_service)
        correct_answers = 0
        total_time = 0
        topic_scores = {}
        topic_counts = {}

        for answer_data in answers:
            question = self.db.query(Question).filter(
                Question.id == answer_data["question_id"]
            ).first()
            if not question:
                continue

            is_correct = answer_data["user_answer"] == question.correct_answer
            if is_correct:
                correct_answers += 1

            total_time += answer_data.get("response_time_ms", 0)

            topic_name = question.topic.name if question.topic else "general"
            if topic_name not in topic_scores:
                topic_scores[topic_name] = 0
                topic_counts[topic_name] = 0
            
            topic_scores[topic_name] += 1 if is_correct else 0
            topic_counts[topic_name] += 1

            # Guardar respuesta
            test_answer = DiagnosticTestAnswer(
                test_id=test_id,
                question_id=answer_data["question_id"],
                user_answer=answer_data["user_answer"],
                is_correct=is_correct,
                response_time_ms=answer_data.get("response_time_ms", 0),
                topic_id=question.topic_id
            )
            self.db.add(test_answer)

        # Calcular puntajes
        score_by_topic = {}
        for topic_name in topic_scores:
            if topic_counts[topic_name] > 0:
                score_by_topic[topic_name] = (topic_scores[topic_name] / topic_counts[topic_name]) * 100

        current_score = (correct_answers / len(answers)) * 100 if answers else 0
        initial_score = float(initial_test.score_percentage)

        # Generar comparación
        comparison = self._generate_comparison(initial_test, reassessment_test, current_score, score_by_topic)

        # Actualizar test de reevaluación
        reassessment_test.questions_answered = len(answers)
        reassessment_test.correct_answers = correct_answers
        reassessment_test.time_spent_seconds = total_time // 1000
        reassessment_test.score_percentage = current_score
        reassessment_test.score_by_topic = score_by_topic
        reassessment_test.comparison_with_initial = comparison
        reassessment_test.status = "completed"
        reassessment_test.completed_at = datetime.utcnow()

        # Generar nuevos objetivos y actualizar plan
        new_goals = self._generate_new_goals(comparison, current_score)
        self._regenerate_study_plan(user_id, subject_id, comparison, new_goals)

        # Marcar como procesado
        reassessment_test.new_goals_generated = True
        reassessment_test.plan_regenerated = True

        self.db.commit()

        return {
            "reassessment_id": str(reassessment_test.id),
            "current_score": current_score,
            "initial_score": initial_score,
            "improvement_percentage": comparison["improvement_percentage"],
            "comparison": comparison,
            "new_goals": new_goals
        }

    def _generate_comparison(self, initial_test: DiagnosticTest, reassessment_test: DiagnosticTest, 
                           current_score: float, current_score_by_topic: Dict[str, float]) -> Dict[str, Any]:
        """Generar comparación entre test inicial y reevaluación"""
        initial_score = float(initial_test.score_percentage)
        improvement_percentage = current_score - initial_score

        # Comparar puntajes por tema
        initial_score_by_topic = initial_test.score_by_topic or {}
        topics_improved = []
        topics_declined = []

        for topic, current_topic_score in current_score_by_topic.items():
            initial_topic_score = initial_score_by_topic.get(topic, 0)
            if current_topic_score > initial_topic_score + 10:  # Mejora significativa
                topics_improved.append(topic)
            elif current_topic_score < initial_topic_score - 10:  # Deterioro significativo
                topics_declined.append(topic)

        # Determinar tendencia general
        if improvement_percentage > 5:
            overall_trend = "improving"
        elif improvement_percentage < -5:
            overall_trend = "declining"
        else:
            overall_trend = "stable"

        return {
            "initial_score": initial_score,
            "current_score": current_score,
            "improvement_percentage": improvement_percentage,
            "days_since_initial": reassessment_test.days_since_initial,
            "topics_improved": topics_improved,
            "topics_declined": topics_declined,
            "overall_trend": overall_trend,
            "initial_score_by_topic": initial_score_by_topic,
            "current_score_by_topic": current_score_by_topic
        }

    def _generate_new_goals(self, comparison: Dict[str, Any], current_score: float) -> List[str]:
        """Generar nuevos objetivos personalizados basados en la comparación"""
        goals = []
        improvement = comparison["improvement_percentage"]
        topics_improved = comparison["topics_improved"]
        topics_declined = comparison["topics_declined"]

        if improvement > 10:
            goals.append("¡Excelente progreso! Mantén tu ritmo de estudio")
            goals.append("Considera aumentar la dificultad de las preguntas")
        elif improvement > 0:
            goals.append("Buen progreso, continúa con tu plan actual")
            goals.append("Enfócate en mantener la consistencia")
        else:
            goals.append("Necesitas ajustar tu estrategia de estudio")
            goals.append("Considera dedicar más tiempo a las áreas débiles")

        if topics_declined:
            goals.append(f"Refuerza los temas: {', '.join(topics_declined)}")
        
        if current_score < 70:
            goals.append("Objetivo: alcanzar al menos 70% en el próximo test")
        elif current_score < 85:
            goals.append("Objetivo: alcanzar al menos 85% en el próximo test")
        else:
            goals.append("Objetivo: mantener tu excelente rendimiento")

        return goals

    def _regenerate_study_plan(self, user_id: str, subject_id: str, comparison: Dict[str, Any], new_goals: List[str]):
        """Regenerar plan de estudio basado en la reevaluación"""
        # Aquí se integraría con el servicio de IA para generar un nuevo plan
        # Por ahora, simulamos la actualización
        pass

    def get_user_reassessments(self, user_id: str) -> List[DiagnosticTest]:
        """Obtener todas las reevaluaciones mensuales de un usuario"""
        return self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.is_monthly_reassessment == True
            )
        ).order_by(DiagnosticTest.created_at.desc()).all()

    def get_reassessment_summary(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """Obtener resumen de reevaluaciones para una materia"""
        reassessments = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.subject_id == subject_id,
                DiagnosticTest.is_monthly_reassessment == True,
                DiagnosticTest.status == "completed"
            )
        ).order_by(DiagnosticTest.created_at.desc()).all()

        if not reassessments:
            return {
                "total_reassessments": 0,
                "average_improvement": 0,
                "best_improvement": 0,
                "trend": "no_data"
            }

        improvements = []
        for reassessment in reassessments:
            if reassessment.comparison_with_initial:
                improvements.append(reassessment.comparison_with_initial.get("improvement_percentage", 0))

        return {
            "total_reassessments": len(reassessments),
            "average_improvement": sum(improvements) / len(improvements) if improvements else 0,
            "best_improvement": max(improvements) if improvements else 0,
            "trend": "improving" if sum(improvements) > 0 else "declining" if sum(improvements) < 0 else "stable"
        } 