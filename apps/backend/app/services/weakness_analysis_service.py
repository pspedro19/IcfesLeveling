"""
PASO 11: Servicio de análisis inteligente de debilidades
Gestiona la vista materializada y proporciona análisis avanzado de debilidades estudiantiles
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text, desc
from sqlalchemy.sql import select
from dataclasses import dataclass

from app.core.database import get_db
from app.models.user_answer import UserAnswer
from app.models.question import Question
from app.models.user import User
from app.models.subject import Subject
from app.models.topic import Topic

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeaknessSeverity(Enum):
    CRITICAL = "critical"
    SIGNIFICANT = "significant"
    TIME_INEFFICIENT = "time_inefficient"
    MINOR = "minor"

class WeaknessType(Enum):
    CONCEPTUAL_GAP = "conceptual_gap"
    PROCEDURAL_SLOWNESS = "procedural_slowness"
    SYSTEMATIC_ERROR = "systematic_error"
    INCONSISTENT_PERFORMANCE = "inconsistent_performance"
    GENERAL_WEAKNESS = "general_weakness"

class AlertType(Enum):
    CRITICAL_WEAKNESS = "critical_weakness"
    SYSTEMATIC_ERROR = "systematic_error"
    PERFORMANCE_DECLINE = "performance_decline"

@dataclass
class WeaknessAnalysis:
    """Estructura de datos para análisis de debilidades"""
    student_id: str
    subject_id: str
    topic_id: str
    subject_name: str
    topic_name: str
    total_attempts: int
    correct_answers: int
    accuracy_percentage: float
    avg_time_seconds: float
    p90_time_seconds: float
    dominant_distractor: Optional[str]
    weakness_severity: WeaknessSeverity
    weakness_type: WeaknessType
    intervention_priority_score: float
    needs_concept_review: bool
    needs_speed_practice: bool
    has_systematic_error: bool
    estimated_sessions_needed: int
    recommended_action: str
    analysis_timestamp: datetime

@dataclass
class WeaknessAlert:
    """Estructura de datos para alertas de debilidades"""
    id: int
    student_id: str
    alert_type: AlertType
    severity: str
    message: str
    recommended_actions: Dict[str, Any]
    intervention_priority_score: float
    created_at: datetime
    status: str

class WeaknessAnalysisService:
    """
    Servicio principal para análisis inteligente de debilidades estudiantiles
    """
    
    def __init__(self):
        # Configuración de umbrales
        self.accuracy_thresholds = {
            'critical': 40,
            'significant': 60,
            'minor': 70
        }
        
        self.time_thresholds = {
            'slow': 120,  # 2 minutos
            'very_slow': 180  # 3 minutos
        }
        
        self.theta_thresholds = {
            'low_ability': -0.5,
            'very_low_ability': -1.0
        }
        
        # Configuración de análisis
        self.min_attempts_for_analysis = 3
        self.analysis_period_days = 90
        self.systematic_error_threshold = 0.6  # 60% del mismo error
        
    async def refresh_weakness_analysis(self, db: Session) -> Dict[str, Any]:
        """
        Ejecuta el refresh de la vista materializada de debilidades
        """
        try:
            start_time = datetime.utcnow()
            
            # Ejecutar refresh de la vista materializada
            db.execute(text("SELECT refresh_student_weaknesses_analysis()"))
            db.commit()
            
            # Obtener estadísticas del refresh
            stats = await self._get_refresh_statistics(db)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                'status': 'success',
                'duration_seconds': duration,
                'statistics': stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Weakness analysis refresh completed in {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error refreshing weakness analysis: {e}")
            raise
    
    async def _get_refresh_statistics(self, db: Session) -> Dict[str, int]:
        """Obtiene estadísticas del refresh ejecutado"""
        try:
            result = db.execute(text("""
                SELECT 
                    COUNT(*) as total_weaknesses,
                    COUNT(*) FILTER (WHERE weakness_severity = 'critical') as critical_count,
                    COUNT(*) FILTER (WHERE weakness_severity = 'significant') as significant_count,
                    COUNT(DISTINCT student_id) as affected_students,
                    COUNT(DISTINCT subject_id) as affected_subjects
                FROM vw_student_weak_topics
            """)).fetchone()
            
            return {
                'total_weaknesses': result[0] or 0,
                'critical_count': result[1] or 0,
                'significant_count': result[2] or 0,
                'affected_students': result[3] or 0,
                'affected_subjects': result[4] or 0
            }
        except Exception:
            return {}
    
    async def get_student_weaknesses(
        self, 
        db: Session, 
        student_id: str,
        severity_filter: Optional[List[WeaknessSeverity]] = None,
        limit: int = 10
    ) -> List[WeaknessAnalysis]:
        """
        Obtiene las debilidades de un estudiante específico
        """
        try:
            query = """
                SELECT * FROM vw_student_weak_topics 
                WHERE student_id = :student_id
            """
            
            params = {'student_id': student_id}
            
            if severity_filter:
                severities = [s.value for s in severity_filter]
                query += " AND weakness_severity = ANY(:severities)"
                params['severities'] = severities
            
            query += " ORDER BY intervention_priority_score DESC LIMIT :limit"
            params['limit'] = limit
            
            result = db.execute(text(query), params).fetchall()
            
            weaknesses = []
            for row in result:
                weakness = WeaknessAnalysis(
                    student_id=str(row.student_id),
                    subject_id=str(row.subject_id),
                    topic_id=str(row.topic_id),
                    subject_name=row.subject_name,
                    topic_name=row.topic_name,
                    total_attempts=row.total_attempts,
                    correct_answers=row.correct_answers,
                    accuracy_percentage=float(row.accuracy_percentage),
                    avg_time_seconds=float(row.avg_time_seconds),
                    p90_time_seconds=float(row.p90_time_seconds),
                    dominant_distractor=row.dominant_distractor,
                    weakness_severity=WeaknessSeverity(row.weakness_severity),
                    weakness_type=WeaknessType(row.weakness_type),
                    intervention_priority_score=float(row.intervention_priority_score),
                    needs_concept_review=row.needs_concept_review,
                    needs_speed_practice=row.needs_speed_practice,
                    has_systematic_error=row.has_systematic_error,
                    estimated_sessions_needed=row.estimated_sessions_needed,
                    recommended_action=row.recommended_action,
                    analysis_timestamp=row.analysis_timestamp
                )
                weaknesses.append(weakness)
            
            return weaknesses
            
        except Exception as e:
            logger.error(f"Error getting student weaknesses: {e}")
            return []
    
    async def get_critical_weaknesses_summary(self, db: Session) -> Dict[str, Any]:
        """
        Obtiene un resumen de las debilidades críticas en el sistema
        """
        try:
            # Debilidades críticas por severidad
            severity_stats = db.execute(text("""
                SELECT 
                    weakness_severity,
                    COUNT(*) as count,
                    COUNT(DISTINCT student_id) as unique_students
                FROM vw_student_weak_topics
                GROUP BY weakness_severity
                ORDER BY 
                    CASE weakness_severity 
                        WHEN 'critical' THEN 1 
                        WHEN 'significant' THEN 2 
                        WHEN 'time_inefficient' THEN 3 
                        ELSE 4 
                    END
            """)).fetchall()
            
            # Top temas con más debilidades
            topic_issues = db.execute(text("""
                SELECT 
                    subject_name,
                    topic_name,
                    COUNT(*) as weakness_count,
                    AVG(intervention_priority_score) as avg_priority,
                    COUNT(DISTINCT student_id) as affected_students
                FROM vw_student_weak_topics
                WHERE weakness_severity IN ('critical', 'significant')
                GROUP BY subject_name, topic_name
                ORDER BY COUNT(*) DESC, AVG(intervention_priority_score) DESC
                LIMIT 10
            """)).fetchall()
            
            # Estadísticas temporales
            temporal_stats = db.execute(text("""
                SELECT 
                    DATE_TRUNC('day', analysis_timestamp) as analysis_date,
                    COUNT(*) as daily_weaknesses,
                    COUNT(*) FILTER (WHERE weakness_severity = 'critical') as daily_critical
                FROM vw_student_weak_topics
                WHERE analysis_timestamp >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE_TRUNC('day', analysis_timestamp)
                ORDER BY analysis_date DESC
                LIMIT 30
            """)).fetchall()
            
            return {
                'severity_breakdown': [
                    {
                        'severity': row.weakness_severity,
                        'count': row.count,
                        'unique_students': row.unique_students
                    }
                    for row in severity_stats
                ],
                'problematic_topics': [
                    {
                        'subject_name': row.subject_name,
                        'topic_name': row.topic_name,
                        'weakness_count': row.weakness_count,
                        'avg_priority_score': float(row.avg_priority),
                        'affected_students': row.affected_students
                    }
                    for row in topic_issues
                ],
                'temporal_trends': [
                    {
                        'date': row.analysis_date.isoformat(),
                        'total_weaknesses': row.daily_weaknesses,
                        'critical_weaknesses': row.daily_critical
                    }
                    for row in temporal_stats
                ],
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting critical weaknesses summary: {e}")
            return {}
    
    async def generate_weakness_alerts(self, db: Session) -> int:
        """
        Genera alertas automáticas para debilidades críticas
        """
        try:
            # Ejecutar función de generación de alertas
            result = db.execute(text("SELECT generate_weakness_alerts()")).fetchone()
            alerts_generated = result[0] if result else 0
            
            db.commit()
            
            logger.info(f"Generated {alerts_generated} weakness alerts")
            return alerts_generated
            
        except Exception as e:
            logger.error(f"Error generating weakness alerts: {e}")
            db.rollback()
            raise
    
    async def get_active_alerts(
        self, 
        db: Session,
        student_id: Optional[str] = None,
        severity_filter: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[WeaknessAlert]:
        """
        Obtiene alertas activas de debilidades
        """
        try:
            query = """
                SELECT 
                    id, student_id, alert_type, severity, alert_message as message,
                    recommended_actions, intervention_priority_score, 
                    created_at, status
                FROM weakness_alerts 
                WHERE status = 'active' 
                  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """
            
            params = {}
            
            if student_id:
                query += " AND student_id = :student_id"
                params['student_id'] = student_id
            
            if severity_filter:
                query += " AND severity = ANY(:severities)"
                params['severities'] = severity_filter
            
            query += " ORDER BY intervention_priority_score DESC, created_at DESC LIMIT :limit"
            params['limit'] = limit
            
            result = db.execute(text(query), params).fetchall()
            
            alerts = []
            for row in result:
                alert = WeaknessAlert(
                    id=row.id,
                    student_id=str(row.student_id),
                    alert_type=AlertType(row.alert_type),
                    severity=row.severity,
                    message=row.message,
                    recommended_actions=row.recommended_actions or {},
                    intervention_priority_score=float(row.intervention_priority_score or 0),
                    created_at=row.created_at,
                    status=row.status
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    async def acknowledge_alert(
        self, 
        db: Session, 
        alert_id: int, 
        acknowledged_by: str
    ) -> bool:
        """
        Marca una alerta como reconocida
        """
        try:
            db.execute(
                text("""
                    UPDATE weakness_alerts 
                    SET status = 'acknowledged',
                        acknowledged_by = :user_id,
                        acknowledged_at = CURRENT_TIMESTAMP
                    WHERE id = :alert_id AND status = 'active'
                """),
                {'alert_id': alert_id, 'user_id': acknowledged_by}
            )
            
            affected_rows = db.rowcount
            db.commit()
            
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            db.rollback()
            return False
    
    async def analyze_performance_trends(
        self, 
        db: Session, 
        student_id: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Analiza tendencias de performance para detectar declives
        """
        try:
            # Performance por días
            daily_performance = db.execute(text("""
                SELECT 
                    DATE_TRUNC('day', created_at) as performance_date,
                    COUNT(*) as total_attempts,
                    COUNT(*) FILTER (WHERE is_correct = true) as correct_answers,
                    AVG(time_spent_seconds) as avg_time,
                    COUNT(DISTINCT question_id) as unique_questions
                FROM user_answers 
                WHERE user_id = :student_id 
                  AND created_at >= CURRENT_DATE - INTERVAL :days_back DAYS
                GROUP BY DATE_TRUNC('day', created_at)
                ORDER BY performance_date DESC
            """), {
                'student_id': student_id,
                'days_back': f"{days_back} days"
            }).fetchall()
            
            # Calcular tendencias
            daily_data = []
            accuracy_trend = []
            time_trend = []
            
            for row in daily_performance:
                accuracy = (row.correct_answers / row.total_attempts * 100) if row.total_attempts > 0 else 0
                daily_data.append({
                    'date': row.performance_date.isoformat(),
                    'accuracy_percentage': round(accuracy, 2),
                    'avg_time_seconds': float(row.avg_time or 0),
                    'total_attempts': row.total_attempts,
                    'unique_questions': row.unique_questions
                })
                accuracy_trend.append(accuracy)
                time_trend.append(float(row.avg_time or 0))
            
            # Detectar declives significativos
            decline_detected = False
            if len(accuracy_trend) >= 7:  # Mínimo una semana de datos
                recent_avg = sum(accuracy_trend[:7]) / 7
                older_avg = sum(accuracy_trend[7:14]) / min(7, len(accuracy_trend[7:14])) if len(accuracy_trend) > 7 else recent_avg
                
                if older_avg - recent_avg > 15:  # Declive de más del 15%
                    decline_detected = True
            
            # Performance por materia/tema
            subject_performance = db.execute(text("""
                SELECT 
                    s.name as subject_name,
                    t.name as topic_name,
                    COUNT(*) as attempts,
                    AVG(CASE WHEN ua.is_correct THEN 100 ELSE 0 END) as accuracy,
                    AVG(ua.time_spent_seconds) as avg_time
                FROM user_answers ua
                JOIN questions q ON ua.question_id = q.id
                LEFT JOIN subjects s ON q.subject_id = s.id
                LEFT JOIN topics t ON q.topic_id = t.id
                WHERE ua.user_id = :student_id 
                  AND ua.created_at >= CURRENT_DATE - INTERVAL :days_back DAYS
                GROUP BY s.name, t.name
                HAVING COUNT(*) >= 3
                ORDER BY accuracy ASC, avg_time DESC
            """), {
                'student_id': student_id,
                'days_back': f"{days_back} days"
            }).fetchall()
            
            return {
                'daily_performance': daily_data,
                'decline_detected': decline_detected,
                'subject_breakdown': [
                    {
                        'subject_name': row.subject_name,
                        'topic_name': row.topic_name,
                        'attempts': row.attempts,
                        'accuracy_percentage': round(float(row.accuracy), 2),
                        'avg_time_seconds': round(float(row.avg_time), 2)
                    }
                    for row in subject_performance
                ],
                'analysis_period_days': days_back,
                'total_data_points': len(daily_data),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
            return {}
    
    async def get_intervention_recommendations(
        self, 
        db: Session, 
        student_id: str
    ) -> Dict[str, Any]:
        """
        Genera recomendaciones específicas de intervención basadas en el análisis de debilidades
        """
        try:
            # Obtener debilidades del estudiante
            weaknesses = await self.get_student_weaknesses(db, student_id, limit=20)
            
            if not weaknesses:
                return {'message': 'No weaknesses detected', 'recommendations': []}
            
            # Agrupar recomendaciones por tipo
            recommendations = {
                'immediate_actions': [],
                'short_term_goals': [],
                'long_term_plan': [],
                'resource_suggestions': []
            }
            
            for weakness in weaknesses:
                # Acciones inmediatas para debilidades críticas
                if weakness.weakness_severity == WeaknessSeverity.CRITICAL:
                    recommendations['immediate_actions'].append({
                        'priority': 'high',
                        'subject': weakness.subject_name,
                        'topic': weakness.topic_name,
                        'action': weakness.recommended_action,
                        'estimated_sessions': weakness.estimated_sessions_needed,
                        'focus_area': weakness.weakness_type.value
                    })
                
                # Metas a corto plazo
                elif weakness.weakness_severity == WeaknessSeverity.SIGNIFICANT:
                    recommendations['short_term_goals'].append({
                        'priority': 'medium',
                        'subject': weakness.subject_name,
                        'topic': weakness.topic_name,
                        'target_accuracy': min(85, weakness.accuracy_percentage + 25),
                        'current_accuracy': weakness.accuracy_percentage,
                        'estimated_sessions': weakness.estimated_sessions_needed
                    })
                
                # Plan a largo plazo
                else:
                    recommendations['long_term_plan'].append({
                        'priority': 'low',
                        'subject': weakness.subject_name,
                        'topic': weakness.topic_name,
                        'maintenance_sessions': 1,
                        'review_frequency': 'weekly'
                    })
            
            # Sugerencias de recursos basadas en tipos de debilidades
            weakness_types = [w.weakness_type for w in weaknesses]
            resource_suggestions = self._generate_resource_suggestions(weakness_types)
            recommendations['resource_suggestions'] = resource_suggestions
            
            return {
                'total_weaknesses': len(weaknesses),
                'critical_count': len([w for w in weaknesses if w.weakness_severity == WeaknessSeverity.CRITICAL]),
                'recommendations': recommendations,
                'estimated_total_sessions': sum([w.estimated_sessions_needed for w in weaknesses]),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating intervention recommendations: {e}")
            return {}
    
    def _generate_resource_suggestions(self, weakness_types: List[WeaknessType]) -> List[Dict[str, str]]:
        """Genera sugerencias de recursos basadas en tipos de debilidades"""
        suggestions = []
        
        if WeaknessType.CONCEPTUAL_GAP in weakness_types:
            suggestions.append({
                'type': 'conceptual_videos',
                'description': 'Videos explicativos de conceptos fundamentales',
                'priority': 'high'
            })
        
        if WeaknessType.PROCEDURAL_SLOWNESS in weakness_types:
            suggestions.append({
                'type': 'speed_drills',
                'description': 'Ejercicios de práctica cronometrada',
                'priority': 'medium'
            })
        
        if WeaknessType.SYSTEMATIC_ERROR in weakness_types:
            suggestions.append({
                'type': 'error_analysis',
                'description': 'Análisis detallado de errores comunes',
                'priority': 'high'
            })
        
        return suggestions
    
    async def schedule_automatic_refresh(self, db: Session) -> bool:
        """
        Programa el refresh automático de la vista materializada
        """
        try:
            # Configurar refresh automático
            db.execute(text("""
                UPDATE materialized_view_refresh_log 
                SET auto_refresh_enabled = true,
                    next_scheduled_refresh = CURRENT_TIMESTAMP + (refresh_frequency_minutes || ' minutes')::interval,
                    updated_at = CURRENT_TIMESTAMP
                WHERE view_name = 'vw_student_weak_topics'
            """))
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling automatic refresh: {e}")
            db.rollback()
            return False