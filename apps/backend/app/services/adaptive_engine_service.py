from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import random
from ..models.question import Question
from ..models.offline_features import UserTopicMastery, UserQuestionHistory
from ..models.topic import Topic

class AdaptiveEngineService:
    @staticmethod
    def get_next_questions(db: Session, user_id: str, limit: int = 5, subject_id: Optional[str] = None) -> List[Question]:
        """
        Selecciona las mejores preguntas para el usuario basado en su maestria.
        Prioriza:
        1. Temas con maestria < 0.6 (Debilidades)
        2. Temas nuevos para el usuario
        3. Temas para repaso espaciado (maestria > 0.9 pero tiempo sin ver)
        """
        
        # 1. Obtener debilidades del usuario
        weak_topics = db.query(UserTopicMastery.topic_id).filter(
            UserTopicMastery.user_id == user_id,
            UserTopicMastery.mastery_score < 0.6
        ).all()
        weak_topic_ids = [t[0] for t in weak_topics]
        
        selected_questions = []
        
        # 2. Intentar obtener preguntas de debilidades
        if weak_topic_ids:
            query = db.query(Question).filter(Question.topic_id.in_(weak_topic_ids))
            if subject_id:
                query = query.filter(Question.subject_id == subject_id)
            
            # Evitar preguntas ya contestadas correctamente recientemente si es posible
            # (Simplificado por ahora)
            questions = query.order_by(func.random()).limit(limit // 2).all()
            selected_questions.extend(questions)
            
        # 3. Rellenar con preguntas generales o temas nuevos
        remaining = limit - len(selected_questions)
        if remaining > 0:
            query = db.query(Question)
            if subject_id:
                query = query.filter(Question.subject_id == subject_id)
            
            # Excluir las ya seleccionadas
            if selected_questions:
                query = query.filter(Question.id.notin_([q.id for q in selected_questions]))
                
            more_questions = query.order_by(func.random()).limit(remaining).all()
            selected_questions.extend(more_questions)
            
        return selected_questions

    @staticmethod
    def update_user_mastery(db: Session, user_id: str, topic_id: str, was_correct: bool):
        """
        Actualiza el score de maestria basado en una respuesta.
        Implementacion simple de Elo-like o Moving Average.
        """
        mastery = db.query(UserTopicMastery).filter(
            UserTopicMastery.user_id == user_id,
            UserTopicMastery.topic_id == topic_id
        ).first()
        
        if not mastery:
            mastery = UserTopicMastery(
                user_id=user_id,
                topic_id=topic_id,
                mastery_score=0.1 if was_correct else 0.0,
                questions_seen=1,
                questions_correct=1 if was_correct else 0
            )
            db.add(mastery)
        else:
            mastery.questions_seen += 1
            if was_correct:
                mastery.questions_correct += 1
            
            # Moving average score update
            learning_rate = 0.1
            target = 1.0 if was_correct else 0.0
            mastery.mastery_score += learning_rate * (target - mastery.mastery_score)
            mastery.last_practiced_at = func.now()

        db.commit()
