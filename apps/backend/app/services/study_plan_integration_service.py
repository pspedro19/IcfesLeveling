from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from .icfes_catalog_service import ICFESCatalogService
from .diagnostic_service import DiagnosticService
from .ai_study_plan_service import AIStudyPlanService
from .adaptive_learning_service import AdaptiveLearningService
from .spaced_repetition_service import SpacedRepetitionService
from .progress_gamification_service import ProgressGamificationService
from .learning_styles_service import LearningStylesService
from .scheduling_service import SchedulingService
from .notification_reminder_service import NotificationReminderService
from .enhanced_video_service import EnhancedVideoService
from ..models.user import User
from ..models.subject import Subject

logger = logging.getLogger(__name__)

class StudyPlanIntegrationService:
    """Servicio para integrar catálogo ICFES con planes de estudio adaptativos"""
    
    def __init__(self, db: Session):
        self.db = db
        self.catalog_service = ICFESCatalogService(db)
        self.diagnostic_service = DiagnosticService(db)
        
        # Initialize all AI-powered services
        self.ai_study_plan_service = AIStudyPlanService(db)
        self.adaptive_learning_service = AdaptiveLearningService(db)
        self.spaced_repetition_service = SpacedRepetitionService(db)
        self.progress_gamification_service = ProgressGamificationService(db)
        self.learning_styles_service = LearningStylesService(db)
        self.scheduling_service = SchedulingService(db)
        self.notification_service = NotificationReminderService(db)
        self.video_service = EnhancedVideoService(db)
    
    def generate_comprehensive_study_plan(
        self, 
        user_id: str, 
        subject_id: str, 
        use_diagnostic: bool = True
    ) -> Dict[str, Any]:
        """Generar plan de estudio completo integrando catálogo ICFES y diagnóstico"""
        try:
            # Obtener información del usuario y materia
            user = self.db.query(User).filter(User.id == user_id).first()
            subject = self.db.query(Subject).filter(Subject.id == subject_id).first()
            
            if not user or not subject:
                raise ValueError("Usuario o materia no encontrados")
            
            # Mapear materia a código de área ICFES
            area_code = self._map_subject_to_area_code(subject.name)
            if not area_code:
                raise ValueError(f"No se pudo mapear la materia {subject.name} a un área ICFES")
            
            # Obtener resultados de diagnóstico si están disponibles
            diagnostic_results = None
            if use_diagnostic:
                diagnostic_results = self._get_user_diagnostic_results(user_id, subject_id)
            
            # Generar unidades basadas en catálogo ICFES
            catalog_units = self.catalog_service.generate_study_units_from_catalog(
                area_code, 
                user.level or 1
            )
            
            # Personalizar unidades basadas en diagnóstico
            personalized_units = self._personalize_units_based_on_diagnostic(
                catalog_units, 
                diagnostic_results, 
                user.level or 1
            )
            
            # Generar plan completo
            study_plan = {
                "id": f"plan_{user_id}_{subject_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "user_id": user_id,
                "subject_id": subject_id,
                "subject": subject.name,
                "title": f"Plan de Conquista de {subject.name} - ICFES",
                "description": f"Plan personalizado basado en el catálogo ICFES y tu nivel actual (Nivel {user.level or 1})",
                "units": personalized_units,
                "total_questions": self._calculate_total_questions(personalized_units),
                "total_videos": self._calculate_total_videos(personalized_units),
                "estimated_time": self._calculate_total_time(personalized_units),
                "difficulty_curve": "adaptive",
                "icfes_weight": self._calculate_total_icfes_weight(personalized_units),
                "exam_sections": [subject.name],
                "personalized_recommendations": {
                    "overall_accuracy": diagnostic_results.get('percentage', 0) if diagnostic_results else 0,
                    "weak_topics": diagnostic_results.get('weaknesses', []) if diagnostic_results else [],
                    "strong_topics": diagnostic_results.get('strengths', []) if diagnostic_results else [],
                    "suggested_focus": self._identify_focus_areas(diagnostic_results, personalized_units),
                    "study_schedule": {
                        "daily_hours": 2,
                        "weekly_sessions": 5,
                        "estimated_weeks": len(personalized_units)
                    },
                    "estimated_improvement": {
                        "current_level": user.level or 1,
                        "target_level": (user.level or 1) + 2,
                        "estimated_weeks": len(personalized_units)
                    }
                },
                "catalog_integration": {
                    "area_code": area_code,
                    "total_catalog_topics": len(self.catalog_service.get_topics_by_area(area_code)),
                    "catalog_coverage": self._calculate_catalog_coverage(personalized_units, area_code)
                }
            }
            
            logger.info(f"✅ Plan de estudio generado para usuario {user_id}, materia {subject.name}")
            return study_plan
            
        except Exception as e:
            logger.error(f"Error generando plan de estudio: {e}")
            raise
    
    def _map_subject_to_area_code(self, subject_name: str) -> Optional[str]:
        """Mapear nombre de materia a código de área ICFES"""
        subject_mapping = {
            'matemáticas': 'MAT',
            'matematicas': 'MAT',
            'math': 'MAT',
            'ciencias naturales': 'CN',
            'ciencias': 'CN',
            'sociales': 'SOC',
            'sociales y ciudadanas': 'SOC',
            'inglés': 'ING',
            'ingles': 'ING',
            'english': 'ING',
            'lectura crítica': 'LC',
            'lectura critica': 'LC',
            'reading': 'LC'
        }
        
        subject_lower = subject_name.lower().strip()
        return subject_mapping.get(subject_lower)
    
    def _get_user_diagnostic_results(self, user_id: str, subject_id: str) -> Optional[Dict[str, Any]]:
        """Obtener resultados de diagnóstico del usuario para una materia específica"""
        try:
            # Obtener el último test diagnóstico completado
            diagnostic_tests = self.diagnostic_service.get_user_diagnostic_tests(user_id)
            
            for test in diagnostic_tests:
                if (str(test.subject_id) == subject_id and 
                    test.status == "completed" and 
                    test.completed_at):
                    return {
                        "percentage": test.score_percentage,
                        "strengths": test.strengths or [],
                        "weaknesses": test.weaknesses or [],
                        "score_by_topic": test.score_by_topic or {},
                        "completed_at": test.completed_at.isoformat()
                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"No se pudieron obtener resultados de diagnóstico: {e}")
            return None
    
    def _personalize_units_based_on_diagnostic(
        self, 
        units: List[Dict[str, Any]], 
        diagnostic_results: Optional[Dict[str, Any]], 
        user_level: int
    ) -> List[Dict[str, Any]]:
        """Personalizar unidades basándose en resultados de diagnóstico"""
        if not diagnostic_results:
            return units
        
        personalized_units = []
        diagnostic_score = diagnostic_results.get('percentage', 0)
        
        for unit in units:
            personalized_unit = unit.copy()
            
            # Ajustar dificultad basada en diagnóstico
            if diagnostic_score < 50:
                # Usuario con bajo rendimiento - enfocar en fundamentos
                if unit['difficulty_level'] == 1:
                    personalized_unit['ai_recommended'] = True
                    personalized_unit['priority'] = 'high'
                else:
                    personalized_unit['unlocked'] = False
                    personalized_unit['ai_recommended'] = False
                    personalized_unit['priority'] = 'low'
                    
            elif diagnostic_score < 70:
                # Usuario con rendimiento medio - balance
                personalized_unit['ai_recommended'] = unit['difficulty_level'] <= 2
                personalized_unit['priority'] = 'medium'
                
            else:
                # Usuario con alto rendimiento - puede acceder a todo
                personalized_unit['unlocked'] = True
                personalized_unit['ai_recommended'] = unit['difficulty_level'] >= 2
                personalized_unit['priority'] = 'high' if unit['difficulty_level'] == 3 else 'medium'
            
            # Agregar recomendaciones personalizadas
            personalized_unit['recommendations'] = self._generate_personalized_recommendations(
                unit, diagnostic_results, user_level
            )
            
            personalized_units.append(personalized_unit)
        
        return personalized_units
    
    async def generate_ai_powered_comprehensive_plan(
        self,
        user_id: str,
        subject_id: str,
        preferences: Dict[str, Any] = None,
        target_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete AI-powered study plan with all advanced features
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            subject = self.db.query(Subject).filter(Subject.id == subject_id).first()
            
            if not user or not subject:
                raise ValueError("Usuario o materia no encontrados")
            
            logger.info(f"🚀 Iniciando generación AI completa para {user.username} - {subject.name}")
            
            # 1. Detect learning style
            learning_style_data = await self.learning_styles_service.detect_learning_style(user_id)
            
            # 2. Get diagnostic results
            diagnostic_results = self._get_user_diagnostic_results(user_id, subject_id)
            
            # 3. Generate AI-powered personalized plan
            ai_study_plan = await self.ai_study_plan_service.generate_intelligent_study_plan(
                user_id=user_id,
                subject_id=subject_id,
                target_date=target_date,
                learning_preferences=learning_style_data
            )
            
            # 4. Create adaptive learning system
            adaptive_system = await self.adaptive_learning_service.evaluate_learning_progress(
                user_id, ai_study_plan["id"]
            )
            
            # 5. Setup spaced repetition
            spaced_repetition_system = await self.spaced_repetition_service.create_spaced_repetition_schedule(
                user_id, ai_study_plan["id"]
            )
            
            # 6. Create intelligent scheduling
            intelligent_schedule = await self.scheduling_service.create_intelligent_schedule(
                user_id, ai_study_plan["id"], preferences, target_date
            )
            
            # 7. Setup gamification and progress tracking
            gamification_system = await self.progress_gamification_service.track_comprehensive_progress(
                user_id, ai_study_plan["id"]
            )
            
            # 8. Create personalized video recommendations
            video_recommendations = await self.video_service.get_personalized_video_recommendations(
                user_id, subject.name, user.level
            )
            
            # 9. Setup notification system
            notification_system = await self.notification_service.create_intelligent_reminder_system(
                user_id, ai_study_plan["id"], preferences
            )
            
            # 10. Create personalized study approach
            study_approach = await self.learning_styles_service.create_personalized_study_approach(
                user_id, subject_id, ai_study_plan["learning_objectives"]
            )
            
            # Combine everything into comprehensive plan
            comprehensive_plan = {
                **ai_study_plan,
                "ai_powered_features": {
                    "learning_style_detection": learning_style_data,
                    "adaptive_learning_system": adaptive_system,
                    "spaced_repetition_system": spaced_repetition_system,
                    "intelligent_scheduling": intelligent_schedule,
                    "gamification_system": gamification_system,
                    "video_recommendations": video_recommendations,
                    "notification_system": notification_system,
                    "personalized_study_approach": study_approach
                },
                "system_capabilities": {
                    "real_time_adaptation": True,
                    "performance_based_adjustments": True,
                    "learning_style_optimization": True,
                    "spaced_repetition_optimization": True,
                    "intelligent_reminders": True,
                    "gamification_elements": True,
                    "video_learning_integration": True,
                    "progress_prediction": True
                },
                "personalization_confidence": await self._calculate_overall_personalization_confidence([
                    learning_style_data, diagnostic_results, adaptive_system
                ]),
                "expected_outcomes": await self._predict_comprehensive_outcomes(
                    user_id, comprehensive_plan
                )
            }
            
            logger.info(f"✅ Plan AI completo generado exitosamente - {len(comprehensive_plan.get('units', []))} unidades")
            return comprehensive_plan
            
        except Exception as e:
            logger.error(f"❌ Error generando plan AI completo: {e}")
            raise
    
    async def _calculate_overall_personalization_confidence(
        self, data_sources: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall confidence in personalization based on available data"""
        
        confidence_scores = []
        
        for source in data_sources:
            if source and isinstance(source, dict):
                # Extract confidence from each data source
                if "confidence_score" in source:
                    confidence_scores.append(source["confidence_score"])
                elif "reliability_indicators" in source:
                    confidence_scores.append(source["reliability_indicators"].get("overall", 0.5))
                elif "success_probability" in source:
                    confidence_scores.append(source["success_probability"])
                else:
                    confidence_scores.append(0.7)  # Default moderate confidence
        
        if not confidence_scores:
            return 0.5  # Default confidence when no data available
        
        # Weighted average with more weight on first sources (learning style, diagnostic)
        weights = [0.4, 0.3, 0.3][:len(confidence_scores)]
        if len(weights) < len(confidence_scores):
            weights.extend([0.1] * (len(confidence_scores) - len(weights)))
        
        weighted_sum = sum(score * weight for score, weight in zip(confidence_scores, weights))
        total_weight = sum(weights[:len(confidence_scores)])
        
        return round(weighted_sum / total_weight, 2)
    
    async def _predict_comprehensive_outcomes(
        self, user_id: str, comprehensive_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict comprehensive learning outcomes"""
        
        ai_features = comprehensive_plan.get("ai_powered_features", {})
        
        # Extract prediction data from various systems
        learning_style_conf = ai_features.get("learning_style_detection", {}).get("confidence_score", 0.5)
        gamification_success = ai_features.get("gamification_system", {}).get("predictions", {}).get("success_probability", 0.7)
        adaptive_health = ai_features.get("adaptive_learning_system", {}).get("overall_health_score", 0.7)
        
        # Calculate various outcome predictions
        completion_probability = (learning_style_conf * 0.3 + gamification_success * 0.4 + adaptive_health * 0.3)
        
        # Estimate time to completion based on user patterns and plan complexity
        total_units = len(comprehensive_plan.get("units", []))
        estimated_weeks = max(4, total_units * 1.2)  # Minimum 4 weeks, 1.2 weeks per unit average
        
        # Calculate improvement prediction
        current_level = comprehensive_plan.get("user_profile", {}).get("current_level", 1)
        improvement_potential = min(3, max(1, 5 - current_level))  # Can improve up to 3 levels
        
        return {
            "completion_probability": round(completion_probability, 2),
            "estimated_completion_weeks": int(estimated_weeks),
            "expected_skill_improvement": improvement_potential,
            "retention_rate_prediction": round(0.75 + (learning_style_conf * 0.2), 2),
            "engagement_sustainability": round(gamification_success, 2),
            "adaptive_efficiency": round(adaptive_health, 2),
            "overall_success_score": round(
                (completion_probability + gamification_success + adaptive_health) / 3, 2
            ),
            "confidence_interval": {
                "low": round(max(0.1, completion_probability - 0.15), 2),
                "high": round(min(1.0, completion_probability + 0.15), 2)
            }
        }
    
    def _generate_personalized_recommendations(
        self, 
        unit: Dict[str, Any], 
        diagnostic_results: Dict[str, Any], 
        user_level: int
    ) -> Dict[str, Any]:
        """Generar recomendaciones personalizadas para una unidad"""
        diagnostic_score = diagnostic_results.get('percentage', 0)
        weaknesses = diagnostic_results.get('weaknesses', [])
        
        recommendations = {
            "priority": unit.get('priority', 'medium'),
            "weak_areas": weaknesses[:3],  # Top 3 debilidades
            "focus_topics": [topic['main_topic'] for topic in unit.get('topics', [])[:5]],
            "study_time": f"{unit.get('estimated_completion_time', 5)}-{unit.get('estimated_completion_time', 5) + 2} horas",
            "custom_tips": []
        }
        
        # Generar tips personalizados
        if diagnostic_score < 50:
            recommendations["custom_tips"].extend([
                "Tu diagnóstico mostró áreas de mejora - enfócate en los fundamentos",
                "Dedica tiempo extra a revisar conceptos básicos",
                "Practica con ejercicios de nivel básico antes de avanzar"
            ])
        elif diagnostic_score < 70:
            recommendations["custom_tips"].extend([
                "Tienes una base sólida - puedes avanzar con confianza",
                "Enfócate en los temas identificados como débiles",
                "Mantén un ritmo constante de estudio"
            ])
        else:
            recommendations["custom_tips"].extend([
                "¡Excelente rendimiento! Puedes abordar temas más desafiantes",
                "Considera ayudar a otros estudiantes",
                "Mantén tu nivel de excelencia"
            ])
        
        # Agregar tips específicos por debilidades
        for weakness in weaknesses[:2]:
            if 'álgebra' in weakness.lower():
                recommendations["custom_tips"].append("Practica más ejercicios de álgebra")
            elif 'geometría' in weakness.lower():
                recommendations["custom_tips"].append("Refuerza conceptos de geometría")
            elif 'comprensión' in weakness.lower():
                recommendations["custom_tips"].append("Mejora tus habilidades de comprensión")
        
        return recommendations
    
    def _calculate_total_questions(self, units: List[Dict[str, Any]]) -> int:
        """Calcular total de preguntas en el plan"""
        total = 0
        for unit in units:
            for topic in unit.get('topics', []):
                # Estimación: 5 preguntas por tema
                total += 5
        return total
    
    def _calculate_total_videos(self, units: List[Dict[str, Any]]) -> int:
        """Calcular total de videos en el plan"""
        total = 0
        for unit in units:
            for topic in unit.get('topics', []):
                if topic.get('youtube_url'):
                    total += 1
        return total
    
    def _calculate_total_time(self, units: List[Dict[str, Any]]) -> str:
        """Calcular tiempo total estimado del plan"""
        total_hours = sum(unit.get('estimated_completion_time', 0) for unit in units)
        
        if total_hours < 24:
            return f"{total_hours} horas"
        else:
            days = total_hours // 24
            remaining_hours = total_hours % 24
            if remaining_hours > 0:
                return f"{days} días y {remaining_hours} horas"
            else:
                return f"{days} días"
    
    def _calculate_total_icfes_weight(self, units: List[Dict[str, Any]]) -> float:
        """Calcular peso total ICFES del plan"""
        return sum(unit.get('icfes_weight', 0) for unit in units)
    
    def _identify_focus_areas(
        self, 
        diagnostic_results: Optional[Dict[str, Any]], 
        units: List[Dict[str, Any]]
    ) -> List[str]:
        """Identificar áreas de enfoque basadas en diagnóstico y unidades"""
        focus_areas = []
        
        if diagnostic_results and diagnostic_results.get('weaknesses'):
            focus_areas.extend([
                f"Reforzar {weakness}" 
                for weakness in diagnostic_results['weaknesses'][:3]
            ])
        
        # Agregar áreas de enfoque basadas en unidades recomendadas
        for unit in units:
            if unit.get('ai_recommended'):
                focus_areas.append(f"Dominar {unit['name']}")
        
        return focus_areas[:5]  # Máximo 5 áreas de enfoque
    
    def _calculate_catalog_coverage(
        self, 
        units: List[Dict[str, Any]], 
        area_code: str
    ) -> Dict[str, Any]:
        """Calcular cobertura del catálogo ICFES en el plan"""
        total_catalog_topics = len(self.catalog_service.get_topics_by_area(area_code))
        
        # Contar temas incluidos en el plan
        included_topics = set()
        for unit in units:
            for topic in unit.get('topics', []):
                included_topics.add(topic.get('code', ''))
        
        coverage_percentage = (len(included_topics) / total_catalog_topics * 100) if total_catalog_topics > 0 else 0
        
        return {
            "total_catalog_topics": total_catalog_topics,
            "included_topics": len(included_topics),
            "coverage_percentage": round(coverage_percentage, 1),
            "missing_topics": total_catalog_topics - len(included_topics)
        }
    
    def get_study_plan_progress(
        self, 
        plan_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """Obtener progreso actual de un plan de estudio"""
        try:
            # Aquí se implementaría la lógica para obtener progreso real
            # Por ahora retornamos un progreso mock
            return {
                "plan_id": plan_id,
                "user_id": user_id,
                "overall_progress": 0,
                "completed_units": 0,
                "total_units": 0,
                "current_unit": 1,
                "estimated_completion": "Pendiente",
                "last_activity": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error obteniendo progreso del plan: {e}")
            return {}
    
    def update_unit_progress(
        self, 
        plan_id: str, 
        unit_number: int, 
        progress_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Actualizar progreso de una unidad específica"""
        try:
            # Aquí se implementaría la lógica para actualizar progreso real
            logger.info(f"Progreso actualizado para plan {plan_id}, unidad {unit_number}")
            
            return {
                "success": True,
                "plan_id": plan_id,
                "unit_number": unit_number,
                "progress_updated": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error actualizando progreso: {e}")
            return {
                "success": False,
                "error": str(e)
            }
