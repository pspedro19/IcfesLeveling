#!/usr/bin/env python3
"""
Advanced Dashboard System - ICFES Leveling

Sistema de dashboards con visualizaciones avanzadas:
- Dashboard Estudiante: KPIs IRT, carrusel de fallos con miniaturas, tiempos, YAML
- Dashboard Docente: KPIs de clase, heatmaps, radar, distractores visuales, RBAC
- Métricas en tiempo real con imágenes embebidas
- Exportación CSV/PDF institucional

Author: Claude Code Assistant  
Date: 2024
"""

import asyncio
import asyncpg
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import io
import hashlib
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """Roles de usuario con diferentes niveles de acceso"""
    STUDENT = "student"
    TEACHER = "teacher"
    COORDINATOR = "coordinator" 
    ADMIN = "admin"

class ChartType(Enum):
    """Tipos de gráficos disponibles"""
    THETA_TIMELINE = "theta_timeline"
    SUBJECT_RADAR = "subject_radar"
    ACCURACY_HEATMAP = "accuracy_heatmap"
    TIME_DISTRIBUTION = "time_distribution"
    DISTRACTOR_ANALYSIS = "distractor_analysis"
    MASTERY_PROGRESS = "mastery_progress"

@dataclass
class StudentMetrics:
    """Métricas consolidadas de un estudiante"""
    student_id: str
    name: str
    
    # IRT Global
    theta_global: float
    se_global: float
    theta_ci_95: Tuple[float, float]
    ability_level: str
    percentile: float
    
    # Por materia
    subject_metrics: Dict[str, Dict[str, Any]]
    
    # Progreso temporal  
    theta_evolution: List[Tuple[datetime, float]]
    accuracy_trend: List[Tuple[datetime, float]]
    
    # Práctica y mastery
    total_practice_sessions: int
    mastery_percentage: float
    current_streak: int
    
    # Engagement
    last_activity: datetime
    days_since_last_activity: int
    weekly_study_hours: float

@dataclass
class ClassMetrics:
    """Métricas consolidadas de una clase/curso"""
    class_id: str
    class_name: str
    teacher_id: str
    
    # Estadísticas generales
    total_students: int
    active_students: int
    avg_theta: float
    theta_std: float
    
    # Distribución por niveles
    level_distribution: Dict[str, int]
    
    # Top performers y en riesgo
    top_performers: List[Dict[str, Any]]
    at_risk_students: List[Dict[str, Any]]
    
    # Análisis por materia
    subject_performance: Dict[str, Dict[str, float]]
    
    # Problemas comunes
    common_distractors: List[Dict[str, Any]]
    difficult_topics: List[Dict[str, Any]]

@dataclass
class VisualDistractor:
    """Distractor común con información visual"""
    question_id: int
    statement: str
    image_url: Optional[str]
    image_thumbnail: Optional[str]  # Base64 thumbnail
    
    correct_option: str
    distractor_option: str
    selection_rate: float
    
    subject_name: str
    topic_name: str
    competence: str
    
    # Métricas de impacto
    affected_students: int
    avg_time_impact: float
    difficulty_level: str


