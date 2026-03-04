from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import random
import json

from ..models.quiz import Quiz, QuizAnswer
from ..models.topic import Topic
from ..models.question import Question
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.user import User
from ..models.mobile_offline import UserLeague, LeagueGroup, LeagueWeek
from ..schemas.quiz import (
    QuizCreate,
    QuizAnswerCreate,
    QuizAnswerResponse,
    QuizGenerationRequest,
    QuizGenerationResponse,
    QuizFeedback
)

class QuizService:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_unit_quiz(self, user_id: str, plan_id: str, unit_number: int, user_level: int = None) -> QuizGenerationResponse:
        """Generar quiz contextualizado para una unidad específica"""
        # Obtener el plan de estudio
        plan = self.db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == user_id
        ).first()
        
        if not plan:
            raise ValueError("Plan de estudio no encontrado")
        
        # Obtener progreso de la unidad
        unit_progress = self.db.query(PlanProgress).filter(
            PlanProgress.plan_id == plan_id,
            PlanProgress.unit_number == unit_number
        ).first()
        
        if not unit_progress:
            raise ValueError("Unidad no encontrada en el plan")
        
        # Extraer temas de la unidad desde el YML (simulado)
        unit_topics = self._extract_unit_topics(plan.plan_data, unit_number)
        
        # Obtener preguntas contextualizadas
        questions = self._get_contextualized_questions(unit_topics, user_level)
        
        if len(questions) < 10:
            # Si no hay suficientes preguntas específicas, agregar preguntas generales del tema
            general_questions = self._get_general_questions(unit_topics, user_level, 10 - len(questions))
            questions.extend(general_questions)
        
        # Limitar a 10 preguntas
        questions = questions[:10]
        
        # Crear el quiz
        quiz = Quiz(
            user_id=user_id,
            plan_id=plan_id,
            unit_number=unit_number,
            quiz_name=f"Quiz Unidad {unit_number} - {unit_progress.unit_name}",
            total_questions=len(questions),
            passing_score=80.0,
            time_limit_minutes=15,
            status="in_progress"
        )
        
        self.db.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)
        
        return QuizGenerationResponse(
            quiz_id=str(quiz.id),
            unit_id=f"{plan_id}_{unit_number}",
            questions=[self._question_to_response(q) for q in questions],
            passing_score=80.0,
            time_limit_minutes=15,
            rewards=self._calculate_rewards(user_level or 1)
        )
    
    def _extract_unit_topics(self, plan_data: Dict[str, Any], unit_number: int) -> List[str]:
        """Extraer temas de la unidad desde el YML del plan"""
        try:
            # Simular extracción de temas del YML
            # En producción, esto parsearía el YML real
            unit_key = f"unit_{unit_number}"
            if unit_key in plan_data:
                unit_content = plan_data[unit_key]
                return unit_content.get("topics", [])
            else:
                # Fallback: temas generales basados en el número de unidad
                return [f"tema_{unit_number}", f"concepto_{unit_number}"]
        except Exception:
            # Fallback si hay error en el parsing
            return [f"tema_{unit_number}"]
    
    def _get_contextualized_questions(self, unit_topics: List[str], user_level: int = None) -> List[Question]:
        """Obtener preguntas contextualizadas para los temas de la unidad"""
        query = self.db.query(Question)
        
        # Filtrar por temas de la unidad
        topic_filters = []
        for topic_name in unit_topics:
            topic_filters.append(Question.topic.has(Topic.name.ilike(f"%{topic_name}%")))
        
        if topic_filters:
            query = query.filter(func.or_(*topic_filters))
        
        # Adaptar dificultad basada en el nivel del usuario
        if user_level:
            if user_level <= 10:
                difficulty_range = (1, 3)
            elif user_level <= 25:
                difficulty_range = (2, 5)
            elif user_level <= 50:
                difficulty_range = (3, 7)
            else:
                difficulty_range = (5, 10)
            
            query = query.filter(Question.difficulty.between(*difficulty_range))
        
        # Obtener preguntas aleatorias
        questions = query.order_by(func.random()).limit(10).all()
        return questions
    
    def _get_general_questions(self, unit_topics: List[str], user_level: int = None, limit: int = 5) -> List[Question]:
        """Obtener preguntas generales del tema si no hay suficientes específicas"""
        query = self.db.query(Question)
        
        # Filtrar por temas relacionados
        topic_filters = []
        for topic_name in unit_topics:
            topic_filters.append(Question.topic.has(Topic.name.ilike(f"%{topic_name}%")))
        
        if topic_filters:
            query = query.filter(func.or_(*topic_filters))
        
        # Adaptar dificultad
        if user_level:
            if user_level <= 10:
                difficulty_range = (1, 3)
            elif user_level <= 25:
                difficulty_range = (2, 5)
            elif user_level <= 50:
                difficulty_range = (3, 7)
            else:
                difficulty_range = (5, 10)
            
            query = query.filter(Question.difficulty.between(*difficulty_range))
        
        return query.order_by(func.random()).limit(limit).all()
    
    def _question_to_response(self, question: Question) -> Dict[str, Any]:
        """Convertir pregunta a formato de respuesta"""
        return {
            "id": str(question.id),
            "question_text": question.question_text,
            "question_type": question.question_type,
            "difficulty": question.difficulty,
            "correct_answer": question.correct_answer,
            "options": question.options,
            "explanation": question.explanation,
            "hint": question.hint,
            "tags": question.tags
        }
    
    def _calculate_rewards(self, user_level: int) -> Dict[str, Any]:
        """Calcular recompensas basadas en el nivel del usuario"""
        base_exp = 50
        base_orbs = 10
        
        level_multiplier = 1 + (user_level - 1) * 0.1
        
        return {
            "experience": int(base_exp * level_multiplier),
            "orbs": int(base_orbs * level_multiplier),
            "crystals": max(1, int(level_multiplier)),
            "items": []
        }
    
    def submit_quiz_answer(self, quiz_id: str, answer_data: QuizAnswerCreate) -> QuizAnswerResponse:
        """Enviar respuesta de quiz con retroalimentación IA"""
        # Obtener quiz
        quiz = self.db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise ValueError("Quiz no encontrado")
        
        if quiz.status != "in_progress":
            raise ValueError("Quiz ya finalizado")
        
        # Obtener pregunta
        question = self.db.query(Question).filter(Question.id == answer_data.question_id).first()
        if not question:
            raise ValueError("Pregunta no encontrada")
        
        # Verificar respuesta
        is_correct = answer_data.user_answer == question.correct_answer
        
        # Generar explicación IA si es incorrecta
        ai_explanation = None
        if not is_correct:
            ai_explanation = self._generate_ai_explanation(question, answer_data.user_answer)
        
        # Crear respuesta de quiz
        quiz_answer = QuizAnswer(
            quiz_id=quiz_id,
            question_id=answer_data.question_id,
            user_answer=answer_data.user_answer,
            is_correct=is_correct,
            response_time_ms=answer_data.response_time_ms,
            ai_explanation=ai_explanation
        )
        
        self.db.add(quiz_answer)
        self.db.commit()
        self.db.refresh(quiz_answer)
        
        return QuizAnswerResponse(
            id=str(quiz_answer.id),
            quiz_id=str(quiz_answer.quiz_id),
            question_id=str(quiz_answer.question_id),
            user_answer=quiz_answer.user_answer,
            is_correct=quiz_answer.is_correct,
            response_time_ms=quiz_answer.response_time_ms,
            ai_explanation=quiz_answer.ai_explanation,
            created_at=quiz_answer.created_at
        )
    
    def _generate_ai_explanation(self, question: Question, user_answer: str) -> str:
        """Generar explicación IA para respuesta incorrecta"""
        # En producción, esto llamaría al servicio de IA
        # Por ahora, simulamos la explicación
        return f"La respuesta correcta es '{question.correct_answer}'. {question.explanation or 'Revisa el tema relacionado.'}"
    
    def complete_quiz(self, quiz_id: str) -> QuizFeedback:
        """Completar quiz y generar retroalimentación"""
        quiz = self.db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise ValueError("Quiz no encontrado")
        
        # Calcular estadísticas
        answers = self.db.query(QuizAnswer).filter(QuizAnswer.quiz_id == quiz_id).all()
        correct_answers = sum(1 for a in answers if a.is_correct)
        total_questions = len(answers)
        
        if total_questions == 0:
            raise ValueError("No hay respuestas para el quiz")
        
        # Calcular puntaje
        score_percentage = (correct_answers / total_questions) * 100
        quiz.score = score_percentage
        quiz.correct_answers = correct_answers
        quiz.status = "completed" if score_percentage >= quiz.passing_score else "failed"
        quiz.completed_at = datetime.utcnow()
        
        # Generar retroalimentación IA
        ai_feedback = self._generate_quiz_feedback(quiz, answers)
        quiz.ai_feedback = ai_feedback

        # Actualizar progreso ponderado
        self._update_weighted_progress(quiz)

        # ====== APLICAR XP AL USUARIO ======
        user = self.db.query(User).filter(User.id == quiz.user_id).first()
        if user and quiz.status == "completed":
            # Calcular XP basado en score (más XP por mejor rendimiento)
            base_xp = 50
            performance_multiplier = score_percentage / 100
            xp_earned = int(base_xp * performance_multiplier * (1 + (correct_answers * 0.1)))

            if xp_earned > 0:
                user.experience = (user.experience or 0) + xp_earned

                # Actualizar XP de liga semanal
                user_league = self.db.query(UserLeague).join(LeagueGroup).join(LeagueWeek).filter(
                    UserLeague.user_id == quiz.user_id,
                    LeagueWeek.is_active == True
                ).first()
                if user_league:
                    user_league.weekly_xp += xp_earned

            # Aplicar orbs si aprobó
            if score_percentage >= quiz.passing_score:
                user.orbs = (user.orbs or 0) + 10

        self.db.commit()
        
        return QuizFeedback(
            quiz_id=str(quiz.id),
            overall_score=score_percentage,
            strengths=ai_feedback.get("strengths", []),
            weaknesses=ai_feedback.get("weaknesses", []),
            recommendations=ai_feedback.get("recommendations", []),
            ai_analysis=ai_feedback
        )
    
    def _generate_quiz_feedback(self, quiz: Quiz, answers: List[QuizAnswer]) -> Dict[str, Any]:
        """Generar retroalimentación IA para el quiz completo"""
        correct_answers = [a for a in answers if a.is_correct]
        incorrect_answers = [a for a in answers if not a.is_correct]
        
        score_percentage = (len(correct_answers) / len(answers)) * 100
        
        feedback = {
            "score_percentage": score_percentage,
            "total_questions": len(answers),
            "correct_answers": len(correct_answers),
            "incorrect_answers": len(incorrect_answers),
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }
        
        if score_percentage >= 80:
            feedback["strengths"].append("Excelente comprensión del tema")
            feedback["recommendations"].append("Puedes avanzar al siguiente tema")
        elif score_percentage >= 60:
            feedback["strengths"].append("Buen progreso en el tema")
            feedback["weaknesses"].append("Algunas áreas necesitan refuerzo")
            feedback["recommendations"].append("Revisa los conceptos que fallaste")
        else:
            feedback["weaknesses"].append("Necesitas más práctica en este tema")
            feedback["recommendations"].append("Revisa el material de la unidad")
            feedback["recommendations"].append("Practica más ejercicios similares")
        
        return feedback
    
    def _update_weighted_progress(self, quiz: Quiz):
        """Actualizar progreso ponderado en plan_progress"""
        progress = self.db.query(PlanProgress).filter(
            PlanProgress.plan_id == quiz.plan_id,
            PlanProgress.unit_number == quiz.unit_number
        ).first()
        
        if progress:
            # Actualizar componente de ejercicios en weighted_progress
            weighted_data = progress.weighted_progress
            exercises = weighted_data.get("exercises", {})
            
            # Incrementar ejercicios completados
            exercises["completed"] = exercises.get("completed", 0) + 1
            exercises["total"] = exercises.get("total", 0) + 1
            
            weighted_data["exercises"] = exercises
            progress.weighted_progress = weighted_data
            
            # Recalcular score ponderado
            total_progress = (
                (weighted_data["videos"]["completed"] / max(weighted_data["videos"]["total"], 1)) * 0.3 +
                (weighted_data["exercises"]["completed"] / max(weighted_data["exercises"]["total"], 1)) * 0.5 +
                (weighted_data["readings"]["completed"] / max(weighted_data["readings"]["total"], 1)) * 0.2
            ) * 100
            
            progress.score = total_progress
            
            # Marcar como completado si alcanza el umbral
            if total_progress >= 80:
                progress.is_completed = True
                progress.completion_date = datetime.utcnow()
    
    def get_user_quizzes(self, user_id: str, plan_id: Optional[str] = None) -> List[Quiz]:
        """Obtener quizzes del usuario"""
        query = self.db.query(Quiz).filter(Quiz.user_id == user_id)
        
        if plan_id:
            query = query.filter(Quiz.plan_id == plan_id)
        
        return query.order_by(desc(Quiz.created_at)).all()
    
    def get_quiz_by_id(self, quiz_id: str, user_id: str) -> Optional[Quiz]:
        """Obtener quiz específico"""
        return self.db.query(Quiz).filter(
            Quiz.id == quiz_id,
            Quiz.user_id == user_id
        ).first() 