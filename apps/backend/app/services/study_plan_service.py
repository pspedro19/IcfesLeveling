from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
import json
import logging

from ..models.study_plan import StudyPlan, PlanProgress, StudyPlanTemplate
from ..models.user import User
from ..models.battle import BattleAnswer
from ..models.question import Question
from ..models.subject import Subject
from ..models.diagnostic_analytics import DiagnosticTestAnalytics, DiagnosticImprovementTracking, DiagnosticErrorPattern
from ..services.cache_service import cache_service
from ..services.diagnostic_analytics_service import DiagnosticAnalyticsService

logger = logging.getLogger(__name__)

class StudyPlanService:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_intelligent_plan_from_diagnostic(
        self,
        user_id: str,
        subject_id: str,
        diagnostic_test_id: str = None
    ) -> Dict[str, Any]:
        """
        Genera un plan de estudio inteligente basado en el análisis detallado del test diagnóstico
        """
        cache_key = f"intelligent_plan:{user_id}:{subject_id}"
        cached_plan = cache_service.get(cache_key)
        if cached_plan:
            return cached_plan
        
        # Obtener análisis de diagnóstico
        analytics_service = DiagnosticAnalyticsService(self.db)
        analytics_summary = analytics_service.get_analytics_summary(user_id, subject_id)
        
        if not analytics_summary['has_data']:
            # Si no hay datos de diagnóstico, usar método tradicional
            return self.generate_personalized_plan(user_id, subject_id)
        
        latest_analytics = analytics_summary['latest_analytics']
        improvement_tracking = analytics_summary['improvement_tracking']
        error_patterns = analytics_summary['error_patterns']
        
        # Crear plan base
        base_plan = self._get_base_plan_for_subject(subject_id, {})
        if not base_plan:
            raise ValueError(f"No se encontró plan base para la materia {subject_id}")
        
        # Aplicar inteligencia basada en diagnóstico
        intelligent_plan = self._apply_diagnostic_intelligence(
            base_plan, 
            latest_analytics, 
            improvement_tracking, 
            error_patterns
        )
        
        # Guardar plan personalizado
        plan_record = StudyPlan(
            user_id=user_id,
            subject_id=subject_id,
            plan_name=f"Plan Inteligente - {base_plan.get('subject_name', 'Materia')}",
            plan_data=intelligent_plan,
            total_units=len(intelligent_plan.get('units', [])),
            is_active=True
        )
        
        self.db.add(plan_record)
        self.db.commit()
        self.db.refresh(plan_record)
        
        intelligent_plan['plan_id'] = str(plan_record.id)
        intelligent_plan['generation_method'] = 'diagnostic_intelligence'
        intelligent_plan['diagnostic_based'] = True
        
        # Cache por 1 hora
        cache_service.set(cache_key, intelligent_plan, 3600)
        
        return intelligent_plan

    def generate_personalized_plan(
        self, 
        user_id: str, 
        subject_id: str,
        user_level: int = 1,
        recent_performance: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Genera un plan de estudio personalizado basado en el rendimiento del usuario
        """
        cache_key = f"study_plan:{user_id}:{subject_id}"
        cached_plan = cache_service.get(cache_key)
        if cached_plan:
            return cached_plan
        
        # Obtener datos del usuario
        user_data = self._analyze_user_performance(user_id, subject_id)
        
        # Obtener plan base para la materia
        base_plan = self._get_base_plan_for_subject(subject_id, user_data)
        if not base_plan:
            raise ValueError(f"No se encontró plan base para la materia {subject_id}")
        
        # Personalizar el plan (si viene de plantillas, ya está personalizado)
        if base_plan.get("difficulty_curve") == "adaptive":
            personalized_plan = base_plan  # Ya está adaptado
        else:
            personalized_plan = self._customize_plan(base_plan, user_data, user_level)
        
        # Guardar plan personalizado
        study_plan = StudyPlan(
            user_id=user_id,
            subject_id=subject_id,
            plan_name=personalized_plan["title"],
            plan_data=personalized_plan,
            total_units=len(personalized_plan["units"]),
            completed_units=0,
            progress_percentage=0.00,
            is_active=True
        )
        
        self.db.add(study_plan)
        self.db.commit()
        self.db.refresh(study_plan)
        
        # Crear progreso inicial para las unidades
        self._create_initial_progress(study_plan.id, personalized_plan["units"])
        
        # Cachear el plan
        cache_service.set(cache_key, personalized_plan, ttl=3600)
        
        return personalized_plan
    
    def _analyze_user_performance(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """
        Analiza el rendimiento del usuario en una materia específica
        """
        # Obtener respuestas recientes (últimos 30 días)
        cutoff_date = datetime.now() - timedelta(days=30)
        
        battle_answers = self.db.query(BattleAnswer).join(
            BattleAnswer.battle
        ).filter(
            BattleAnswer.battle.has(user_id=user_id),
            BattleAnswer.created_at >= cutoff_date,
            BattleAnswer.question.has(subject_id=subject_id)
        ).all()
        
        if not battle_answers:
            return {
                "total_questions": 0,
                "correct_answers": 0,
                "accuracy": 0.0,
                "weak_topics": [],
                "strong_topics": [],
                "average_response_time": 0,
                "difficulty_distribution": {"easy": 0, "medium": 0, "hard": 0}
            }
        
        # Calcular estadísticas
        total_questions = len(battle_answers)
        correct_answers = sum(1 for answer in battle_answers if answer.is_correct)
        accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Análisis por temas
        topic_performance = {}
        for answer in battle_answers:
            if answer.question and answer.question.topic:
                topic_name = answer.question.topic.name
                if topic_name not in topic_performance:
                    topic_performance[topic_name] = {"correct": 0, "total": 0}
                
                topic_performance[topic_name]["total"] += 1
                if answer.is_correct:
                    topic_performance[topic_name]["correct"] += 1
        
        # Identificar temas débiles y fuertes
        weak_topics = []
        strong_topics = []
        
        for topic, stats in topic_performance.items():
            topic_accuracy = (stats["correct"] / stats["total"]) * 100
            if topic_accuracy < 60:
                weak_topics.append({
                    "topic": topic,
                    "accuracy": topic_accuracy,
                    "questions_answered": stats["total"]
                })
            elif topic_accuracy > 80:
                strong_topics.append({
                    "topic": topic,
                    "accuracy": topic_accuracy,
                    "questions_answered": stats["total"]
                })
        
        # Ordenar por precisión
        weak_topics.sort(key=lambda x: x["accuracy"])
        strong_topics.sort(key=lambda x: x["accuracy"], reverse=True)
        
        # Distribución por dificultad
        difficulty_distribution = {"easy": 0, "medium": 0, "hard": 0}
        for answer in battle_answers:
            if answer.question:
                if answer.question.difficulty <= 3:
                    difficulty_distribution["easy"] += 1
                elif answer.question.difficulty <= 7:
                    difficulty_distribution["medium"] += 1
                else:
                    difficulty_distribution["hard"] += 1
        
        # Tiempo promedio de respuesta
        response_times = [answer.response_time_ms for answer in battle_answers if answer.response_time_ms]
        average_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "accuracy": accuracy,
            "weak_topics": weak_topics[:5],  # Top 5 temas débiles
            "strong_topics": strong_topics[:5],  # Top 5 temas fuertes
            "average_response_time": average_response_time,
            "difficulty_distribution": difficulty_distribution
        }
    
    def _build_plan_from_templates(self, templates: List[StudyPlanTemplate], user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Construye un plan de estudio adaptativo desde las plantillas de la base de datos
        """
        if not templates:
            return None
        
        subject = templates[0].subject
        units = []
        
        for template in templates:
            # Verificar prerequisitos
            prerequisites_met = self._check_prerequisites(template.prerequisite_units or [], user_data)
            
            # Construir temas desde el array de topics con videos
            topics = []
            for i, topic_name in enumerate(template.topics or []):
                # Obtener video URL específico para este tema
                video_url = None
                if template.video_urls and topic_name in template.video_urls:
                    video_url = template.video_urls[topic_name]
                
                topics.append({
                    "name": topic_name,
                    "difficulty": template.difficulty_level,
                    "questions": template.exercise_count // len(template.topics or [1]) if template.topics else 15,
                    "tags": template.focus_topics or [],
                    "video_url": video_url,
                    "completed": False,
                    "video_watched": False,
                    "exercises_completed": 0,
                    "total_exercises": template.exercise_count // len(template.topics or [1]) if template.topics else 15
                })
            
            # Adaptar contenido basado en rendimiento del usuario
            adapted_content = self._adapt_content_for_user(template, user_data)
            
            unit = {
                "unit_number": template.unit_number,
                "name": template.unit_name,
                "description": template.unit_description,
                "topics": topics,
                "video_urls": template.video_urls or {},
                "reading_materials": template.reading_materials or {},
                "learning_objectives": template.learning_objectives or [],
                "exercise_count": template.exercise_count,
                "recommendations": {
                    "priority": adapted_content["priority"],
                    "weak_areas": template.weak_areas or [],
                    "focus_topics": adapted_content["focus_topics"],
                    "study_time": adapted_content["study_time"],
                    "custom_tips": adapted_content["custom_tips"]
                },
                "unlocked": prerequisites_met and (template.unit_number == 1 or adapted_content["should_unlock"]),
                "progress": 0,
                "video_progress": {},
                "exercise_progress": {},
                "ai_recommended": template.recommendations_priority == "high" or adapted_content["ai_boost"],
                "estimated_completion_time": template.estimated_hours,
                "difficulty_level": template.difficulty_level,
                "icfes_weight": template.icfes_weight
            }
            units.append(unit)
        
        total_questions = sum(template.exercise_count for template in templates)
        total_videos = sum(len(template.video_urls or {}) for template in templates)
        
        return {
            "subject": subject.name,
            "title": f"Mazmorra Adaptativa de {subject.name}",
            "description": f"Plan personalizado para conquistar {subject.name} en el ICFES",
            "units": units,
            "total_questions": total_questions,
            "total_videos": total_videos,
            "estimated_time": f"{sum(template.estimated_hours for template in templates)}-{sum(template.estimated_hours for template in templates) + 2} horas",
            "difficulty_curve": "adaptive",
            "icfes_weight": sum(template.icfes_weight for template in templates),
            "exam_sections": [subject.name],
            "personalization": {
                "based_on_performance": bool(user_data),
                "adaptation_date": datetime.now().isoformat(),
                "focus_areas": self._get_user_focus_areas(user_data) if user_data else []
            }
        }
    
    def _check_prerequisites(self, prerequisite_units: List[int], user_data: Dict[str, Any]) -> bool:
        """Verifica si el usuario ha completado las unidades prerequisito"""
        if not prerequisite_units or not user_data:
            return True
        
        # Aquí verificarías el progreso real del usuario en las unidades prerequisito
        # Por ahora, retorna True para permitir el acceso
        return True
    
    def _adapt_content_for_user(self, template: StudyPlanTemplate, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adapta el contenido de la plantilla basado en el rendimiento del usuario"""
        if not user_data:
            return {
                "priority": template.recommendations_priority,
                "focus_topics": template.focus_topics or [],
                "study_time": template.study_time,
                "custom_tips": [],
                "should_unlock": template.unit_number <= 2,
                "ai_boost": False
            }
        
        # Analizar el rendimiento en temas relacionados
        user_accuracy = user_data.get("accuracy", 0)
        weak_topics = user_data.get("weak_topics", [])
        
        # Adaptaciones basadas en rendimiento
        adapted_priority = template.recommendations_priority
        adapted_focus = list(template.focus_topics or [])
        adapted_time = template.study_time
        custom_tips = []
        ai_boost = False
        
        if user_accuracy < 60:  # Rendimiento bajo
            adapted_priority = "high"
            adapted_time = f"{template.estimated_hours + 1}-{template.estimated_hours + 2} horas"
            custom_tips.append("Dedica tiempo extra a repasar los conceptos básicos")
            ai_boost = True
        elif user_accuracy > 85:  # Rendimiento alto
            adapted_priority = "medium"
            adapted_time = f"{max(1, template.estimated_hours - 1)}-{template.estimated_hours} horas"
            custom_tips.append("Puedes avanzar más rápido, enfócate en ejercicios complejos")
        
        # Agregar temas débiles a focus_topics si coinciden con los temas de la unidad
        for weak_topic in weak_topics:
            if any(weak_topic.lower() in topic.lower() for topic in (template.topics or [])):
                if weak_topic not in adapted_focus:
                    adapted_focus.append(weak_topic)
                custom_tips.append(f"Presta especial atención a {weak_topic}")
        
        return {
            "priority": adapted_priority,
            "focus_topics": adapted_focus,
            "study_time": adapted_time,
            "custom_tips": custom_tips,
            "should_unlock": True,  # Basado en lógica más compleja en producción
            "ai_boost": ai_boost
        }
    
    def _get_user_focus_areas(self, user_data: Dict[str, Any]) -> List[str]:
        """Obtiene las áreas de enfoque del usuario basadas en su rendimiento"""
        if not user_data:
            return []
        
        focus_areas = []
        
        if user_data.get("accuracy", 0) < 70:
            focus_areas.append("Reforzar conceptos básicos")
        
        weak_topics = user_data.get("weak_topics", [])
        if weak_topics:
            focus_areas.extend([f"Mejorar en {topic}" for topic in weak_topics[:3]])
        
        return focus_areas

    def _get_base_plan_for_subject(self, subject_id: str, user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Obtiene el plan base para una materia específica desde las plantillas de la BD
        """
        # Primero intentar obtener plantillas desde la base de datos
        try:
            templates = self.db.query(StudyPlanTemplate).filter(
                StudyPlanTemplate.subject_id == subject_id
            ).order_by(StudyPlanTemplate.unit_number).all()
            
            if templates:
                return self._build_plan_from_templates(templates, user_data)
                
        except Exception as e:
            logger.warning(f"Error obteniendo plantillas de BD para {subject_id}: {e}")
        
        # Fallback a planes hardcodeados si no hay plantillas en BD
        # Get the actual subject to use its correct UUID
        subject = self.db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            logger.error(f"Subject not found: {subject_id}")
            return {"units": [], "estimated_duration": "0 horas", "difficulty": "unknown"}
        
        base_plans = {
            subject.id: {  # Use actual subject ID
                "subject": subject.name,
                "title": f"Mazmorra de {subject.name}: Fundamentos",
                "description": f"Conquista los conceptos fundamentales de {subject.name} ICFES",
                "units": [
                    {
                        "unit_number": 1,
                        "name": "Álgebra Básica y Ecuaciones",
                        "description": "Dominio de operaciones algebraicas y resolución de ecuaciones",
                        "topics": [
                            {"name": "Operaciones con números reales", "difficulty": 1, "questions": 15, "tags": ["aritmética", "básico"]},
                            {"name": "Ecuaciones lineales", "difficulty": 2, "questions": 20, "tags": ["ecuaciones", "álgebra"]},
                            {"name": "Sistemas de ecuaciones", "difficulty": 2, "questions": 18, "tags": ["sistemas", "álgebra"]}
                        ],
                        "recommendations": {
                            "priority": "high",
                            "weak_areas": ["operaciones básicas", "despeje de variables"],
                            "focus_topics": ["ecuaciones lineales", "sistemas 2x2"],
                            "study_time": "3-4 horas"
                        },
                        "unlocked": True,
                        "progress": 0,
                        "ai_recommended": True
                    },
                    {
                        "unit_number": 2,
                        "name": "Geometría Euclidiana",
                        "description": "Propiedades de figuras geométricas y teoremas fundamentales",
                        "topics": [
                            {"name": "Triángulos y teoremas", "difficulty": 2, "questions": 20, "tags": ["triángulos", "teoremas"]},
                            {"name": "Círculos y circunferencias", "difficulty": 2, "questions": 18, "tags": ["círculos", "geometría"]},
                            {"name": "Polígonos regulares", "difficulty": 3, "questions": 15, "tags": ["polígonos", "regular"]}
                        ],
                        "recommendations": {
                            "priority": "high",
                            "weak_areas": ["teorema de Pitágoras", "áreas y perímetros"],
                            "focus_topics": ["triángulos rectángulos", "círculos"],
                            "study_time": "3-4 horas"
                        },
                        "unlocked": True,
                        "progress": 0,
                        "ai_recommended": True
                    },
                    {
                        "unit_number": 3,
                        "name": "Funciones y Gráficas",
                        "description": "Análisis de funciones lineales, cuadráticas y sus representaciones",
                        "topics": [
                            {"name": "Funciones lineales", "difficulty": 2, "questions": 18, "tags": ["funciones", "lineales"]},
                            {"name": "Funciones cuadráticas", "difficulty": 3, "questions": 20, "tags": ["cuadráticas", "parábolas"]},
                            {"name": "Análisis gráfico", "difficulty": 3, "questions": 15, "tags": ["gráficas", "análisis"]}
                        ],
                        "recommendations": {
                            "priority": "medium",
                            "weak_areas": ["dominio y rango", "intersecciones"],
                            "focus_topics": ["funciones cuadráticas", "gráficas"],
                            "study_time": "4-5 horas"
                        },
                        "unlocked": False,
                        "progress": 0,
                        "ai_recommended": True
                    }
                ],
                "total_questions": 300,
                "estimated_time": "22-28 horas",
                "difficulty_curve": "progressive",
                "icfes_weight": 0.25,
                "exam_sections": ["Pensamiento Matemático", "Razonamiento Cuantitativo"]
            },
            "550e8400-e29b-41d4-a716-446655440002": {  # Lenguaje
                "subject": "Lenguaje",
                "title": "Mazmorra de Lenguaje: Comprensión y Análisis",
                "description": "Domina la comprensión lectora y el análisis textual del ICFES",
                "units": [
                    {
                        "unit_number": 1,
                        "name": "Comprensión Lectora Básica",
                        "description": "Estrategias fundamentales para la comprensión de textos",
                        "topics": [
                            {"name": "Identificación de ideas principales", "difficulty": 1, "questions": 20, "tags": ["idea principal", "texto"]},
                            {"name": "Inferencia y deducción", "difficulty": 2, "questions": 18, "tags": ["inferencia", "deducción"]},
                            {"name": "Vocabulario contextual", "difficulty": 2, "questions": 15, "tags": ["vocabulario", "contexto"]}
                        ],
                        "recommendations": {
                            "priority": "high",
                            "weak_areas": ["identificación de ideas", "vocabulario"],
                            "focus_topics": ["ideas principales", "inferencias"],
                            "study_time": "3-4 horas"
                        },
                        "unlocked": True,
                        "progress": 0,
                        "ai_recommended": True
                    },
                    {
                        "unit_number": 2,
                        "name": "Análisis de Textos Informativos",
                        "description": "Comprensión y análisis de textos expositivos y argumentativos",
                        "topics": [
                            {"name": "Estructura de textos informativos", "difficulty": 2, "questions": 18, "tags": ["estructura", "informativo"]},
                            {"name": "Argumentación y tesis", "difficulty": 3, "questions": 20, "tags": ["argumentación", "tesis"]},
                            {"name": "Evidencia y soporte", "difficulty": 3, "questions": 15, "tags": ["evidencia", "soporte"]}
                        ],
                        "recommendations": {
                            "priority": "high",
                            "weak_areas": ["identificación de tesis", "evidencia"],
                            "focus_topics": ["argumentación", "estructura"],
                            "study_time": "4-5 horas"
                        },
                        "unlocked": True,
                        "progress": 0,
                        "ai_recommended": True
                    }
                ],
                "total_questions": 250,
                "estimated_time": "18-23 horas",
                "difficulty_curve": "progressive",
                "icfes_weight": 0.25,
                "exam_sections": ["Lectura Crítica", "Comprensión Lectora"]
            }
        }
        
        return base_plans.get(subject_id)
    
    def _customize_plan(
        self, 
        base_plan: Dict[str, Any], 
        user_data: Dict[str, Any], 
        user_level: int
    ) -> Dict[str, Any]:
        """
        Personaliza el plan base según el rendimiento del usuario
        """
        customized_plan = base_plan.copy()
        
        # Ajustar unidades según el nivel del usuario
        for unit in customized_plan["units"]:
            # Desbloquear unidades basado en el nivel
            if user_level >= unit["unit_number"] * 2:
                unit["unlocked"] = True
            
            # Ajustar recomendaciones basado en temas débiles
            if user_data["weak_topics"]:
                weak_topic_names = [topic["topic"] for topic in user_data["weak_topics"]]
                unit_topics = [topic["name"] for topic in unit["topics"]]
                
                # Si hay temas débiles en esta unidad, aumentar prioridad
                if any(weak_topic in unit_topics for weak_topic in weak_topic_names):
                    unit["recommendations"]["priority"] = "high"
                    unit["ai_recommended"] = True
                
                # Actualizar áreas débiles específicas
                unit["recommendations"]["weak_areas"] = [
                    topic["topic"] for topic in user_data["weak_topics"]
                    if topic["topic"] in unit_topics
                ]
            
            # Ajustar tiempo de estudio basado en precisión
            if user_data["accuracy"] < 60:
                unit["recommendations"]["study_time"] = "5-6 horas"
            elif user_data["accuracy"] < 80:
                unit["recommendations"]["study_time"] = "4-5 horas"
            else:
                unit["recommendations"]["study_time"] = "2-3 horas"
        
        # Agregar recomendaciones personalizadas
        customized_plan["personalized_recommendations"] = {
            "overall_accuracy": user_data["accuracy"],
            "weak_topics": user_data["weak_topics"][:3],
            "strong_topics": user_data["strong_topics"][:3],
            "suggested_focus": self._get_suggested_focus(user_data),
            "study_schedule": self._generate_study_schedule(user_data, user_level),
            "estimated_improvement": self._estimate_improvement(user_data)
        }
        
        return customized_plan
    
    def _get_suggested_focus(self, user_data: Dict[str, Any]) -> List[str]:
        """
        Obtiene sugerencias de enfoque basadas en el rendimiento
        """
        suggestions = []
        
        if user_data["accuracy"] < 60:
            suggestions.append("Enfócate en conceptos básicos y fundamentos")
            suggestions.append("Practica más preguntas de dificultad baja")
        elif user_data["accuracy"] < 80:
            suggestions.append("Refuerza temas intermedios")
            suggestions.append("Practica análisis y aplicación")
        else:
            suggestions.append("Enfócate en temas avanzados")
            suggestions.append("Practica problemas complejos")
        
        if user_data["weak_topics"]:
            suggestions.append(f"Prioriza: {', '.join([t['topic'] for t in user_data['weak_topics'][:2]])}")
        
        return suggestions
    
    def _generate_study_schedule(self, user_data: Dict[str, Any], user_level: int) -> Dict[str, Any]:
        """
        Genera un horario de estudio personalizado
        """
        if user_data["accuracy"] < 60:
            sessions_per_day = 3
            session_duration = 45
        elif user_data["accuracy"] < 80:
            sessions_per_day = 2
            session_duration = 40
        else:
            sessions_per_day = 2
            session_duration = 30
        
        return {
            "sessions_per_day": sessions_per_day,
            "session_duration_minutes": session_duration,
            "total_study_time_per_day": sessions_per_day * session_duration,
            "recommended_days": ["Lunes", "Miércoles", "Viernes", "Sábado"],
            "break_duration": 15,
            "focus_areas": [topic["topic"] for topic in user_data["weak_topics"][:2]]
        }
    
    def _estimate_improvement(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estima la mejora potencial basada en el rendimiento actual
        """
        current_accuracy = user_data["accuracy"]
        
        if current_accuracy < 60:
            potential_improvement = 20
            weeks_to_improve = 8
        elif current_accuracy < 80:
            potential_improvement = 15
            weeks_to_improve = 6
        else:
            potential_improvement = 10
            weeks_to_improve = 4
        
        return {
            "current_accuracy": current_accuracy,
            "potential_improvement": potential_improvement,
            "target_accuracy": min(100, current_accuracy + potential_improvement),
            "weeks_to_improve": weeks_to_improve,
            "confidence_level": "high" if user_data["total_questions"] > 50 else "medium"
        }
    
    def _create_initial_progress(self, plan_id: str, units: List[Dict[str, Any]]):
        """
        Crea registros de progreso inicial para todas las unidades
        """
        for unit in units:
            progress = PlanProgress(
                plan_id=plan_id,
                unit_number=unit["unit_number"],
                unit_name=unit["name"],
                unit_description=unit["description"],
                unit_content={
                    "videos": [f"https://youtube.com/watch?v={unit['name'].lower().replace(' ', '')}1"],
                    "exercises": sum(topic["questions"] for topic in unit["topics"]),
                    "readings": 3
                },
                is_completed=False,
                score=0.00,
                weighted_progress={
                    "videos": {"completed": 0, "total": 1, "weight": 0.3},
                    "exercises": {"completed": 0, "total": sum(topic["questions"] for topic in unit["topics"]), "weight": 0.5},
                    "readings": {"completed": 0, "total": 3, "weight": 0.2}
                }
            )
            self.db.add(progress)
        
        self.db.commit()
    
    def get_user_study_plans(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los planes de estudio de un usuario
        """
        plans = self.db.query(StudyPlan).filter(
            StudyPlan.user_id == user_id,
            StudyPlan.is_active == True
        ).all()
        
        result = []
        for plan in plans:
            plan_data = json.loads(plan.plan_data) if isinstance(plan.plan_data, str) else plan.plan_data
            
            # Calcular progreso detallado
            progress_details = self._calculate_detailed_progress(plan.id)
            
            # Convert units to proper format if they exist
            units = plan_data.get("units", [])
            if units:
                from ..schemas.study_plan import StudyUnit, StudyTopic, UnitRecommendations
                
                converted_units = []
                for unit in units:
                    # Convert topics to StudyTopic schema
                    study_topics = []
                    for topic in unit.get("topics", []):
                        study_topics.append(StudyTopic(
                            name=topic.get("main_topic", "Tema"),
                            difficulty=topic.get("difficulty", 1),
                            questions=5,  # Default 5 questions per topic
                            tags=[topic.get("code", ""), topic.get("main_topic", "")]
                        ))
                    
                    # Create UnitRecommendations
                    unit_recommendations = UnitRecommendations(
                        priority=unit.get("recommendations", {}).get("priority", "medium"),
                        weak_areas=unit.get("recommendations", {}).get("weak_areas", []),
                        focus_topics=unit.get("recommendations", {}).get("focus_topics", []),
                        study_time=unit.get("recommendations", {}).get("study_time", "2 horas")
                    )
                    
                    # Create StudyUnit
                    study_unit = StudyUnit(
                        unit_number=unit.get("unit_number", 1),
                        name=unit.get("name", "Unidad"),
                        description=unit.get("description", "Descripción de la unidad"),
                        topics=study_topics,
                        recommendations=unit_recommendations,
                        unlocked=unit.get("unlocked", True),
                        progress=0.0,  # Initial progress
                        ai_recommended=unit.get("ai_recommended", False)
                    )
                    converted_units.append(study_unit)
            else:
                converted_units = []
            
            result.append({
                "id": str(plan.id),
                "plan_name": plan.plan_name,
                "subject": plan_data.get("subject", "Desconocido"),
                "title": plan_data.get("title", ""),
                "description": plan_data.get("description", ""),
                "units": converted_units,
                "total_units": plan.total_units,
                "completed_units": plan.completed_units,
                "progress_percentage": float(plan.progress_percentage),
                "estimated_time": plan_data.get("estimated_time", ""),
                "difficulty_curve": plan_data.get("difficulty_curve", "progressive"),
                "icfes_weight": plan_data.get("icfes_weight", 0.0),
                "exam_sections": plan_data.get("exam_sections", []),
                "personalized_recommendations": {
                    "overall_accuracy": plan_data.get("personalized_recommendations", {}).get("overall_accuracy", 0.0),
                    "weak_topics": plan_data.get("personalized_recommendations", {}).get("weak_topics", []),
                    "strong_topics": plan_data.get("personalized_recommendations", {}).get("strong_topics", []),
                    "suggested_focus": plan_data.get("personalized_recommendations", {}).get("suggested_focus", []),
                    "study_schedule": plan_data.get("personalized_recommendations", {}).get("study_schedule", {}),
                    "estimated_improvement": plan_data.get("personalized_recommendations", {}).get("estimated_improvement", {})
                },
                "progress_details": progress_details,
                "last_updated": plan.updated_at.isoformat() if plan.updated_at else None
            })
        
        return result
    
    def _calculate_detailed_progress(self, plan_id: str) -> Dict[str, Any]:
        """
        Calcula el progreso detallado de un plan
        """
        progress_records = self.db.query(PlanProgress).filter(
            PlanProgress.plan_id == plan_id
        ).all()
        
        total_progress = 0
        completed_units = 0
        unit_details = []
        
        for progress in progress_records:
            # Calcular progreso ponderado
            weighted_data = progress.weighted_progress
            if isinstance(weighted_data, str):
                weighted_data = json.loads(weighted_data)
            
            unit_progress = (
                (weighted_data["videos"]["completed"] / weighted_data["videos"]["total"] * weighted_data["videos"]["weight"]) +
                (weighted_data["exercises"]["completed"] / weighted_data["exercises"]["total"] * weighted_data["exercises"]["weight"]) +
                (weighted_data["readings"]["completed"] / weighted_data["readings"]["total"] * weighted_data["readings"]["weight"])
            ) * 100
            
            total_progress += unit_progress
            if progress.is_completed:
                completed_units += 1
            
            unit_details.append({
                "unit_number": progress.unit_number,
                "unit_name": progress.unit_name,
                "is_completed": progress.is_completed,
                "score": float(progress.score),
                "progress_percentage": unit_progress,
                "weighted_progress": weighted_data
            })
        
        return {
            "overall_progress": total_progress / len(progress_records) if progress_records else 0,
            "completed_units": completed_units,
            "unit_details": unit_details
        }
    
    def update_unit_progress(
        self, 
        plan_id: str, 
        unit_number: int, 
        progress_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualiza el progreso de una unidad específica
        """
        progress = self.db.query(PlanProgress).filter(
            PlanProgress.plan_id == plan_id,
            PlanProgress.unit_number == unit_number
        ).first()
        
        if not progress:
            raise ValueError("Progreso de unidad no encontrado")
        
        # Actualizar progreso ponderado
        current_weighted = progress.weighted_progress
        if isinstance(current_weighted, str):
            current_weighted = json.loads(current_weighted)
        
        # Actualizar según el tipo de progreso
        if "videos_completed" in progress_data:
            current_weighted["videos"]["completed"] = min(
                current_weighted["videos"]["completed"] + progress_data["videos_completed"],
                current_weighted["videos"]["total"]
            )
        
        if "exercises_completed" in progress_data:
            current_weighted["exercises"]["completed"] = min(
                current_weighted["exercises"]["completed"] + progress_data["exercises_completed"],
                current_weighted["exercises"]["total"]
            )
        
        if "readings_completed" in progress_data:
            current_weighted["readings"]["completed"] = min(
                current_weighted["readings"]["completed"] + progress_data["readings_completed"],
                current_weighted["readings"]["total"]
            )
        
        # Calcular progreso total
        total_progress = (
            (current_weighted["videos"]["completed"] / current_weighted["videos"]["total"] * current_weighted["videos"]["weight"]) +
            (current_weighted["exercises"]["completed"] / current_weighted["exercises"]["total"] * current_weighted["exercises"]["weight"]) +
            (current_weighted["readings"]["completed"] / current_weighted["readings"]["total"] * current_weighted["readings"]["weight"])
        ) * 100
        
        # Actualizar registro
        progress.weighted_progress = current_weighted
        progress.score = progress_data.get("score", progress.score)
        
        # Marcar como completada si alcanza 80%
        if total_progress >= 80 and not progress.is_completed:
            progress.is_completed = True
            progress.completion_date = datetime.now()
        
        self.db.commit()
        
        return {
            "unit_number": unit_number,
            "progress_percentage": total_progress,
            "is_completed": progress.is_completed,
            "weighted_progress": current_weighted
        }
    
    def _apply_diagnostic_intelligence(
        self, 
        base_plan: Dict[str, Any], 
        analytics: DiagnosticTestAnalytics, 
        tracking: DiagnosticImprovementTracking, 
        error_patterns: List[DiagnosticErrorPattern]
    ) -> Dict[str, Any]:
        """
        Aplica inteligencia artificial basada en el diagnóstico para personalizar el plan
        """
        intelligent_plan = base_plan.copy()
        
        # 1. Reordenar unidades basado en debilidades críticas
        critical_weaknesses = analytics.critical_weaknesses if analytics.critical_weaknesses else []
        recommended_topics = analytics.recommended_topics if analytics.recommended_topics else []
        
        # 2. Ajustar dificultad basada en performance
        score_percentage = float(analytics.score_percentage)
        difficulty_adjustment = self._calculate_difficulty_adjustment(score_percentage)
        
        # 3. Personalizar tiempo de estudio basado en patrones de respuesta
        learning_style = analytics.learning_style_indicators or {}
        time_multiplier = self._calculate_time_multiplier(learning_style, tracking)
        
        # 4. Aplicar modificaciones a las unidades
        if 'units' in intelligent_plan:
            intelligent_plan['units'] = self._reorder_and_enhance_units(
                intelligent_plan['units'],
                critical_weaknesses,
                recommended_topics,
                difficulty_adjustment,
                time_multiplier,
                error_patterns
            )
        
        # 5. Añadir sección de análisis personalizado
        intelligent_plan['diagnostic_insights'] = {
            'score_percentage': score_percentage,
            'percentile_rank': float(analytics.percentile_rank) if analytics.percentile_rank else 50,
            'critical_weaknesses': critical_weaknesses,
            'recommended_focus': recommended_topics,
            'learning_style_detected': learning_style,
            'improvement_trend': tracking.score_trend if tracking and tracking.score_trend else [],
            'estimated_study_time': tracking.estimated_study_time_hours if tracking else None,
            'error_patterns_summary': [
                {
                    'type': pattern.error_type,
                    'frequency': pattern.frequency,
                    'recommended_actions': pattern.recommended_actions
                }
                for pattern in error_patterns
            ]
        }
        
        # 6. Generar objetivos SMART basados en análisis
        intelligent_plan['smart_goals'] = self._generate_smart_goals(analytics, tracking)
        
        # 7. Configurar sistema de alertas y recordatorios
        intelligent_plan['intelligent_alerts'] = self._configure_intelligent_alerts(analytics, error_patterns)
        
        # 8. Añadir recomendaciones de recursos específicos
        intelligent_plan['resource_recommendations'] = self._generate_resource_recommendations(
            critical_weaknesses, error_patterns
        )
        
        return intelligent_plan
    
    def _calculate_difficulty_adjustment(self, score_percentage: float) -> float:
        """Calcular ajuste de dificultad basado en el score"""
        if score_percentage >= 80:
            return 1.2  # Incrementar dificultad 20%
        elif score_percentage >= 60:
            return 1.0  # Mantener dificultad estándar
        elif score_percentage >= 40:
            return 0.8  # Reducir dificultad 20%
        else:
            return 0.6  # Reducir dificultad 40%
    
    def _calculate_time_multiplier(self, learning_style: Dict, tracking: DiagnosticImprovementTracking) -> float:
        """Calcular multiplicador de tiempo basado en estilo de aprendizaje"""
        base_multiplier = 1.0
        
        if learning_style.get('thorough_analyzer', False):
            base_multiplier *= 1.3  # Necesita más tiempo
        elif learning_style.get('fast_responder', False):
            base_multiplier *= 0.8  # Puede ir más rápido
        
        # Ajustar basado en consistencia
        if tracking and tracking.consistency_score:
            consistency = float(tracking.consistency_score)
            if consistency < 50:  # Baja consistencia
                base_multiplier *= 1.2  # Más tiempo para consolidar
        
        return base_multiplier
    
    def _reorder_and_enhance_units(
        self, 
        units: List[Dict], 
        critical_weaknesses: List[str], 
        recommended_topics: List[str],
        difficulty_adjustment: float,
        time_multiplier: float,
        error_patterns: List[DiagnosticErrorPattern]
    ) -> List[Dict]:
        """Reordenar y mejorar unidades basado en análisis"""
        enhanced_units = []
        
        # Crear mapa de prioridades
        topic_priorities = {}
        for i, weakness in enumerate(critical_weaknesses):
            topic_priorities[weakness.lower()] = 10 - i  # Mayor prioridad para primeras debilidades
        
        for topic in recommended_topics:
            if topic.lower() not in topic_priorities:
                topic_priorities[topic.lower()] = 5  # Prioridad media
        
        # Procesar cada unidad
        for unit in units:
            enhanced_unit = unit.copy()
            unit_topics = unit.get('topics', [])
            
            # Calcular prioridad de la unidad
            unit_priority = 0
            for topic in unit_topics:
                if isinstance(topic, str):
                    unit_priority += topic_priorities.get(topic.lower(), 1)
            
            enhanced_unit['priority_score'] = unit_priority
            
            # Ajustar tiempo estimado
            if 'estimated_hours' in enhanced_unit:
                enhanced_unit['estimated_hours'] = int(enhanced_unit['estimated_hours'] * time_multiplier)
            
            # Añadir recursos específicos para errores
            enhanced_unit['error_specific_resources'] = self._get_error_specific_resources(
                unit_topics, error_patterns
            )
            
            # Ajustar ejercicios basado en dificultad
            if 'exercise_count' in enhanced_unit:
                enhanced_unit['exercise_count'] = int(enhanced_unit['exercise_count'] * difficulty_adjustment)
            
            enhanced_units.append(enhanced_unit)
        
        # Reordenar por prioridad (mayor prioridad primero)
        enhanced_units.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        return enhanced_units
    
    def _generate_smart_goals(self, analytics: DiagnosticTestAnalytics, tracking: DiagnosticImprovementTracking) -> List[Dict]:
        """Generar objetivos SMART basados en análisis"""
        goals = []
        current_score = float(analytics.score_percentage)
        
        # Objetivo principal de mejora de score
        if current_score < 70:
            target_improvement = min(20, 70 - current_score)
            goals.append({
                'type': 'score_improvement',
                'description': f"Mejorar puntaje del {current_score:.1f}% al {current_score + target_improvement:.1f}%",
                'target_value': current_score + target_improvement,
                'current_value': current_score,
                'timeline_weeks': 4,
                'measurable': True,
                'specific': True
            })
        
        # Objetivos por debilidades críticas
        for weakness in analytics.critical_weaknesses[:3]:  # Top 3 debilidades
            goals.append({
                'type': 'topic_mastery',
                'description': f"Dominar el tema: {weakness}",
                'target_value': 80,  # 80% de dominio
                'current_value': analytics.score_by_topic.get(weakness, 0) if analytics.score_by_topic else 0,
                'timeline_weeks': 2,
                'topic': weakness,
                'measurable': True,
                'specific': True
            })
        
        # Objetivo de consistencia si hay tracking
        if tracking and tracking.consistency_score and float(tracking.consistency_score) < 70:
            goals.append({
                'type': 'consistency',
                'description': "Mejorar consistencia en el rendimiento",
                'target_value': 80,
                'current_value': float(tracking.consistency_score),
                'timeline_weeks': 6,
                'measurable': True,
                'specific': True
            })
        
        return goals
    
    def _configure_intelligent_alerts(self, analytics: DiagnosticTestAnalytics, error_patterns: List[DiagnosticErrorPattern]) -> List[Dict]:
        """Configurar alertas inteligentes basadas en patrones"""
        alerts = []
        
        # Alertas por patrones de error frecuentes
        for pattern in error_patterns:
            if pattern.frequency >= 3:
                alerts.append({
                    'type': 'error_pattern_alert',
                    'message': f"Patrón de error detectado en {pattern.error_type}",
                    'frequency': 'weekly',
                    'action_required': pattern.recommended_actions,
                    'priority': 'high' if pattern.frequency >= 5 else 'medium'
                })
        
        # Alert por score bajo en competencias
        if analytics.competency_scores:
            for competency, score in analytics.competency_scores.items():
                if score < 50:
                    alerts.append({
                        'type': 'competency_alert',
                        'message': f"Score bajo en {competency}: {score:.1f}%",
                        'frequency': 'bi-weekly',
                        'action_required': [f"Reforzar práctica en {competency}"],
                        'priority': 'high'
                    })
        
        return alerts
    
    def _generate_resource_recommendations(self, critical_weaknesses: List[str], error_patterns: List[DiagnosticErrorPattern]) -> Dict[str, List[Dict]]:
        """Generar recomendaciones de recursos específicos"""
        recommendations = {
            'videos': [],
            'exercises': [],
            'readings': [],
            'tools': []
        }
        
        # Recursos por debilidades
        for weakness in critical_weaknesses:
            recommendations['videos'].append({
                'title': f"Videos explicativos: {weakness}",
                'description': f"Material audiovisual para reforzar {weakness}",
                'priority': 'high',
                'estimated_time': '30-45 minutos'
            })
            
            recommendations['exercises'].append({
                'title': f"Ejercicios prácticos: {weakness}",
                'description': f"Problemas específicos de {weakness}",
                'priority': 'high',
                'estimated_time': '1-2 horas'
            })
        
        # Recursos por patrones de error
        error_type_resources = {
            'conceptual': {
                'videos': 'Videos de conceptos fundamentales',
                'readings': 'Material teórico de base',
                'tools': 'Simuladores conceptuales'
            },
            'procedural': {
                'videos': 'Videos paso a paso',
                'exercises': 'Ejercicios guiados',
                'tools': 'Calculadoras especializadas'
            },
            'computational': {
                'exercises': 'Ejercicios de cálculo',
                'tools': 'Herramientas de cálculo',
                'videos': 'Técnicas de cálculo mental'
            },
            'reading': {
                'readings': 'Ejercicios de comprensión',
                'videos': 'Técnicas de lectura',
                'tools': 'Herramientas de análisis de texto'
            }
        }
        
        for pattern in error_patterns:
            if pattern.error_type in error_type_resources:
                resources = error_type_resources[pattern.error_type]
                for resource_type, description in resources.items():
                    if resource_type in recommendations:
                        recommendations[resource_type].append({
                            'title': description,
                            'description': f"Para resolver errores de tipo {pattern.error_type}",
                            'priority': 'medium',
                            'estimated_time': '30-60 minutos'
                        })
        
        return recommendations
    
    def _get_error_specific_resources(self, unit_topics: List[str], error_patterns: List[DiagnosticErrorPattern]) -> List[Dict]:
        """Obtener recursos específicos para errores en una unidad"""
        resources = []
        
        for pattern in error_patterns:
            # Si el error está relacionado con temas de esta unidad
            for topic in unit_topics:
                if isinstance(topic, str) and topic.lower() in pattern.error_description.lower():
                    resources.extend(pattern.recommended_actions)
                    break
        
        return [{'action': action, 'type': 'error_resolution'} for action in set(resources)] 