from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, case, cast, Float
from typing import List, Dict, Optional
import uuid
from datetime import datetime, timedelta
import math

from ..models.battle import Battle, BattleAnswer
from ..models.question import Question
from ..models.user import User
from ..models.subject import Subject
from ..models.topic import Topic
from ..models.question import Question
from ..schemas.analytics import (
    PersonalAnalytics, SubjectProgress, ICFESProjection, 
    NationalComparison, StrengthWeaknessHeatmap
)

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_personal_analytics(self, user_id: str) -> PersonalAnalytics:
        """Obtener analytics personales completos del usuario"""
        # Check if this is the development mock user
        if user_id == "00000000-0000-0000-0000-000000000001":
            # Return mock analytics for development
            return self._get_mock_analytics()
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Usuario no encontrado")
        
        # Obtener progreso por materia
        subjects_progress = self._get_subjects_progress(user_id)
        
        # Calcular proyección ICFES
        icfes_projection = self._calculate_icfes_projection(user_id)
        
        # Comparación nacional
        national_comparison = self._get_national_comparison(user_id)
        
        # Heatmap de fortalezas/debilidades
        strength_weakness_heatmap = self._get_strength_weakness_heatmap(user_id)
        
        # Métricas generales
        total_battles = self._get_total_battles(user_id)
        win_rate = self._calculate_win_rate(user_id)
        average_session_duration = self._get_average_session_duration(user_id)
        streak_days = self._get_streak_days(user_id)
        total_questions_answered = self._get_total_questions_answered(user_id)
        overall_accuracy = self._calculate_overall_accuracy(user_id)
        
        # Tendencias temporales
        weekly_progress = self._get_weekly_progress(user_id)
        monthly_trends = self._get_monthly_trends(user_id)
        
        return PersonalAnalytics(
            user_id=str(user.id),
            username=user.username,
            current_level=user.level,
            current_rank=user.rank,
            total_experience=user.experience,
            subjects_progress=subjects_progress,
            icfes_projection=icfes_projection,
            national_comparison=national_comparison,
            strength_weakness_heatmap=strength_weakness_heatmap,
            total_battles=total_battles,
            win_rate=win_rate,
            average_session_duration=average_session_duration,
            streak_days=streak_days,
            total_questions_answered=total_questions_answered,
            overall_accuracy=overall_accuracy,
            weekly_progress=weekly_progress,
            monthly_trends=monthly_trends,
            generated_at=datetime.utcnow()
        )
    
    def _get_subjects_progress(self, user_id: str) -> List[SubjectProgress]:
        """Obtener progreso detallado por materia"""
        # Consulta para obtener estadísticas por materia
        subject_stats = self.db.query(
            Subject.id,
            Subject.name,
            func.count(BattleAnswer.id).label('questions_answered'),
            func.sum(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('correct_answers'),
            func.avg(Question.difficulty).label('average_difficulty'),
            func.sum(Battle.experience_gained).label('total_experience'),
            func.max(Battle.created_at).label('last_activity')
        ).join(
            BattleAnswer, BattleAnswer.battle_id == Battle.id
        ).join(
            Question, Question.id == BattleAnswer.question_id
        ).join(
            Subject, Subject.id == Question.subject_id
        ).filter(
            Battle.user_id == user_id
        ).group_by(
            Subject.id, Subject.name
        ).all()
        
        progress_list = []
        for stat in subject_stats:
            accuracy = (stat.correct_answers / stat.questions_answered * 100) if stat.questions_answered > 0 else 0
            level_progress = min(100, (stat.total_experience or 0) / 1000 * 100)  # Progreso basado en experiencia
            
            progress_list.append(SubjectProgress(
                subject_id=str(stat.id),
                subject_name=stat.name,
                questions_answered=stat.questions_answered or 0,
                correct_answers=stat.correct_answers or 0,
                accuracy_percentage=round(accuracy, 2),
                average_difficulty=round(stat.average_difficulty or 0, 2),
                total_experience=stat.total_experience or 0,
                level_progress=round(level_progress, 2),
                last_activity=stat.last_activity or datetime.utcnow()
            ))
        
        return progress_list
    
    def _calculate_icfes_projection(self, user_id: str) -> ICFESProjection:
        """Calcular proyección de puntaje ICFES"""
        # Obtener rendimiento reciente
        recent_performance = self.db.query(
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('recent_accuracy'),
            func.avg(Question.difficulty).label('average_difficulty'),
            func.count(BattleAnswer.id).label('total_questions')
        ).join(
            BattleAnswer, BattleAnswer.battle_id == Battle.id
        ).join(
            Question, Question.id == BattleAnswer.question_id
        ).filter(
            Battle.user_id == user_id,
            Battle.created_at >= datetime.utcnow() - timedelta(days=30)
        ).first()
        
        if not recent_performance or recent_performance.total_questions == 0:
            return ICFESProjection(
                current_score=200.0,
                projected_score=200.0,
                improvement_rate=0.0,
                target_score=300.0,
                weeks_to_target=52,
                confidence_level=0.5
            )
        
        # Calcular puntaje actual basado en rendimiento
        accuracy = recent_performance.recent_accuracy * 100
        difficulty_bonus = (recent_performance.average_difficulty - 5) * 10
        current_score = 200 + (accuracy * 0.8) + difficulty_bonus
        
        # Calcular tasa de mejora (últimas 2 semanas vs 2 semanas anteriores)
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        four_weeks_ago = datetime.utcnow() - timedelta(days=28)
        
        recent_accuracy = self.db.query(
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0))
        ).join(
            BattleAnswer, BattleAnswer.battle_id == Battle.id
        ).filter(
            Battle.user_id == user_id,
            Battle.created_at >= two_weeks_ago
        ).scalar() or 0
        
        previous_accuracy = self.db.query(
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0))
        ).join(
            BattleAnswer, BattleAnswer.battle_id == Battle.id
        ).filter(
            Battle.user_id == user_id,
            Battle.created_at >= four_weeks_ago,
            Battle.created_at < two_weeks_ago
        ).scalar() or 0
        
        improvement_rate = (recent_accuracy - previous_accuracy) * 100 if previous_accuracy > 0 else 0
        
        # Proyección a 6 meses
        projected_score = current_score + (improvement_rate * 26)  # 26 semanas
        projected_score = min(500, max(200, projected_score))  # Límites ICFES
        
        # Calcular semanas hasta objetivo
        target_score = 350  # Puntaje objetivo
        weeks_to_target = max(1, int((target_score - current_score) / (improvement_rate * 2))) if improvement_rate > 0 else 52
        
        # Nivel de confianza basado en consistencia
        confidence_level = min(0.95, max(0.3, 0.5 + (accuracy / 200)))
        
        return ICFESProjection(
            current_score=round(current_score, 1),
            projected_score=round(projected_score, 1),
            improvement_rate=round(improvement_rate, 2),
            target_score=target_score,
            weeks_to_target=weeks_to_target,
            confidence_level=round(confidence_level, 2)
        )
    
    def _get_national_comparison(self, user_id: str) -> NationalComparison:
        """Obtener comparación con promedio nacional"""
        # Simular datos nacionales (en producción vendrían de estadísticas reales)
        national_average = 280.0
        total_students = 500000
        
        # Calcular puntaje del usuario
        user_performance = self.db.query(
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('accuracy'),
            func.avg(Question.difficulty).label('difficulty')
        ).join(
            BattleAnswer, BattleAnswer.battle_id == Battle.id
        ).join(
            Question, Question.id == BattleAnswer.question_id
        ).filter(
            Battle.user_id == user_id,
            Battle.created_at >= datetime.utcnow() - timedelta(days=30)
        ).first()
        
        if not user_performance:
            user_score = national_average
        else:
            accuracy = user_performance.accuracy * 100
            difficulty_bonus = (user_performance.difficulty - 5) * 10
            user_score = 200 + (accuracy * 0.8) + difficulty_bonus
        
        # Calcular percentil (simulado)
        user_percentile = min(99.9, max(0.1, 50 + ((user_score - national_average) / 50) * 25))
        
        # Posición en ranking
        ranking_position = max(1, int(total_students * (1 - user_percentile / 100)))
        
        return NationalComparison(
            user_percentile=round(user_percentile, 1),
            national_average=national_average,
            user_score=round(user_score, 1),
            difference_from_average=round(user_score - national_average, 1),
            ranking_position=ranking_position,
            total_students=total_students
        )
    
    def _get_strength_weakness_heatmap(self, user_id: str) -> List[StrengthWeaknessHeatmap]:
        """Obtener heatmap de fortalezas y debilidades por materia"""
        # Obtener rendimiento por tema dentro de cada materia
        topic_performance = self.db.query(
            Subject.name.label('subject_name'),
            Topic.name.label('topic_name'),
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('accuracy'),
            func.count(BattleAnswer.id).label('questions_count')
        ).join(
            BattleAnswer, BattleAnswer.battle_id == Battle.id
        ).join(
            Question, Question.id == BattleAnswer.question_id
        ).join(
            Subject, Subject.id == Question.subject_id
        ).join(
            Topic, Topic.id == Question.topic_id
        ).filter(
            Battle.user_id == user_id,
            Battle.created_at >= datetime.utcnow() - timedelta(days=90)
        ).group_by(
            Subject.name, Topic.name
        ).having(
            func.count(BattleAnswer.id) >= 5  # Mínimo 5 preguntas para estadística válida
        ).all()
        
        # Agrupar por materia
        subject_data = {}
        for perf in topic_performance:
            if perf.subject_name not in subject_data:
                subject_data[perf.subject_name] = {
                    'topics': [],
                    'strength_scores': [],
                    'weakness_scores': []
                }
            
            accuracy = perf.accuracy * 100
            subject_data[perf.subject_name]['topics'].append(perf.topic_name)
            subject_data[perf.subject_name]['strength_scores'].append(accuracy)
            subject_data[perf.subject_name]['weakness_scores'].append(100 - accuracy)
        
        heatmap_list = []
        for subject_name, data in subject_data.items():
            if data['topics']:
                overall_strength = sum(data['strength_scores']) / len(data['strength_scores'])
                overall_weakness = sum(data['weakness_scores']) / len(data['weakness_scores'])
                
                heatmap_list.append(StrengthWeaknessHeatmap(
                    subject=subject_name,
                    topics=data['topics'],
                    strength_scores=[round(score, 2) for score in data['strength_scores']],
                    weakness_scores=[round(score, 2) for score in data['weakness_scores']],
                    overall_strength=round(overall_strength, 2),
                    overall_weakness=round(overall_weakness, 2)
                ))
        
        return heatmap_list
    
    def _get_total_battles(self, user_id: str) -> int:
        """Obtener total de batallas del usuario"""
        return self.db.query(Battle).filter(Battle.user_id == user_id).count()
    
    def _calculate_win_rate(self, user_id: str) -> float:
        """Calcular tasa de victoria"""
        total_battles = self.db.query(Battle).filter(
            Battle.user_id == user_id,
            Battle.status == 'completed'
        ).count()
        
        won_battles = self.db.query(Battle).filter(
            Battle.user_id == user_id,
            Battle.status == 'completed',
            Battle.correct_answers > 0
        ).count()
        
        return round((won_battles / total_battles * 100) if total_battles > 0 else 0, 2)
    
    def _get_average_session_duration(self, user_id: str) -> int:
        """Obtener duración promedio de sesión"""
        avg_duration = self.db.query(
            func.avg(Battle.duration_seconds)
        ).filter(
            Battle.user_id == user_id,
            Battle.duration_seconds.isnot(None)
        ).scalar()
        
        return int(avg_duration or 0)
    
    def _get_streak_days(self, user_id: str) -> int:
        """Obtener días de racha actual"""
        # Simular cálculo de racha (en producción sería más complejo)
        recent_activity = self.db.query(
            func.max(Battle.created_at)
        ).filter(
            Battle.user_id == user_id
        ).scalar()
        
        if recent_activity:
            days_since_last = (datetime.utcnow() - recent_activity).days
            return max(0, 7 - days_since_last)  # Simulación de racha
        return 0
    
    def _get_total_questions_answered(self, user_id: str) -> int:
        """Obtener total de preguntas respondidas"""
        return self.db.query(BattleAnswer).join(
            Battle, Battle.id == BattleAnswer.battle_id
        ).filter(
            Battle.user_id == user_id
        ).count()
    
    def _calculate_overall_accuracy(self, user_id: str) -> float:
        """Calcular precisión general"""
        total_answers = self.db.query(BattleAnswer).join(
            Battle, Battle.id == BattleAnswer.battle_id
        ).filter(
            Battle.user_id == user_id
        ).count()
        
        correct_answers = self.db.query(BattleAnswer).join(
            Battle, Battle.id == BattleAnswer.battle_id
        ).filter(
            Battle.user_id == user_id,
            BattleAnswer.is_correct == True
        ).count()
        
        return round((correct_answers / total_answers * 100) if total_answers > 0 else 0, 2)
    
    def _get_weekly_progress(self, user_id: str) -> List[Dict[str, float]]:
        """Obtener progreso semanal"""
        # Simular datos de progreso semanal
        weeks = []
        for i in range(8):  # Últimas 8 semanas
            week_start = datetime.utcnow() - timedelta(weeks=i+1)
            week_end = datetime.utcnow() - timedelta(weeks=i)
            
            week_accuracy = self.db.query(
                func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0))
            ).join(
                BattleAnswer, BattleAnswer.battle_id == Battle.id
            ).filter(
                Battle.user_id == user_id,
                Battle.created_at >= week_start,
                Battle.created_at < week_end
            ).scalar() or 0
            
            weeks.append({
                'week': f"Semana {8-i}",
                'accuracy': round(week_accuracy * 100, 2),
                'questions': 0  # Se calcularía en producción
            })
        
        return weeks[::-1]  # Invertir para orden cronológico
    
    def _get_monthly_trends(self, user_id: str) -> List[Dict[str, float]]:
        """Obtener tendencias mensuales"""
        # Simular datos de tendencias mensuales
        months = []
        for i in range(6):  # Últimos 6 meses
            month_start = datetime.utcnow() - timedelta(days=30*(i+1))
            month_end = datetime.utcnow() - timedelta(days=30*i)
            
            month_accuracy = self.db.query(
                func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0))
            ).join(
                BattleAnswer, BattleAnswer.battle_id == Battle.id
            ).filter(
                Battle.user_id == user_id,
                Battle.created_at >= month_start,
                Battle.created_at < month_end
            ).scalar() or 0
            
            months.append({
                'month': f"Mes {6-i}",
                'accuracy': round(month_accuracy * 100, 2),
                'experience': 0  # Se calcularía en producción
            })
        
        return months[::-1]  # Invertir para orden cronológico
    
    def _get_mock_analytics(self) -> PersonalAnalytics:
        """Return mock analytics for development mode"""
        from ..core.config import settings
        
        if settings.ENVIRONMENT != "development":
            raise ValueError("Mock analytics only available in development mode")
        
        return PersonalAnalytics(
            user_id="00000000-0000-0000-0000-000000000001",
            username="dev_user",
            current_level=5,
            current_rank="C",
            total_experience=2500,
            subjects_progress=[
                SubjectProgress(
                    subject_id="1",
                    subject_name="Matemáticas",
                    questions_answered=50,
                    correct_answers=35,
                    accuracy_percentage=70.0,
                    level_progress=65.0,
                    average_difficulty=3.2,
                    total_experience=800,
                    last_activity=datetime.utcnow()
                ),
                SubjectProgress(
                    subject_id="2", 
                    subject_name="Lenguaje",
                    questions_answered=45,
                    correct_answers=32,
                    accuracy_percentage=71.1,
                    level_progress=58.0,
                    average_difficulty=2.8,
                    total_experience=650,
                    last_activity=datetime.utcnow()
                )
            ],
            icfes_projection=ICFESProjection(
                current_score=280.0,
                projected_score=320.0,
                improvement_rate=0.15,
                target_score=350.0,
                weeks_to_target=8,
                confidence_level=0.85
            ),
            national_comparison=NationalComparison(
                user_percentile=75.5,
                national_average=280.0,
                user_score=320.0,
                difference_from_average=40.0,
                ranking_position=12500,
                total_students=50000
            ),
            strength_weakness_heatmap=[
                StrengthWeaknessHeatmap(
                    subject="Matemáticas",
                    topics=["Álgebra", "Geometría", "Trigonometría"],
                    strength_scores=[0.8, 0.7, 0.3],
                    weakness_scores=[0.2, 0.3, 0.7],
                    overall_strength=0.6,
                    overall_weakness=0.4
                )
            ],
            total_battles=25,
            win_rate=68.0,
            average_session_duration=1800,
            streak_days=3,
            total_questions_answered=95,
            overall_accuracy=70.5,
            weekly_progress=[
                {"week": 1.0, "experience": 150.0, "accuracy": 72.0},
                {"week": 2.0, "experience": 200.0, "accuracy": 68.0}
            ],
            monthly_trends=[
                {"month": 1.0, "experience": 800.0, "accuracy": 70.0},
                {"month": 2.0, "experience": 1200.0, "accuracy": 71.0}
            ],
            generated_at=datetime.utcnow()
        ) 