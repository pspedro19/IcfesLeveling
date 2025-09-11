#!/usr/bin/env python3
"""
Practice from Failures System - ICFES Leveling

Sistema de práctica basado EXCLUSIVAMENTE en preguntas falladas en diagnósticos.
Implementa tres modos:
- Recuperación: 20 preguntas priorizadas por recencia/severidad
- Repaso Completo: Todos los errores de la materia  
- Sprint: Top 10 errores críticos en 10 minutos

Regla fundamental: SOLO preguntas que el estudiante respondió incorrectamente en diagnósticos.

Author: Claude Code Assistant
Date: 2024
"""

import asyncio
import asyncpg
import pandas as pd
import numpy as np
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PracticeMode(Enum):
    """Modos de práctica disponibles"""
    RECOVERY = "recovery"      # 20 preguntas priorizadas
    FULL_REVIEW = "full_review"  # Todos los errores
    SPRINT = "sprint"          # Top 10 críticos en 10 min

class ErrorSeverity(Enum):
    """Niveles de severidad de errores"""
    CRITICAL = "critical"      # Error en pregunta fácil
    HIGH = "high"             # Tiempo alto + distractor común
    MEDIUM = "medium"         # Error estándar
    LOW = "low"               # Error en pregunta muy difícil

@dataclass
class FailedQuestion:
    """Representa una pregunta fallada en diagnóstico"""
    question_id: int
    student_id: str
    subject_id: int
    topic_id: int
    
    # Datos del fallo original
    failed_at: datetime
    selected_option: str
    correct_option: str
    time_seconds: float
    diagnostic_attempt_id: int
    
    # Metadatos de la pregunta
    statement: str
    difficulty_level: str
    irt_b: float
    competence: str
    image_url: Optional[str] = None
    
    # Estado de práctica
    practice_attempts: int = 0
    successful_attempts: int = 0
    current_streak: int = 0
    is_mastered: bool = False
    mastery_date: Optional[datetime] = None
    
    # Métricas de mejora
    best_time_seconds: Optional[float] = None
    average_time_seconds: Optional[float] = None
    last_practice_date: Optional[datetime] = None
    
    @property
    def days_since_failure(self) -> int:
        """Días desde el fallo original"""
        return (datetime.now() - self.failed_at).days
    
    @property
    def days_since_practice(self) -> int:
        """Días desde la última práctica"""
        if self.last_practice_date:
            return (datetime.now() - self.last_practice_date).days
        return self.days_since_failure
    
    @property
    def severity(self) -> ErrorSeverity:
        """Calcula severidad del error basado en múltiples factores"""
        # Error en pregunta fácil = crítico
        if self.irt_b < -1.0:
            return ErrorSeverity.CRITICAL
        
        # Tiempo muy alto = alto
        if self.time_seconds > 45:  # Más de 45 segundos
            return ErrorSeverity.HIGH
            
        # Error en pregunta muy difícil = bajo
        if self.irt_b > 1.5:
            return ErrorSeverity.LOW
            
        return ErrorSeverity.MEDIUM
    
    def calculate_priority_score(self) -> float:
        """Calcula puntaje de prioridad para selección"""
        score = 0.0
        
        # RECENCIA (40% - más peso)
        if self.days_since_failure <= 7:
            score += 0.4  # Máxima prioridad
        elif self.days_since_failure <= 30:
            score += 0.25
        else:
            score += 0.1
        
        # SEVERIDAD (30%)
        severity_weights = {
            ErrorSeverity.CRITICAL: 0.3,
            ErrorSeverity.HIGH: 0.22,
            ErrorSeverity.MEDIUM: 0.15,
            ErrorSeverity.LOW: 0.05
        }
        score += severity_weights[self.severity]
        
        # FRECUENCIA DE PRÁCTICA (30%)
        if self.practice_attempts == 0:
            score += 0.3  # Nunca practicada = máxima prioridad
        elif self.days_since_practice > 7:
            score += 0.2  # No practicada recientemente
        elif self.current_streak == 0:  # Falló en último intento
            score += 0.25
        else:
            score += 0.05  # Practicada recientemente con éxito
        
        return min(score, 1.0)


