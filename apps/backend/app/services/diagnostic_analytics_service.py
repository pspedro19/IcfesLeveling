from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
import logging
from collections import Counter, defaultdict

from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.diagnostic_analytics import DiagnosticTestAnalytics, DiagnosticImprovementTracking, DiagnosticErrorPattern
from ..models.question import Question, Topic
from ..models.subject import Subject
from ..models.user import User

logger = logging.getLogger(__name__)

class DiagnosticAnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_detailed_analysis(self, diagnostic_test_id: str) -> DiagnosticTestAnalytics:
        """Crear análisis detallado del test diagnóstico"""
        test = self.db.query(DiagnosticTest).filter(DiagnosticTest.id == diagnostic_test_id).first()
        if not test:
            raise ValueError(f"Test diagnóstico {diagnostic_test_id} no encontrado")
        
        # Obtener todas las respuestas del test
        answers = self.db.query(DiagnosticTestAnswer).filter(
            DiagnosticTestAnswer.test_id == diagnostic_test_id
        ).all()
        
        if not answers:
            raise ValueError("No se encontraron respuestas para el test")
        
        # Análisis básico
        total_questions = len(answers)
        correct_answers = sum(1 for answer in answers if answer.is_correct)
        wrong_answers = total_questions - correct_answers
        score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Análisis temporal
        total_time = sum(answer.response_time_ms for answer in answers if answer.response_time_ms)
        avg_time_per_question = total_time / total_questions if total_questions > 0 else 0
        
        # Análisis por competencia y componente (extraer de Excel data)
        competency_scores = self._analyze_competencies(answers)
        component_scores = self._analyze_components(answers)
        cognitive_process_scores = self._analyze_cognitive_processes(answers)
        
        # Análisis de dificultad
        difficulty_performance = self._analyze_difficulty_performance(answers)
        
        # Análisis temporal detallado
        time_analysis = self._analyze_response_times(answers)
        
        # Patrones de respuesta
        response_patterns = self._analyze_response_patterns(answers)
        
        # Análisis comparativo
        percentile_rank = self._calculate_percentile_rank(score_percentage, str(test.subject_id))
        performance_vs_expected = self._calculate_performance_vs_expected(str(test.user_id), str(test.subject_id), score_percentage)
        
        # Recomendaciones inteligentes
        recommendations = self._generate_intelligent_recommendations(answers, score_percentage)
        
        # Crear registro de análisis
        analytics = DiagnosticTestAnalytics(
            diagnostic_test_id=diagnostic_test_id,
            user_id=test.user_id,
            subject_id=test.subject_id,
            total_questions=total_questions,
            correct_answers=correct_answers,
            wrong_answers=wrong_answers,
            score_percentage=score_percentage,
            competency_scores=competency_scores,
            component_scores=component_scores,
            cognitive_process_scores=cognitive_process_scores,
            total_time_seconds=total_time // 1000,
            average_time_per_question=avg_time_per_question / 1000,
            time_per_topic=time_analysis['time_per_topic'],
            questions_with_slow_response=time_analysis['slow_questions'],
            questions_with_fast_response=time_analysis['fast_questions'],
            difficulty_performance=difficulty_performance,
            easy_questions_score=difficulty_performance.get('easy', 0),
            medium_questions_score=difficulty_performance.get('medium', 0),
            hard_questions_score=difficulty_performance.get('hard', 0),
            response_patterns=response_patterns,
            percentile_rank=percentile_rank,
            performance_vs_expected=performance_vs_expected,
            recommended_topics=recommendations['topics'],
            critical_weaknesses=recommendations['weaknesses'],
            learning_style_indicators=recommendations['learning_style']
        )
        
        self.db.add(analytics)
        self.db.commit()
        self.db.refresh(analytics)
        
        # Actualizar tracking de mejora
        self._update_improvement_tracking(str(test.user_id), str(test.subject_id), score_percentage)
        
        # Identificar y registrar patrones de error
        self._identify_error_patterns(str(test.user_id), str(test.subject_id), answers)
        
        return analytics
    
    def _analyze_competencies(self, answers: List[DiagnosticTestAnswer]) -> Dict[str, float]:
        """Analizar performance por competencias ICFES"""
        competency_stats = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for answer in answers:
            question = answer.question
            # Extraer competencia de los tags o usar un mapeo predefinido
            competency = self._extract_competency_from_question(question)
            
            competency_stats[competency]['total'] += 1
            if answer.is_correct:
                competency_stats[competency]['correct'] += 1
        
        return {
            comp: (stats['correct'] / stats['total']) * 100 
            for comp, stats in competency_stats.items() 
            if stats['total'] > 0
        }
    
    def _analyze_components(self, answers: List[DiagnosticTestAnswer]) -> Dict[str, float]:
        """Analizar performance por componentes ICFES"""
        component_stats = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for answer in answers:
            question = answer.question
            component = self._extract_component_from_question(question)
            
            component_stats[component]['total'] += 1
            if answer.is_correct:
                component_stats[component]['correct'] += 1
        
        return {
            comp: (stats['correct'] / stats['total']) * 100 
            for comp, stats in component_stats.items() 
            if stats['total'] > 0
        }
    
    def _analyze_cognitive_processes(self, answers: List[DiagnosticTestAnswer]) -> Dict[str, float]:
        """Analizar performance por procesos cognitivos"""
        process_stats = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for answer in answers:
            question = answer.question
            process = self._extract_cognitive_process_from_question(question)
            
            process_stats[process]['total'] += 1
            if answer.is_correct:
                process_stats[process]['correct'] += 1
        
        return {
            proc: (stats['correct'] / stats['total']) * 100 
            for proc, stats in process_stats.items() 
            if stats['total'] > 0
        }
    
    def _analyze_difficulty_performance(self, answers: List[DiagnosticTestAnswer]) -> Dict[str, float]:
        """Analizar performance por nivel de dificultad"""
        difficulty_stats = {1: {'correct': 0, 'total': 0}, 2: {'correct': 0, 'total': 0}, 3: {'correct': 0, 'total': 0}}
        
        for answer in answers:
            difficulty = answer.question.difficulty
            if difficulty in difficulty_stats:
                difficulty_stats[difficulty]['total'] += 1
                if answer.is_correct:
                    difficulty_stats[difficulty]['correct'] += 1
        
        return {
            'easy': (difficulty_stats[1]['correct'] / difficulty_stats[1]['total']) * 100 if difficulty_stats[1]['total'] > 0 else 0,
            'medium': (difficulty_stats[2]['correct'] / difficulty_stats[2]['total']) * 100 if difficulty_stats[2]['total'] > 0 else 0,
            'hard': (difficulty_stats[3]['correct'] / difficulty_stats[3]['total']) * 100 if difficulty_stats[3]['total'] > 0 else 0
        }
    
    def _analyze_response_times(self, answers: List[DiagnosticTestAnswer]) -> Dict[str, Any]:
        """Analizar tiempos de respuesta"""
        if not answers:
            return {'time_per_topic': {}, 'slow_questions': [], 'fast_questions': []}
        
        # Calcular estadísticas de tiempo
        response_times = [answer.response_time_ms for answer in answers if answer.response_time_ms]
        if not response_times:
            return {'time_per_topic': {}, 'slow_questions': [], 'fast_questions': []}
        
        avg_time = sum(response_times) / len(response_times)
        
        # Tiempo por tema
        topic_times = defaultdict(list)
        for answer in answers:
            if answer.response_time_ms and answer.topic:
                topic_times[answer.topic.name].append(answer.response_time_ms)
        
        time_per_topic = {
            topic: sum(times) / len(times) 
            for topic, times in topic_times.items()
        }
        
        # Preguntas lentas (> 1.5x promedio) y rápidas (< 0.5x promedio)
        slow_threshold = avg_time * 1.5
        fast_threshold = avg_time * 0.5
        
        slow_questions = [str(answer.question_id) for answer in answers 
                         if answer.response_time_ms and answer.response_time_ms > slow_threshold]
        fast_questions = [str(answer.question_id) for answer in answers 
                         if answer.response_time_ms and answer.response_time_ms < fast_threshold]
        
        return {
            'time_per_topic': time_per_topic,
            'slow_questions': slow_questions,
            'fast_questions': fast_questions
        }
    
    def _analyze_response_patterns(self, answers: List[DiagnosticTestAnswer]) -> Dict[str, Any]:
        """Analizar patrones de respuesta"""
        patterns = {
            'consecutive_errors': 0,
            'error_streaks': [],
            'topic_consistency': {},
            'confidence_indicators': {}
        }
        
        # Analizar rachas de errores
        current_streak = 0
        error_streaks = []
        
        for answer in answers:
            if not answer.is_correct:
                current_streak += 1
            else:
                if current_streak > 0:
                    error_streaks.append(current_streak)
                current_streak = 0
        
        if current_streak > 0:
            error_streaks.append(current_streak)
        
        patterns['consecutive_errors'] = max(error_streaks) if error_streaks else 0
        patterns['error_streaks'] = error_streaks
        
        return patterns
    
    def _calculate_percentile_rank(self, score: float, subject_id: str) -> float:
        """Calcular percentil respecto a otros usuarios"""
        # Obtener scores de otros usuarios en la misma materia (últimos 30 días)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        other_scores = self.db.query(DiagnosticTestAnalytics.score_percentage).filter(
            and_(
                DiagnosticTestAnalytics.subject_id == subject_id,
                DiagnosticTestAnalytics.created_at >= cutoff_date
            )
        ).all()
        
        if not other_scores:
            return 50.0  # Si no hay datos, asumir percentil 50
        
        scores_list = [float(s[0]) for s in other_scores]
        scores_below = sum(1 for s in scores_list if s < score)
        
        return (scores_below / len(scores_list)) * 100
    
    def _calculate_performance_vs_expected(self, user_id: str, subject_id: str, current_score: float) -> float:
        """Calcular performance vs expectativa basada en historial"""
        # Obtener scores históricos del usuario
        historical_scores = self.db.query(DiagnosticTestAnalytics.score_percentage).filter(
            and_(
                DiagnosticTestAnalytics.user_id == user_id,
                DiagnosticTestAnalytics.subject_id == subject_id
            )
        ).order_by(desc(DiagnosticTestAnalytics.created_at)).limit(5).all()
        
        if not historical_scores:
            return 0.0  # No hay historial
        
        avg_historical = sum(float(s[0]) for s in historical_scores) / len(historical_scores)
        return current_score - avg_historical
    
    def _generate_intelligent_recommendations(self, answers: List[DiagnosticTestAnswer], score: float) -> Dict[str, Any]:
        """Generar recomendaciones inteligentes basadas en el análisis"""
        topics_to_improve = []
        critical_weaknesses = []
        learning_style = {}
        
        # Análizar temas con bajo rendimiento
        topic_performance = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for answer in answers:
            topic_name = answer.topic.name if answer.topic else "General"
            topic_performance[topic_name]['total'] += 1
            if answer.is_correct:
                topic_performance[topic_name]['correct'] += 1
        
        for topic, stats in topic_performance.items():
            if stats['total'] > 0:
                performance = (stats['correct'] / stats['total']) * 100
                if performance < 60:  # Menos del 60% correcto
                    topics_to_improve.append(topic)
                if performance < 40:  # Menos del 40% correcto
                    critical_weaknesses.append(topic)
        
        # Analizar estilo de aprendizaje basado en patrones de tiempo
        response_times = [answer.response_time_ms for answer in answers if answer.response_time_ms]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            learning_style = {
                'fast_responder': avg_time < 30000,  # Menos de 30 segundos promedio
                'thorough_analyzer': avg_time > 90000,  # Más de 90 segundos promedio
                'consistent_pace': max(response_times) / min(response_times) < 3 if min(response_times) > 0 else False
            }
        
        return {
            'topics': topics_to_improve,
            'weaknesses': critical_weaknesses,
            'learning_style': learning_style
        }
    
    def _update_improvement_tracking(self, user_id: str, subject_id: str, current_score: float):
        """Actualizar tracking de mejora del usuario"""
        tracking = self.db.query(DiagnosticImprovementTracking).filter(
            and_(
                DiagnosticImprovementTracking.user_id == user_id,
                DiagnosticImprovementTracking.subject_id == subject_id
            )
        ).first()
        
        if not tracking:
            # Crear nuevo tracking
            tracking = DiagnosticImprovementTracking(
                user_id=user_id,
                subject_id=subject_id,
                first_test_score=current_score,
                latest_test_score=current_score,
                score_trend=[current_score],
                tests_taken=1
            )
            self.db.add(tracking)
        else:
            # Actualizar tracking existente
            tracking.latest_test_score = current_score
            tracking.tests_taken += 1
            
            # Actualizar tendencia de scores
            if not tracking.score_trend:
                tracking.score_trend = []
            tracking.score_trend.append(current_score)
            
            # Mantener solo los últimos 10 scores
            if len(tracking.score_trend) > 10:
                tracking.score_trend = tracking.score_trend[-10:]
            
            # Calcular mejora
            if tracking.first_test_score:
                tracking.improvement_percentage = current_score - tracking.first_test_score
            
            # Calcular consistencia
            if len(tracking.score_trend) >= 3:
                scores = tracking.score_trend
                avg_score = sum(scores) / len(scores)
                variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
                tracking.consistency_score = max(0, 100 - variance)  # Mayor consistencia = menor varianza
        
        self.db.commit()
    
    def _identify_error_patterns(self, user_id: str, subject_id: str, answers: List[DiagnosticTestAnswer]):
        """Identificar y registrar patrones de error"""
        # Analizar errores por tipo de pregunta, dificultad, etc.
        error_types = {
            'conceptual': 0,
            'procedural': 0,
            'computational': 0,
            'reading': 0
        }
        
        for answer in answers:
            if not answer.is_correct:
                # Determinar tipo de error basado en características de la pregunta
                error_type = self._classify_error_type(answer.question)
                if error_type in error_types:
                    error_types[error_type] += 1
        
        # Registrar patrones significativos (más de 2 errores del mismo tipo)
        for error_type, count in error_types.items():
            if count >= 2:
                # Buscar patrón existente
                existing_pattern = self.db.query(DiagnosticErrorPattern).filter(
                    and_(
                        DiagnosticErrorPattern.user_id == user_id,
                        DiagnosticErrorPattern.subject_id == subject_id,
                        DiagnosticErrorPattern.error_type == error_type
                    )
                ).first()
                
                if existing_pattern:
                    existing_pattern.frequency += count
                    existing_pattern.last_occurrence = datetime.utcnow()
                else:
                    new_pattern = DiagnosticErrorPattern(
                        user_id=user_id,
                        subject_id=subject_id,
                        error_type=error_type,
                        frequency=count,
                        error_description=f"Errores frecuentes en preguntas de tipo {error_type}",
                        recommended_actions=self._get_recommended_actions(error_type)
                    )
                    self.db.add(new_pattern)
        
        self.db.commit()
    
    def _extract_competency_from_question(self, question: Question) -> str:
        """Extraer competencia ICFES de la pregunta"""
        if question.tags:
            for tag in question.tags:
                if 'competencia' in tag.lower():
                    return tag
        return "Competencia General"
    
    def _extract_component_from_question(self, question: Question) -> str:
        """Extraer componente ICFES de la pregunta"""
        if question.tags:
            for tag in question.tags:
                if 'componente' in tag.lower():
                    return tag
        return "Componente General"
    
    def _extract_cognitive_process_from_question(self, question: Question) -> str:
        """Extraer proceso cognitivo de la pregunta"""
        if question.tags:
            for tag in question.tags:
                if any(process in tag.lower() for process in ['interpretación', 'argumentación', 'proposición']):
                    return tag
        return "Proceso General"
    
    def _classify_error_type(self, question: Question) -> str:
        """Clasificar tipo de error basado en la pregunta"""
        # Clasificación simple basada en tags y características
        if question.tags:
            tags_text = ' '.join(question.tags).lower()
            if 'lectura' in tags_text or 'interpretación' in tags_text:
                return 'reading'
            elif 'cálculo' in tags_text or 'operación' in tags_text:
                return 'computational'
            elif 'procedimiento' in tags_text or 'método' in tags_text:
                return 'procedural'
        
        return 'conceptual'  # Default
    
    def _get_recommended_actions(self, error_type: str) -> List[str]:
        """Obtener acciones recomendadas para cada tipo de error"""
        recommendations = {
            'conceptual': [
                "Revisar conceptos fundamentales del tema",
                "Practicar con ejemplos básicos",
                "Ver videos explicativos de conceptos"
            ],
            'procedural': [
                "Practicar step-by-step solutions",
                "Revisar metodologías de resolución",
                "Hacer ejercicios guiados"
            ],
            'computational': [
                "Practicar operaciones básicas",
                "Revisar uso de calculadora",
                "Hacer ejercicios de cálculo mental"
            ],
            'reading': [
                "Practicar comprensión de lectura",
                "Técnicas de análisis de texto",
                "Ejercicios de interpretación"
            ]
        }
        
        return recommendations.get(error_type, ["Estudiar más el tema", "Practicar ejercicios similares"])
    
    def get_analytics_summary(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """Obtener resumen de analíticas para un usuario y materia"""
        # Obtener último análisis
        latest_analytics = self.db.query(DiagnosticTestAnalytics).filter(
            and_(
                DiagnosticTestAnalytics.user_id == user_id,
                DiagnosticTestAnalytics.subject_id == subject_id
            )
        ).order_by(desc(DiagnosticTestAnalytics.created_at)).first()
        
        # Obtener tracking de mejora
        improvement_tracking = self.db.query(DiagnosticImprovementTracking).filter(
            and_(
                DiagnosticImprovementTracking.user_id == user_id,
                DiagnosticImprovementTracking.subject_id == subject_id
            )
        ).first()
        
        # Obtener patrones de error activos
        error_patterns = self.db.query(DiagnosticErrorPattern).filter(
            and_(
                DiagnosticErrorPattern.user_id == user_id,
                DiagnosticErrorPattern.subject_id == subject_id,
                DiagnosticErrorPattern.error_resolved == False
            )
        ).all()
        
        return {
            'latest_analytics': latest_analytics,
            'improvement_tracking': improvement_tracking,
            'error_patterns': error_patterns,
            'has_data': latest_analytics is not None
        }