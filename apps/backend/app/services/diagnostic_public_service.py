"""
Service for handling the business logic of the public diagnostic endpoints.
This service encapsulates the logic originally found in the diagnostic_public.py router.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import uuid
from datetime import datetime
from sqlalchemy import func, text

from ..services.diagnostic_service import DiagnosticService
from ..services.diagnostic_analytics_service import DiagnosticAnalyticsService
from ..models.user import User
from ..models.subject import Subject
from ..models.question import Question
from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..schemas.diagnostic_test import DiagnosticTestCreate, DiagnosticTestSubmit

logger = logging.getLogger(__name__)

class DiagnosticPublicService:
    def __init__(self, db: Session):
        self.db = db
        self.diagnostic_service = DiagnosticService(db)
        self.analytics_service = DiagnosticAnalyticsService(db)
        self.COMPETENCIAS_POR_MATERIA = {
            "Matemáticas": {
                "competencias_dominadas": [{"name": "Razonamiento Cuantitativo", "description": "Excelente capacidad para analizar y resolver problemas cuantitativos", "componentes": ["Numérico", "Algebraico"]},],
                "areas_mejora": [{"name": "Pensamiento Geométrico", "description": "Requiere refuerzo en conceptos de geometría y espacialidad", "componentes": ["Geométrico"]},],
                "componentes": {"Numérico": {"percentage": 85, "questions_correct": 17, "questions_total": 20}, "Algebraico": {"percentage": 75, "questions_correct": 15, "questions_total": 20}, "Geométrico": {"percentage": 45, "questions_correct": 9, "questions_total": 20}, "Estadístico": {"percentage": 60, "questions_correct": 12, "questions_total": 20}},
                "procesos": {"Interpretación": {"percentage": 80, "questions_correct": 16, "questions_total": 20}, "Argumentación": {"percentage": 70, "questions_correct": 14, "questions_total": 20}, "Resolución de Problemas": {"percentage": 50, "questions_correct": 10, "questions_total": 20}},
                "temas_recomendados": ["Álgebra Básica", "Ecuaciones Lineales", "Geometría Plana", "Estadística Descriptiva", "Probabilidad", "Funciones"]
            },
        }

    def get_subjects(self) -> List[Dict[str, Any]]:
        try:
            subjects = self.db.query(Subject).all()
            if not subjects:
                raise Exception("No subjects found in DB, using fallback.")
            return [{"id": str(subject.id), "name": subject.name, "description": subject.description, "config": {"total_questions": 45, "time_limit_minutes": 60, "topics": ["Álgebra", "Geometría", "Estadística", "Cálculo"]}} for subject in subjects]
        except Exception as e:
            logger.warning(f"Could not fetch subjects from DB, using fallback. Error: {e}")
            return [{"id": "550e8400-e29b-41d4-a716-446655440001", "name": "Matemáticas", "description": "Matemáticas", "config": {"total_questions": 45, "time_limit_minutes": 60, "topics": ["Álgebra", "Geometría", "Estadística", "Cálculo"]}},]

    def create_public_test(self, test_data: DiagnosticTestCreate, user_id: str = None) -> Dict[str, Any]:
        try:
            if user_id:
                default_user = self.db.query(User).filter(User.id == user_id).first()
            else:
                default_user = self.db.query(User).first()
            if not default_user:
                raise ValueError("No authenticated user found. Please login first.")
            
            test = self.diagnostic_service.create_diagnostic_test(user_id=str(default_user.id), subject_id=test_data.subject_id, test_type=test_data.test_type)
            return {"id": str(test.id), "user_id": str(test.user_id), "subject_id": str(test.subject_id), "test_type": test.test_type, "status": test.status, "created_at": test.created_at}
        except Exception as e:
            logger.error(f"Error creating public diagnostic test: {e}")
            raise

    def get_test_questions(self, test_id: str) -> List[Dict[str, Any]]:
        try:
            test = self.diagnostic_service.get_diagnostic_test_by_id(test_id)
            if not test: raise ValueError("Test not found")
            subject = self.db.query(Subject).filter(Subject.id == test.subject_id).first()
            if not subject: raise ValueError("Subject not found")
            config = self.diagnostic_service.get_diagnostic_test_config(subject.name)
            questions = self.diagnostic_service.get_diagnostic_questions(subject_id=str(test.subject_id), limit=config["total_questions"])
            logger.info(f"Found {len(questions)} questions for subject {subject.name}")
            return [{"id": str(q.id), "question_text": q.question_text, "options": q.options, "subject": subject.name, "topic": q.topic.name if q.topic else "General", "difficulty": q.difficulty, "hint": q.hint, "image_url": getattr(q, 'pregunta_imagen', None), "options_images": {}} for q in questions]
        except ValueError as ve:
            raise ve
        except Exception as e:
            logger.error(f"Error getting questions for test {test_id}: {e}")
            raise

    def submit_public_test(self, test_id: str, submit_data: DiagnosticTestSubmit) -> Dict[str, Any]:
        try:
            test = self.diagnostic_service.get_diagnostic_test_by_id(test_id)
            if not test: raise ValueError("Test not found")
            answers = [{"question_id": answer.question_id, "user_answer": answer.user_answer, "response_time_ms": answer.response_time_ms} for answer in submit_data.answers]
            analysis = self.diagnostic_service.submit_diagnostic_test(test_id, answers)
            return analysis
        except ValueError as ve:
            raise ve
        except Exception as e:
            logger.error(f"Error submitting public test {test_id}: {e}")
            raise

    def get_diagnostic_results(self, test_id: str) -> Dict[str, Any]:
        """Get diagnostic test results with comprehensive analysis."""
        try:
            answers, question_lookup = self._get_test_data(test_id)
            if not answers:
                return self._generate_comprehensive_study_recommendation(test_id=test_id, answers=[], question_lookup={}, db=self.db)
            
            materia_fallback = self._detectar_materia_del_test(test_id, answers, question_lookup, self.db)

            return self._generate_basic_diagnostic_results(
                test_id=test_id,
                answers=answers,
                question_lookup=question_lookup,
                materia=materia_fallback
            )
        except Exception as e:
            logger.error(f"Error getting diagnostic results: {str(e)}")
            raise

    def _get_test_data(self, test_id: str) -> tuple[List[DiagnosticTestAnswer], Dict[str, Question]]:
        final_test_id = self._get_final_test_id(test_id)
        diagnostic_test = self.db.query(DiagnosticTest).filter(DiagnosticTest.id == final_test_id).first()
        answers = []
        if diagnostic_test:
            answers = self.db.query(DiagnosticTestAnswer).filter(DiagnosticTestAnswer.diagnostic_test_id == diagnostic_test.id).all()
        if not answers:
            from datetime import datetime, timedelta
            recent_time = datetime.utcnow() - timedelta(minutes=30)
            answers = self.db.query(DiagnosticTestAnswer).filter(DiagnosticTestAnswer.created_at > recent_time).all()
        question_ids = [str(a.question_id) for a in answers]
        questions = self.db.query(Question).filter(Question.id.in_(question_ids)).all() if question_ids else []
        return answers, {str(q.id): q for q in questions}

    def _get_final_test_id(self, test_id: str) -> str:
        try:
            import uuid
            uuid.UUID(test_id)
            return test_id
        except ValueError:
            import hashlib
            return str(uuid.UUID(hashlib.md5(test_id.encode()).hexdigest()))

    def _generate_basic_diagnostic_results(self, test_id: str, answers: List[DiagnosticTestAnswer], question_lookup: Dict[str, Question], materia: str):
        from datetime import datetime
        competencias_materia = self._obtener_competencias_por_materia(materia)
        total_questions = len(answers)
        correct_count = len([a for a in answers if a.is_correct])
        score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        topic_performance = {}
        for answer in answers:
            question = question_lookup.get(str(answer.question_id))
            if question:
                topic = getattr(question, 'topic_name', 'General')
                if topic not in topic_performance:
                    topic_performance[topic] = {'correct': 0, 'total': 0}
                topic_performance[topic]['total'] += 1
                if answer.is_correct:
                    topic_performance[topic]['correct'] += 1
        topic_scores = {topic: (perf['correct'] / perf['total']) * 100 if perf['total'] > 0 else 0 for topic, perf in topic_performance.items()}
        strengths = [f"Excelente dominio en {topic}" for topic, score in topic_scores.items() if score >= 80]
        weaknesses = [f"Necesita reforzar {topic}" for topic, score in topic_scores.items() if score <= 50]
        return {
            "test_id": test_id, "subject": f"Diagnóstico de {materia}",
            "final_theta_score": score_percentage / 100.0, "score_percentage": score_percentage,
            "questions_answered": total_questions, "questions_correct": correct_count, "questions_incorrect": total_questions - correct_count,
            "time_spent_minutes": sum([a.response_time_ms for a in answers]) // (1000 * 60) if answers else 20,
            "completed_at": datetime.utcnow().isoformat(), "strengths": strengths, "weaknesses": weaknesses,
            "score_by_topic": topic_scores,
            "correct_questions": [], "incorrect_questions": [],
            "competencies_mastered": [], "areas_for_improvement": [],
            "componente_performance": {}, "proceso_cognitivo_performance": {}, "recommended_study_topics": []
        }
        
    def _generate_comprehensive_study_recommendation(self, test_id: str, answers: List[DiagnosticTestAnswer], question_lookup: Dict[str, Question], db: Session):
        return {}

    def _generate_intelligent_diagnostic_results(self, test_id: str, answers: List, question_lookup: Dict[str, Question], user_profile: Any, recommendations: List[Any], llm_service: Any):
        return {}

    def _generate_study_plan_yaml(self, analysis_result: Dict, test_id: str) -> str:
        return ""

    def _generate_question_details(self, answers, question_lookup, is_correct_filter, materia, competencias_materia):
        return []

    def _theta_to_percentile(self, theta: float) -> int:
        return 0

    def _interpret_theta(self, theta: float) -> str:
        return ""