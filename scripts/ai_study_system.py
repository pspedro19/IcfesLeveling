#!/usr/bin/env python3
"""
AI Study System - ICFES Leveling

Sistema de estudio con IA contextual que proporciona:
- Chat IA contextual sobre preguntas específicas
- Explicaciones paso a paso personalizadas
- Detección de conceptos erróneos
- Generación de preguntas similares
- Estrategias de estudio adaptativas
- Integración con videos de YouTube (timestamps)

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
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import openai
import hashlib
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InteractionType(Enum):
    """Tipos de interacciones con IA"""
    EXPLANATION = "explanation"          # Explicación de pregunta
    CONCEPT_CLARIFICATION = "concept"    # Clarificación conceptual
    STRATEGY_HELP = "strategy"          # Ayuda estratégica 
    SIMILAR_QUESTION = "similar"        # Pregunta similar
    VIDEO_ANALYSIS = "video"            # Análisis de video
    STUDY_PLAN = "study_plan"           # Plan de estudio

class DifficultyLevel(Enum):
    """Niveles de dificultad para adaptación"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate" 
    ADVANCED = "advanced"

@dataclass
class StudyContext:
    """Contexto de estudio del estudiante"""
    student_id: str
    subject_id: int
    topic_id: Optional[int]
    
    # Estado del estudiante
    theta_estimate: float
    recent_accuracy: float
    difficulty_level: DifficultyLevel
    
    # Historial de errores
    recent_failures: List[Dict[str, Any]]
    common_mistakes: List[str]
    
    # Preferencias de aprendizaje
    preferred_explanation_style: str  # "visual", "step_by_step", "conceptual"
    language_level: str  # "simple", "standard", "technical"

@dataclass
class AIResponse:
    """Respuesta generada por IA"""
    interaction_id: str
    interaction_type: InteractionType
    student_id: str
    
    # Contenido principal
    main_response: str
    follow_up_questions: List[str]
    
    # Contexto usado
    question_context: Optional[Dict[str, Any]]
    topic_context: Optional[str]
    
    # Metadatos
    tokens_used: int
    response_time_ms: float
    confidence_score: float
    
    # Recursos adicionales
    related_videos: List[Dict[str, str]]
    practice_suggestions: List[str]
    
    created_at: datetime

