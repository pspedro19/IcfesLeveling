#!/usr/bin/env python3
"""
Recommendation Engine with Embeddings - ICFES Leveling

Motor de recomendaciones que cruza:
- Preguntas falladas del estudiante
- Catálogo de videos de YouTube 
- Embeddings semánticos con pgvector
- Reglas de negocio y popularidad

Genera planes de estudio YAML mensuales con:
- Análisis de debilidades por tema/competencia
- Recomendaciones priorizadas (videos, práctica, lecturas)
- Calendario de estudio adaptativo
- Métricas de seguimiento

Author: Claude Code Assistant
Date: 2024
"""

import asyncio
import asyncpg
import pandas as pd
import numpy as np
import logging
import json
import yaml
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import openai
import hashlib
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Tipos de contenido educativo"""
    VIDEO = "video"
    PRACTICE_SET = "practice_set"  
    READING = "reading"
    INTERACTIVE = "interactive"

class Priority(Enum):
    """Niveles de prioridad"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class WeaknessProfile:
    """Perfil de debilidad de un estudiante en un tema específico"""
    student_id: str
    subject_id: int
    topic_id: int
    subject_name: str
    topic_name: str
    competence: str
    
    # Métricas de debilidad
    accuracy: float  # 0.0 - 1.0
    n_responses: int
    avg_time_seconds: float
    p90_time_seconds: float
    
    # Análisis de errores
    dominant_distractor: str
    error_pattern: str
    theta_estimate: float
    
    # Metadatos
    last_failed_at: datetime
    days_since_failure: int
    
    @property
    def severity_score(self) -> float:
        """Calcula severidad de la debilidad (0-1)"""
        score = 0.0
        
        # Precisión baja = alta severidad
        accuracy_weight = (1.0 - self.accuracy) * 0.4
        
        # Tiempo alto = alta severidad  
        time_weight = min(self.avg_time_seconds / 60.0, 1.0) * 0.3
        
        # Theta bajo = alta severidad
        theta_weight = max(0, (-self.theta_estimate + 1.0) / 3.0) * 0.2
        
        # Recencia = alta severidad
        recency_weight = max(0, (30 - self.days_since_failure) / 30.0) * 0.1
        
        return min(accuracy_weight + time_weight + theta_weight + recency_weight, 1.0)
    
    def generate_embedding_text(self) -> str:
        """Genera texto descriptivo para embedding de debilidad"""
        return (f"{self.subject_name}:{self.topic_name} | "
                f"competencia:{self.competence} | "
                f"error:{self.dominant_distractor} | "
                f"theta:{self.theta_estimate:.2f} | "
                f"accuracy:{self.accuracy:.2f} | "
                f"pattern:{self.error_pattern}")

@dataclass
class VideoContent:
    """Representa un video educativo del catálogo"""
    video_id: int
    youtube_id: str
    url: str
    title: str
    description: str
    channel: str
    
    # Metadatos educativos
    subject_id: int
    topic_id: Optional[int]
    competence: str
    component: str
    language: str
    duration_sec: int
    
    # Parámetros IRT del contenido
    irt_b: Optional[float]  # Nivel de dificultad del contenido
    cognitive_level: str    # bloom_level
    
    # Métricas de popularidad
    ctr_7d: float = 0.0           # Click-through rate 7 días
    completion_rate_7d: float = 0.0  # Tasa de finalización 7 días  
    avg_watch_sec_7d: int = 0     # Tiempo promedio de visualización
    
    # Embedding semántico
    embedding: Optional[List[float]] = None
    
    def calculate_engagement_score(self) -> float:
        """Calcula puntaje de engagement normalizado (0-1)"""
        # Normalizar métricas (asumiendo rangos típicos)
        ctr_norm = min(self.ctr_7d / 0.15, 1.0)  # CTR promedio ~10%, excelente >15%
        completion_norm = self.completion_rate_7d  # Ya normalizada 0-1
        watch_ratio = min((self.avg_watch_sec_7d / self.duration_sec), 1.0) if self.duration_sec > 0 else 0.0
        
        # Promedio ponderado
        return (ctr_norm * 0.3 + completion_norm * 0.4 + watch_ratio * 0.3)