class PracticeFromFailuresSystem:
    """Sistema principal de práctica basado en fallos"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        
        # Criterios de mastery
        self.mastery_consecutive_correct = 3
        self.mastery_min_hours_between = 24
        
        # Límites de tiempo por modo
        self.mode_time_limits = {
            PracticeMode.RECOVERY: 30 * 60,      # 30 minutos
            PracticeMode.FULL_REVIEW: 60 * 60,   # 60 minutos  
            PracticeMode.SPRINT: 10 * 60         # 10 minutos
        }
        
    async def validate_practice_access(self, student_id: str, subject_id: int) -> Dict[str, Any]:
        """Valida si el estudiante puede acceder a práctica en esta materia"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Verificar si tiene diagnóstico completo
            diagnostic = await conn.fetchrow("""
                SELECT id, finished_at, total_q, correct_q
                FROM diagnostic_attempts 
                WHERE student_id = $1 AND subject_id = $2 AND finished_at IS NOT NULL
                ORDER BY finished_at DESC LIMIT 1
            """, student_id, subject_id)
            
            if not diagnostic:
                return {
                    "allowed": False,
                    "reason": "NO_DIAGNOSTIC",
                    "message": "Primero debes completar el diagnóstico de esta materia",
                    "redirect_to": f"/diagnostic/{subject_id}"
                }
            
            # Contar preguntas falladas
            failed_count = await conn.fetchval("""
                SELECT COUNT(DISTINCT q.id)
                FROM questions q
                JOIN question_responses qr ON q.id = qr.question_id
                JOIN diagnostic_attempts da ON qr.attempt_id = da.id
                WHERE da.student_id = $1 AND q.subject_id = $2 AND qr.is_correct = FALSE
            """, student_id, subject_id)
            
            if failed_count == 0:
                return {
                    "allowed": False,
                    "reason": "NO_FAILURES", 
                    "message": f"¡Perfecto! No tienes errores que practicar en esta materia",
                    "suggestion": "Intenta otra materia o realiza un nuevo diagnóstico"
                }
            
            # Contar preguntas ya dominadas
            mastered_count = await conn.fetchval("""
                SELECT COUNT(*) FROM practice_from_failures 
                WHERE student_id = $1 AND is_mastered = TRUE
            """, student_id)
            
            return {
                "allowed": True,
                "pool_size": failed_count,
                "mastered_count": mastered_count,
                "mastery_percentage": (mastered_count / failed_count) * 100 if failed_count > 0 else 0,
                "warning": "Pool limitado - las preguntas se repetirán" if failed_count < 10 else None
            }
            
        finally:
            await conn.close()
    
    async def get_failed_questions_pool(self, student_id: str, subject_id: int) -> List[FailedQuestion]:
        """Obtiene pool de preguntas falladas para el estudiante"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Query principal para obtener fallos con metadatos de práctica
            query = """
            SELECT DISTINCT
                q.id as question_id,
                q.statement,
                q.subject_id,
                q.topic_id,
                q.difficulty,
                q.irt_b,
                q.image_url,
                qr.selected_option,
                q.correct_answer,
                COALESCE(qr.time_sec, qr.time_seconds, 30) as time_seconds,
                da.id as diagnostic_attempt_id,
                da.finished_at as failed_at,
                COALESCE(t.competence, '') as competence,
                
                -- Métricas de práctica (LEFT JOIN con practice_from_failures)
                COALESCE(pff.total_practice_attempts, 0) as practice_attempts,
                COALESCE(pff.successful_attempts, 0) as successful_attempts,
                COALESCE(pff.current_streak, 0) as current_streak,
                COALESCE(pff.is_mastered, false) as is_mastered,
                pff.mastery_date,
                pff.best_time_seconds,
                pff.average_time_seconds,
                pff.last_practice_date
                
            FROM questions q
            JOIN question_responses qr ON q.id = qr.question_id
            JOIN diagnostic_attempts da ON qr.attempt_id = da.id
            LEFT JOIN topics t ON q.topic_id = t.id
            LEFT JOIN practice_from_failures pff ON (
                pff.student_id = $1 AND pff.question_id = q.id
            )
            WHERE 
                da.student_id = $1 
                AND q.subject_id = $2 
                AND qr.is_correct = FALSE
                AND da.finished_at IS NOT NULL
            ORDER BY da.finished_at DESC
            """
            
            rows = await conn.fetch(query, student_id, subject_id)
            
            failed_questions = []
            for row in rows:
                fq = FailedQuestion(
                    question_id=row['question_id'],
                    student_id=student_id,
                    subject_id=row['subject_id'],
                    topic_id=row['topic_id'],
                    failed_at=row['failed_at'],
                    selected_option=row['selected_option'] or '',
                    correct_option=row['correct_answer'] or 'A',
                    time_seconds=float(row['time_seconds']),
                    diagnostic_attempt_id=row['diagnostic_attempt_id'],
                    statement=row['statement'],
                    difficulty_level=row['difficulty'] or 'mid',
                    irt_b=float(row['irt_b']) if row['irt_b'] else 0.0,
                    competence=row['competence'],
                    image_url=row['image_url'],
                    practice_attempts=row['practice_attempts'],
                    successful_attempts=row['successful_attempts'],
                    current_streak=row['current_streak'],
                    is_mastered=row['is_mastered'],
                    mastery_date=row['mastery_date'],
                    best_time_seconds=row['best_time_seconds'],
                    average_time_seconds=row['average_time_seconds'],
                    last_practice_date=row['last_practice_date']
                )
                failed_questions.append(fq)
            
            return failed_questions
            
        finally:
            await conn.close()
    
    def select_questions_for_mode(self, failed_questions: List[FailedQuestion], 
                                 mode: PracticeMode) -> List[FailedQuestion]:
        """Selecciona preguntas según el modo de práctica"""
        # Filtrar preguntas no dominadas
        available = [fq for fq in failed_questions if not fq.is_mastered]
        
        if not available:
            logger.warning("No hay preguntas no-dominadas disponibles")
            return []
        
        # Calcular puntajes de prioridad
        for fq in available:
            fq._priority_score = fq.calculate_priority_score()
        
        # Ordenar por prioridad
        available.sort(key=lambda x: x._priority_score, reverse=True)
        
        if mode == PracticeMode.RECOVERY:
            # Top 20 preguntas con mayor prioridad
            return available[:20]
            
        elif mode == PracticeMode.SPRINT:
            # Top 10 más críticas
            critical_and_high = [
                fq for fq in available 
                if fq.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]
            ]
            return critical_and_high[:10] if critical_and_high else available[:10]
            
        elif mode == PracticeMode.FULL_REVIEW:
            # Todas las preguntas no dominadas
            return available
        
        return available
    
    async def start_practice_session(self, student_id: str, subject_id: int, 
                                   mode: PracticeMode) -> Dict[str, Any]:
        """Inicia nueva sesión de práctica"""
        
        # Validar acceso
        validation = await self.validate_practice_access(student_id, subject_id)
        if not validation["allowed"]:
            return validation
        
        # Obtener pool de fallos
        failed_questions = await self.get_failed_questions_pool(student_id, subject_id)
        
        # Seleccionar preguntas para este modo
        selected_questions = self.select_questions_for_mode(failed_questions, mode)
        
        if not selected_questions:
            return {
                "success": False,
                "message": "No hay preguntas disponibles para este modo",
                "suggestion": "Todas las preguntas están dominadas o intenta otro modo"
            }
        
        # Crear sesión
        session_data = {
            "session_id": str(uuid.uuid4()),
            "student_id": student_id,
            "subject_id": subject_id,
            "mode": mode.value,
            "started_at": datetime.now().isoformat(),
            "questions": [fq.question_id for fq in selected_questions],
            "total_questions": len(selected_questions),
            "time_limit_seconds": self.mode_time_limits[mode],
            "current_index": 0,
            "responses": []
        }
        
        logger.info(f"Sesión de práctica iniciada: {session_data['session_id']}")
        logger.info(f"Modo: {mode.value}, Preguntas: {len(selected_questions)}")
        
        return {
            "success": True,
            "session": session_data,
            "first_question": asdict(selected_questions[0]),
            "pool_stats": {
                "total_available": len(failed_questions),
                "selected": len(selected_questions),
                "mastered": validation["mastered_count"]
            }
        }
    
    async def process_practice_response(self, session_id: str, question_id: int, 
                                      correct: bool, time_seconds: float, 
                                      selected_option: str) -> Dict[str, Any]:
        """Procesa respuesta de práctica y actualiza métricas"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Registrar la respuesta de práctica
            await conn.execute("""
                INSERT INTO practice_responses (
                    id, session_id, question_id, is_correct, time_seconds, 
                    selected_option, timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, str(uuid.uuid4()), session_id, question_id, correct, 
                time_seconds, selected_option, datetime.now())
            
            # Actualizar métricas en practice_from_failures
            student_id = await conn.fetchval("""
                SELECT student_id FROM practice_sessions WHERE id = $1
            """, session_id)
            
            if not student_id:
                # Manejar caso donde no existe la tabla practice_sessions
                # Usar información del contexto de la sesión
                pass
            
            # Upsert en practice_from_failures 
            await self._update_practice_metrics(conn, student_id, question_id, correct, time_seconds)
            
            # Verificar si alcanzó mastery
            is_mastered = await self._check_mastery(conn, student_id, question_id)
            
            response_data = {
                "correct": correct,
                "time_seconds": time_seconds,
                "is_mastered": is_mastered,
                "improvement_shown": await self._calculate_improvement(conn, student_id, question_id)
            }
            
            return response_data
            
        finally:
            await conn.close()
    
    async def _update_practice_metrics(self, conn, student_id: str, question_id: int, 
                                     correct: bool, time_seconds: float):
        """Actualiza métricas de práctica para una pregunta"""
        
        # Upsert con conflicto en (student_id, question_id)
        await conn.execute("""
            INSERT INTO practice_from_failures (
                id, student_id, question_id, diagnostic_attempt_id,
                first_practice_date, last_practice_date, 
                total_practice_attempts, successful_attempts,
                current_streak, best_time_seconds, average_time_seconds
            ) VALUES (
                $1, $2, $3, 
                (SELECT da.id FROM diagnostic_attempts da 
                 JOIN question_responses qr ON da.id = qr.attempt_id
                 WHERE da.student_id = $2 AND qr.question_id = $3 AND qr.is_correct = FALSE
                 ORDER BY da.finished_at DESC LIMIT 1),
                NOW(), NOW(), 1, $4, $5, $6, $6
            )
            ON CONFLICT (student_id, question_id) DO UPDATE SET
                last_practice_date = NOW(),
                total_practice_attempts = practice_from_failures.total_practice_attempts + 1,
                successful_attempts = practice_from_failures.successful_attempts + $4,
                current_streak = CASE WHEN $4 THEN practice_from_failures.current_streak + 1 ELSE 0 END,
                best_time_seconds = CASE 
                    WHEN $6 < COALESCE(practice_from_failures.best_time_seconds, 999) THEN $6
                    ELSE COALESCE(practice_from_failures.best_time_seconds, $6)
                END,
                average_time_seconds = (
                    COALESCE(practice_from_failures.average_time_seconds, 0) * 
                    practice_from_failures.total_practice_attempts + $6
                ) / (practice_from_failures.total_practice_attempts + 1)
        """, str(uuid.uuid4()), student_id, question_id, 
             1 if correct else 0, 1 if correct else 0, time_seconds)
    
    async def _check_mastery(self, conn, student_id: str, question_id: int) -> bool:
        """Verifica si una pregunta ha alcanzado mastery"""
        
        practice_data = await conn.fetchrow("""
            SELECT current_streak, last_practice_date, average_time_seconds,
                   is_mastered
            FROM practice_from_failures 
            WHERE student_id = $1 AND question_id = $2
        """, student_id, question_id)
        
        if not practice_data or practice_data['is_mastered']:
            return practice_data['is_mastered'] if practice_data else False
        
        # Criterios de mastery
        meets_streak = practice_data['current_streak'] >= self.mastery_consecutive_correct
        meets_time = True  # TODO: Implementar criterio de tiempo si es necesario
        
        if meets_streak and meets_time:
            # Marcar como dominada
            await conn.execute("""
                UPDATE practice_from_failures 
                SET is_mastered = TRUE, mastery_date = NOW()
                WHERE student_id = $1 AND question_id = $2
            """, student_id, question_id)
            
            logger.info(f"Pregunta {question_id} dominada por estudiante {student_id}")
            return True
        
        return False
    
    async def _calculate_improvement(self, conn, student_id: str, question_id: int) -> Dict[str, Any]:
        """Calcula métricas de mejora para la pregunta"""
        
        metrics = await conn.fetchrow("""
            SELECT 
                total_practice_attempts,
                successful_attempts,
                best_time_seconds,
                average_time_seconds,
                current_streak
            FROM practice_from_failures
            WHERE student_id = $1 AND question_id = $2
        """, student_id, question_id)
        
        if not metrics:
            return {}
        
        # Obtener tiempo original del diagnóstico
        original_time = await conn.fetchval("""
            SELECT COALESCE(qr.time_sec, qr.time_seconds, 30)
            FROM question_responses qr
            JOIN diagnostic_attempts da ON qr.attempt_id = da.id
            WHERE da.student_id = $1 AND qr.question_id = $2 AND qr.is_correct = FALSE
            ORDER BY da.finished_at DESC LIMIT 1
        """, student_id, question_id)
        
        improvement_data = {
            "accuracy_improvement": (metrics['successful_attempts'] / max(metrics['total_practice_attempts'], 1)) * 100,
            "time_improvement_percent": 0,
            "current_streak": metrics['current_streak']
        }
        
        if original_time and metrics['best_time_seconds']:
            time_improvement = ((original_time - metrics['best_time_seconds']) / original_time) * 100
            improvement_data["time_improvement_percent"] = max(0, time_improvement)
        
        return improvement_data
    
    async def generate_practice_report(self, student_id: str, subject_id: int) -> Dict[str, Any]:
        """Genera reporte de progreso en práctica para una materia"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Estadísticas generales
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_failed_questions,
                    COUNT(*) FILTER (WHERE is_mastered) as mastered_questions,
                    COUNT(*) FILTER (WHERE total_practice_attempts > 0) as practiced_questions,
                    AVG(CASE WHEN total_practice_attempts > 0 
                        THEN successful_attempts::float / total_practice_attempts 
                        ELSE NULL END) as avg_practice_accuracy,
                    AVG(CASE WHEN best_time_seconds IS NOT NULL AND original_time_seconds IS NOT NULL
                        THEN ((original_time_seconds - best_time_seconds) / original_time_seconds) * 100
                        ELSE NULL END) as avg_time_improvement
                FROM practice_from_failures pff
                WHERE pff.student_id = $1 
                AND EXISTS (
                    SELECT 1 FROM questions q 
                    WHERE q.id = pff.question_id AND q.subject_id = $2
                )
            """, student_id, subject_id)
            
            total_failed = stats['total_failed_questions'] or 0
            mastered = stats['mastered_questions'] or 0
            
            # Distribución por severidad
            severity_stats = await conn.fetch("""
                SELECT 
                    CASE 
                        WHEN q.irt_b < -1.0 THEN 'critical'
                        WHEN qr.time_seconds > 45 THEN 'high'  
                        WHEN q.irt_b > 1.5 THEN 'low'
                        ELSE 'medium'
                    END as severity,
                    COUNT(*) as count,
                    COUNT(*) FILTER (WHERE pff.is_mastered) as mastered_count
                FROM practice_from_failures pff
                JOIN questions q ON pff.question_id = q.id
                JOIN question_responses qr ON (
                    qr.question_id = q.id AND qr.attempt_id = pff.diagnostic_attempt_id
                )
                WHERE pff.student_id = $1 AND q.subject_id = $2
                GROUP BY severity
            """, student_id, subject_id)
            
            report = {
                "student_id": student_id,
                "subject_id": subject_id,
                "generated_at": datetime.now().isoformat(),
                
                "summary": {
                    "total_failed_questions": total_failed,
                    "mastered_questions": mastered,
                    "in_progress": total_failed - mastered,
                    "mastery_percentage": (mastered / total_failed) * 100 if total_failed > 0 else 0,
                    "practiced_questions": stats['practiced_questions'] or 0,
                    "avg_practice_accuracy": float(stats['avg_practice_accuracy'] or 0) * 100,
                    "avg_time_improvement": float(stats['avg_time_improvement'] or 0)
                },
                
                "by_severity": {
                    row['severity']: {
                        "total": row['count'],
                        "mastered": row['mastered_count'],
                        "mastery_rate": (row['mastered_count'] / row['count']) * 100 if row['count'] > 0 else 0
                    }
                    for row in severity_stats
                },
                
                "recommendations": self._generate_practice_recommendations(stats, severity_stats)
            }
            
            return report
            
        finally:
            await conn.close()
    
    def _generate_practice_recommendations(self, stats: Dict, severity_stats: List) -> List[str]:
        """Genera recomendaciones personalizadas de práctica"""
        recommendations = []
        
        mastery_pct = (stats['mastered_questions'] or 0) / max(stats['total_failed_questions'] or 1, 1) * 100
        
        if mastery_pct < 25:
            recommendations.append("🎯 Prioriza el Modo Recuperación para mejorar errores recientes")
        elif mastery_pct < 60:
            recommendations.append("🚀 Combina Modo Sprint con Recuperación para acelerar el progreso")
        else:
            recommendations.append("🏆 ¡Excelente progreso! Usa Repaso Completo para consolidar")
        
        # Recomendaciones por severidad
        critical_data = next((s for s in severity_stats if s['severity'] == 'critical'), None)
        if critical_data and critical_data['count'] > critical_data['mastered_count']:
            recommendations.append("⚠️ Tienes errores críticos pendientes - priorízalos primero")
        
        if stats['avg_time_improvement'] and stats['avg_time_improvement'] < 10:
            recommendations.append("⏱️ Trabaja en mejorar la velocidad de respuesta")
        
        return recommendations


# Ejemplo de uso y testing
async def main():
    """Función principal para testing del sistema"""
    database_url = "postgresql://gameplay:gameplay123@localhost:5433/gameplay_db"
    
    practice_system = PracticeFromFailuresSystem(database_url)
    
    # Test de validación de acceso
    student_id = "test_student_001"
    subject_id = 1
    
    try:
        validation = await practice_system.validate_practice_access(student_id, subject_id)
        print("Validación de acceso:", json.dumps(validation, indent=2))
        
        if validation.get("allowed"):
            # Test de inicio de sesión
            session = await practice_system.start_practice_session(
                student_id, subject_id, PracticeMode.RECOVERY
            )
            print("Sesión iniciada:", json.dumps(session, indent=2, default=str))
            
            # Test de reporte de progreso
            report = await practice_system.generate_practice_report(student_id, subject_id)
            print("Reporte de progreso:", json.dumps(report, indent=2, default=str))
        
    except Exception as e:
        logger.error(f"Error en testing: {e}")


if __name__ == "__main__":
    asyncio.run(main())