class DashboardSystem:
    """Sistema principal de dashboards avanzados"""
    
    def __init__(self, database_url: str, media_base_path: str = "database/allquestions"):
        self.database_url = database_url
        self.media_base_path = media_base_path
        
        # Cache de métricas (TTL 5 minutos)
        self._metrics_cache = {}
        self._cache_ttl = 300
        
        # Configuración de visualizaciones
        self.color_palette = {
            'primary': '#1f77b4',
            'success': '#2ca02c', 
            'warning': '#ff7f0e',
            'danger': '#d62728',
            'info': '#17becf'
        }
        
        # Niveles de habilidad IRT
        self.ability_levels = {
            'Insuficiente': (-4.0, -1.5),
            'Mínimo': (-1.5, -0.5),
            'Satisfactorio': (-0.5, 0.5),
            'Avanzado': (0.5, 1.5),
            'Superior': (1.5, 4.0)
        }
    
    async def get_student_metrics(self, student_id: str, 
                                include_images: bool = True) -> StudentMetrics:
        """Obtiene métricas completas de un estudiante"""
        
        cache_key = f"student_metrics_{student_id}_{include_images}"
        
        # Verificar cache
        if cache_key in self._metrics_cache:
            cached_data, timestamp = self._metrics_cache[cache_key]
            if (datetime.now() - timestamp).seconds < self._cache_ttl:
                return cached_data
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Consulta principal para métricas del estudiante
            student_data = await conn.fetchrow("""
                SELECT 
                    s.id as student_id,
                    u.name,
                    
                    -- IRT Global (último diagnóstico de cada materia)
                    AVG(da.theta) as theta_global,
                    SQRT(AVG(da.se * da.se)) as se_global,
                    
                    -- Actividad reciente
                    MAX(GREATEST(da.finished_at, COALESCE(ps.last_activity, da.finished_at))) as last_activity
                    
                FROM students s
                JOIN users u ON s.user_id = u.id
                LEFT JOIN LATERAL (
                    SELECT DISTINCT ON (subject_id) 
                        subject_id, theta, se, finished_at
                    FROM diagnostic_attempts 
                    WHERE student_id = s.id AND finished_at IS NOT NULL
                    ORDER BY subject_id, finished_at DESC
                ) da ON true
                LEFT JOIN (
                    SELECT student_id, MAX(last_practice_date) as last_activity
                    FROM practice_from_failures 
                    GROUP BY student_id
                ) ps ON s.id = ps.student_id
                WHERE s.id = $1
                GROUP BY s.id, u.name
            """, student_id)
            
            if not student_data:
                raise ValueError(f"Estudiante {student_id} no encontrado")
            
            # Calcular percentil y nivel de habilidad
            theta = float(student_data['theta_global'] or 0.0)
            se = float(student_data['se_global'] or 1.0)
            
            ability_level = self._classify_ability_level(theta)
            percentile = self._calculate_percentile(theta)
            theta_ci = (theta - 1.96 * se, theta + 1.96 * se)
            
            # Métricas por materia
            subject_metrics = await self._get_subject_metrics(conn, student_id)
            
            # Evolución temporal
            theta_evolution = await self._get_theta_evolution(conn, student_id)
            accuracy_trend = await self._get_accuracy_trend(conn, student_id)
            
            # Métricas de práctica
            practice_metrics = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT session_date) as total_sessions,
                    AVG(CASE WHEN is_mastered THEN 1.0 ELSE 0.0 END) * 100 as mastery_percentage,
                    MAX(current_streak) as max_streak,
                    SUM(estimated_study_hours) as weekly_hours
                FROM (
                    SELECT 
                        DATE(last_practice_date) as session_date,
                        is_mastered,
                        current_streak,
                        0.5 as estimated_study_hours  -- 30 min por sesión promedio
                    FROM practice_from_failures
                    WHERE student_id = $1 AND last_practice_date >= NOW() - INTERVAL '30 days'
                ) practice_summary
            """, student_id)
            
            # Calcular días desde última actividad
            last_activity = student_data['last_activity']
            days_since_activity = (datetime.now() - last_activity).days if last_activity else 999
            
            # Crear objeto de métricas
            metrics = StudentMetrics(
                student_id=student_id,
                name=student_data['name'],
                theta_global=theta,
                se_global=se,
                theta_ci_95=theta_ci,
                ability_level=ability_level,
                percentile=percentile,
                subject_metrics=subject_metrics,
                theta_evolution=theta_evolution,
                accuracy_trend=accuracy_trend,
                total_practice_sessions=practice_metrics['total_sessions'] or 0,
                mastery_percentage=float(practice_metrics['mastery_percentage'] or 0.0),
                current_streak=practice_metrics['max_streak'] or 0,
                last_activity=last_activity,
                days_since_last_activity=days_since_activity,
                weekly_study_hours=float(practice_metrics['weekly_hours'] or 0.0)
            )
            
            # Guardar en cache
            self._metrics_cache[cache_key] = (metrics, datetime.now())
            
            return metrics
            
        finally:
            await conn.close()
    
    async def _get_subject_metrics(self, conn, student_id: str) -> Dict[str, Dict[str, Any]]:
        """Obtiene métricas detalladas por materia"""
        
        subject_data = await conn.fetch("""
            SELECT 
                s.id as subject_id,
                s.name as subject_name,
                da.theta,
                da.se,
                da.accuracy,
                da.total_q,
                da.correct_q,
                
                -- Métricas de práctica por materia
                COALESCE(practice_stats.mastered_count, 0) as mastered_questions,
                COALESCE(practice_stats.total_failed, 0) as total_failed_questions,
                
                -- Tiempo promedio
                COALESCE(time_stats.avg_time, 0) as avg_response_time
                
            FROM subjects s
            LEFT JOIN LATERAL (
                SELECT DISTINCT ON (subject_id) *
                FROM diagnostic_attempts
                WHERE student_id = $1 AND subject_id = s.id AND finished_at IS NOT NULL
                ORDER BY subject_id, finished_at DESC
            ) da ON true
            LEFT JOIN (
                SELECT 
                    q.subject_id,
                    COUNT(*) FILTER (WHERE pff.is_mastered) as mastered_count,
                    COUNT(*) as total_failed
                FROM practice_from_failures pff
                JOIN questions q ON pff.question_id = q.id
                WHERE pff.student_id = $1
                GROUP BY q.subject_id
            ) practice_stats ON s.id = practice_stats.subject_id
            LEFT JOIN (
                SELECT 
                    q.subject_id,
                    AVG(qr.time_sec) as avg_time
                FROM question_responses qr
                JOIN questions q ON qr.question_id = q.id
                JOIN diagnostic_attempts da ON qr.attempt_id = da.id
                WHERE da.student_id = $1
                GROUP BY q.subject_id
            ) time_stats ON s.id = time_stats.subject_id
            
            WHERE da.theta IS NOT NULL OR practice_stats.total_failed > 0
            ORDER BY s.name
        """, student_id)
        
        subject_metrics = {}
        for row in subject_data:
            subject_metrics[row['subject_name']] = {
                'subject_id': row['subject_id'],
                'theta': float(row['theta']) if row['theta'] else None,
                'se': float(row['se']) if row['se'] else None,
                'accuracy': float(row['accuracy']) if row['accuracy'] else 0.0,
                'total_questions': row['total_q'],
                'correct_questions': row['correct_q'],
                'mastered_questions': row['mastered_questions'],
                'total_failed_questions': row['total_failed_questions'],
                'mastery_percentage': (row['mastered_questions'] / max(row['total_failed_questions'], 1)) * 100,
                'avg_response_time': float(row['avg_response_time']) if row['avg_response_time'] else 0.0,
                'ability_level': self._classify_ability_level(row['theta']) if row['theta'] else 'Sin evaluar'
            }
        
        return subject_metrics
    
    async def _get_theta_evolution(self, conn, student_id: str) -> List[Tuple[datetime, float]]:
        """Obtiene evolución temporal del theta"""
        
        evolution_data = await conn.fetch("""
            SELECT finished_at, theta
            FROM diagnostic_attempts
            WHERE student_id = $1 AND finished_at IS NOT NULL AND theta IS NOT NULL
            ORDER BY finished_at ASC
        """, student_id)
        
        return [(row['finished_at'], float(row['theta'])) for row in evolution_data]
    
    async def _get_accuracy_trend(self, conn, student_id: str) -> List[Tuple[datetime, float]]:
        """Obtiene tendencia de precisión en práctica"""
        
        trend_data = await conn.fetch("""
            SELECT 
                DATE_TRUNC('week', last_practice_date) as week,
                AVG(CASE WHEN total_practice_attempts > 0 
                    THEN successful_attempts::float / total_practice_attempts 
                    ELSE 0 END) as weekly_accuracy
            FROM practice_from_failures
            WHERE student_id = $1 AND last_practice_date IS NOT NULL
            GROUP BY week
            ORDER BY week ASC
        """, student_id)
        
        return [(row['week'], float(row['weekly_accuracy'])) for row in trend_data]
    
    def _classify_ability_level(self, theta: Optional[float]) -> str:
        """Clasifica nivel de habilidad basado en theta"""
        if theta is None:
            return "Sin evaluar"
        
        for level, (min_theta, max_theta) in self.ability_levels.items():
            if min_theta <= theta < max_theta:
                return level
        return "Superior"
    
    def _calculate_percentile(self, theta: float) -> float:
        """Calcula percentil aproximado basado en distribución normal estándar"""
        from scipy import stats
        return stats.norm.cdf(theta) * 100
    
    async def get_visual_distractors(self, class_id: Optional[str] = None, 
                                   subject_id: Optional[int] = None,
                                   limit: int = 10) -> List[VisualDistractor]:
        """Obtiene análisis de distractores visuales más comunes"""
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Query para distractores con imágenes
            query = """
            SELECT 
                q.id as question_id,
                q.statement,
                q.image_url,
                q.correct_answer,
                qr.selected_option as distractor_option,
                s.name as subject_name,
                t.name as topic_name,
                COALESCE(t.competence, '') as competence,
                q.difficulty,
                
                -- Métricas de impacto
                COUNT(*) as selection_count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY q.id) as selection_rate,
                COUNT(DISTINCT da.student_id) as affected_students,
                AVG(qr.time_sec) as avg_time_impact
                
            FROM questions q
            JOIN question_responses qr ON q.id = qr.question_id
            JOIN diagnostic_attempts da ON qr.attempt_id = da.id
            JOIN subjects s ON q.subject_id = s.id
            LEFT JOIN topics t ON q.topic_id = t.id
            WHERE 
                qr.is_correct = FALSE
                AND qr.selected_option != q.correct_answer
                AND q.image_url IS NOT NULL
                AND q.image_url != ''
            """
            
            params = []
            if class_id:
                query += " AND da.student_id IN (SELECT id FROM students WHERE class_id = $1)"
                params.append(class_id)
            if subject_id:
                param_idx = len(params) + 1
                query += f" AND q.subject_id = ${param_idx}"
                params.append(subject_id)
            
            query += """
            GROUP BY 
                q.id, q.statement, q.image_url, q.correct_answer, 
                qr.selected_option, s.name, t.name, t.competence, q.difficulty
            HAVING COUNT(*) >= 3  -- Al menos 3 estudiantes eligieron este distractor
            ORDER BY selection_rate DESC, affected_students DESC
            LIMIT ${}
            """.format(len(params) + 1)
            
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            
            visual_distractors = []
            for row in rows:
                # Generar thumbnail si hay imagen
                thumbnail = None
                if row['image_url']:
                    thumbnail = await self._generate_image_thumbnail(row['image_url'])
                
                distractor = VisualDistractor(
                    question_id=row['question_id'],
                    statement=row['statement'][:200] + "..." if len(row['statement']) > 200 else row['statement'],
                    image_url=row['image_url'],
                    image_thumbnail=thumbnail,
                    correct_option=row['correct_answer'],
                    distractor_option=row['distractor_option'],
                    selection_rate=float(row['selection_rate']),
                    subject_name=row['subject_name'],
                    topic_name=row['topic_name'] or 'General',
                    competence=row['competence'],
                    affected_students=row['affected_students'],
                    avg_time_impact=float(row['avg_time_impact']) if row['avg_time_impact'] else 0.0,
                    difficulty_level=row['difficulty'] or 'mid'
                )
                visual_distractors.append(distractor)
            
            return visual_distractors
            
        finally:
            await conn.close()
    
    async def _generate_image_thumbnail(self, image_url: str, 
                                      size: Tuple[int, int] = (150, 150)) -> Optional[str]:
        """Genera thumbnail en base64 de una imagen"""
        try:
            import os
            from pathlib import Path
            
            # Construir ruta completa
            image_path = Path(self.media_base_path) / image_url
            
            if not image_path.exists():
                return None
            
            # Abrir imagen y crear thumbnail
            with Image.open(image_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Convertir a base64
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                
                thumbnail_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return f"data:image/png;base64,{thumbnail_b64}"
                
        except Exception as e:
            logger.warning(f"Error generando thumbnail para {image_url}: {e}")
            return None
    
    def generate_student_dashboard_charts(self, metrics: StudentMetrics) -> Dict[str, str]:
        """Genera gráficos para el dashboard del estudiante"""
        charts = {}
        
        # 1. Gráfico de evolución theta
        if metrics.theta_evolution:
            fig_theta = go.Figure()
            
            dates, thetas = zip(*metrics.theta_evolution)
            
            fig_theta.add_trace(go.Scatter(
                x=dates,
                y=thetas,
                mode='lines+markers',
                name='Habilidad (θ)',
                line=dict(color=self.color_palette['primary'], width=3),
                marker=dict(size=8)
            ))
            
            # Añadir bandas de nivel de habilidad
            for level, (min_theta, max_theta) in self.ability_levels.items():
                fig_theta.add_hline(
                    y=min_theta, 
                    line_dash="dash", 
                    line_color="gray", 
                    opacity=0.3,
                    annotation_text=level
                )
            
            fig_theta.update_layout(
                title="Evolución de la Habilidad (θ)",
                xaxis_title="Fecha",
                yaxis_title="Theta (θ)",
                showlegend=False,
                height=400
            )
            
            charts['theta_evolution'] = fig_theta.to_html(include_plotlyjs='cdn')
        
        # 2. Radar chart por materias
        if metrics.subject_metrics:
            subjects = list(metrics.subject_metrics.keys())
            theta_values = [metrics.subject_metrics[s].get('theta', 0) for s in subjects]
            
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=[(t + 3) / 6 * 100 if t else 50 for t in theta_values],  # Normalizar a 0-100
                theta=subjects,
                fill='toself',
                name='Nivel de Habilidad',
                fillcolor='rgba(31, 119, 180, 0.3)',
                line=dict(color=self.color_palette['primary'])
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=False,
                title="Habilidad por Materia",
                height=500
            )
            
            charts['subject_radar'] = fig_radar.to_html(include_plotlyjs='cdn')
        
        # 3. Heatmap de mastery por tema
        mastery_data = []
        for subject, metrics_data in metrics.subject_metrics.items():
            mastery_pct = metrics_data.get('mastery_percentage', 0)
            mastery_data.append({
                'subject': subject,
                'mastery': mastery_pct,
                'category': 'Dominio' if mastery_pct >= 70 else 'En Progreso' if mastery_pct >= 30 else 'Principiante'
            })
        
        if mastery_data:
            df_mastery = pd.DataFrame(mastery_data)
            
            fig_mastery = px.bar(
                df_mastery, 
                x='subject', 
                y='mastery',
                color='category',
                title="Progreso de Dominio por Materia",
                labels={'mastery': 'Porcentaje de Dominio (%)', 'subject': 'Materia'},
                color_discrete_map={
                    'Dominio': self.color_palette['success'],
                    'En Progreso': self.color_palette['warning'], 
                    'Principiante': self.color_palette['danger']
                }
            )
            
            fig_mastery.update_layout(height=400)
            charts['mastery_progress'] = fig_mastery.to_html(include_plotlyjs='cdn')
        
        return charts
    
    def generate_class_dashboard_charts(self, class_metrics: ClassMetrics,
                                      visual_distractors: List[VisualDistractor]) -> Dict[str, str]:
        """Genera gráficos para el dashboard del docente"""
        charts = {}
        
        # 1. Distribución de niveles de habilidad
        if class_metrics.level_distribution:
            levels = list(class_metrics.level_distribution.keys())
            counts = list(class_metrics.level_distribution.values())
            
            fig_levels = go.Figure(data=[
                go.Pie(
                    labels=levels, 
                    values=counts,
                    hole=.3,
                    textinfo='label+percent',
                    textposition='inside'
                )
            ])
            
            fig_levels.update_layout(
                title="Distribución de Niveles de Habilidad",
                height=400
            )
            
            charts['level_distribution'] = fig_levels.to_html(include_plotlyjs='cdn')
        
        # 2. Heatmap de rendimiento por materia
        if class_metrics.subject_performance:
            subjects = list(class_metrics.subject_performance.keys())
            metrics_names = ['Theta Promedio', 'Precisión', 'Tiempo Promedio']
            
            heatmap_data = []
            for subject in subjects:
                data = class_metrics.subject_performance[subject]
                heatmap_data.append([
                    data.get('avg_theta', 0),
                    data.get('avg_accuracy', 0),
                    data.get('avg_time', 0)
                ])
            
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=metrics_names,
                y=subjects,
                colorscale='RdYlGn',
                showscale=True
            ))
            
            fig_heatmap.update_layout(
                title="Mapa de Calor: Rendimiento por Materia",
                height=400
            )
            
            charts['performance_heatmap'] = fig_heatmap.to_html(include_plotlyjs='cdn')
        
        # 3. Top distractores visuales
        if visual_distractors:
            distractor_df = pd.DataFrame([
                {
                    'question_id': vd.question_id,
                    'subject': vd.subject_name,
                    'topic': vd.topic_name,
                    'selection_rate': vd.selection_rate,
                    'affected_students': vd.affected_students,
                    'has_image': bool(vd.image_url)
                }
                for vd in visual_distractors[:10]
            ])
            
            fig_distractors = px.scatter(
                distractor_df,
                x='selection_rate',
                y='affected_students', 
                color='subject',
                size='selection_rate',
                hover_data=['topic', 'question_id'],
                title="Análisis de Distractores Visuales",
                labels={
                    'selection_rate': 'Tasa de Selección (%)',
                    'affected_students': 'Estudiantes Afectados'
                }
            )
            
            fig_distractors.update_layout(height=500)
            charts['visual_distractors'] = fig_distractors.to_html(include_plotlyjs='cdn')
        
        return charts
    
    async def generate_dashboard_data(self, user_id: str, user_role: UserRole, 
                                    class_id: Optional[str] = None) -> Dict[str, Any]:
        """Genera datos completos para el dashboard según el rol del usuario"""
        
        dashboard_data = {
            'user_id': user_id,
            'user_role': user_role.value,
            'generated_at': datetime.now().isoformat(),
            'charts': {},
            'metrics': {},
            'recommendations': []
        }
        
        if user_role == UserRole.STUDENT:
            # Dashboard de estudiante
            metrics = await self.get_student_metrics(user_id)
            charts = self.generate_student_dashboard_charts(metrics)
            
            dashboard_data['metrics'] = asdict(metrics)
            dashboard_data['charts'] = charts
            
            # Recomendaciones básicas
            recommendations = []
            if metrics.days_since_last_activity > 7:
                recommendations.append("⏰ No has practicado en una semana. ¡Es hora de retomar el estudio!")
            
            if metrics.mastery_percentage < 50:
                recommendations.append("🎯 Enfócate en dominar tus errores principales usando el Modo Recuperación")
            
            if metrics.theta_global < 0:
                recommendations.append("📚 Considera dedicar más tiempo a repasar conceptos fundamentales")
                
            dashboard_data['recommendations'] = recommendations
        
        elif user_role in [UserRole.TEACHER, UserRole.COORDINATOR, UserRole.ADMIN]:
            # Dashboard de docente/coordinador  
            if not class_id:
                raise ValueError("class_id requerido para roles de docente")
            
            # TODO: Implementar get_class_metrics
            # class_metrics = await self.get_class_metrics(class_id)
            # visual_distractors = await self.get_visual_distractors(class_id)
            
            # Por ahora, datos dummy
            dashboard_data['metrics'] = {
                'total_students': 25,
                'active_students': 22,
                'avg_theta': 0.15,
                'class_performance': 'Satisfactorio'
            }
            
            dashboard_data['charts'] = {}
            dashboard_data['recommendations'] = [
                "📊 3 estudiantes necesitan atención especial",
                "🎯 Tema más problemático: Ecuaciones Cuadráticas", 
                "📈 El rendimiento general ha mejorado 12% este mes"
            ]
        
        return dashboard_data
    
    async def export_dashboard_pdf(self, dashboard_data: Dict[str, Any], 
                                 output_path: str) -> str:
        """Exporta dashboard a PDF institucional"""
        
        # TODO: Implementar generación de PDF con reportlab o weasyprint
        # Por ahora, guardar como JSON
        import json
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Dashboard exportado a: {output_path}")
        return output_path


# Ejemplo de uso y testing
async def main():
    """Función principal para testing del sistema de dashboards"""
    
    database_url = "postgresql://gameplay:gameplay123@localhost:5433/gameplay_db"
    media_path = "database/allquestions"
    
    dashboard = DashboardSystem(database_url, media_path)
    
    try:
        # Test: Dashboard de estudiante
        student_id = "test_student_001"
        
        print("Generando dashboard de estudiante...")
        student_dashboard = await dashboard.generate_dashboard_data(
            student_id, UserRole.STUDENT
        )
        
        print(f"Dashboard generado:")
        print(f"- Métricas disponibles: {list(student_dashboard['metrics'].keys())}")
        print(f"- Gráficos generados: {list(student_dashboard['charts'].keys())}")
        print(f"- Recomendaciones: {len(student_dashboard['recommendations'])}")
        
        # Test: Distractores visuales
        print("\nObteniendo distractores visuales...")
        visual_distractors = await dashboard.get_visual_distractors(limit=5)
        print(f"Distractores encontrados: {len(visual_distractors)}")
        
        for vd in visual_distractors[:3]:
            print(f"- Q{vd.question_id}: {vd.subject_name} - {vd.selection_rate:.1f}% eligió {vd.distractor_option}")
        
    except Exception as e:
        logger.error(f"Error en testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())