class AIStudySystem:
    """Sistema principal de estudio con IA"""
    
    def __init__(self, database_url: str, openai_api_key: Optional[str] = None):
        self.database_url = database_url
        self.openai_client = openai.OpenAI(api_key=openai_api_key) if openai_api_key else None
        
        # Configuración de prompts
        self.base_prompts = {
            InteractionType.EXPLANATION: """
                Eres un tutor experto en {subject}. Un estudiante falló esta pregunta:
                
                PREGUNTA: {question}
                RESPUESTA ELEGIDA: {selected_answer}
                RESPUESTA CORRECTA: {correct_answer}
                
                CONTEXTO DEL ESTUDIANTE:
                - Nivel de habilidad: {ability_level}
                - Precisión reciente: {accuracy:.1%}
                - Errores comunes: {common_mistakes}
                
                Proporciona una explicación clara y adaptada a su nivel que:
                1. Explique por qué su respuesta está incorrecta
                2. Muestre el razonamiento correcto paso a paso
                3. Identifique el concepto clave que debe reforzar
                4. Sugiera cómo evitar este error en el futuro
                
                Usa un lenguaje {language_level} y estilo {explanation_style}.
            """,
            
            InteractionType.CONCEPT: """
                Un estudiante necesita clarificación sobre el concepto: {concept}
                
                CONTEXTO:
                - Materia: {subject}
                - Tema: {topic}
                - Nivel del estudiante: {ability_level}
                - Errores previos relacionados: {related_errors}
                
                Proporciona una explicación conceptual que:
                1. Defina el concepto claramente
                2. Use ejemplos concretos y relevantes
                3. Conecte con conceptos que ya domina
                4. Anticipe malentendidos comunes
                5. Incluya una analogía útil si es apropiado
                
                Mantén un tono {language_level} y enfoque {explanation_style}.
            """,
            
            InteractionType.STRATEGY: """
                Un estudiante con nivel {ability_level} en {subject} necesita estrategias para:
                PROBLEMA: {problem_description}
                
                PATRÓN DE ERRORES: {error_pattern}
                TIEMPO PROMEDIO: {avg_time}s
                DIFICULTADES ESPECÍFICAS: {specific_difficulties}
                
                Proporciona estrategias específicas que incluyan:
                1. Técnicas para abordar este tipo de problemas
                2. Métodos para evitar errores comunes
                3. Gestión del tiempo durante el examen
                4. Pasos de verificación de respuestas
                5. Recursos de práctica recomendados
                
                Sé práctico y específico. Incluye ejemplos de aplicación.
            """,
            
            InteractionType.VIDEO_ANALYSIS: """
                Analiza este video educativo en el contexto de las necesidades del estudiante:
                
                VIDEO: {video_title}
                DESCRIPCIÓN: {video_description}
                DURACIÓN: {duration} minutos
                
                NECESIDADES DEL ESTUDIANTE:
                - Debilidades: {weaknesses}
                - Nivel: {ability_level}
                - Conceptos a reforzar: {concepts_to_reinforce}
                
                Proporciona:
                1. Resumen de qué conceptos cubre el video
                2. Minutos específicos más relevantes para sus necesidades
                3. Cómo conecta con sus errores recientes
                4. Actividades de seguimiento recomendadas
                5. Nivel de dificultad del contenido (1-10)
                
                Formato: timestamps [MM:SS] con descripción breve.
            """
        }
        
        # Cache de contextos de estudiante
        self._context_cache = {}
        self._cache_ttl = 600  # 10 minutos
        
    async def get_study_context(self, student_id: str, 
                              subject_id: Optional[int] = None) -> StudyContext:
        """Obtiene contexto completo del estudiante para IA"""
        
        cache_key = f"context_{student_id}_{subject_id}"
        
        # Verificar cache
        if cache_key in self._context_cache:
            cached_data, timestamp = self._context_cache[cache_key]
            if (datetime.now() - timestamp).seconds < self._cache_ttl:
                return cached_data
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # 1. Obtener estado actual del estudiante
            student_state = await conn.fetchrow("""
                SELECT 
                    AVG(da.theta) as avg_theta,
                    AVG(da.se) as avg_se,
                    
                    -- Precisión reciente (últimos 30 días)
                    (SELECT AVG(CASE WHEN pff.total_practice_attempts > 0 
                         THEN pff.successful_attempts::float / pff.total_practice_attempts 
                         ELSE NULL END)
                     FROM practice_from_failures pff
                     WHERE pff.student_id = $1 
                     AND pff.last_practice_date >= NOW() - INTERVAL '30 days') as recent_accuracy
                     
                FROM diagnostic_attempts da
                WHERE da.student_id = $1 
                AND da.finished_at IS NOT NULL
                AND ($2::int IS NULL OR da.subject_id = $2)
            """, student_id, subject_id)
            
            # 2. Obtener errores recientes con contexto
            recent_failures = await conn.fetch("""
                SELECT 
                    q.id as question_id,
                    q.statement,
                    q.correct_answer,
                    qr.selected_option,
                    q.irt_b as difficulty,
                    s.name as subject_name,
                    t.name as topic_name,
                    COALESCE(t.competence, '') as competence,
                    qr.time_sec,
                    da.finished_at as failed_at
                FROM questions q
                JOIN question_responses qr ON q.id = qr.question_id
                JOIN diagnostic_attempts da ON qr.attempt_id = da.id
                JOIN subjects s ON q.subject_id = s.id
                LEFT JOIN topics t ON q.topic_id = t.id
                WHERE 
                    da.student_id = $1 
                    AND qr.is_correct = FALSE
                    AND da.finished_at >= NOW() - INTERVAL '60 days'
                    AND ($2::int IS NULL OR q.subject_id = $2)
                ORDER BY da.finished_at DESC
                LIMIT 10
            """, student_id, subject_id)
            
            # 3. Identificar errores comunes (distractores más seleccionados)
            common_mistakes = await conn.fetch("""
                SELECT 
                    qr.selected_option,
                    COUNT(*) as frequency,
                    STRING_AGG(DISTINCT t.name, ', ') as topics_affected
                FROM question_responses qr
                JOIN diagnostic_attempts da ON qr.attempt_id = da.id
                JOIN questions q ON qr.question_id = q.id
                LEFT JOIN topics t ON q.topic_id = t.id
                WHERE 
                    da.student_id = $1
                    AND qr.is_correct = FALSE
                    AND ($2::int IS NULL OR q.subject_id = $2)
                GROUP BY qr.selected_option
                ORDER BY frequency DESC
                LIMIT 5
            """, student_id, subject_id)
            
            # 4. Determinar nivel de dificultad apropiado
            theta = float(student_state['avg_theta']) if student_state['avg_theta'] else 0.0
            
            if theta < -1.0:
                difficulty = DifficultyLevel.BEGINNER
            elif theta < 0.5:
                difficulty = DifficultyLevel.INTERMEDIATE
            else:
                difficulty = DifficultyLevel.ADVANCED
            
            # 5. Inferir preferencias de aprendizaje (simplificado por ahora)
            explanation_style = "step_by_step"  # Default
            language_level = "standard"        # Default
            
            # Crear contexto
            context = StudyContext(
                student_id=student_id,
                subject_id=subject_id or 0,
                topic_id=None,  # Se especifica por interacción
                theta_estimate=theta,
                recent_accuracy=float(student_state['recent_accuracy'] or 0.5),
                difficulty_level=difficulty,
                recent_failures=[dict(f) for f in recent_failures],
                common_mistakes=[f['selected_option'] for f in common_mistakes],
                preferred_explanation_style=explanation_style,
                language_level=language_level
            )
            
            # Guardar en cache
            self._context_cache[cache_key] = (context, datetime.now())
            
            return context
            
        finally:
            await conn.close()
    
    async def generate_ai_response(self, interaction_type: InteractionType,
                                 student_context: StudyContext,
                                 user_message: str,
                                 additional_context: Dict[str, Any] = None) -> AIResponse:
        """Genera respuesta de IA contextualizada"""
        
        if not self.openai_client:
            return self._generate_dummy_response(interaction_type, student_context, user_message)
        
        start_time = datetime.now()
        
        # Preparar prompt contextual
        prompt = await self._prepare_contextual_prompt(
            interaction_type, student_context, user_message, additional_context
        )
        
        try:
            # Llamada a OpenAI
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un tutor experto en educación secundaria colombiana, especializado en preparación para ICFES."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            main_response = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Generar preguntas de seguimiento
            follow_up_questions = self._generate_follow_up_questions(
                interaction_type, student_context, main_response
            )
            
            # Buscar recursos relacionados
            related_videos = await self._find_related_videos(
                student_context, additional_context
            )
            
            practice_suggestions = self._generate_practice_suggestions(
                interaction_type, student_context
            )
            
        except Exception as e:
            logger.error(f"Error en llamada OpenAI: {e}")
            return self._generate_dummy_response(interaction_type, student_context, user_message)
        
        # Calcular tiempo de respuesta
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Crear respuesta AI
        ai_response = AIResponse(
            interaction_id=str(uuid.uuid4()),
            interaction_type=interaction_type,
            student_id=student_context.student_id,
            main_response=main_response,
            follow_up_questions=follow_up_questions,
            question_context=additional_context,
            topic_context=self._extract_topic_context(additional_context),
            tokens_used=tokens_used,
            response_time_ms=response_time,
            confidence_score=0.85,  # Estimación basada en contexto disponible
            related_videos=related_videos,
            practice_suggestions=practice_suggestions,
            created_at=datetime.now()
        )
        
        # Guardar interacción en base de datos
        await self._save_ai_interaction(ai_response)
        
        return ai_response
    
    async def _prepare_contextual_prompt(self, interaction_type: InteractionType,
                                       student_context: StudyContext,
                                       user_message: str,
                                       additional_context: Dict[str, Any]) -> str:
        """Prepara prompt contextualizado para IA"""
        
        base_template = self.base_prompts.get(interaction_type, "")
        
        # Obtener información de materia/tema
        subject_info = await self._get_subject_info(student_context.subject_id)
        topic_info = await self._get_topic_info(student_context.topic_id) if student_context.topic_id else {}
        
        # Variables de contexto
        context_vars = {
            'subject': subject_info.get('name', 'Matemáticas'),
            'topic': topic_info.get('name', 'General'),
            'ability_level': student_context.difficulty_level.value,
            'accuracy': student_context.recent_accuracy,
            'common_mistakes': ', '.join(student_context.common_mistakes[:3]) or 'No identificados',
            'language_level': student_context.language_level,
            'explanation_style': student_context.preferred_explanation_style,
            'user_message': user_message
        }
        
        # Agregar contexto específico del tipo de interacción
        if interaction_type == InteractionType.EXPLANATION and additional_context:
            context_vars.update({
                'question': additional_context.get('question', ''),
                'selected_answer': additional_context.get('selected_answer', ''),
                'correct_answer': additional_context.get('correct_answer', '')
            })
        elif interaction_type == InteractionType.CONCEPT:
            context_vars['concept'] = user_message
            context_vars['related_errors'] = self._get_related_errors(student_context, user_message)
        elif interaction_type == InteractionType.STRATEGY:
            context_vars.update({
                'problem_description': user_message,
                'error_pattern': self._analyze_error_pattern(student_context),
                'avg_time': np.mean([f.get('time_sec', 30) for f in student_context.recent_failures]) if student_context.recent_failures else 30,
                'specific_difficulties': self._identify_specific_difficulties(student_context)
            })
        elif interaction_type == InteractionType.VIDEO_ANALYSIS and additional_context:
            context_vars.update({
                'video_title': additional_context.get('video_title', ''),
                'video_description': additional_context.get('video_description', ''),
                'duration': additional_context.get('duration_minutes', 0),
                'weaknesses': self._summarize_weaknesses(student_context),
                'concepts_to_reinforce': self._identify_concepts_to_reinforce(student_context)
            })
        
        # Formatear prompt
        try:
            formatted_prompt = base_template.format(**context_vars)
        except KeyError as e:
            logger.warning(f"Error formateando prompt: {e}")
            formatted_prompt = f"Ayuda al estudiante con: {user_message}"
        
        return formatted_prompt
    
    async def _get_subject_info(self, subject_id: int) -> Dict[str, Any]:
        """Obtiene información de la materia"""
        if not subject_id:
            return {'name': 'Matemáticas'}  # Default
        
        conn = await asyncpg.connect(self.database_url)
        try:
            result = await conn.fetchrow("SELECT name FROM subjects WHERE id = $1", subject_id)
            return {'name': result['name']} if result else {'name': 'Matemáticas'}
        except:
            return {'name': 'Matemáticas'}
        finally:
            await conn.close()
    
    async def _get_topic_info(self, topic_id: Optional[int]) -> Dict[str, Any]:
        """Obtiene información del tema"""
        if not topic_id:
            return {}
        
        conn = await asyncpg.connect(self.database_url)
        try:
            result = await conn.fetchrow("SELECT name, competence FROM topics WHERE id = $1", topic_id)
            return dict(result) if result else {}
        except:
            return {}
        finally:
            await conn.close()
    
    def _get_related_errors(self, context: StudyContext, concept: str) -> str:
        """Obtiene errores relacionados con un concepto"""
        related = []
        for failure in context.recent_failures:
            if concept.lower() in failure.get('topic_name', '').lower() or \
               concept.lower() in failure.get('competence', '').lower():
                related.append(f"Eligió {failure.get('selected_option')} en lugar de {failure.get('correct_answer')}")
        
        return '; '.join(related[:3]) if related else "Ninguno identificado"
    
    def _analyze_error_pattern(self, context: StudyContext) -> str:
        """Analiza patrón de errores del estudiante"""
        if not context.recent_failures:
            return "Patrón no identificado"
        
        patterns = []
        
        # Analizar tiempo
        times = [f.get('time_sec', 30) for f in context.recent_failures]
        avg_time = np.mean(times)
        if avg_time > 60:
            patterns.append("Toma demasiado tiempo")
        elif avg_time < 15:
            patterns.append("Responde muy rápido (posible falta de análisis)")
        
        # Analizar dificultad
        difficulties = [f.get('difficulty', 0) for f in context.recent_failures if f.get('difficulty')]
        if difficulties:
            if np.mean(difficulties) < -0.5:
                patterns.append("Errores en preguntas fáciles")
            elif np.mean(difficulties) > 0.5:
                patterns.append("Dificultades con preguntas complejas")
        
        # Analizar temas
        topics = [f.get('topic_name', '') for f in context.recent_failures]
        topic_counts = pd.Series(topics).value_counts()
        if len(topic_counts) > 0 and topic_counts.iloc[0] >= 3:
            patterns.append(f"Dificultades recurrentes en {topic_counts.index[0]}")
        
        return '; '.join(patterns) if patterns else "Errores variados sin patrón claro"
    
    def _identify_specific_difficulties(self, context: StudyContext) -> str:
        """Identifica dificultades específicas"""
        difficulties = []
        
        if context.recent_accuracy < 0.4:
            difficulties.append("Baja precisión general")
        
        if context.theta_estimate < -1.0:
            difficulties.append("Conceptos fundamentales por reforzar")
        
        common_topics = pd.Series([f.get('topic_name', '') for f in context.recent_failures]).value_counts()
        if len(common_topics) > 0:
            difficulties.append(f"Problemas recurrentes en {common_topics.index[0]}")
        
        return '; '.join(difficulties) if difficulties else "Dificultades generales de comprensión"
    
    async def _find_related_videos(self, context: StudyContext, 
                                 additional_context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Busca videos relacionados con el contexto del estudiante"""
        
        if not context.subject_id:
            return []
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            videos = await conn.fetch("""
                SELECT 
                    yc.youtube_id,
                    yc.title,
                    yc.url,
                    yc.duration_sec,
                    yc.description
                FROM youtube_catalog yc
                WHERE yc.subject_id = $1
                AND yc.duration_sec BETWEEN 180 AND 900  -- 3-15 minutos
                ORDER BY RANDOM()
                LIMIT 3
            """, context.subject_id)
            
            return [
                {
                    'title': v['title'],
                    'url': v['url'],
                    'duration': f"{v['duration_sec']//60}:{v['duration_sec']%60:02d}",
                    'description': v['description'][:100] + "..." if v['description'] else ""
                }
                for v in videos
            ]
            
        except Exception as e:
            logger.warning(f"Error buscando videos relacionados: {e}")
            return []
        finally:
            await conn.close()
    
    def _generate_follow_up_questions(self, interaction_type: InteractionType,
                                    context: StudyContext, response: str) -> List[str]:
        """Genera preguntas de seguimiento apropiadas"""
        
        base_questions = {
            InteractionType.EXPLANATION: [
                "¿Te queda claro por qué esta opción es correcta?",
                "¿Quieres que practiques con una pregunta similar?",
                "¿Hay algún concepto que necesites repasar más?"
            ],
            InteractionType.CONCEPT: [
                "¿Quieres ver ejemplos adicionales de este concepto?",
                "¿Te gustaría practicar ejercicios relacionados?",
                "¿Hay alguna parte que aún no te quede clara?"
            ],
            InteractionType.STRATEGY: [
                "¿Quieres que practiquemos esta estrategia con un ejemplo?",
                "¿Te parece útil este enfoque para tus dificultades?",
                "¿Necesitas estrategias adicionales para otros tipos de problemas?"
            ]
        }
        
        questions = base_questions.get(interaction_type, [
            "¿Te fue útil esta explicación?",
            "¿Hay algo más en lo que pueda ayudarte?",
            "¿Quieres continuar con este tema o pasar a otro?"
        ])
        
        return questions[:3]  # Máximo 3 preguntas
    
    def _generate_practice_suggestions(self, interaction_type: InteractionType,
                                     context: StudyContext) -> List[str]:
        """Genera sugerencias de práctica personalizadas"""
        
        suggestions = []
        
        # Basado en precisión
        if context.recent_accuracy < 0.5:
            suggestions.append("Practica con preguntas de dificultad baja a media")
            suggestions.append("Enfócate en dominar los conceptos básicos antes de avanzar")
        elif context.recent_accuracy > 0.8:
            suggestions.append("Intenta preguntas más desafiantes")
            suggestions.append("Practica bajo presión de tiempo")
        
        # Basado en nivel theta
        if context.theta_estimate < -0.5:
            suggestions.append("Repasa los fundamentos conceptuales")
            suggestions.append("Usa recursos visuales y ejemplos concretos")
        elif context.theta_estimate > 0.5:
            suggestions.append("Enfócate en problemas de aplicación compleja")
            suggestions.append("Practica análisis crítico y razonamiento avanzado")
        
        # Sugerencias específicas por tipo de interacción
        if interaction_type == InteractionType.EXPLANATION:
            suggestions.append("Resuelve problemas similares variando los números")
        elif interaction_type == InteractionType.CONCEPT:
            suggestions.append("Crea tus propios ejemplos del concepto")
            suggestions.append("Explica el concepto a alguien más")
        
        return suggestions[:4]  # Máximo 4 sugerencias
    
    def _summarize_weaknesses(self, context: StudyContext) -> str:
        """Resume las debilidades principales del estudiante"""
        weaknesses = []
        
        if context.recent_accuracy < 0.6:
            weaknesses.append("Precisión baja")
        
        if context.theta_estimate < 0:
            weaknesses.append("Habilidad por debajo del promedio")
        
        # Temas problemáticos
        if context.recent_failures:
            topics = [f.get('topic_name', '') for f in context.recent_failures]
            topic_counts = pd.Series(topics).value_counts()
            if len(topic_counts) > 0:
                weaknesses.append(f"Dificultades en {topic_counts.index[0]}")
        
        return ', '.join(weaknesses) if weaknesses else "Rendimiento general a mejorar"
    
    def _identify_concepts_to_reinforce(self, context: StudyContext) -> str:
        """Identifica conceptos que necesitan refuerzo"""
        concepts = []
        
        # Basado en competencias de errores recientes
        competences = [f.get('competence', '') for f in context.recent_failures if f.get('competence')]
        if competences:
            comp_counts = pd.Series(competences).value_counts()
            concepts.extend(comp_counts.index[:3].tolist())
        
        # Conceptos por nivel de habilidad
        if context.theta_estimate < -1.0:
            concepts.extend(["Conceptos básicos", "Operaciones fundamentales"])
        elif context.theta_estimate < 0:
            concepts.extend(["Aplicación de procedimientos", "Resolución de problemas"])
        
        return ', '.join(concepts[:5]) if concepts else "Conceptos generales"
    
    def _extract_topic_context(self, additional_context: Dict[str, Any]) -> Optional[str]:
        """Extrae contexto del tema desde contexto adicional"""
        if not additional_context:
            return None
        
        return additional_context.get('topic_name') or additional_context.get('subject_name')
    
    async def _save_ai_interaction(self, ai_response: AIResponse):
        """Guarda interacción de IA en base de datos"""
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            await conn.execute("""
                INSERT INTO ai_interactions (
                    id, student_id, interaction_type, 
                    question_context, response_content, 
                    tokens_used, response_time_ms, confidence_score,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
            ai_response.interaction_id,
            ai_response.student_id,
            ai_response.interaction_type.value,
            json.dumps(ai_response.question_context) if ai_response.question_context else None,
            ai_response.main_response,
            ai_response.tokens_used,
            ai_response.response_time_ms,
            ai_response.confidence_score,
            ai_response.created_at
            )
            
        except Exception as e:
            logger.warning(f"Error guardando interacción AI: {e}")
        finally:
            await conn.close()
    
    def _generate_dummy_response(self, interaction_type: InteractionType,
                                context: StudyContext, user_message: str) -> AIResponse:
        """Genera respuesta dummy cuando OpenAI no está disponible"""
        
        dummy_responses = {
            InteractionType.EXPLANATION: f"""
                Entiendo que necesitas ayuda con esta pregunta. Basándome en tu nivel actual 
                ({context.difficulty_level.value}), te recomiendo repasar los conceptos fundamentales 
                antes de intentar problemas más complejos. 
                
                Para mejorar tu precisión actual ({context.recent_accuracy:.1%}), enfócate en:
                1. Leer cuidadosamente cada pregunta
                2. Identificar qué te están preguntando exactamente  
                3. Revisar tu respuesta antes de confirmar
                """,
                
            InteractionType.CONCEPT: f"""
                El concepto que mencionas es fundamental para tu desarrollo en esta materia. 
                Dado tu nivel actual, te sugiero:
                
                1. Empezar con definiciones básicas
                2. Ver ejemplos concretos y sencillos
                3. Practicar con ejercicios graduales
                4. Conectar con lo que ya sabes
                """,
                
            InteractionType.STRATEGY: f"""
                Para mejorar tu estrategia de estudio, considerando tu rendimiento actual 
                ({context.recent_accuracy:.1%}), te recomiendo:
                
                1. Dedicar más tiempo a conceptos básicos
                2. Practicar problemas similares varias veces
                3. Hacer resúmenes de los procedimientos
                4. Revisar errores comunes antes de exámenes
                """
        }
        
        main_response = dummy_responses.get(interaction_type, 
                                          f"Gracias por tu pregunta: '{user_message}'. Te ayudo a resolverla paso a paso.")
        
        return AIResponse(
            interaction_id=str(uuid.uuid4()),
            interaction_type=interaction_type,
            student_id=context.student_id,
            main_response=main_response,
            follow_up_questions=["¿Te fue útil esta respuesta?", "¿Hay algo más que quieras saber?"],
            question_context=None,
            topic_context=None,
            tokens_used=0,
            response_time_ms=100.0,
            confidence_score=0.7,
            related_videos=[],
            practice_suggestions=["Practica con problemas similares", "Repasa los conceptos básicos"],
            created_at=datetime.now()
        )
    
    async def chat_with_ai(self, student_id: str, message: str, 
                         subject_id: Optional[int] = None,
                         question_context: Optional[Dict[str, Any]] = None) -> AIResponse:
        """Interfaz principal para chat con IA"""
        
        # Obtener contexto del estudiante
        context = await self.get_study_context(student_id, subject_id)
        
        # Determinar tipo de interacción basado en el mensaje
        interaction_type = self._classify_interaction_type(message)
        
        # Generar respuesta contextual
        ai_response = await self.generate_ai_response(
            interaction_type, context, message, question_context
        )
        
        logger.info(f"Chat AI completado para {student_id}: {interaction_type.value}")
        return ai_response
    
    def _classify_interaction_type(self, message: str) -> InteractionType:
        """Clasifica el tipo de interacción basado en el mensaje del usuario"""
        
        message_lower = message.lower()
        
        # Palabras clave para diferentes tipos
        if any(word in message_lower for word in ['por qué', 'porqué', 'explica', 'no entiendo', 'cómo', 'explicación']):
            return InteractionType.EXPLANATION
            
        elif any(word in message_lower for word in ['qué es', 'que es', 'concepto', 'definición', 'significa']):
            return InteractionType.CONCEPT
            
        elif any(word in message_lower for word in ['estrategia', 'cómo estudiar', 'método', 'técnica', 'mejor forma']):
            return InteractionType.STRATEGY
            
        elif any(word in message_lower for word in ['video', 'timestamp', 'minuto', 'ver en']):
            return InteractionType.VIDEO_ANALYSIS
            
        elif any(word in message_lower for word in ['similar', 'parecida', 'otro ejemplo', 'más preguntas']):
            return InteractionType.SIMILAR_QUESTION
            
        else:
            return InteractionType.EXPLANATION  # Default


# Ejemplo de uso y testing
async def main():
    """Función principal para testing del sistema AI"""
    
    database_url = "postgresql://gameplay:gameplay123@localhost:5433/gameplay_db" 
    openai_api_key = None  # Configurar si está disponible
    
    ai_system = AIStudySystem(database_url, openai_api_key)
    
    try:
        # Test: Chat con IA
        student_id = "test_student_001"
        
        print("Obteniendo contexto del estudiante...")
        context = await ai_system.get_study_context(student_id, subject_id=1)
        
        print(f"Contexto obtenido:")
        print(f"- Theta: {context.theta_estimate:.3f}")
        print(f"- Precisión reciente: {context.recent_accuracy:.1%}")
        print(f"- Nivel: {context.difficulty_level.value}")
        print(f"- Errores recientes: {len(context.recent_failures)}")
        
        # Test de chat
        user_message = "No entiendo por qué mi respuesta está mal en esta pregunta de matemáticas"
        
        print(f"\nPregunta del usuario: {user_message}")
        
        ai_response = await ai_system.chat_with_ai(
            student_id, 
            user_message, 
            subject_id=1,
            question_context={
                'question': 'Resuelve: 2x + 5 = 11',
                'selected_answer': 'C',
                'correct_answer': 'B'
            }
        )
        
        print(f"\nRespuesta IA ({ai_response.interaction_type.value}):")
        print(f"{ai_response.main_response}")
        print(f"\nPreguntas de seguimiento:")
        for q in ai_response.follow_up_questions:
            print(f"- {q}")
        
        print(f"\nRecursos relacionados: {len(ai_response.related_videos)} videos")
        print(f"Sugerencias de práctica: {len(ai_response.practice_suggestions)}")
        
    except Exception as e:
        logger.error(f"Error en testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())