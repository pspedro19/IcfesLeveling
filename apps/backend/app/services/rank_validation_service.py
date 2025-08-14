from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from ..models.user import User
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.diagnostic_test import DiagnosticTest
from ..models.subject import Subject
from ..models.video_tracking import VideoTracking
from ..models.battle import BattleAnswer

logger = logging.getLogger(__name__)

class RankValidationService:
    """
    Servicio para validar y controlar el acceso a reevaluaciones de rango
    basado en completación de planes de estudio
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Requisitos mínimos por materia para reevaluación
        self.MIN_COMPLETION_PERCENTAGE = 85.0  # 85% de plan completado
        self.MIN_UNITS_COMPLETED = 3  # Al menos 3 unidades completadas
        self.MIN_VIDEO_WATCH_PERCENTAGE = 70.0  # 70% de videos vistos
        self.MIN_EXERCISES_COMPLETED = 80.0  # 80% de ejercicios hechos
        
        # Configuración de examen de reevaluación
        self.REEVALUATION_QUESTIONS_PER_SUBJECT = 45
        self.MIN_ACCURACY_FOR_RANK_UP = 75.0  # Precisión mínima para subir de rango
        
    def check_reevaluation_eligibility(
        self, 
        user_id: str, 
        subject_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verifica si el usuario puede solicitar una reevaluación de rango
        
        Args:
            user_id: ID del usuario
            subject_id: ID de la materia específica (opcional, si None verifica todas)
            
        Returns:
            Dict con elegibilidad y detalles
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"eligible": False, "reason": "Usuario no encontrado"}
        
        if subject_id:
            # Verificar una materia específica
            return self._check_subject_eligibility(user_id, subject_id)
        else:
            # Verificar todas las materias
            return self._check_overall_eligibility(user_id)
    
    def _check_subject_eligibility(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """Verifica elegibilidad para una materia específica"""
        
        # Obtener el plan de estudio activo para esta materia
        active_plan = self.db.query(StudyPlan).filter(
            and_(
                StudyPlan.user_id == user_id,
                StudyPlan.subject_id == subject_id,
                StudyPlan.is_active == True
            )
        ).first()
        
        if not active_plan:
            return {
                "eligible": False,
                "reason": "No tienes un plan de estudio activo para esta materia",
                "subject_id": subject_id,
                "requirements_met": False
            }
        
        # Verificar progreso del plan
        plan_completion = self._calculate_plan_completion(active_plan.id)
        
        # Verificar progreso de videos
        video_completion = self._calculate_video_completion(user_id, active_plan.id)
        
        # Verificar progreso de ejercicios
        exercise_completion = self._calculate_exercise_completion(user_id, active_plan.id)
        
        # Verificar reevaluaciones previas recientes
        recent_reevaluation = self._check_recent_reevaluations(user_id, subject_id)
        
        # Determinar elegibilidad
        requirements_met = (
            plan_completion["percentage"] >= self.MIN_COMPLETION_PERCENTAGE and
            plan_completion["completed_units"] >= self.MIN_UNITS_COMPLETED and
            video_completion["percentage"] >= self.MIN_VIDEO_WATCH_PERCENTAGE and
            exercise_completion["percentage"] >= self.MIN_EXERCISES_COMPLETED and
            not recent_reevaluation["has_recent"]
        )
        
        return {
            "eligible": requirements_met,
            "subject_id": subject_id,
            "subject_name": active_plan.subject.name if active_plan.subject else "Unknown",
            "requirements_met": requirements_met,
            "plan_completion": plan_completion,
            "video_completion": video_completion,
            "exercise_completion": exercise_completion,
            "recent_reevaluation": recent_reevaluation,
            "reason": self._generate_eligibility_reason(
                requirements_met, plan_completion, video_completion, 
                exercise_completion, recent_reevaluation
            ),
            "next_exam_info": {
                "questions_count": self.REEVALUATION_QUESTIONS_PER_SUBJECT,
                "estimated_duration": "45-60 minutos",
                "passing_score": self.MIN_ACCURACY_FOR_RANK_UP
            }
        }
    
    def _check_overall_eligibility(self, user_id: str) -> Dict[str, Any]:
        """Verifica elegibilidad general para reevaluación de rango"""
        
        # Obtener todas las materias con planes activos
        subjects = self.db.query(Subject).join(StudyPlan).filter(
            and_(
                StudyPlan.user_id == user_id,
                StudyPlan.is_active == True
            )
        ).all()
        
        if not subjects:
            return {
                "eligible": False,
                "reason": "No tienes planes de estudio activos",
                "subjects_status": {}
            }
        
        subjects_status = {}
        eligible_subjects = []
        
        for subject in subjects:
            subject_eligibility = self._check_subject_eligibility(user_id, str(subject.id))
            subjects_status[str(subject.id)] = subject_eligibility
            
            if subject_eligibility["eligible"]:
                eligible_subjects.append(subject.name)
        
        overall_eligible = len(eligible_subjects) > 0
        
        return {
            "eligible": overall_eligible,
            "eligible_subjects": eligible_subjects,
            "subjects_status": subjects_status,
            "total_subjects": len(subjects),
            "eligible_count": len(eligible_subjects),
            "reason": f"Puedes reevaluar en: {', '.join(eligible_subjects)}" if eligible_subjects 
                     else "Necesitas completar más contenido en tus planes de estudio"
        }
    
    def _calculate_plan_completion(self, plan_id: str) -> Dict[str, Any]:
        """Calcula el progreso de completación de un plan"""
        
        # Obtener progreso de unidades
        unit_progresses = self.db.query(PlanProgress).filter(
            PlanProgress.plan_id == plan_id
        ).all()
        
        if not unit_progresses:
            return {"percentage": 0.0, "completed_units": 0, "total_units": 0}
        
        total_units = len(unit_progresses)
        completed_units = sum(1 for up in unit_progresses if up.is_completed)
        
        # Calcular porcentaje promedio de todas las unidades
        total_score = sum(float(up.score or 0) for up in unit_progresses)
        average_score = total_score / total_units if total_units > 0 else 0
        
        return {
            "percentage": round(average_score, 2),
            "completed_units": completed_units,
            "total_units": total_units,
            "completion_rate": round((completed_units / total_units) * 100, 2) if total_units > 0 else 0
        }
    
    def _calculate_video_completion(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        """Calcula el progreso de videos vistos"""
        
        video_trackings = self.db.query(VideoTracking).filter(
            and_(
                VideoTracking.user_id == user_id,
                VideoTracking.plan_id == plan_id
            )
        ).all()
        
        if not video_trackings:
            return {"percentage": 0.0, "completed_videos": 0, "total_videos": 0}
        
        total_videos = len(video_trackings)
        completed_videos = sum(1 for vt in video_trackings if vt.is_completed)
        
        # Calcular porcentaje promedio de visualización
        total_watch_percentage = sum(vt.watch_percentage for vt in video_trackings)
        average_watch_percentage = total_watch_percentage / total_videos if total_videos > 0 else 0
        
        return {
            "percentage": round(average_watch_percentage, 2),
            "completed_videos": completed_videos,
            "total_videos": total_videos,
            "completion_rate": round((completed_videos / total_videos) * 100, 2) if total_videos > 0 else 0
        }
    
    def _calculate_exercise_completion(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        """Calcula el progreso de ejercicios completados"""
        
        # Obtener progreso de ejercicios de las unidades
        unit_progresses = self.db.query(PlanProgress).filter(
            PlanProgress.plan_id == plan_id
        ).all()
        
        if not unit_progresses:
            return {"percentage": 0.0, "completed_exercises": 0, "total_exercises": 0}
        
        total_exercises = 0
        completed_exercises = 0
        total_accuracy = 0
        
        for unit_progress in unit_progresses:
            exercises_data = unit_progress.weighted_progress.get("exercises", {})
            
            unit_total = exercises_data.get("total", 0)
            unit_completed = exercises_data.get("completed", 0)
            unit_accuracy = exercises_data.get("accuracy", 0)
            
            total_exercises += unit_total
            completed_exercises += unit_completed
            total_accuracy += unit_accuracy
        
        completion_percentage = (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0
        average_accuracy = total_accuracy / len(unit_progresses) if unit_progresses else 0
        
        return {
            "percentage": round(completion_percentage, 2),
            "completed_exercises": completed_exercises,
            "total_exercises": total_exercises,
            "average_accuracy": round(average_accuracy, 2)
        }
    
    def _check_recent_reevaluations(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """Verifica si hay reevaluaciones recientes que bloqueen una nueva"""
        
        # Buscar reevaluaciones en los últimos 30 días
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_test = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.subject_id == subject_id,
                DiagnosticTest.reassessment_type == "rank_reevaluation",
                DiagnosticTest.created_at >= thirty_days_ago
            )
        ).order_by(DiagnosticTest.created_at.desc()).first()
        
        if recent_test:
            days_since = (datetime.utcnow() - recent_test.created_at).days
            return {
                "has_recent": True,
                "days_since_last": days_since,
                "last_score": float(recent_test.score_percentage),
                "can_retake_in_days": max(0, 30 - days_since)
            }
        
        return {"has_recent": False, "days_since_last": None}
    
    def _generate_eligibility_reason(
        self, 
        requirements_met: bool, 
        plan_completion: Dict[str, Any],
        video_completion: Dict[str, Any],
        exercise_completion: Dict[str, Any],
        recent_reevaluation: Dict[str, Any]
    ) -> str:
        """Genera un mensaje explicativo sobre la elegibilidad"""
        
        if requirements_met:
            return "¡Cumples todos los requisitos para la reevaluación de rango!"
        
        reasons = []
        
        if plan_completion["percentage"] < self.MIN_COMPLETION_PERCENTAGE:
            needed = self.MIN_COMPLETION_PERCENTAGE - plan_completion["percentage"]
            reasons.append(f"Completa {needed:.1f}% más del plan de estudio")
        
        if plan_completion["completed_units"] < self.MIN_UNITS_COMPLETED:
            needed = self.MIN_UNITS_COMPLETED - plan_completion["completed_units"]
            reasons.append(f"Completa {needed} unidades más")
        
        if video_completion["percentage"] < self.MIN_VIDEO_WATCH_PERCENTAGE:
            needed = self.MIN_VIDEO_WATCH_PERCENTAGE - video_completion["percentage"]
            reasons.append(f"Ve {needed:.1f}% más de los videos")
        
        if exercise_completion["percentage"] < self.MIN_EXERCISES_COMPLETED:
            needed = self.MIN_EXERCISES_COMPLETED - exercise_completion["percentage"]
            reasons.append(f"Completa {needed:.1f}% más de ejercicios")
        
        if recent_reevaluation["has_recent"]:
            days_to_wait = recent_reevaluation["can_retake_in_days"]
            reasons.append(f"Espera {days_to_wait} días para la próxima reevaluación")
        
        return "Para reevaluar necesitas: " + "; ".join(reasons)
    
    def create_rank_reevaluation_exam(
        self, 
        user_id: str, 
        subject_id: str
    ) -> DiagnosticTest:
        """
        Crea un examen de reevaluación de rango con 45 preguntas
        """
        # Verificar elegibilidad
        eligibility = self._check_subject_eligibility(user_id, subject_id)
        if not eligibility["eligible"]:
            raise ValueError(f"No eligible for reevaluation: {eligibility['reason']}")
        
        # Crear test de reevaluación
        reevaluation_test = DiagnosticTest(
            user_id=user_id,
            subject_id=subject_id,
            test_type="rank_reevaluation",
            reassessment_type="rank_reevaluation",
            is_monthly_reassessment=False,
            status="in_progress"
        )
        
        self.db.add(reevaluation_test)
        self.db.commit()
        self.db.refresh(reevaluation_test)
        
        logger.info(f"Created rank reevaluation exam {reevaluation_test.id} for user {user_id}")
        
        return reevaluation_test
    
    def get_reevaluation_dashboard(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene un dashboard completo del estado de reevaluación del usuario
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}
        
        # Verificar elegibilidad general
        overall_eligibility = self._check_overall_eligibility(user_id)
        
        # Obtener información del usuario
        user_info = {
            "current_level": user.level,
            "current_rank": user.rank,
            "experience": user.experience,
            "next_rank_requirements": self._calculate_next_rank_requirements(user.rank)
        }
        
        # Obtener historial de reevaluaciones
        reevaluation_history = self._get_reevaluation_history(user_id)
        
        return {
            "user_info": user_info,
            "eligibility": overall_eligibility,
            "reevaluation_history": reevaluation_history,
            "exam_config": {
                "questions_per_subject": self.REEVALUATION_QUESTIONS_PER_SUBJECT,
                "min_accuracy_for_rank_up": self.MIN_ACCURACY_FOR_RANK_UP,
                "cooldown_days": 30
            },
            "requirements": {
                "min_plan_completion": self.MIN_COMPLETION_PERCENTAGE,
                "min_units_completed": self.MIN_UNITS_COMPLETED,
                "min_video_completion": self.MIN_VIDEO_WATCH_PERCENTAGE,
                "min_exercise_completion": self.MIN_EXERCISES_COMPLETED
            }
        }
    
    def _calculate_next_rank_requirements(self, current_rank: str) -> Dict[str, Any]:
        """Calcula los requisitos para el siguiente rango"""
        rank_order = ["E", "D", "C", "B", "A", "S", "SS", "SSS"]
        
        try:
            current_index = rank_order.index(current_rank)
            if current_index >= len(rank_order) - 1:
                return {"next_rank": current_rank, "is_max_rank": True}
            
            next_rank = rank_order[current_index + 1]
            
            return {
                "next_rank": next_rank,
                "is_max_rank": False,
                "requirements": f"Aprobar examen de reevaluación con {self.MIN_ACCURACY_FOR_RANK_UP}% de precisión"
            }
        except ValueError:
            return {"next_rank": "D", "is_max_rank": False}
    
    def _get_reevaluation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene el historial de reevaluaciones del usuario"""
        
        tests = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.reassessment_type == "rank_reevaluation"
            )
        ).order_by(DiagnosticTest.created_at.desc()).limit(10).all()
        
        history = []
        for test in tests:
            history.append({
                "id": str(test.id),
                "subject_name": test.subject.name if test.subject else "Unknown",
                "score": float(test.score_percentage),
                "passed": test.score_percentage >= self.MIN_ACCURACY_FOR_RANK_UP,
                "date": test.created_at.isoformat(),
                "questions_answered": test.questions_answered,
                "status": test.status
            })
        
        return history