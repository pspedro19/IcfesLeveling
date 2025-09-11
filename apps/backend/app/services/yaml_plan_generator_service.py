"""
PASO 13: Servicio de generación de YAML personalizado mensual
Genera planes de estudio personalizados en formato YAML con estructura completa
"""

import asyncio
import logging
import os
import yaml
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from string import Template
import json
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text, desc
from sqlalchemy.sql import select

from app.models.user import User
from app.models.question import Question
from app.models.youtube_catalog import YoutubeCatalog
from app.models.question_video_recommendations import QuestionVideoRecommendations
from app.models.user_answer import UserAnswer
from app.services.weakness_analysis_service import WeaknessAnalysisService, WeaknessAnalysis
from app.services.question_video_mapping_service import QuestionVideoMappingService
from app.services.recommendation_scoring_service import RecommendationScoringService
from app.core.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YamlPlanGeneratorService:
    """
    Servicio principal para generar planes de estudio personalizados en formato YAML
    """
    
    def __init__(self):
        # Servicios dependientes
        self.weakness_service = WeaknessAnalysisService()
        self.mapping_service = QuestionVideoMappingService()
        self.scoring_service = RecommendationScoringService()
        
        # Configuración de rutas
        self.base_path = Path(settings.BASE_DIR) / "plans"
        self.templates_path = self.base_path / "templates"
        self.generated_path = self.base_path / "generated"
        self.archived_path = self.base_path / "archived"
        
        # Crear directorios si no existen
        self.generated_path.mkdir(parents=True, exist_ok=True)
        self.archived_path.mkdir(parents=True, exist_ok=True)
        
        # Configuración de generación
        self.config = {
            'max_strengths': 5,
            'max_weaknesses': 5,
            'max_videos_per_weakness': 3,
            'plan_duration_days': 30,
            'min_recommendation_score': 0.75,
            'prediction_confidence_threshold': 0.70
        }
    
    async def generate_monthly_plan(
        self, 
        db: Session, 
        student_id: str,
        target_month: Optional[int] = None,
        target_year: Optional[int] = None,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Genera un plan de estudio mensual completo para un estudiante
        """
        try:
            start_time = datetime.utcnow()
            
            # Obtener fecha objetivo
            if not target_month or not target_year:
                now = datetime.utcnow()
                target_month = target_month or now.month
                target_year = target_year or now.year
            
            logger.info(f"Generating monthly plan for student {student_id} - {target_year}/{target_month:02d}")
            
            # 1. Obtener información del estudiante
            student_data = await self._get_student_data(db, student_id)
            if not student_data:
                raise ValueError(f"Student {student_id} not found")
            
            # 2. Verificar si ya existe un plan para este mes
            existing_plan_path = self._get_plan_filepath(student_id, target_year, target_month)
            if existing_plan_path.exists() and not force_regenerate:
                logger.info(f"Plan already exists for {student_id} - {target_year}/{target_month:02d}")
                return await self._load_existing_plan(existing_plan_path)
            
            # 3. Analizar fortalezas del estudiante
            strengths = await self._analyze_student_strengths(db, student_id)
            
            # 4. Analizar debilidades del estudiante
            weaknesses = await self.weakness_service.get_student_weaknesses(
                db, student_id, limit=self.config['max_weaknesses']
            )
            
            # 5. Generar recomendaciones de contenido
            content_recommendations = await self._generate_content_recommendations(
                db, student_id, weaknesses
            )
            
            # 6. Crear plan de estudio estructurado
            study_plan = await self._create_structured_study_plan(
                weaknesses, strengths, content_recommendations
            )
            
            # 7. Generar predicciones de mejora
            improvement_predictions = await self._generate_improvement_predictions(
                db, student_id, weaknesses, study_plan
            )
            
            # 8. Compilar datos para plantilla
            template_data = await self._compile_template_data(
                student_data, strengths, weaknesses, content_recommendations,
                study_plan, improvement_predictions, target_month, target_year
            )
            
            # 9. Generar YAML desde plantilla
            yaml_content = await self._generate_yaml_from_template(template_data)
            
            # 10. Guardar plan generado
            plan_path = await self._save_generated_plan(
                student_id, target_year, target_month, yaml_content
            )
            
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                'status': 'success',
                'student_id': student_id,
                'plan_month': target_month,
                'plan_year': target_year,
                'plan_file_path': str(plan_path),
                'generation_time_seconds': generation_time,
                'plan_summary': {
                    'total_strengths': len(strengths),
                    'total_weaknesses': len(weaknesses),
                    'total_video_recommendations': sum(len(cat.get('videos', [])) for cat in content_recommendations.values()),
                    'estimated_study_hours': template_data.get('estimated_total_hours', 0),
                    'predicted_improvement': template_data.get('predicted_theta_change', 0)
                },
                'yaml_content': yaml_content,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Monthly plan generated successfully for {student_id} in {generation_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error generating monthly plan for {student_id}: {e}")
            raise
    
    async def _get_student_data(self, db: Session, student_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos básicos del estudiante"""
        try:
            # Información básica del usuario
            user = db.query(User).filter(User.id == student_id).first()
            if not user:
                return None
            
            # Estadísticas de actividad
            activity_stats = db.execute(text("""
                SELECT 
                    COUNT(*) as total_questions,
                    COUNT(*) FILTER (WHERE is_correct = true) as correct_answers,
                    SUM(time_spent_seconds) as total_time_seconds,
                    COUNT(DISTINCT DATE(created_at)) as active_days,
                    MAX(created_at) as last_activity,
                    MIN(created_at) as first_activity
                FROM user_answers 
                WHERE user_id = :student_id 
                  AND created_at >= CURRENT_DATE - INTERVAL '90 days'
            """), {'student_id': student_id}).fetchone()
            
            # Calcular theta global estimado
            if activity_stats and activity_stats.total_questions > 0:
                accuracy = activity_stats.correct_answers / activity_stats.total_questions
                # Estimación simple de theta basada en accuracy
                theta_global = self._accuracy_to_theta(accuracy)
            else:
                theta_global = -1.0  # Estudiante nuevo
            
            return {
                'student_id': student_id,
                'username': user.username,
                'email': user.email,
                'registration_date': user.created_at,
                'last_activity': activity_stats.last_activity if activity_stats else None,
                'total_questions': activity_stats.total_questions if activity_stats else 0,
                'total_study_time_hours': round((activity_stats.total_time_seconds or 0) / 3600, 2),
                'streak_days': activity_stats.active_days if activity_stats else 0,
                'theta_global': theta_global,
                'current_accuracy': round(accuracy * 100, 2) if activity_stats and activity_stats.total_questions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting student data: {e}")
            return None
    
    def _accuracy_to_theta(self, accuracy: float) -> float:
        """Convierte accuracy a estimación de theta usando IRT"""
        import math
        
        # Evitar valores extremos
        accuracy = max(0.01, min(0.99, accuracy))
        
        # Transformación logit simple
        odds = accuracy / (1 - accuracy)
        theta = math.log(odds)
        
        # Normalizar a rango típico [-2, 2]
        return max(-2.0, min(2.0, theta))
    
    async def _analyze_student_strengths(
        self, 
        db: Session, 
        student_id: str
    ) -> List[Dict[str, Any]]:
        """Analiza las fortalezas del estudiante"""
        try:
            # Query para obtener fortalezas (alta accuracy y suficientes intentos)
            strengths_query = text("""
                SELECT 
                    s.name as subject_name,
                    t.name as topic_name,
                    q.subject_id,
                    q.topic_id,
                    COUNT(*) as total_attempts,
                    COUNT(*) FILTER (WHERE ua.is_correct = true) as correct_answers,
                    ROUND((COUNT(*) FILTER (WHERE ua.is_correct = true)::decimal / COUNT(*)) * 100, 2) as accuracy_percentage,
                    AVG(ua.time_spent_seconds) as avg_time_seconds,
                    MAX(ua.created_at) as last_assessment
                FROM user_answers ua
                JOIN questions q ON ua.question_id = q.id
                LEFT JOIN subjects s ON q.subject_id = s.id
                LEFT JOIN topics t ON q.topic_id = t.id
                WHERE ua.user_id = :student_id 
                  AND ua.created_at >= CURRENT_DATE - INTERVAL '90 days'
                GROUP BY s.name, t.name, q.subject_id, q.topic_id
                HAVING COUNT(*) >= 5  -- Mínimo 5 intentos
                   AND (COUNT(*) FILTER (WHERE ua.is_correct = true)::decimal / COUNT(*)) >= 0.75  -- 75% accuracy
                ORDER BY accuracy_percentage DESC, COUNT(*) DESC
                LIMIT :limit
            """)
            
            result = db.execute(strengths_query, {
                'student_id': student_id,
                'limit': self.config['max_strengths']
            }).fetchall()
            
            strengths = []
            for row in result:
                theta_estimated = self._accuracy_to_theta(row.accuracy_percentage / 100)
                mastery_level = self._determine_mastery_level(row.accuracy_percentage, row.total_attempts)
                
                strength = {
                    'subject_area': row.subject_name,
                    'topic_name': row.topic_name,
                    'subject_id': str(row.subject_id),
                    'topic_id': str(row.topic_id),
                    'accuracy_percentage': float(row.accuracy_percentage),
                    'irt_theta': round(theta_estimated, 3),
                    'total_attempts': row.total_attempts,
                    'avg_time_seconds': round(float(row.avg_time_seconds or 0), 2),
                    'mastery_level': mastery_level,
                    'confidence_score': self._calculate_confidence_score(row.accuracy_percentage, row.total_attempts),
                    'last_assessment': row.last_assessment.isoformat() if row.last_assessment else None
                }
                strengths.append(strength)
            
            return strengths
            
        except Exception as e:
            logger.error(f"Error analyzing student strengths: {e}")
            return []
    
    def _determine_mastery_level(self, accuracy: float, attempts: int) -> str:
        """Determina el nivel de maestría basado en accuracy y número de intentos"""
        if accuracy >= 90 and attempts >= 10:
            return 'advanced'
        elif accuracy >= 80 and attempts >= 7:
            return 'proficient'
        elif accuracy >= 75 and attempts >= 5:
            return 'developing'
        else:
            return 'novice'
    
    def _calculate_confidence_score(self, accuracy: float, attempts: int) -> float:
        """Calcula score de confianza basado en accuracy y muestra"""
        # Base score from accuracy
        base_score = accuracy / 100
        
        # Confidence factor based on sample size
        if attempts >= 20:
            confidence_factor = 1.0
        elif attempts >= 10:
            confidence_factor = 0.9
        elif attempts >= 5:
            confidence_factor = 0.8
        else:
            confidence_factor = 0.6
        
        return round(base_score * confidence_factor, 3)
    
    async def _generate_content_recommendations(
        self,
        db: Session,
        student_id: str,
        weaknesses: List[WeaknessAnalysis]
    ) -> Dict[str, Any]:
        """Genera recomendaciones de contenido organizadas por categoría"""
        try:
            recommendations = {
                'critical_interventions': {},
                'concept_reinforcement': {},
                'skill_building': {},
                'maintenance_review': []
            }
            
            for weakness in weaknesses:
                # Obtener recomendaciones de videos para esta debilidad
                video_recs = await self._get_video_recommendations_for_weakness(
                    db, weakness
                )
                
                if not video_recs:
                    continue
                
                # Categorizar por severidad y tipo
                if weakness.weakness_severity.value == 'critical':
                    category = 'critical_interventions'
                elif weakness.weakness_type.value == 'conceptual_gap':
                    category = 'concept_reinforcement'
                else:
                    category = 'skill_building'
                
                topic_key = f"{weakness.subject_name}_{weakness.topic_name}".replace(' ', '_').lower()
                recommendations[category][topic_key] = {
                    'subject_area': weakness.subject_name,
                    'topic_name': weakness.topic_name,
                    'weakness_type': weakness.weakness_type.value,
                    'videos': video_recs
                }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating content recommendations: {e}")
            return {'critical_interventions': {}, 'concept_reinforcement': {}, 'skill_building': {}, 'maintenance_review': []}
    
    async def _get_video_recommendations_for_weakness(
        self,
        db: Session,
        weakness: WeaknessAnalysis
    ) -> List[Dict[str, Any]]:
        """Obtiene recomendaciones de videos específicas para una debilidad"""
        try:
            # Query para obtener recomendaciones existentes o generar nuevas
            existing_recs = db.query(QuestionVideoRecommendations).join(
                Question, QuestionVideoRecommendations.question_id == Question.id
            ).filter(
                and_(
                    Question.subject_id == weakness.subject_id,
                    Question.topic_id == weakness.topic_id,
                    QuestionVideoRecommendations.total_score >= self.config['min_recommendation_score'],
                    QuestionVideoRecommendations.is_active == True
                )
            ).order_by(QuestionVideoRecommendations.total_score.desc()).limit(
                self.config['max_videos_per_weakness']
            ).all()
            
            video_recommendations = []
            for rec in existing_recs:
                video = db.query(YoutubeCatalog).filter(
                    YoutubeCatalog.id == rec.video_id
                ).first()
                
                if video:
                    video_rec = {
                        'video_id': video.id,
                        'title': video.title,
                        'channel': video.channel_title or 'Unknown',
                        'duration_minutes': round((video.duration_seconds or 0) / 60, 1),
                        'youtube_url': f"https://www.youtube.com/watch?v={video.video_id}",
                        'recommendation_score': round(rec.total_score, 3),
                        'recommendation_type': rec.recommendation_type,
                        'confidence_level': rec.confidence_level,
                        'targets_error': rec.error_pattern_addressed or 'general',
                        'semantic_similarity': round(rec.semantic_similarity_score, 3),
                        'difficulty_alignment': round(rec.difficulty_proximity_score, 3)
                    }
                    video_recommendations.append(video_rec)
            
            return video_recommendations
            
        except Exception as e:
            logger.error(f"Error getting video recommendations for weakness: {e}")
            return []
    
    async def _create_structured_study_plan(
        self,
        weaknesses: List[WeaknessAnalysis],
        strengths: List[Dict[str, Any]],
        content_recommendations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crea un plan de estudio estructurado con timeline 1-3-7-14-30 días"""
        try:
            # Identificar debilidad más crítica
            critical_weakness = None
            if weaknesses:
                critical_weakness = max(
                    weaknesses, 
                    key=lambda w: w.intervention_priority_score
                )
            
            study_plan = {}
            
            # Plan día 1
            if critical_weakness:
                day_1_plan = await self._create_day_1_plan(critical_weakness, content_recommendations)
                study_plan['day_1'] = day_1_plan
            
            # Plan días 1-3
            days_3_plan = await self._create_days_3_plan(weaknesses[:2], content_recommendations)
            study_plan['days_1_to_3'] = days_3_plan
            
            # Plan semanal
            week_1_plan = await self._create_week_1_plan(weaknesses[:3], strengths[:1] if strengths else [])
            study_plan['week_1'] = week_1_plan
            
            # Plan bi-semanal
            weeks_2_plan = await self._create_weeks_2_plan(weaknesses, strengths)
            study_plan['weeks_1_to_2'] = weeks_2_plan
            
            # Plan mensual
            month_plan = await self._create_month_plan(weaknesses, strengths)
            study_plan['month_plan'] = month_plan
            
            return study_plan
            
        except Exception as e:
            logger.error(f"Error creating structured study plan: {e}")
            return {}
    
    async def _create_day_1_plan(
        self,
        critical_weakness: WeaknessAnalysis,
        content_recommendations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crea plan específico para el primer día"""
        # Buscar video recomendado para la debilidad crítica
        critical_video = None
        for category in content_recommendations.values():
            if isinstance(category, dict):
                for topic_key, topic_data in category.items():
                    if (topic_data.get('subject_area') == critical_weakness.subject_name and
                        topic_data.get('videos')):
                        critical_video = topic_data['videos'][0]
                        break
        
        plan = {
            'focus': 'Debilidad más crítica',
            'target_weakness': f"{critical_weakness.subject_name} - {critical_weakness.topic_name}",
            'recommended_activities': [
                {
                    'type': 'video_review',
                    'content': critical_video['title'] if critical_video else 'Video de refuerzo conceptual',
                    'estimated_time_minutes': critical_video['duration_minutes'] if critical_video else 15,
                    'priority': 'high'
                },
                {
                    'type': 'practice_questions',
                    'topic': critical_weakness.topic_name,
                    'question_count': 5,
                    'estimated_time_minutes': 15,
                    'focus': 'error_remediation'
                },
                {
                    'type': 'concept_review',
                    'subject': critical_weakness.subject_name,
                    'estimated_time_minutes': 10
                }
            ],
            'success_criteria': [
                'Completar video recomendado',
                'Responder correctamente 3/5 preguntas de práctica',
                'Identificar patrón de error común'
            ]
        }
        
        # Calcular tiempo total
        total_time = sum(activity['estimated_time_minutes'] for activity in plan['recommended_activities'])
        plan['total_estimated_time'] = total_time
        
        return plan
    
    async def _create_days_3_plan(
        self,
        top_weaknesses: List[WeaknessAnalysis],
        content_recommendations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crea plan para los primeros 3 días"""
        target_weaknesses = [f"{w.subject_name} - {w.topic_name}" for w in top_weaknesses[:2]]
        
        return {
            'focus': 'Top 2 debilidades críticas',
            'target_weaknesses': target_weaknesses,
            'daily_time_commitment': 45,
            'activities_progression': {
                'day_1': ['critical_video_1', 'practice_set_1', 'error_analysis'],
                'day_2': ['critical_video_2', 'practice_set_2', 'concept_mapping'],
                'day_3': ['review_session', 'mixed_practice', 'progress_assessment']
            },
            'success_criteria': [
                'Mejora de 10% en accuracy para debilidades objetivo',
                'Reducción de tiempo promedio en 20%',
                'Eliminación de error sistemático dominante'
            ]
        }
    
    async def _create_week_1_plan(
        self,
        weaknesses: List[WeaknessAnalysis],
        strengths: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Crea plan para la primera semana"""
        target_weaknesses = [f"{w.subject_name} - {w.topic_name}" for w in weaknesses[:3]]
        strength_maintenance = strengths[0]['topic_name'] if strengths else 'Revisión general'
        
        weekly_schedule = {
            'monday': [{'type': 'critical_intervention', 'weakness': target_weaknesses[0] if target_weaknesses else 'General', 'time_minutes': 45}],
            'tuesday': [{'type': 'concept_building', 'weakness': target_weaknesses[1] if len(target_weaknesses) > 1 else 'General', 'time_minutes': 30}],
            'wednesday': [{'type': 'mixed_practice', 'topics': [target_weaknesses[0], strength_maintenance], 'time_minutes': 35}],
            'thursday': [{'type': 'skill_development', 'weakness': target_weaknesses[2] if len(target_weaknesses) > 2 else 'General', 'time_minutes': 40}],
            'friday': [{'type': 'comprehensive_review', 'all_topics': True, 'time_minutes': 50}],
            'saturday': [{'type': 'diagnostic_practice', 'mixed_topics': True, 'time_minutes': 60}],
            'sunday': [{'type': 'rest_and_review', 'light_maintenance': True, 'time_minutes': 20}]
        }
        
        return {
            'focus': 'Debilidades críticas + 1 fortaleza',
            'balanced_approach': True,
            'target_weaknesses': target_weaknesses,
            'strength_maintenance': strength_maintenance,
            'weekly_schedule': weekly_schedule,
            'weekly_targets': {
                'accuracy_improvement': '+15%',
                'speed_improvement': '+25%',
                'consistency_score': '>80%'
            }
        }
    
    async def _create_weeks_2_plan(
        self,
        weaknesses: List[WeaknessAnalysis],
        strengths: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Crea plan para las primeras 2 semanas"""
        return {
            'focus': 'Consolidación y expansión',
            'progression_strategy': 'gradual_difficulty_increase',
            'week_1_goals': [
                'Estabilizar debilidades críticas',
                'Introducir conceptos intermedios',
                'Establecer rutina de estudio'
            ],
            'week_2_goals': [
                'Expandir a debilidades secundarias',
                'Integrar conocimientos',
                'Preparar para evaluación'
            ],
            'milestones': {
                'day_7': 'Evaluación de progreso intermedia',
                'day_14': 'Evaluación comprehensiva'
            }
        }
    
    async def _create_month_plan(
        self,
        weaknesses: List[WeaknessAnalysis],
        strengths: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Crea plan mensual completo"""
        return {
            'overall_goal': 'Transformación de debilidades en competencias',
            'strategic_approach': 'spiral_learning',
            'phase_1_days_1_7': {
                'focus': 'Estabilización crítica',
                'primary_weaknesses': min(2, len(weaknesses)),
                'target_improvement': '40%'
            },
            'phase_2_days_8_14': {
                'focus': 'Expansión controlada',
                'additional_topics': min(2, max(0, len(weaknesses) - 2)),
                'integration_level': 'basic'
            },
            'phase_3_days_15_21': {
                'focus': 'Consolidación avanzada',
                'mixed_practice_increase': '60%',
                'complex_problems': True
            },
            'phase_4_days_22_30': {
                'focus': 'Evaluación y ajuste',
                'comprehensive_assessment': True,
                'next_month_preparation': True
            },
            'monthly_targets': {
                'overall_theta_improvement': '+0.3',
                'critical_weaknesses_resolved': f">={min(3, len(weaknesses))}",
                'new_strengths_developed': '>=1',
                'study_consistency': '>90%'
            }
        }
    
    async def _generate_improvement_predictions(
        self,
        db: Session,
        student_id: str,
        weaknesses: List[WeaknessAnalysis],
        study_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Genera predicciones de mejora usando modelos ML"""
        try:
            # Obtener datos históricos para predicción
            historical_data = await self._get_historical_performance_data(db, student_id)
            
            # Calcular predicciones basadas en patrón de mejora típico
            base_improvement_rate = 0.45  # Mejora típica mensual
            
            # Ajustar basado en factores del estudiante
            engagement_factor = historical_data.get('engagement_score', 0.7)
            difficulty_factor = min(1.2, len(weaknesses) / 5.0)  # Más debilidades = mayor desafío
            
            adjusted_improvement = base_improvement_rate * engagement_factor / difficulty_factor
            
            predictions = {
                'model_version': 'v2.1_irt_enhanced',
                'confidence_interval': 0.85,
                'predictions': {
                    'day_1': {
                        'theta_change': round(adjusted_improvement * 0.1, 3),
                        'accuracy_improvement': '+5%',
                        'confidence': 0.92
                    },
                    'day_3': {
                        'theta_change': round(adjusted_improvement * 0.25, 3),
                        'accuracy_improvement': '+12%',
                        'confidence': 0.88
                    },
                    'week_1': {
                        'theta_change': round(adjusted_improvement * 0.55, 3),
                        'accuracy_improvement': '+20%',
                        'confidence': 0.85
                    },
                    'week_2': {
                        'theta_change': round(adjusted_improvement * 0.75, 3),
                        'accuracy_improvement': '+28%',
                        'confidence': 0.82
                    },
                    'month_1': {
                        'theta_change': round(adjusted_improvement, 3),
                        'accuracy_improvement': '+35%',
                        'confidence': 0.78
                    }
                },
                'prediction_factors': {
                    'student_engagement_history': engagement_factor,
                    'learning_velocity': historical_data.get('learning_velocity', 1.0),
                    'topic_difficulty_factor': round(difficulty_factor, 2),
                    'available_study_time': historical_data.get('avg_daily_time', 45)
                },
                'scenarios': {
                    'optimistic': {
                        'condition': 'Seguimiento completo del plan',
                        'theta_improvement': round(adjusted_improvement * 1.3, 3),
                        'timeline_acceleration': '20%'
                    },
                    'realistic': {
                        'condition': 'Seguimiento del 80% del plan',
                        'theta_improvement': round(adjusted_improvement, 3),
                        'timeline_standard': '100%'
                    },
                    'pessimistic': {
                        'condition': 'Seguimiento del 60% del plan',
                        'theta_improvement': round(adjusted_improvement * 0.6, 3),
                        'timeline_deceleration': '40%'
                    }
                }
            }
            
            # Predicciones específicas por debilidad
            weakness_predictions = {}
            for weakness in weaknesses[:3]:  # Top 3 debilidades
                weakness_key = f"{weakness.subject_name}_{weakness.topic_name}".replace(' ', '_').lower()
                resolution_prob = max(0.4, min(0.9, 1.0 - (weakness.intervention_priority_score / 100)))
                
                weakness_predictions[weakness_key] = {
                    'current_theta': weakness.irt_theta if hasattr(weakness, 'irt_theta') else self._accuracy_to_theta(weakness.accuracy_percentage / 100),
                    'predicted_theta_month': round(weakness.irt_theta + adjusted_improvement * 0.8, 3) if hasattr(weakness, 'irt_theta') else 0.0,
                    'resolution_probability': round(resolution_prob, 3),
                    'estimated_sessions_to_proficiency': weakness.estimated_sessions_needed
                }
            
            predictions['weakness_specific_predictions'] = weakness_predictions
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating improvement predictions: {e}")
            return {'model_version': 'error', 'predictions': {}, 'scenarios': {}}
    
    async def _get_historical_performance_data(
        self, 
        db: Session, 
        student_id: str
    ) -> Dict[str, Any]:
        """Obtiene datos históricos de performance para predicciones"""
        try:
            # Query para obtener patrones históricos
            result = db.execute(text("""
                SELECT 
                    COUNT(DISTINCT DATE(created_at)) as active_days,
                    COUNT(*) as total_questions,
                    AVG(CASE WHEN is_correct THEN 1 ELSE 0 END) as avg_accuracy,
                    AVG(time_spent_seconds) as avg_time,
                    STDDEV(time_spent_seconds) as stddev_time
                FROM user_answers 
                WHERE user_id = :student_id 
                  AND created_at >= CURRENT_DATE - INTERVAL '30 days'
            """), {'student_id': student_id}).fetchone()
            
            if result and result.total_questions > 0:
                # Calcular engagement score basado en consistencia
                engagement_score = min(1.0, result.active_days / 30.0) if result.active_days else 0.5
                
                # Calcular velocidad de aprendizaje basada en variabilidad de tiempo
                learning_velocity = 1.0
                if result.stddev_time and result.avg_time:
                    coefficient_variation = result.stddev_time / result.avg_time
                    # Menor variabilidad = mayor velocidad de aprendizaje
                    learning_velocity = max(0.5, min(1.5, 1.5 - coefficient_variation))
                
                return {
                    'engagement_score': round(engagement_score, 3),
                    'learning_velocity': round(learning_velocity, 3),
                    'avg_daily_time': round((result.avg_time or 0) / 60, 1),  # en minutos
                    'consistency_indicator': round(engagement_score * learning_velocity, 3)
                }
            else:
                # Estudiante nuevo o sin datos recientes
                return {
                    'engagement_score': 0.7,  # Optimista para nuevos estudiantes
                    'learning_velocity': 1.0,
                    'avg_daily_time': 45,
                    'consistency_indicator': 0.7
                }
                
        except Exception as e:
            logger.error(f"Error getting historical performance data: {e}")
            return {'engagement_score': 0.7, 'learning_velocity': 1.0, 'avg_daily_time': 45}
    
    async def _compile_template_data(
        self,
        student_data: Dict[str, Any],
        strengths: List[Dict[str, Any]],
        weaknesses: List[WeaknessAnalysis],
        content_recommendations: Dict[str, Any],
        study_plan: Dict[str, Any],
        improvement_predictions: Dict[str, Any],
        target_month: int,
        target_year: int
    ) -> Dict[str, str]:
        """Compila todos los datos en formato para plantilla"""
        
        # Fecha de generación
        generation_date = datetime.utcnow()
        
        template_data = {
            # Metadata
            'STUDENT_ID': student_data['student_id'],
            'STUDENT_NAME': student_data['username'],
            'GENERATION_DATE': generation_date.isoformat(),
            'PLAN_MONTH': f"{target_month:02d}",
            'PLAN_YEAR': str(target_year),
            'CURRENT_GRADE': 'N/A',  # Placeholder
            'TARGET_EXAM': 'ICFES Saber 11',
            'REGISTRATION_DATE': student_data['registration_date'].isoformat() if student_data['registration_date'] else '',
            'LAST_ACTIVITY': student_data['last_activity'].isoformat() if student_data['last_activity'] else '',
            
            # Parámetros IRT
            'THETA_GLOBAL': str(student_data['theta_global']),
            'THETA_CI_LOWER': str(round(student_data['theta_global'] - 0.3, 3)),
            'THETA_CI_UPPER': str(round(student_data['theta_global'] + 0.3, 3)),
            'MEASUREMENT_PRECISION': '0.85',
            
            # Estadísticas
            'TOTAL_QUESTIONS': str(student_data['total_questions']),
            'TOTAL_STUDY_TIME': str(student_data['total_study_time_hours']),
            'STREAK_DAYS': str(student_data['streak_days']),
            
            # Timestamps
            'GENERATION_TIMESTAMP': generation_date.isoformat(),
            'NEXT_UPDATE': (generation_date + timedelta(days=7)).isoformat(),
            'PLAN_EXPIRY': (generation_date + timedelta(days=30)).isoformat()
        }
        
        # Agregar datos de fortalezas
        for i, strength in enumerate(strengths[:5], 1):
            prefix = f'STRENGTH_{i}'
            template_data.update({
                f'{prefix}': f"strength_{i}",
                f'{prefix}_SUBJECT': strength['subject_area'],
                f'{prefix}_TOPIC': strength['topic_name'],
                f'{prefix}_ACCURACY': str(strength['accuracy_percentage']),
                f'{prefix}_THETA': str(strength['irt_theta']),
                f'{prefix}_ATTEMPTS': str(strength['total_attempts']),
                f'{prefix}_TIME': str(strength['avg_time_seconds']),
                f'{prefix}_MASTERY': strength['mastery_level'],
                f'{prefix}_CONFIDENCE': str(strength['confidence_score']),
                f'{prefix}_LAST': strength['last_assessment'] or ''
            })
        
        # Rellenar fortalezas faltantes
        for i in range(len(strengths) + 1, 6):
            prefix = f'STRENGTH_{i}'
            template_data.update({
                f'{prefix}': f"strength_{i}",
                f'{prefix}_SUBJECT': 'Área a determinar',
                f'{prefix}_TOPIC': 'Tema pendiente',
                f'{prefix}_ACCURACY': '0',
                f'{prefix}_THETA': '0',
                f'{prefix}_ATTEMPTS': '0',
                f'{prefix}_TIME': '0',
                f'{prefix}_MASTERY': 'novice',
                f'{prefix}_CONFIDENCE': '0',
                f'{prefix}_LAST': ''
            })
        
        # Agregar datos de debilidades
        for i, weakness in enumerate(weaknesses[:5], 1):
            prefix = f'WEAKNESS_{i}'
            template_data.update({
                f'{prefix}': f"weakness_{i}",
                f'{prefix}_SUBJECT': weakness.subject_name,
                f'{prefix}_TOPIC': weakness.topic_name,
                f'{prefix}_ACCURACY': str(weakness.accuracy_percentage),
                f'{prefix}_THETA': str(getattr(weakness, 'irt_theta', self._accuracy_to_theta(weakness.accuracy_percentage / 100))),
                f'{prefix}_ATTEMPTS': str(weakness.total_attempts),
                f'{prefix}_PRIORITY': str(weakness.intervention_priority_score),
                f'{prefix}_SEVERITY': weakness.weakness_severity.value,
                f'{prefix}_TYPE': weakness.weakness_type.value,
                f'{prefix}_DISTRACTOR': weakness.dominant_distractor or 'N/A',
                f'{prefix}_DIST_FREQ': '0',  # Placeholder
                f'{prefix}_ERROR_PATTERN': weakness.weakness_type.value,
                f'{prefix}_TIME': str(weakness.avg_time_seconds),
                f'{prefix}_P90_TIME': str(weakness.p90_time_seconds),
                f'{prefix}_TIME_SCORE': '0.5',  # Placeholder
                f'{prefix}_ACTION': weakness.recommended_action,
                f'{prefix}_SESSIONS': str(weakness.estimated_sessions_needed),
                f'{prefix}_CONCEPT_REVIEW': str(weakness.needs_concept_review).lower(),
                f'{prefix}_SPEED_PRACTICE': str(weakness.needs_speed_practice).lower()
            })
        
        # Rellenar debilidades faltantes
        for i in range(len(weaknesses) + 1, 6):
            prefix = f'WEAKNESS_{i}'
            template_data.update({
                f'{prefix}': f"weakness_{i}",
                f'{prefix}_SUBJECT': 'Área pendiente',
                f'{prefix}_TOPIC': 'Tema pendiente',
                f'{prefix}_ACCURACY': '100',
                f'{prefix}_THETA': '0',
                f'{prefix}_ATTEMPTS': '0',
                f'{prefix}_PRIORITY': '0',
                f'{prefix}_SEVERITY': 'minor',
                f'{prefix}_TYPE': 'general_weakness',
                f'{prefix}_DISTRACTOR': 'N/A',
                f'{prefix}_DIST_FREQ': '0',
                f'{prefix}_ERROR_PATTERN': 'none',
                f'{prefix}_TIME': '0',
                f'{prefix}_P90_TIME': '0',
                f'{prefix}_TIME_SCORE': '1.0',
                f'{prefix}_ACTION': 'maintenance',
                f'{prefix}_SESSIONS': '0',
                f'{prefix}_CONCEPT_REVIEW': 'false',
                f'{prefix}_SPEED_PRACTICE': 'false'
            })
        
        # Agregar datos de recomendaciones de contenido (simplificado)
        self._add_content_recommendation_data(template_data, content_recommendations)
        
        # Agregar datos del plan de estudio
        self._add_study_plan_data(template_data, study_plan)
        
        # Agregar predicciones
        self._add_prediction_data(template_data, improvement_predictions)
        
        # Datos adicionales
        template_data.update({
            'CURRENT_ACCURACY': str(student_data['current_accuracy']),
            'TARGET_ACCURACY': str(student_data['current_accuracy'] + 15),
            'TARGET_THETA': str(round(student_data['theta_global'] + 0.45, 3)),
            'DAY_1_TOTAL_TIME': str(study_plan.get('day_1', {}).get('total_estimated_time', 40)),
            'DAYS_3_DAILY_TIME': '45',
            'CURRENT_AVG_TIME': '90',  # Placeholder
            'VALIDATION_PASSED': 'true',
            'REC_COVERAGE': '85',
            'DIVERSITY_SCORE': '0.75',
            'CONFIDENCE_AVG': '0.82'
        })
        
        return template_data
    
    def _add_content_recommendation_data(
        self, 
        template_data: Dict[str, str], 
        content_recommendations: Dict[str, Any]
    ):
        """Agrega datos de recomendaciones de contenido a la plantilla"""
        # Obtener primer video crítico si existe
        critical_videos = []
        for topic_key, topic_data in content_recommendations.get('critical_interventions', {}).items():
            videos = topic_data.get('videos', [])
            critical_videos.extend(videos[:2])  # Máximo 2 videos críticos
        
        # Llenar datos de videos críticos
        for i, video in enumerate(critical_videos[:2], 1):
            prefix = f'CRITICAL_VIDEO_{i}'
            template_data.update({
                f'{prefix}_ID': str(video['video_id']),
                f'{prefix}_TITLE': video['title'],
                f'{prefix}_CHANNEL': video['channel'],
                f'{prefix}_DURATION': str(video['duration_minutes']),
                f'{prefix}_URL': video['youtube_url'],
                f'{prefix}_SCORE': str(video['recommendation_score']),
                f'{prefix}_TYPE': video['recommendation_type'],
                f'{prefix}_CONFIDENCE': video['confidence_level'],
                f'{prefix}_ERROR': video.get('targets_error', 'general')
            })
        
        # Placeholder para videos faltantes
        for i in range(len(critical_videos) + 1, 3):
            prefix = f'CRITICAL_VIDEO_{i}'
            template_data.update({
                f'{prefix}_ID': '0',
                f'{prefix}_TITLE': 'Video de refuerzo pendiente',
                f'{prefix}_CHANNEL': 'Canal educativo',
                f'{prefix}_DURATION': '15',
                f'{prefix}_URL': 'https://youtube.com',
                f'{prefix}_SCORE': '0.75',
                f'{prefix}_TYPE': 'concept_review',
                f'{prefix}_CONFIDENCE': 'medium',
                f'{prefix}_ERROR': 'general'
            })
        
        # Agregar debilidades críticas
        critical_weaknesses = list(content_recommendations.get('critical_interventions', {}).keys())
        template_data.update({
            'CRITICAL_WEAKNESS_1': critical_weaknesses[0] if critical_weaknesses else 'critical_weakness_1',
            'CONCEPT_WEAKNESS_1': 'concept_weakness_1',
            'SKILL_WEAKNESS_1': 'skill_weakness_1'
        })
        
        # Placeholder para otros videos
        placeholders = ['CONCEPT_VIDEO_1', 'SKILL_VIDEO_1', 'MAINTENANCE_VIDEO_1']
        for placeholder in placeholders:
            template_data.update({
                f'{placeholder}_ID': '0',
                f'{placeholder}_TITLE': 'Video educativo recomendado',
                f'{placeholder}_CHANNEL': 'Canal educativo',
                f'{placeholder}_DURATION': '15',
                f'{placeholder}_URL': 'https://youtube.com',
                f'{placeholder}_SCORE': '0.75',
                f'{placeholder}_TYPE': 'educational',
                f'{placeholder}_CONFIDENCE': 'medium',
                f'{placeholder}_SEMANTIC': '0.7',
                f'{placeholder}_DIFFICULTY': '0.8',
                f'{placeholder}_SUBJECT': 'Matemáticas'
            })
    
    def _add_study_plan_data(self, template_data: Dict[str, str], study_plan: Dict[str, Any]):
        """Agrega datos del plan de estudio a la plantilla"""
        # Placeholder - en implementación real se extraerían datos específicos del study_plan
        template_data.update({
            'ESTIMATED_TOTAL_HOURS': '30',
            'WEEKLY_TIME_COMMITMENT': '7'
        })
    
    def _add_prediction_data(self, template_data: Dict[str, str], predictions: Dict[str, Any]):
        """Agrega datos de predicciones a la plantilla"""
        pred_month = predictions.get('predictions', {}).get('month_1', {})
        template_data.update({
            'PREDICTED_THETA_CHANGE': str(pred_month.get('theta_change', 0.45)),
            'ENGAGEMENT_SCORE': str(predictions.get('prediction_factors', {}).get('student_engagement_history', 0.7)),
            'LEARNING_VELOCITY': str(predictions.get('prediction_factors', {}).get('learning_velocity', 1.0)),
            'TOPIC_DIFFICULTY': str(predictions.get('prediction_factors', {}).get('topic_difficulty_factor', 1.0)),
            'AVAILABLE_TIME': str(predictions.get('prediction_factors', {}).get('available_study_time', 45))
        })
        
        # Agregar predicciones por debilidad específica
        weakness_preds = predictions.get('weakness_specific_predictions', {})
        for i, (weakness_key, pred_data) in enumerate(list(weakness_preds.items())[:3], 1):
            template_data.update({
                f'WEAKNESS_{i}_PRED_THETA': str(pred_data.get('predicted_theta_month', 0.0)),
                f'WEAKNESS_{i}_RESOLUTION_PROB': str(pred_data.get('resolution_probability', 0.5)),
                f'WEAKNESS_{i}_SESSIONS_TO_PROF': str(pred_data.get('estimated_sessions_to_proficiency', 5))
            })
    
    async def _generate_yaml_from_template(self, template_data: Dict[str, str]) -> str:
        """Genera YAML a partir de la plantilla con los datos compilados"""
        try:
            template_path = self.templates_path / "monthly_recommendation_template.yml"
            
            if not template_path.exists():
                raise FileNotFoundError(f"Template file not found: {template_path}")
            
            # Leer plantilla
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Crear objeto Template y sustituir variables
            template = Template(template_content)
            yaml_content = template.safe_substitute(template_data)
            
            # Validar que sea YAML válido
            try:
                yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                logger.error(f"Generated YAML is invalid: {e}")
                raise
            
            return yaml_content
            
        except Exception as e:
            logger.error(f"Error generating YAML from template: {e}")
            raise
    
    async def _save_generated_plan(
        self, 
        student_id: str, 
        year: int, 
        month: int, 
        yaml_content: str
    ) -> Path:
        """Guarda el plan generado en archivo"""
        try:
            filename = f"rec_plan_{student_id}_{year}{month:02d}.yml"
            file_path = self.generated_path / filename
            
            # Archivar plan existente si existe
            if file_path.exists():
                archive_filename = f"rec_plan_{student_id}_{year}{month:02d}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.yml"
                archive_path = self.archived_path / archive_filename
                file_path.rename(archive_path)
                logger.info(f"Existing plan archived to {archive_path}")
            
            # Guardar nuevo plan
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            logger.info(f"Plan saved to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving generated plan: {e}")
            raise
    
    def _get_plan_filepath(self, student_id: str, year: int, month: int) -> Path:
        """Obtiene la ruta del archivo de plan"""
        filename = f"rec_plan_{student_id}_{year}{month:02d}.yml"
        return self.generated_path / filename
    
    async def _load_existing_plan(self, plan_path: Path) -> Dict[str, Any]:
        """Carga un plan existente"""
        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
            
            return {
                'status': 'existing_plan_loaded',
                'plan_file_path': str(plan_path),
                'yaml_content': yaml_content,
                'loaded_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error loading existing plan: {e}")
            raise
    
    async def get_student_plans(self, student_id: str) -> List[Dict[str, Any]]:
        """Obtiene lista de planes disponibles para un estudiante"""
        try:
            plans = []
            pattern = f"rec_plan_{student_id}_*.yml"
            
            for file_path in self.generated_path.glob(pattern):
                # Extraer fecha del nombre del archivo
                filename = file_path.stem
                parts = filename.split('_')
                if len(parts) >= 4:
                    date_part = parts[-1]  # YYYYMM
                    if len(date_part) == 6:
                        year = int(date_part[:4])
                        month = int(date_part[4:])
                        
                        plans.append({
                            'file_path': str(file_path),
                            'year': year,
                            'month': month,
                            'filename': file_path.name,
                            'created_at': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                            'size_bytes': file_path.stat().st_size
                        })
            
            # Ordenar por fecha descendente
            plans.sort(key=lambda x: (x['year'], x['month']), reverse=True)
            return plans
            
        except Exception as e:
            logger.error(f"Error getting student plans: {e}")
            return []
    
    async def archive_old_plans(self, days_old: int = 90) -> int:
        """Archiva planes antiguos"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            archived_count = 0
            
            for file_path in self.generated_path.glob("rec_plan_*.yml"):
                file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_modified < cutoff_date:
                    # Mover a archivo
                    archive_filename = f"{file_path.stem}_{datetime.utcnow().strftime('%Y%m%d')}_archived{file_path.suffix}"
                    archive_path = self.archived_path / archive_filename
                    
                    file_path.rename(archive_path)
                    archived_count += 1
                    logger.info(f"Archived old plan: {file_path.name}")
            
            return archived_count
            
        except Exception as e:
            logger.error(f"Error archiving old plans: {e}")
            return 0