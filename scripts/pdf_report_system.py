#!/usr/bin/env python3
"""
PDF Report System - ICFES Leveling

Sistema de reportes PDF auto-contenidos con imágenes embebidas:
- Portada con datos del estudiante y nivel alcanzado
- Tabla IRT detallada por materia con percentiles
- Gráficos de evolución y radar de habilidades
- Miniaturas de preguntas falladas más críticas (6-12)
- QR codes a playlist YouTube y plan YAML
- Interacciones IA destacadas
- Watermarks y branding institucional

Author: Claude Code Assistant
Date: 2024  
"""

import asyncio
import asyncpg
import pandas as pd
import numpy as np
import logging
import json
import base64
import qrcode
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import io
from pathlib import Path

# PDF generation libraries
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, 
                               Table, TableStyle, PageBreak, Frame, KeepTogether)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.spider import SpiderChart
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

# Image processing
from PIL import Image as PILImage
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StudentReportData:
    """Datos completos para generar reporte PDF de estudiante"""
    # Información básica
    student_id: str
    student_name: str
    course: str
    institution: str
    report_date: datetime
    report_period: str  # Ej: "Septiembre 2024"
    
    # Métricas IRT globales
    theta_global: float
    se_global: float
    theta_ci_95: Tuple[float, float]
    global_percentile: float
    ability_level: str
    
    # Métricas por materia
    subject_results: List[Dict[str, Any]]
    
    # Evolución temporal
    theta_evolution: List[Tuple[datetime, float]]
    practice_sessions: List[Dict[str, Any]]
    
    # Preguntas críticas falladas (con imágenes)
    critical_failures: List[Dict[str, Any]]
    
    # Recomendaciones y contenido
    youtube_playlist_url: Optional[str]
    study_plan_yaml_url: Optional[str]
    ai_interactions_summary: List[str]
    
    # Gráficos (como bytes)
    theta_chart_bytes: Optional[bytes]
    radar_chart_bytes: Optional[bytes]
    progress_chart_bytes: Optional[bytes]