@dataclass  
class ContentRecommendation:
    """Recomendación de contenido específica"""
    content_type: ContentType
    content_id: Union[int, str]
    title: str
    url: str
    priority: Priority
    
    # Scoring y matching
    semantic_similarity: float
    difficulty_match: float
    popularity_score: float  
    total_score: float
    
    # Metadatos específicos
    duration_minutes: Optional[int] = None
    estimated_effort_hours: Optional[float] = None
    prerequisite_topics: List[str] = None
    addresses_weaknesses: List[str] = None
    
    def __post_init__(self):
        if self.prerequisite_topics is None:
            self.prerequisite_topics = []
        if self.addresses_weaknesses is None:
            self.addresses_weaknesses = []

@dataclass
class StudyPlan:
    """Plan de estudio mensual generado"""
    student_id: str
    month: str  # YYYY-MM
    generated_at: datetime
    
    # Perfil del estudiante
    theta_global: float
    theta_ci: Tuple[float, float]  # Intervalo de confianza 95%
    subjects_evaluated: List[str]
    
    # Análisis de fortalezas/debilidades
    strengths: List[Dict[str, Any]]
    weaknesses: List[WeaknessProfile]
    
    # Recomendaciones priorizadas
    priority_high: List[ContentRecommendation]
    priority_medium: List[ContentRecommendation]
    priority_low: List[ContentRecommendation]
    
    # Calendario y metas
    weekly_goals: List[Dict[str, Any]]
    estimated_hours_per_week: float
    study_schedule: Dict[str, List[str]]  # día -> actividades
    
    # Parámetros adaptativos
    next_diagnostic_date: Optional[str]
    difficulty_adjustment: float
    content_filters: Dict[str, Any]


