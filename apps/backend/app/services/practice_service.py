from uuid import UUID
from sqlalchemy.orm import Session, subqueryload
from sqlalchemy import func, case
from typing import List, Optional, Dict, Any
from datetime import datetime
import random

from ..models.practice_session import PracticeSession, PracticeAnswer, UserQuestionMastery
from ..models.question import Question
from ..models.user import User
from ..models.mobile_offline import UserLeague, LeagueGroup, LeagueWeek


class PracticeService:
    """Servicio para el modo de juego estilo Millonario"""

    def __init__(self, db: Session):
        self.db = db

    # ========== SESIONES ==========

    def create_session(
        self,
        user_id: UUID,
        session_type: str = "practice",
        subject_id: Optional[UUID] = None,
        topic_id: Optional[UUID] = None,
        difficulty: int = 5,
        max_questions: int = 15
    ) -> PracticeSession:
        """
        Crea nueva sesión de práctica.
        """
        questions = self._select_questions(
            user_id=user_id,
            count=max_questions,
            subject_id=subject_id,
            topic_id=topic_id,
            target_difficulty=difficulty
        )

        if not questions:
            raise ValueError("No questions found for the specified criteria.")

        session = PracticeSession(
            user_id=user_id,
            session_type=session_type,
            target_subject_id=subject_id,
            target_topic_id=topic_id,
            difficulty_level=difficulty,
            max_questions=len(questions),
            lifelines_available={"fifty_fifty": True, "ask_ai": True, "skip": True}
        )
        self.db.add(session)
        self.db.flush()  # Flush to get the session ID

        # Create placeholder answers
        for i, question in enumerate(questions):
            answer = PracticeAnswer(
                session_id=session.id,
                question_id=question.id,
                question_order=i
            )
            self.db.add(answer)
        
        self.db.commit()
        self.db.refresh(session)
        
        return session

    def get_session(self, session_id: UUID) -> PracticeSession:
        """Obtener sesión por ID"""
        return self.db.query(PracticeSession).filter(PracticeSession.id == session_id).first()

    def get_current_question(self, session_id: UUID) -> Question:
        """
        Obtener la pregunta actual de la sesión.
        """
        session = self.get_session(session_id)
        if not session or session.status != 'active':
            return None

        answer = self.db.query(PracticeAnswer).filter(
            PracticeAnswer.session_id == session_id,
            PracticeAnswer.question_order == session.current_question_index
        ).options(subqueryload(PracticeAnswer.question)).first()

        return answer.question if answer else None

    # ========== RESPUESTAS ==========

    def submit_answer(
        self,
        session_id: UUID,
        question_id: UUID,
        answer: str,
        response_time_ms: int
    ) -> Dict[str, Any]:
        """
        Procesar respuesta del usuario.
        """
        session = self.get_session(session_id)
        if not session or session.status != 'active':
            raise ValueError("Invalid or completed session.")

        practice_answer = self.db.query(PracticeAnswer).filter(
            PracticeAnswer.session_id == session_id,
            PracticeAnswer.question_id == question_id,
            PracticeAnswer.question_order == session.current_question_index
        ).options(subqueryload(PracticeAnswer.question)).first()

        if not practice_answer:
            raise ValueError("Question not found in this session or out of order.")

        question = practice_answer.question
        is_correct = (answer.upper() == question.correct_answer.upper())

        # Update session
        session.questions_answered += 1
        if is_correct:
            session.correct_answers += 1
            session.current_streak += 1
            if session.current_streak > session.max_streak:
                session.max_streak = session.current_streak
        else:
            session.current_streak = 0
        
        # Calculate XP
        xp_earned = self._calculate_xp(is_correct, response_time_ms, session.current_streak, question.difficulty)
        session.total_xp_earned += xp_earned

        # Update PracticeAnswer
        practice_answer.user_answer = answer.upper()
        practice_answer.is_correct = is_correct
        practice_answer.response_time_ms = response_time_ms
        practice_answer.xp_earned = xp_earned

        # Update UserQuestionMastery
        mastery = self.db.query(UserQuestionMastery).filter_by(user_id=session.user_id, question_id=question.id).first()
        if not mastery:
            mastery = UserQuestionMastery(user_id=session.user_id, question_id=question.id, first_attempt_date=datetime.utcnow())
            self.db.add(mastery)
        mastery.update_performance(is_correct, response_time_ms, answer)
        
        # Advance session
        session.current_question_index += 1
        session_complete = session.current_question_index >= session.max_questions

        if session_complete:
            session.status = "completed"
            session.completed_at = datetime.utcnow()

        self.db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "xp_earned": xp_earned,
            "gold_earned": 10 if is_correct else 0, # Simple gold reward
            "current_streak": session.current_streak,
            "session_progress": (session.current_question_index / session.max_questions) * 100,
            "next_question_available": not session_complete,
            "session_complete": session_complete
        }

    # ========== COMODINES ==========

    def use_fifty_fifty(self, session_id: UUID, question_id: UUID) -> List[str]:
        """
        Usar comodín 50/50.
        """
        session = self.get_session(session_id)
        if not session or not session.lifelines_available.get("fifty_fifty"):
            raise ValueError("50/50 lifeline not available.")

        question = self.db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise ValueError("Question not found.")

        session.use_lifeline("fifty_fifty")
        
        correct_answer = question.correct_answer.upper()
        options = list(question.options.keys())
        incorrect_options = [opt for opt in options if opt != correct_answer]
        
        # Remove one random incorrect option, leaving one incorrect and the correct one
        random.shuffle(incorrect_options)
        to_eliminate = incorrect_options[1:] # Eliminate all but one incorrect option

        # Update the answer to track lifeline usage
        practice_answer = self.db.query(PracticeAnswer).filter_by(session_id=session.id, question_id=question.id).first()
        if practice_answer:
            lifelines = practice_answer.lifelines_used or []
            lifelines.append("fifty_fifty")
            practice_answer.lifelines_used = lifelines
            practice_answer.fifty_fifty_eliminated = to_eliminate

        self.db.commit()
        return to_eliminate

    def use_ask_ai(self, session_id: UUID, question_id: UUID) -> str:
        """
        Usar comodín "Preguntar a la IA".
        """
        session = self.get_session(session_id)
        if not session or not session.lifelines_available.get("ask_ai"):
            raise ValueError("Ask AI lifeline not available.")

        question = self.db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise ValueError("Question not found.")

        session.use_lifeline("ask_ai")
        
        # Update the answer to track lifeline usage
        practice_answer = self.db.query(PracticeAnswer).filter_by(session_id=session.id, question_id=question.id).first()
        if practice_answer:
            lifelines = practice_answer.lifelines_used or []
            lifelines.append("ask_ai")
            practice_answer.lifelines_used = lifelines
            practice_answer.ai_hint_shown = True
        
        self.db.commit()

        # Placeholder for real AI integration
        return f"Pista para la pregunta: {question.hint or 'Intenta pensar en el tema principal.'}"

    def use_skip(self, session_id: UUID) -> Dict[str, Any]:
        """
        Saltar pregunta actual.
        """
        session = self.get_session(session_id)
        if not session or not session.lifelines_available.get("skip"):
            raise ValueError("Skip lifeline not available.")
        
        if session.current_question_index >= session.max_questions - 1:
            raise ValueError("Cannot skip the last question.")

        session.use_lifeline("skip")
        session.current_question_index += 1
        
        self.db.commit()

        next_question = self.get_current_question(session_id)

        return {
            "success": True,
            "next_question_id": next_question.id if next_question else None
        }

    # ========== FINALIZACIÓN ==========

    def complete_session(self, session_id: UUID) -> Dict[str, Any]:
        """
        Finalizar sesión y calcular resultados.
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found.")

        if session.status != "completed":
            session.status = "completed"
            session.completed_at = datetime.utcnow()

        user = self.db.query(User).filter(User.id == session.user_id).first()
        if user:
            user.gold += session.total_gold_earned
            user.orbs += session.total_orbs_earned

            # Aplicar XP ganado al usuario
            if session.total_xp_earned > 0:
                user.experience = (user.experience or 0) + session.total_xp_earned

                # Actualizar XP de liga semanal
                user_league = self.db.query(UserLeague).join(LeagueGroup).join(LeagueWeek).filter(
                    UserLeague.user_id == session.user_id,
                    LeagueWeek.is_active == True
                ).first()
                if user_league:
                    user_league.weekly_xp += session.total_xp_earned
        
        # Placeholder for achievement check
        achievements_unlocked = []
        if session.correct_answers == session.max_questions:
            achievements_unlocked.append("millionaire_perfect")
        elif session.questions_answered == session.max_questions:
            achievements_unlocked.append("millionaire_complete")

        session.achievements_unlocked = achievements_unlocked
        
        # Calculate final stats
        accuracy = (session.correct_answers / session.questions_answered) * 100 if session.questions_answered > 0 else 0
        
        all_answers = self.db.query(PracticeAnswer).filter(PracticeAnswer.session_id == session.id).all()
        total_response_time = sum(a.response_time_ms for a in all_answers if a.response_time_ms > 0)
        avg_response_time = total_response_time / len(all_answers) if all_answers else 0

        self.db.commit()

        return {
            "session_id": session.id,
            "total_questions": session.max_questions,
            "correct_answers": session.correct_answers,
            "wrong_answers": session.questions_answered - session.correct_answers,
            "skipped": session.max_questions - session.questions_answered,
            "accuracy": round(accuracy, 2),
            "max_streak": session.max_streak,
            "total_time_seconds": session.total_time_seconds,
            "avg_response_time_ms": avg_response_time,
            "xp_earned": session.total_xp_earned,
            "gold_earned": session.total_gold_earned,
            "orbs_earned": session.total_orbs_earned,
            "achievements_unlocked": achievements_unlocked,
            "mastery_improvements": session.mastery_improvements
        }

    def get_user_history(self, user_id: UUID, limit: int = 10) -> List[PracticeSession]:
        """Gets the user's practice session history."""
        return self.db.query(PracticeSession).filter(
            PracticeSession.user_id == user_id
        ).order_by(PracticeSession.completed_at.desc()).limit(limit).all()

    # ========== SELECCIÓN DE PREGUNTAS ==========

    def _select_questions(
        self,
        user_id: UUID,
        count: int,
        subject_id: Optional[UUID],
        topic_id: Optional[UUID],
        target_difficulty: int
    ) -> List[Question]:
        """
        Seleccionar preguntas para la sesión.
        """
        # 1. Get failed questions
        failed_questions_query = self.db.query(Question).join(UserQuestionMastery).filter(
            UserQuestionMastery.user_id == user_id,
            UserQuestionMastery.needs_review == True
        )
        if subject_id:
            failed_questions_query = failed_questions_query.filter(Question.subject_id == subject_id)
        if topic_id:
            failed_questions_query = failed_questions_query.filter(Question.topic_id == topic_id)
        
        failed_questions = failed_questions_query.order_by(func.random()).limit(int(count * 0.6)).all()

        # 2. Get new questions
        new_questions_count = count - len(failed_questions)
        if new_questions_count > 0:
            answered_question_ids = self.db.query(UserQuestionMastery.question_id).filter(UserQuestionMastery.user_id == user_id)
            
            new_questions_query = self.db.query(Question).filter(
                Question.id.notin_(answered_question_ids)
            )
            if subject_id:
                new_questions_query = new_questions_query.filter(Question.subject_id == subject_id)
            if topic_id:
                new_questions_query = new_questions_query.filter(Question.topic_id == topic_id)

            new_questions = new_questions_query.order_by(func.random()).limit(new_questions_count).all()
        else:
            new_questions = []

        # 3. Mix and sort
        selected_questions = failed_questions + new_questions
        
        # Sort by difficulty with some randomness
        selected_questions.sort(key=lambda q: q.difficulty + random.uniform(-0.5, 0.5))
        
        return selected_questions

    def _calculate_xp(
        self,
        is_correct: bool,
        response_time_ms: int,
        streak: int,
        difficulty: int
    ) -> int:
        """
        Calcular XP ganado por respuesta.
        """
        if not is_correct:
            return 0

        # Base XP
        base_xp = 10

        # Speed bonus
        speed_bonus = 0
        if response_time_ms < 10000:  # < 10s
            speed_bonus = 5
        elif response_time_ms < 20000:  # < 20s
            speed_bonus = 3

        # Streak bonus
        streak_bonus = (streak - 1) * 2 if streak > 0 else 0
        
        # Difficulty multiplier
        difficulty_multiplier = 1.0 + ((difficulty - 5) / 10.0) # From 0.6 to 1.5 for diff 1-10

        total_xp = (base_xp + speed_bonus + streak_bonus) * difficulty_multiplier
        
        return int(total_xp)