class PDFReportSystem:
    """Sistema principal para generar reportes PDF"""
    
    def __init__(self, database_url: str, media_base_path: str = "database/allquestions"):
        self.database_url = database_url
        self.media_base_path = Path(media_base_path)
        
        # Configuración de estilo
        self.colors = {
            'primary': colors.Color(31/255, 119/255, 180/255),     # #1f77b4
            'secondary': colors.Color(255/255, 127/255, 14/255),   # #ff7f0e  
            'success': colors.Color(44/255, 160/255, 44/255),      # #2ca02c
            'danger': colors.Color(214/255, 39/255, 40/255),       # #d62728
            'light_gray': colors.Color(0.9, 0.9, 0.9),
            'dark_gray': colors.Color(0.3, 0.3, 0.3)
        }
        
        # Estilos de párrafo
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=self.colors['primary'],
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'], 
            fontSize=16,
            textColor=self.colors['primary'],
            spaceBefore=20,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='CriticalNote',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.colors['danger'],
            leftIndent=20,
            italic=True
        ))
        
    async def collect_student_report_data(self, student_id: str, 
                                        report_period: str = None) -> StudentReportData:
        """Recopila todos los datos necesarios para el reporte PDF"""
        
        if not report_period:
            report_period = datetime.now().strftime("%B %Y")
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # 1. Información básica del estudiante
            student_info = await conn.fetchrow("""
                SELECT 
                    s.id,
                    u.name as student_name,
                    COALESCE(c.name, 'Sin Asignar') as course,
                    COALESCE(inst.name, 'ICFES Leveling') as institution
                FROM students s
                JOIN users u ON s.user_id = u.id
                LEFT JOIN classes c ON s.class_id = c.id  
                LEFT JOIN institutions inst ON c.institution_id = inst.id
                WHERE s.id = $1
            """, student_id)
            
            if not student_info:
                raise ValueError(f"Estudiante {student_id} no encontrado")
            
            # 2. Métricas IRT globales y por materia
            subject_results = await conn.fetch("""
                SELECT DISTINCT ON (s.id)
                    s.id as subject_id,
                    s.name as subject_name,
                    da.theta,
                    da.se,
                    da.accuracy,
                    da.total_q,
                    da.correct_q,
                    da.finished_at,
                    
                    -- Calcular percentil aproximado
                    (SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM diagnostic_attempts da2 
                     WHERE da2.subject_id = da.subject_id AND da2.finished_at IS NOT NULL)
                     FROM diagnostic_attempts da3 
                     WHERE da3.subject_id = da.subject_id AND da3.theta <= da.theta
                     AND da3.finished_at IS NOT NULL) as percentile
                     
                FROM subjects s
                JOIN diagnostic_attempts da ON s.id = da.subject_id
                WHERE da.student_id = $1 AND da.finished_at IS NOT NULL
                ORDER BY s.id, da.finished_at DESC
            """, student_id)
            
            # Calcular métricas globales
            if subject_results:
                thetas = [float(r['theta']) for r in subject_results if r['theta']]
                ses = [float(r['se']) for r in subject_results if r['se']]
                
                theta_global = np.mean(thetas) if thetas else 0.0
                se_global = np.sqrt(np.mean(np.square(ses))) if ses else 1.0
                global_percentile = np.mean([r['percentile'] for r in subject_results if r['percentile']])
            else:
                theta_global = se_global = global_percentile = 0.0
            
            # 3. Evolución temporal del theta
            theta_evolution = await conn.fetch("""
                SELECT finished_at, theta
                FROM diagnostic_attempts
                WHERE student_id = $1 AND finished_at IS NOT NULL AND theta IS NOT NULL
                ORDER BY finished_at ASC
            """, student_id)
            
            # 4. Preguntas críticas falladas con imágenes
            critical_failures = await conn.fetch("""
                SELECT 
                    q.id as question_id,
                    q.statement,
                    q.image_url,
                    q.correct_answer,
                    qr.selected_option,
                    s.name as subject_name,
                    t.name as topic_name,
                    q.irt_b as difficulty,
                    qr.time_sec,
                    da.finished_at as failed_at,
                    
                    -- Calcular severidad del error
                    CASE 
                        WHEN q.irt_b < -1.0 THEN 'CRÍTICO'
                        WHEN qr.time_sec > 45 THEN 'ALTO' 
                        WHEN q.irt_b > 1.5 THEN 'BAJO'
                        ELSE 'MEDIO'
                    END as severity
                    
                FROM questions q
                JOIN question_responses qr ON q.id = qr.question_id
                JOIN diagnostic_attempts da ON qr.attempt_id = da.id
                JOIN subjects s ON q.subject_id = s.id
                LEFT JOIN topics t ON q.topic_id = t.id
                WHERE 
                    da.student_id = $1 
                    AND qr.is_correct = FALSE
                    AND q.image_url IS NOT NULL 
                    AND q.image_url != ''
                ORDER BY 
                    CASE severity 
                        WHEN 'CRÍTICO' THEN 1
                        WHEN 'ALTO' THEN 2  
                        WHEN 'MEDIO' THEN 3
                        ELSE 4 
                    END,
                    da.finished_at DESC
                LIMIT 12
            """, student_id)
            
            # 5. Sesiones de práctica recientes
            practice_sessions = await conn.fetch("""
                SELECT 
                    DATE(last_practice_date) as session_date,
                    COUNT(*) as questions_practiced,
                    SUM(CASE WHEN is_mastered THEN 1 ELSE 0 END) as questions_mastered,
                    AVG(CASE WHEN total_practice_attempts > 0 
                        THEN successful_attempts::float / total_practice_attempts 
                        ELSE 0 END) * 100 as session_accuracy
                FROM practice_from_failures
                WHERE student_id = $1 AND last_practice_date >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(last_practice_date)
                ORDER BY session_date DESC
                LIMIT 10
            """, student_id)
            
            # 6. Resumen de interacciones IA (simulado por ahora)
            ai_interactions = [
                "Explicación detallada sobre ecuaciones cuadráticas",
                "Ayuda paso a paso en problema de geometría",
                "Clarificación de conceptos de probabilidad",
                "Estrategias para mejorar velocidad de cálculo"
            ]
            
            # Crear objeto con todos los datos
            report_data = StudentReportData(
                student_id=student_id,
                student_name=student_info['student_name'],
                course=student_info['course'],
                institution=student_info['institution'],
                report_date=datetime.now(),
                report_period=report_period,
                theta_global=theta_global,
                se_global=se_global,
                theta_ci_95=(theta_global - 1.96 * se_global, theta_global + 1.96 * se_global),
                global_percentile=global_percentile,
                ability_level=self._classify_ability_level(theta_global),
                subject_results=[dict(r) for r in subject_results],
                theta_evolution=[(r['finished_at'], float(r['theta'])) for r in theta_evolution],
                practice_sessions=[dict(r) for r in practice_sessions],
                critical_failures=[dict(r) for r in critical_failures],
                youtube_playlist_url=f"https://youtube.com/playlist?list=PLExample_{student_id}",
                study_plan_yaml_url=f"https://app.icfesleveling.com/plans/{student_id}",
                ai_interactions_summary=ai_interactions,
                theta_chart_bytes=None,
                radar_chart_bytes=None,
                progress_chart_bytes=None
            )
            
            return report_data
            
        finally:
            await conn.close()
    
    def _classify_ability_level(self, theta: float) -> str:
        """Clasifica nivel de habilidad basado en theta"""
        if theta < -1.5:
            return "Insuficiente"
        elif theta < -0.5:
            return "Mínimo"
        elif theta < 0.5:
            return "Satisfactorio"
        elif theta < 1.5:
            return "Avanzado"
        else:
            return "Superior"
    
    def generate_charts(self, report_data: StudentReportData) -> StudentReportData:
        """Genera gráficos en formato bytes para embeber en PDF"""
        
        # 1. Gráfico de evolución theta
        if report_data.theta_evolution:
            plt.figure(figsize=(10, 6))
            dates, thetas = zip(*report_data.theta_evolution)
            
            plt.plot(dates, thetas, 'o-', linewidth=2, markersize=6, color='#1f77b4')
            plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5, label='Promedio Nacional')
            plt.title('Evolución de la Habilidad (θ)', fontsize=16, fontweight='bold')
            plt.xlabel('Fecha')
            plt.ylabel('Theta (θ)')
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Convertir a bytes
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            report_data.theta_chart_bytes = buffer.getvalue()
            plt.close()
        
        # 2. Gráfico radar de materias
        if report_data.subject_results:
            subjects = [r['subject_name'] for r in report_data.subject_results]
            thetas = [float(r['theta']) if r['theta'] else 0 for r in report_data.subject_results]
            
            # Normalizar thetas a escala 0-100
            normalized_thetas = [(t + 3) / 6 * 100 for t in thetas]  # Rango [-3,3] -> [0,100]
            
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
            
            angles = np.linspace(0, 2 * np.pi, len(subjects), endpoint=False).tolist()
            normalized_thetas += normalized_thetas[:1]  # Cerrar el polígono
            angles += angles[:1]
            
            ax.plot(angles, normalized_thetas, 'o-', linewidth=2, color='#1f77b4')
            ax.fill(angles, normalized_thetas, color='#1f77b4', alpha=0.25)
            ax.set_theta_offset(np.pi / 2)
            ax.set_theta_direction(-1)
            ax.set_thetagrids(np.degrees(angles[:-1]), subjects)
            ax.set_ylim(0, 100)
            ax.set_title('Habilidad por Materia', fontsize=16, fontweight='bold', pad=20)
            ax.grid(True)
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            report_data.radar_chart_bytes = buffer.getvalue()
            plt.close()
        
        # 3. Gráfico de progreso en práctica
        if report_data.practice_sessions:
            plt.figure(figsize=(10, 6))
            
            sessions_df = pd.DataFrame(report_data.practice_sessions)
            sessions_df['session_date'] = pd.to_datetime(sessions_df['session_date'])
            sessions_df = sessions_df.sort_values('session_date')
            
            plt.bar(sessions_df['session_date'], sessions_df['questions_practiced'], 
                   alpha=0.7, label='Preguntas Practicadas', color='#ff7f0e')
            plt.bar(sessions_df['session_date'], sessions_df['questions_mastered'], 
                   alpha=0.9, label='Preguntas Dominadas', color='#2ca02c')
            
            plt.title('Progreso en Sesiones de Práctica', fontsize=16, fontweight='bold')
            plt.xlabel('Fecha')
            plt.ylabel('Número de Preguntas')
            plt.legend()
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            report_data.progress_chart_bytes = buffer.getvalue()
            plt.close()
        
        return report_data
    
    def generate_qr_code(self, url: str, size: int = 100) -> bytes:
        """Genera código QR en formato bytes"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()
    
    def create_thumbnail_from_path(self, image_path: str, 
                                 size: Tuple[int, int] = (150, 150)) -> Optional[bytes]:
        """Crea thumbnail de imagen desde ruta del filesystem"""
        try:
            full_path = self.media_base_path / image_path
            
            if not full_path.exists():
                return None
            
            with PILImage.open(full_path) as img:
                img.thumbnail(size, PILImage.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                return buffer.getvalue()
                
        except Exception as e:
            logger.warning(f"Error creando thumbnail de {image_path}: {e}")
            return None
    
    async def generate_pdf_report(self, report_data: StudentReportData, 
                                output_path: str) -> str:
        """Genera reporte PDF completo"""
        
        logger.info(f"Generando reporte PDF para {report_data.student_name}")
        
        # Generar gráficos
        report_data = self.generate_charts(report_data)
        
        # Crear documento PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=72
        )
        
        story = []
        
        # 1. PORTADA
        story.extend(self._create_cover_page(report_data))
        story.append(PageBreak())
        
        # 2. RESUMEN EJECUTIVO
        story.extend(self._create_executive_summary(report_data))
        story.append(PageBreak())
        
        # 3. RESULTADOS IRT DETALLADOS  
        story.extend(self._create_irt_results_section(report_data))
        story.append(PageBreak())
        
        # 4. GRÁFICOS DE EVOLUCIÓN
        story.extend(self._create_charts_section(report_data))
        story.append(PageBreak())
        
        # 5. ANÁLISIS DE ERRORES CRÍTICOS (CON IMÁGENES)
        story.extend(self._create_critical_failures_section(report_data))
        story.append(PageBreak())
        
        # 6. RECOMENDACIONES Y PLAN DE ESTUDIO
        story.extend(self._create_recommendations_section(report_data))
        
        # Construir PDF
        doc.build(story)
        
        logger.info(f"Reporte PDF generado: {output_path}")
        return output_path
    
    def _create_cover_page(self, report_data: StudentReportData) -> List:
        """Crea página de portada"""
        elements = []
        
        # Logo y título principal (simulado)
        elements.append(Paragraph("ICFES LEVELING", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.5*inch))
        
        elements.append(Paragraph("REPORTE DE RENDIMIENTO ACADÉMICO", 
                                self.styles['CustomHeading2']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Información del estudiante
        student_info = [
            ['Estudiante:', report_data.student_name],
            ['Curso:', report_data.course],
            ['Institución:', report_data.institution],
            ['Período:', report_data.report_period],
            ['Fecha de Reporte:', report_data.report_date.strftime('%d/%m/%Y')]
        ]
        
        student_table = Table(student_info, colWidths=[2*inch, 4*inch])
        student_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), self.colors['primary']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, self.colors['light_gray']),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, self.colors['light_gray']])
        ]))
        
        elements.append(student_table)
        elements.append(Spacer(1, 1*inch))
        
        # Resumen de nivel alcanzado
        level_text = f"""
        <b>Nivel de Habilidad Alcanzado: {report_data.ability_level}</b><br/>
        <i>Percentil Nacional: {report_data.global_percentile:.1f}%</i><br/>
        <i>Theta Global: {report_data.theta_global:.3f} ± {report_data.se_global:.3f}</i>
        """
        
        elements.append(Paragraph(level_text, self.styles['Normal']))
        elements.append(Spacer(1, 1*inch))
        
        # Disclaimer
        disclaimer = """
        <i>Este reporte contiene un análisis detallado del rendimiento académico basado en la 
        Teoría de Respuesta al Ítem (IRT). Los resultados reflejan el nivel de habilidad 
        demostrado en las evaluaciones diagnósticas y sesiones de práctica.</i>
        """
        
        elements.append(Paragraph(disclaimer, self.styles['Normal']))
        
        return elements
    
    def _create_executive_summary(self, report_data: StudentReportData) -> List:
        """Crea resumen ejecutivo"""
        elements = []
        
        elements.append(Paragraph("RESUMEN EJECUTIVO", self.styles['CustomHeading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Tabla de resultados por materia
        if report_data.subject_results:
            headers = ['Materia', 'Theta (θ)', 'Nivel', 'Percentil', 'Precisión']
            rows = [headers]
            
            for result in report_data.subject_results:
                level = self._classify_ability_level(result['theta']) if result['theta'] else 'N/A'
                theta_str = f"{result['theta']:.2f}" if result['theta'] else 'N/A'
                percentile_str = f"{result['percentile']:.1f}%" if result['percentile'] else 'N/A'
                accuracy_str = f"{result['accuracy']*100:.1f}%" if result['accuracy'] else 'N/A'
                
                rows.append([
                    result['subject_name'],
                    theta_str,
                    level,
                    percentile_str,
                    accuracy_str
                ])
            
            results_table = Table(rows, colWidths=[1.5*inch, 0.8*inch, 1.2*inch, 0.8*inch, 0.8*inch])
            results_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, self.colors['dark_gray']),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colors['light_gray']])
            ]))
            
            elements.append(results_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # Destacar fortalezas y debilidades
        strengths_weaknesses = f"""
        <b>Fortalezas Identificadas:</b><br/>
        • Materias con mejor rendimiento: {', '.join([r['subject_name'] for r in report_data.subject_results if r['theta'] and r['theta'] > 0][:3])}<br/>
        • Progreso sostenido en práctica: {len(report_data.practice_sessions)} sesiones recientes<br/>
        <br/>
        <b>Áreas de Mejora:</b><br/>
        • Enfocar estudio en materias con theta < 0<br/>
        • Practicar preguntas de mayor dificultad<br/>
        • Mejorar velocidad de respuesta (tiempo promedio)
        """
        
        elements.append(Paragraph(strengths_weaknesses, self.styles['Normal']))
        
        return elements
    
    def _create_irt_results_section(self, report_data: StudentReportData) -> List:
        """Crea sección detallada de resultados IRT"""
        elements = []
        
        elements.append(Paragraph("RESULTADOS IRT DETALLADOS", self.styles['CustomHeading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Explicación de IRT
        irt_explanation = """
        <b>¿Qué es Theta (θ)?</b><br/>
        Theta representa tu nivel de habilidad en una escala continua. Un theta de 0 
        corresponde al promedio nacional. Valores positivos indican habilidad superior 
        al promedio, y valores negativos indican necesidad de refuerzo.<br/><br/>
        
        <b>Interpretación de Niveles:</b><br/>
        • <b>Superior (θ > 1.5):</b> Dominio excepcional<br/>
        • <b>Avanzado (0.5 < θ ≤ 1.5):</b> Muy buen rendimiento<br/>
        • <b>Satisfactorio (-0.5 < θ ≤ 0.5):</b> Rendimiento adecuado<br/>
        • <b>Mínimo (-1.5 < θ ≤ -0.5):</b> Necesita refuerzo<br/>
        • <b>Insuficiente (θ ≤ -1.5):</b> Requiere intervención<br/>
        """
        
        elements.append(Paragraph(irt_explanation, self.styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Intervalo de confianza
        ci_text = f"""
        <b>Tu Habilidad Global:</b> θ = {report_data.theta_global:.3f}<br/>
        <b>Intervalo de Confianza 95%:</b> [{report_data.theta_ci_95[0]:.3f}, {report_data.theta_ci_95[1]:.3f}]<br/>
        <i>Esto significa que tu verdadera habilidad está en este rango con 95% de probabilidad.</i>
        """
        
        elements.append(Paragraph(ci_text, self.styles['Normal']))
        
        return elements
    
    def _create_charts_section(self, report_data: StudentReportData) -> List:
        """Crea sección con gráficos"""
        elements = []
        
        elements.append(Paragraph("ANÁLISIS VISUAL DE RENDIMIENTO", self.styles['CustomHeading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Gráfico de evolución theta
        if report_data.theta_chart_bytes:
            elements.append(Paragraph("<b>Evolución de tu Habilidad</b>", self.styles['Normal']))
            
            theta_img = Image(io.BytesIO(report_data.theta_chart_bytes), width=6*inch, height=3.6*inch)
            elements.append(theta_img)
            elements.append(Spacer(1, 0.3*inch))
        
        # Gráfico radar
        if report_data.radar_chart_bytes:
            elements.append(Paragraph("<b>Perfil de Habilidades por Materia</b>", self.styles['Normal']))
            
            radar_img = Image(io.BytesIO(report_data.radar_chart_bytes), width=5*inch, height=5*inch)
            elements.append(radar_img)
            elements.append(Spacer(1, 0.3*inch))
        
        # Gráfico de progreso
        if report_data.progress_chart_bytes:
            elements.append(Paragraph("<b>Progreso en Sesiones de Práctica</b>", self.styles['Normal']))
            
            progress_img = Image(io.BytesIO(report_data.progress_chart_bytes), width=6*inch, height=3.6*inch)
            elements.append(progress_img)
        
        return elements
    
    def _create_critical_failures_section(self, report_data: StudentReportData) -> List:
        """Crea sección de errores críticos con imágenes"""
        elements = []
        
        elements.append(Paragraph("ERRORES CRÍTICOS A REVISAR", self.styles['CustomHeading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        intro_text = """
        Las siguientes preguntas representan los errores más importantes que debes revisar. 
        Se priorizan por severidad: errores en preguntas fáciles son más críticos.
        """
        
        elements.append(Paragraph(intro_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Mostrar hasta 6 errores críticos con miniaturas
        for i, failure in enumerate(report_data.critical_failures[:6]):
            elements.append(self._create_failure_item(failure, i+1))
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_failure_item(self, failure: Dict[str, Any], item_number: int) -> Table:
        """Crea item individual de error crítico"""
        
        # Crear thumbnail si hay imagen
        thumbnail_data = None
        if failure['image_url']:
            thumbnail_data = self.create_thumbnail_from_path(failure['image_url'])
        
        # Datos del error
        error_info = [
            f"<b>{item_number}. {failure['subject_name']} - {failure['topic_name'] or 'General'}</b>",
            f"<i>Severidad: {failure['severity']}</i>",
            f"Elegiste: <b>{failure['selected_option']}</b> | Correcta: <b>{failure['correct_answer']}</b>",
            f"Tiempo: {failure['time_sec']:.1f}s | Dificultad: {failure['difficulty']:.2f}" if failure['difficulty'] else "Tiempo: {failure['time_sec']:.1f}s"
        ]
        
        # Truncar enunciado
        statement = failure['statement'][:200] + "..." if len(failure['statement']) > 200 else failure['statement']
        error_info.append(f"<i>{statement}</i>")
        
        text_content = "<br/>".join(error_info)
        text_cell = Paragraph(text_content, self.styles['Normal'])
        
        # Crear tabla con thumbnail a la izquierda y texto a la derecha
        if thumbnail_data:
            thumbnail_img = Image(io.BytesIO(thumbnail_data), width=1*inch, height=1*inch)
            table_data = [[thumbnail_img, text_cell]]
            col_widths = [1.2*inch, 4.8*inch]
        else:
            table_data = [[text_cell]]
            col_widths = [6*inch]
        
        item_table = Table(table_data, colWidths=col_widths)
        item_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.98)),
            ('BOX', (0, 0), (-1, -1), 1, self.colors['light_gray'])
        ]))
        
        return item_table
    
    def _create_recommendations_section(self, report_data: StudentReportData) -> List:
        """Crea sección de recomendaciones y plan de estudio"""
        elements = []
        
        elements.append(Paragraph("PLAN DE ESTUDIO PERSONALIZADO", self.styles['CustomHeading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Recomendaciones basadas en IA
        elements.append(Paragraph("<b>Recomendaciones Personalizadas:</b>", self.styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        for interaction in report_data.ai_interactions_summary[:5]:
            elements.append(Paragraph(f"• {interaction}", self.styles['Normal']))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # QR codes para recursos
        qr_section = []
        
        if report_data.youtube_playlist_url:
            youtube_qr = self.generate_qr_code(report_data.youtube_playlist_url)
            qr_section.append([
                Image(io.BytesIO(youtube_qr), width=1*inch, height=1*inch),
                "Videos de YouTube\nPersonalizados"
            ])
        
        if report_data.study_plan_yaml_url:
            plan_qr = self.generate_qr_code(report_data.study_plan_yaml_url)
            qr_section.append([
                Image(io.BytesIO(plan_qr), width=1*inch, height=1*inch),
                "Plan de Estudio\nCompleto (YAML)"
            ])
        
        if qr_section:
            elements.append(Paragraph("<b>Recursos Digitales:</b>", self.styles['Normal']))
            
            qr_table = Table(qr_section, colWidths=[1.2*inch, 2*inch])
            qr_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (1, -1), 10)
            ]))
            
            elements.append(qr_table)
        
        # Footer
        elements.append(Spacer(1, 0.5*inch))
        footer_text = f"""
        <i>Reporte generado automáticamente por ICFES Leveling el {report_data.report_date.strftime('%d/%m/%Y %H:%M')}.<br/>
        Para más información, visita: https://icfesleveling.com</i>
        """
        elements.append(Paragraph(footer_text, self.styles['Normal']))
        
        return elements


# Ejemplo de uso y testing  
async def main():
    """Función principal para testing del sistema de reportes PDF"""
    
    database_url = "postgresql://gameplay:gameplay123@localhost:5433/gameplay_db"
    media_path = "database/allquestions"
    
    pdf_system = PDFReportSystem(database_url, media_path)
    
    try:
        # Test: Generar reporte para estudiante
        student_id = "test_student_001"
        
        print("Recopilando datos del estudiante...")
        report_data = await pdf_system.collect_student_report_data(student_id, "Septiembre 2024")
        
        print(f"Datos recopilados:")
        print(f"- Estudiante: {report_data.student_name}")
        print(f"- Theta global: {report_data.theta_global:.3f}")
        print(f"- Materias evaluadas: {len(report_data.subject_results)}")
        print(f"- Errores críticos: {len(report_data.critical_failures)}")
        
        # Generar PDF
        output_path = f"reports/reporte_{student_id}_{datetime.now().strftime('%Y%m')}.pdf"
        import os
        os.makedirs("reports", exist_ok=True)
        
        print(f"Generando PDF: {output_path}")
        final_path = await pdf_system.generate_pdf_report(report_data, output_path)
        
        print(f"Reporte PDF generado exitosamente: {final_path}")
        
    except Exception as e:
        logger.error(f"Error en testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())