class RecommendationEngine:
    """Motor principal de recomendaciones con embeddings"""
    
    def __init__(self, database_url: str, openai_api_key: Optional[str] = None):
        self.database_url = database_url
        self.openai_client = openai.OpenAI(api_key=openai_api_key) if openai_api_key else None
        
        # Parámetros de scoring
        self.scoring_weights = {
            'semantic_similarity': 0.50,
            'difficulty_match': 0.20,
            'ctr_7d': 0.15,
            'completion_rate_7d': 0.15
        }
        
        # Umbrales
        self.min_semantic_similarity = 0.75
        self.max_recommendations_per_priority = 5
        
        # Cache de embeddings
        self._embedding_cache = {}
        
    async def get_student_weakness_profile(self, student_id: str, 
                                         subject_id: Optional[int] = None) -> List[WeaknessProfile]:
        """Obtiene perfil completo de debilidades del estudiante"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Query para obtener debilidades usando vista materializada optimizada
            base_query = """
            SELECT 
                w.student_id,
                w.subject_id, 
                w.topic_id,
                s.name as subject_name,
                t.name as topic_name,
                COALESCE(t.competence, '') as competence,
                w.accuracy,
                w.n_responses,
                w.p90_time,
                w.dominant_distractor,
                
                -- Métricas adicionales desde diagnostic_attempts
                COALESCE(da_latest.theta, 0.0) as theta_estimate,
                GREATEST(da_latest.finished_at) as last_failed_at,
                EXTRACT(DAYS FROM NOW() - GREATEST(da_latest.finished_at))::int as days_since_failure
                
            FROM vw_student_weak_topics w
            JOIN subjects s ON w.subject_id = s.id  
            JOIN topics t ON w.topic_id = t.id
            LEFT JOIN (
                SELECT 
                    student_id, subject_id, 
                    MAX(theta) as theta, 
                    MAX(finished_at) as finished_at
                FROM diagnostic_attempts 
                WHERE finished_at IS NOT NULL
                GROUP BY student_id, subject_id
            ) da_latest ON w.student_id = da_latest.student_id AND w.subject_id = da_latest.subject_id
            
            WHERE w.student_id = $1 AND w.accuracy < 0.6
            """
            
            params = [student_id]
            if subject_id:
                base_query += " AND w.subject_id = $2"
                params.append(subject_id)
            
            base_query += " ORDER BY w.accuracy ASC, w.n_responses DESC"
            
            rows = await conn.fetch(base_query, *params)
            
            weaknesses = []
            for row in rows:
                # Inferir patrón de error
                error_pattern = self._infer_error_pattern(
                    row['dominant_distractor'], 
                    row['accuracy'], 
                    row['p90_time']
                )
                
                weakness = WeaknessProfile(
                    student_id=row['student_id'],
                    subject_id=row['subject_id'],
                    topic_id=row['topic_id'],
                    subject_name=row['subject_name'],
                    topic_name=row['topic_name'],
                    competence=row['competence'],
                    accuracy=float(row['accuracy']),
                    n_responses=row['n_responses'],
                    avg_time_seconds=float(row['p90_time']) * 0.8,  # Estimación del promedio
                    p90_time_seconds=float(row['p90_time']),
                    dominant_distractor=row['dominant_distractor'] or '',
                    error_pattern=error_pattern,
                    theta_estimate=float(row['theta_estimate']),
                    last_failed_at=row['last_failed_at'],
                    days_since_failure=row['days_since_failure']
                )
                weaknesses.append(weakness)
            
            return weaknesses
            
        finally:
            await conn.close()
    
    def _infer_error_pattern(self, distractor: str, accuracy: float, p90_time: float) -> str:
        """Infiere patrón de error basado en datos observados"""
        patterns = []
        
        if accuracy < 0.3:
            patterns.append("conceptual_gap")
        elif accuracy < 0.5:
            patterns.append("procedural_error")
        else:
            patterns.append("careless_mistake")
            
        if p90_time > 60:
            patterns.append("time_pressure")
        elif p90_time < 15:
            patterns.append("rushed_response")
            
        if distractor and len(distractor) == 1:
            patterns.append(f"distractor_{distractor.lower()}")
            
        return "|".join(patterns)
    
    async def get_video_catalog(self, subject_ids: List[int]) -> List[VideoContent]:
        """Obtiene catálogo de videos filtrado por materias"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            query = """
            SELECT 
                yc.video_id,
                yc.youtube_id,
                yc.url,
                yc.title,
                yc.description,
                yc.channel,
                yc.subject_id,
                yc.topic_id,
                COALESCE(yc.competence, '') as competence,
                COALESCE(yc.component, '') as component,
                yc.language,
                yc.duration_sec,
                yc.irt_b,
                
                -- Métricas de engagement (con fallback a 0)
                COALESCE(vs.ctr_7d, 0.0) as ctr_7d,
                COALESCE(vs.completion_rate_7d, 0.0) as completion_rate_7d,
                COALESCE(vs.avg_watch_sec_7d, 0) as avg_watch_sec_7d
                
            FROM youtube_catalog yc
            LEFT JOIN video_stats vs ON yc.video_id = vs.video_id
            WHERE yc.subject_id = ANY($1::int[])
                AND yc.language IN ('es', 'spanish', 'español')
                AND yc.duration_sec BETWEEN 120 AND 1800  -- 2-30 minutos
            ORDER BY 
                COALESCE(vs.ctr_7d, 0.0) DESC,
                COALESCE(vs.completion_rate_7d, 0.0) DESC
            """
            
            rows = await conn.fetch(query, subject_ids)
            
            videos = []
            for row in rows:
                video = VideoContent(
                    video_id=row['video_id'],
                    youtube_id=row['youtube_id'],
                    url=row['url'],
                    title=row['title'],
                    description=row['description'] or '',
                    channel=row['channel'] or '',
                    subject_id=row['subject_id'],
                    topic_id=row['topic_id'],
                    competence=row['competence'],
                    component=row['component'],
                    language=row['language'],
                    duration_sec=row['duration_sec'],
                    irt_b=row['irt_b'],
                    ctr_7d=float(row['ctr_7d']),
                    completion_rate_7d=float(row['completion_rate_7d']),
                    avg_watch_sec_7d=row['avg_watch_sec_7d']
                )
                videos.append(video)
            
            return videos
            
        finally:
            await conn.close()
    
    async def get_embedding(self, text: str, content_type: str = "weakness") -> List[float]:
        """Obtiene embedding de texto usando OpenAI o cache"""
        
        # Generar clave de cache
        cache_key = hashlib.md5(f"{content_type}:{text}".encode()).hexdigest()
        
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        if not self.openai_client:
            logger.warning("OpenAI client no disponible, usando embedding dummy")
            # Embedding dummy para desarrollo
            return np.random.random(1536).tolist()
        
        try:
            response = await self.openai_client.embeddings.acreate(
                model="text-embedding-ada-002",
                input=text
            )
            embedding = response.data[0].embedding
            
            # Guardar en cache
            self._embedding_cache[cache_key] = embedding
            return embedding
            
        except Exception as e:
            logger.error(f"Error obteniendo embedding: {e}")
            return np.random.random(1536).tolist()  # Fallback
    
    def calculate_semantic_similarity(self, embedding1: List[float], 
                                    embedding2: List[float]) -> float:
        """Calcula similitud coseno entre dos embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Similitud coseno
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            similarity = dot_product / (norm1 * norm2)
            return float(max(0.0, similarity))  # Asegurar no negativo
            
        except Exception as e:
            logger.error(f"Error calculando similitud: {e}")
            return 0.0
    
    def calculate_difficulty_match(self, theta_student: float, 
                                 content_irt_b: Optional[float]) -> float:
        """Calcula qué tan bien coincide la dificultad del contenido con el nivel del estudiante"""
        if content_irt_b is None:
            return 0.5  # Neutral si no hay información
        
        # Distancia absoluta entre theta y dificultad del contenido
        distance = abs(theta_student - content_irt_b)
        
        # Convertir a similitud (0 distancia = 1.0 similitud)
        # Penalizar distancias > 2.0 fuertemente
        if distance > 2.0:
            return 0.1
        else:
            return max(0.1, 1.0 - (distance / 2.0))
    
    async def generate_content_recommendations(self, weakness: WeaknessProfile, 
                                            video_catalog: List[VideoContent]) -> List[ContentRecommendation]:
        """Genera recomendaciones de contenido para una debilidad específica"""
        
        # Obtener embedding de la debilidad
        weakness_text = weakness.generate_embedding_text()
        weakness_embedding = await self.get_embedding(weakness_text, "weakness")
        
        recommendations = []
        
        for video in video_catalog:
            # Filtros básicos
            if video.subject_id != weakness.subject_id:
                continue
                
            # Obtener/calcular embedding del video
            video_text = f"{video.title} {video.description} {video.competence} {video.component}"
            video_embedding = await self.get_embedding(video_text, "video")
            
            # Calcular componentes del score
            semantic_sim = self.calculate_semantic_similarity(weakness_embedding, video_embedding)
            
            # Filtro de umbral mínimo
            if semantic_sim < self.min_semantic_similarity:
                continue
            
            difficulty_match = self.calculate_difficulty_match(weakness.theta_estimate, video.irt_b)
            engagement_score = video.calculate_engagement_score()
            
            # Score total ponderado
            total_score = (
                semantic_sim * self.scoring_weights['semantic_similarity'] +
                difficulty_match * self.scoring_weights['difficulty_match'] +
                video.ctr_7d * self.scoring_weights['ctr_7d'] +  
                video.completion_rate_7d * self.scoring_weights['completion_rate_7d']
            )
            
            # Determinar prioridad basada en severidad y score
            if weakness.severity_score > 0.7 and total_score > 0.8:
                priority = Priority.HIGH
            elif total_score > 0.6:
                priority = Priority.MEDIUM  
            else:
                priority = Priority.LOW
            
            recommendation = ContentRecommendation(
                content_type=ContentType.VIDEO,
                content_id=video.video_id,
                title=video.title,
                url=video.url,
                priority=priority,
                semantic_similarity=semantic_sim,
                difficulty_match=difficulty_match,
                popularity_score=engagement_score,
                total_score=total_score,
                duration_minutes=video.duration_sec // 60,
                estimated_effort_hours=video.duration_sec / 3600.0,
                addresses_weaknesses=[f"{weakness.subject_name}:{weakness.topic_name}"]
            )
            
            recommendations.append(recommendation)
        
        # Ordenar por score total y retornar top recomendaciones
        recommendations.sort(key=lambda x: x.total_score, reverse=True)
        return recommendations
    
    def generate_study_calendar(self, recommendations: List[ContentRecommendation], 
                              estimated_hours_per_week: float = 8.0) -> Dict[str, List[str]]:
        """Genera calendario de estudio semanal"""
        
        # Distribuir contenido en 7 días
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        schedule = {day: [] for day in days}
        
        # Separar por prioridad
        high_priority = [r for r in recommendations if r.priority == Priority.HIGH]
        medium_priority = [r for r in recommendations if r.priority == Priority.MEDIUM]
        low_priority = [r for r in recommendations if r.priority == Priority.LOW]
        
        current_day = 0
        hours_assigned = 0.0
        
        # Asignar contenido de alta prioridad primero
        for rec in high_priority:
            if hours_assigned >= estimated_hours_per_week:
                break
                
            day = days[current_day % 7]
            schedule[day].append({
                'type': rec.content_type.value,
                'title': rec.title,
                'url': rec.url,
                'duration_minutes': rec.duration_minutes,
                'priority': rec.priority.value
            })
            
            hours_assigned += rec.estimated_effort_hours or 0.5
            current_day += 1
        
        # Llenar con contenido de prioridad media/baja
        for rec_list in [medium_priority, low_priority]:
            for rec in rec_list:
                if hours_assigned >= estimated_hours_per_week:
                    break
                    
                day = days[current_day % 7]
                if len(schedule[day]) < 2:  # Max 2 actividades por día
                    schedule[day].append({
                        'type': rec.content_type.value,
                        'title': rec.title,
                        'url': rec.url,
                        'duration_minutes': rec.duration_minutes,
                        'priority': rec.priority.value
                    })
                    
                    hours_assigned += rec.estimated_effort_hours or 0.5
                    current_day += 1
        
        return schedule
    
    async def generate_monthly_study_plan(self, student_id: str, 
                                        month: str = None) -> StudyPlan:
        """Genera plan de estudio mensual completo"""
        
        if not month:
            month = datetime.now().strftime("%Y-%m")
        
        logger.info(f"Generando plan de estudio para {student_id} - {month}")
        
        # 1. Obtener perfil de debilidades
        weaknesses = await self.get_student_weakness_profile(student_id)
        
        if not weaknesses:
            logger.warning(f"No se encontraron debilidades para {student_id}")
            return self._generate_empty_plan(student_id, month)
        
        # 2. Obtener catálogo de videos para las materias relevantes
        subject_ids = list(set(w.subject_id for w in weaknesses))
        video_catalog = await self.get_video_catalog(subject_ids)
        
        logger.info(f"Catálogo cargado: {len(video_catalog)} videos para materias {subject_ids}")
        
        # 3. Generar recomendaciones para cada debilidad
        all_recommendations = []
        for weakness in weaknesses[:10]:  # Top 10 debilidades más severas
            recs = await self.generate_content_recommendations(weakness, video_catalog)
            all_recommendations.extend(recs[:3])  # Top 3 por debilidad
        
        # 4. Filtrar y priorizar recomendaciones finales
        final_recs = self._prioritize_recommendations(all_recommendations)
        
        # 5. Generar calendario de estudio
        study_schedule = self.generate_study_calendar(final_recs['all'])
        
        # 6. Calcular métricas del estudiante
        theta_global = np.mean([w.theta_estimate for w in weaknesses])
        theta_std = np.std([w.theta_estimate for w in weaknesses])
        theta_ci = (theta_global - 1.96 * theta_std, theta_global + 1.96 * theta_std)
        
        # 7. Generar plan completo
        study_plan = StudyPlan(
            student_id=student_id,
            month=month,
            generated_at=datetime.now(),
            theta_global=theta_global,
            theta_ci=theta_ci,
            subjects_evaluated=[w.subject_name for w in weaknesses],
            strengths=[],  # TODO: Implementar análisis de fortalezas
            weaknesses=weaknesses,
            priority_high=final_recs['high'],
            priority_medium=final_recs['medium'], 
            priority_low=final_recs['low'],
            weekly_goals=self._generate_weekly_goals(final_recs['all']),
            estimated_hours_per_week=8.0,
            study_schedule=study_schedule,
            next_diagnostic_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            difficulty_adjustment=0.0,
            content_filters={}
        )
        
        logger.info(f"Plan generado exitosamente: {len(final_recs['all'])} recomendaciones")
        return study_plan
    
    def _prioritize_recommendations(self, recommendations: List[ContentRecommendation]) -> Dict[str, List[ContentRecommendation]]:
        """Prioriza y filtra recomendaciones finales"""
        
        # Remover duplicados por content_id
        unique_recs = {}
        for rec in recommendations:
            key = f"{rec.content_type.value}_{rec.content_id}"
            if key not in unique_recs or rec.total_score > unique_recs[key].total_score:
                unique_recs[key] = rec
        
        all_recs = list(unique_recs.values())
        
        # Ordenar por score total
        all_recs.sort(key=lambda x: x.total_score, reverse=True)
        
        # Separar por prioridad
        high = [r for r in all_recs if r.priority == Priority.HIGH][:self.max_recommendations_per_priority]
        medium = [r for r in all_recs if r.priority == Priority.MEDIUM][:self.max_recommendations_per_priority]
        low = [r for r in all_recs if r.priority == Priority.LOW][:self.max_recommendations_per_priority]
        
        return {
            'high': high,
            'medium': medium,
            'low': low,
            'all': high + medium + low
        }
    
    def _generate_weekly_goals(self, recommendations: List[ContentRecommendation]) -> List[Dict[str, Any]]:
        """Genera metas semanales basadas en recomendaciones"""
        
        goals = []
        
        # Semana 1: Contenido de alta prioridad
        week1_content = [r for r in recommendations if r.priority == Priority.HIGH]
        if week1_content:
            goals.append({
                'week': 1,
                'focus': 'Abordar debilidades críticas',
                'content_items': len(week1_content),
                'estimated_hours': sum(r.estimated_effort_hours or 0.5 for r in week1_content),
                'success_criteria': 'Completar al menos 80% del contenido asignado'
            })
        
        # Semana 2-3: Contenido de prioridad media
        medium_content = [r for r in recommendations if r.priority == Priority.MEDIUM]
        for week in [2, 3]:
            week_content = medium_content[(week-2)*3:(week-1)*3]  # 3 items por semana
            if week_content:
                goals.append({
                    'week': week,
                    'focus': 'Reforzar conceptos fundamentales',
                    'content_items': len(week_content),
                    'estimated_hours': sum(r.estimated_effort_hours or 0.5 for r in week_content),
                    'success_criteria': 'Mejorar comprensión en temas identificados'
                })
        
        # Semana 4: Repaso y evaluación
        goals.append({
            'week': 4,
            'focus': 'Repaso integral y autoevaluación',
            'content_items': 0,
            'estimated_hours': 2.0,
            'success_criteria': 'Completar práctica de repaso con 70%+ de aciertos'
        })
        
        return goals
    
    def _generate_empty_plan(self, student_id: str, month: str) -> StudyPlan:
        """Genera plan vacío cuando no hay debilidades identificadas"""
        return StudyPlan(
            student_id=student_id,
            month=month,
            generated_at=datetime.now(),
            theta_global=0.0,
            theta_ci=(-1.0, 1.0),
            subjects_evaluated=[],
            strengths=[],
            weaknesses=[],
            priority_high=[],
            priority_medium=[],
            priority_low=[],
            weekly_goals=[],
            estimated_hours_per_week=0.0,
            study_schedule={day: [] for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']},
            next_diagnostic_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            difficulty_adjustment=0.0,
            content_filters={}
        )
    
    async def save_study_plan_yaml(self, study_plan: StudyPlan, 
                                 output_dir: str = "plans") -> str:
        """Guarda plan de estudio en formato YAML"""
        
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Convertir plan a dict serializable
        plan_dict = {
            'metadata': {
                'student_id': study_plan.student_id,
                'month': study_plan.month,
                'generated_at': study_plan.generated_at.isoformat(),
                'theta_global': float(study_plan.theta_global),
                'theta_ci_95': [float(study_plan.theta_ci[0]), float(study_plan.theta_ci[1])],
                'subjects_evaluated': study_plan.subjects_evaluated
            },
            'analysis': {
                'strengths': study_plan.strengths,
                'weaknesses': [
                    {
                        'subject': w.subject_name,
                        'topic': w.topic_name,
                        'competence': w.competence,
                        'accuracy': float(w.accuracy),
                        'severity_score': float(w.severity_score),
                        'days_since_failure': w.days_since_failure
                    }
                    for w in study_plan.weaknesses[:10]  # Top 10
                ]
            },
            'content_recommendations': {
                'priority_high': [self._rec_to_dict(r) for r in study_plan.priority_high],
                'priority_medium': [self._rec_to_dict(r) for r in study_plan.priority_medium],
                'priority_low': [self._rec_to_dict(r) for r in study_plan.priority_low]
            },
            'study_plan': {
                'weekly_goals': study_plan.weekly_goals,
                'estimated_hours_per_week': study_plan.estimated_hours_per_week,
                'study_schedule': study_plan.study_schedule
            },
            'adaptive_parameters': {
                'next_diagnostic_date': study_plan.next_diagnostic_date,
                'difficulty_adjustment': study_plan.difficulty_adjustment,
                'content_filters': study_plan.content_filters
            }
        }
        
        # Guardar archivo YAML
        filename = f"rec_plan_{study_plan.student_id}_{study_plan.month.replace('-', '')}.yml"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(plan_dict, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        logger.info(f"Plan guardado en: {filepath}")
        return filepath
    
    def _rec_to_dict(self, rec: ContentRecommendation) -> Dict[str, Any]:
        """Convierte recomendación a diccionario serializable"""
        return {
            'type': rec.content_type.value,
            'title': rec.title,
            'url': rec.url,
            'priority': rec.priority.value,
            'duration_minutes': rec.duration_minutes,
            'estimated_effort_hours': rec.estimated_effort_hours,
            'semantic_similarity': float(rec.semantic_similarity),
            'total_score': float(rec.total_score),
            'addresses_weaknesses': rec.addresses_weaknesses
        }


# Ejemplo de uso y testing
async def main():
    """Función principal para testing del motor de recomendaciones"""
    
    database_url = "postgresql://gameplay:gameplay123@localhost:5433/gameplay_db"
    openai_api_key = None  # Configurar si está disponible
    
    engine = RecommendationEngine(database_url, openai_api_key)
    
    try:
        # Test: Generar plan para estudiante
        student_id = "test_student_001"
        month = "2024-09"
        
        study_plan = await engine.generate_monthly_study_plan(student_id, month)
        
        print(f"Plan generado para {student_id}:")
        print(f"- Theta global: {study_plan.theta_global:.3f}")
        print(f"- Debilidades: {len(study_plan.weaknesses)}")
        print(f"- Recomendaciones alta prioridad: {len(study_plan.priority_high)}")
        print(f"- Recomendaciones media prioridad: {len(study_plan.priority_medium)}")
        print(f"- Horas estimadas/semana: {study_plan.estimated_hours_per_week}")
        
        # Guardar plan YAML
        yaml_path = await engine.save_study_plan_yaml(study_plan)
        print(f"Plan guardado en: {yaml_path}")
        
    except Exception as e:
        logger.error(f"Error en testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())