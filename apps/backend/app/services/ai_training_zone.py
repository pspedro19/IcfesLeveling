#!/usr/bin/env python3
"""
AI Training Zone Service - Enhanced Learning Support

Comprehensive AI-powered training zone that provides:
- Intelligent question explanations
- Adaptive hint generation
- Personalized tutoring responses
- AI-generated practice questions
- Learning path recommendations
- Progress analysis and feedback
- Natural language concept explanations

Author: Claude Code Assistant
Date: 2024
"""

import asyncio
import asyncpg
import openai
import json
import uuid
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import hashlib
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InteractionType(Enum):
    """Types of AI interactions"""
    EXPLANATION = "explanation"
    HINT = "hint"
    CONCEPT = "concept"
    STRATEGY = "strategy"
    PRACTICE_GENERATION = "practice_generation"
    LEARNING_PATH = "learning_path"
    PROGRESS_ANALYSIS = "progress_analysis"
    CHAT = "chat"

class DifficultyLevel(Enum):
    """Difficulty levels for adaptive learning"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

@dataclass
class StudentContext:
    """Comprehensive student context for AI personalization"""
    student_id: str
    subject_id: Optional[int]
    topic_id: Optional[int]
    
    # Performance metrics
    recent_accuracy: float
    avg_response_time: float
    difficulty_preference: DifficultyLevel
    theta_estimate: float
    
    # Learning patterns
    problem_areas: List[str]
    strong_areas: List[str]
    common_mistakes: List[str]
    learning_style_preferences: Dict[str, Any]
    
    # Session context
    current_session_performance: Dict[str, Any]
    recent_topics_studied: List[str]
    time_of_day: str
    session_duration: int

@dataclass
class AIResponse:
    """Structured AI response with metadata"""
    interaction_id: str
    interaction_type: InteractionType
    student_id: str
    
    # Main content
    response_text: str
    confidence_score: float
    
    # Interactive elements
    follow_up_questions: List[str]
    suggested_actions: List[str]
    related_resources: List[Dict[str, Any]]
    
    # Educational metadata
    learning_objectives: List[str]
    difficulty_level: str
    estimated_time_needed: int
    
    # Technical metadata
    tokens_used: int
    response_time_ms: float
    cache_key: Optional[str]
    created_at: datetime

class AITrainingZoneService:
    """Comprehensive AI Training Zone Service"""
    
    def __init__(self, database_url: str, redis_url: str, openai_api_key: Optional[str] = None):
        self.database_url = database_url
        self.redis_client = redis.from_url(redis_url)
        self.openai_client = openai.OpenAI(api_key=openai_api_key) if openai_api_key else None
        
        # AI Prompts for different interaction types
        self.prompts = {
            InteractionType.EXPLANATION: """
                Eres un tutor experto especializado en preparación ICFES. Un estudiante necesita una explicación sobre esta pregunta:
                
                PREGUNTA: {question_text}
                RESPUESTA DEL ESTUDIANTE: {student_answer}
                RESPUESTA CORRECTA: {correct_answer}
                
                CONTEXTO DEL ESTUDIANTE:
                - Nivel de habilidad: {difficulty_level}
                - Precisión reciente: {recent_accuracy:.1%}
                - Áreas problemáticas: {problem_areas}
                - Tiempo promedio de respuesta: {avg_time:.1f}s
                
                Proporciona una explicación que:
                1. Analice por qué la respuesta del estudiante está incorrecta (si aplica)
                2. Explique paso a paso la solución correcta
                3. Identifique el concepto clave que debe reforzar
                4. Proporcione un truco o estrategia para recordar
                5. Sugiera una pregunta similar para practicar
                
                Adapta tu lenguaje a su nivel y sé motivador. Usa ejemplos concretos y analogías útiles.
            """,
            
            InteractionType.HINT: """
                Un estudiante está resolviendo esta pregunta ICFES y necesita una pista:
                
                PREGUNTA: {question_text}
                OPCIONES: A) {option_a} B) {option_b} C) {option_c} D) {option_d}
                
                CONTEXTO:
                - Intento número: {attempt_number}
                - Nivel del estudiante: {difficulty_level}
                - Tiempo transcurrido: {time_spent}s
                
                Proporciona una pista que:
                - Sea apropiada para el intento número {attempt_number}
                - No revele directamente la respuesta
                - Guíe el razonamiento hacia la solución
                - Sea específica y útil
                
                Si es el primer intento, da una pista general sobre el enfoque.
                Si es el segundo intento, sé más específico sobre el método.
                Si es el tercer intento, proporciona una guía muy detallada.
            """,
            
            InteractionType.CONCEPT: """
                Un estudiante necesita comprensión conceptual sobre: {concept_name}
                
                CONTEXTO EDUCATIVO:
                - Materia: {subject_name}
                - Tema: {topic_name}
                - Nivel del estudiante: {difficulty_level}
                - Errores previos relacionados: {related_errors}
                
                Proporciona una explicación conceptual que:
                1. Defina el concepto claramente y sin jerga
                2. Explique por qué es importante para el ICFES
                3. Use ejemplos concretos de la vida cotidiana
                4. Conecte con conceptos que ya domina
                5. Incluya una analogía memorable
                6. Anticipe y aclare malentendidos comunes
                
                Estructura tu respuesta de manera lógica y progresiva.
            """,
            
            InteractionType.STRATEGY: """
                Un estudiante con nivel {difficulty_level} necesita estrategias para mejorar en:
                PROBLEMA ESPECÍFICO: {problem_description}
                
                ANÁLISIS DE RENDIMIENTO:
                - Patrón de errores: {error_pattern}
                - Tiempo promedio: {avg_time}s (óptimo: 90s)
                - Precisión actual: {accuracy:.1%}
                - Dificultades principales: {main_difficulties}
                
                Proporciona estrategias específicas que incluyan:
                1. Técnicas de análisis de preguntas
                2. Métodos para evitar errores comunes
                3. Estrategias de manejo del tiempo
                4. Técnicas de verificación de respuestas
                5. Plan de práctica estructurado
                6. Recursos específicos recomendados
                
                Sé muy práctico y específico. Incluye ejemplos de aplicación inmediata.
            """,
            
            InteractionType.CHAT: """
                Eres un tutor de ICFES amigable y experto. Un estudiante te dice:
                "{student_message}"
                
                CONTEXTO DEL ESTUDIANTE:
                - Rendimiento reciente: {recent_accuracy:.1%} de precisión
                - Nivel: {difficulty_level}
                - Áreas problemáticas: {problem_areas}
                - Sesión actual: {session_context}
                
                Responde de manera:
                - Personalizada a su nivel y situación
                - Motivadora y constructiva
                - Específica y accionable
                - Apropiada para preparación ICFES
                
                Si menciona conceptos específicos, explícalos claramente.
                Si expresa frustración, sé empático y motivador.
                Si pide ayuda específica, proporciona pasos concretos.
            """
        }
        
        # Context cache
        self._context_cache = {}
        self._cache_ttl = 600  # 10 minutes
    
    async def get_student_context(self, student_id: str, subject_id: Optional[int] = None) -> StudentContext:
        """Get comprehensive student context for AI personalization"""
        
        cache_key = f"student_context:{student_id}:{subject_id}"
        
        # Check cache first
        if cache_key in self._context_cache:
            cached_context, timestamp = self._context_cache[cache_key]
            if (datetime.now() - timestamp).seconds < self._cache_ttl:
                return cached_context
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Get recent performance data
            performance_data = await conn.fetch("""
                SELECT 
                    qr.is_correct,
                    qr.time_sec,
                    qr.created_at,
                    q.irt_b as difficulty,
                    q.subject_id,
                    s.name as subject_name,
                    t.name as topic_name,
                    q.statement as question_text
                FROM question_responses qr
                JOIN questions q ON qr.question_id = q.id
                JOIN subjects s ON q.subject_id = s.id
                LEFT JOIN topics t ON q.topic_id = t.id
                WHERE qr.user_id = $1
                AND ($2::int IS NULL OR q.subject_id = $2)
                AND qr.created_at >= NOW() - INTERVAL '30 days'
                ORDER BY qr.created_at DESC
                LIMIT 100
            """, student_id, subject_id)
            
            # Calculate performance metrics
            if performance_data:
                correct_answers = [r for r in performance_data if r['is_correct']]
                recent_accuracy = len(correct_answers) / len(performance_data)
                avg_response_time = sum(r['time_sec'] for r in performance_data) / len(performance_data)
                
                # Calculate theta estimate (simplified IRT)
                difficulties = [r['difficulty'] for r in performance_data if r['difficulty']]
                if difficulties:
                    theta_estimate = np.mean(difficulties) + (recent_accuracy - 0.5) * 2
                else:
                    theta_estimate = (recent_accuracy - 0.5) * 2
            else:
                recent_accuracy = 0.5
                avg_response_time = 60.0
                theta_estimate = 0.0
            
            # Determine difficulty level
            if recent_accuracy < 0.5 or theta_estimate < -1.0:
                difficulty_level = DifficultyLevel.BEGINNER
            elif recent_accuracy > 0.8 and theta_estimate > 0.5:
                difficulty_level = DifficultyLevel.ADVANCED
            else:
                difficulty_level = DifficultyLevel.INTERMEDIATE
            
            # Analyze problem and strong areas
            topic_performance = {}
            for record in performance_data:
                topic = record['topic_name'] or 'General'
                if topic not in topic_performance:
                    topic_performance[topic] = {'correct': 0, 'total': 0}
                topic_performance[topic]['total'] += 1
                if record['is_correct']:
                    topic_performance[topic]['correct'] += 1
            
            problem_areas = []
            strong_areas = []
            for topic, perf in topic_performance.items():
                if perf['total'] >= 3:  # Minimum attempts for significance
                    accuracy = perf['correct'] / perf['total']
                    if accuracy < 0.6:
                        problem_areas.append(topic)
                    elif accuracy > 0.8:
                        strong_areas.append(topic)
            
            # Identify common mistakes (simplified)
            common_mistakes = []
            recent_incorrect = [r for r in performance_data[:20] if not r['is_correct']]
            if len(recent_incorrect) > 5:
                common_mistakes.append("Errores en preguntas de tiempo limitado")
            if avg_response_time > 120:
                common_mistakes.append("Tiempo excesivo de análisis")
            
            # Create context
            context = StudentContext(
                student_id=student_id,
                subject_id=subject_id,
                topic_id=None,  # Will be set per interaction
                recent_accuracy=recent_accuracy,
                avg_response_time=avg_response_time,
                difficulty_preference=difficulty_level,
                theta_estimate=theta_estimate,
                problem_areas=problem_areas,
                strong_areas=strong_areas,
                common_mistakes=common_mistakes,
                learning_style_preferences={
                    'prefers_visual': theta_estimate < 0,
                    'needs_repetition': recent_accuracy < 0.6,
                    'ready_for_challenges': recent_accuracy > 0.8
                },
                current_session_performance={
                    'questions_answered': 0,
                    'session_accuracy': 1.0,
                    'session_start_time': datetime.now()
                },
                recent_topics_studied=list(set([r['topic_name'] for r in performance_data[:10] if r['topic_name']])),
                time_of_day=datetime.now().strftime("%H:%M"),
                session_duration=0
            )
            
            # Cache the context
            self._context_cache[cache_key] = (context, datetime.now())
            
            return context
            
        finally:
            await conn.close()
    
    async def generate_ai_response(self, interaction_type: InteractionType, 
                                 context: StudentContext, 
                                 prompt_variables: Dict[str, Any]) -> AIResponse:
        """Generate AI response using OpenAI or fallback logic"""
        
        start_time = datetime.now()
        interaction_id = str(uuid.uuid4())
        
        # Prepare the prompt
        prompt_template = self.prompts.get(interaction_type, self.prompts[InteractionType.CHAT])
        
        # Add context variables to prompt variables
        context_vars = {
            'difficulty_level': context.difficulty_preference.value,
            'recent_accuracy': context.recent_accuracy,
            'problem_areas': ', '.join(context.problem_areas) or 'Ninguna identificada',
            'strong_areas': ', '.join(context.strong_areas) or 'Ninguna identificada',
            'avg_time': context.avg_response_time,
            'session_context': f"Pregunta #{context.current_session_performance['questions_answered'] + 1}"
        }
        context_vars.update(prompt_variables)
        
        try:
            full_prompt = prompt_template.format(**context_vars)
        except KeyError as e:
            logger.warning(f"Missing variable in prompt: {e}")
            full_prompt = f"Ayuda al estudiante con su consulta sobre ICFES: {prompt_variables.get('student_message', 'consulta general')}"
        
        # Generate response
        if self.openai_client:
            try:
                response = await self.openai_client.chat.completions.acreate(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Eres un tutor experto en preparación ICFES, especializado en educación secundaria colombiana."},
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=800,
                    temperature=0.7
                )
                
                response_text = response.choices[0].message.content
                tokens_used = response.usage.total_tokens
                confidence_score = 0.9
                
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                response_text = self._generate_fallback_response(interaction_type, context, prompt_variables)
                tokens_used = 0
                confidence_score = 0.7
        else:
            response_text = self._generate_fallback_response(interaction_type, context, prompt_variables)
            tokens_used = 0
            confidence_score = 0.7
        
        # Generate follow-up questions based on interaction type
        follow_up_questions = self._generate_follow_up_questions(interaction_type, context)
        
        # Generate suggested actions
        suggested_actions = self._generate_suggested_actions(interaction_type, context)
        
        # Find related resources
        related_resources = await self._find_related_resources(context, prompt_variables)
        
        # Generate learning objectives
        learning_objectives = self._generate_learning_objectives(interaction_type, prompt_variables)
        
        # Calculate response time
        response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Create AI response
        ai_response = AIResponse(
            interaction_id=interaction_id,
            interaction_type=interaction_type,
            student_id=context.student_id,
            response_text=response_text,
            confidence_score=confidence_score,
            follow_up_questions=follow_up_questions,
            suggested_actions=suggested_actions,
            related_resources=related_resources,
            learning_objectives=learning_objectives,
            difficulty_level=context.difficulty_preference.value,
            estimated_time_needed=self._estimate_time_needed(interaction_type, response_text),
            tokens_used=tokens_used,
            response_time_ms=response_time_ms,
            cache_key=None,
            created_at=datetime.now()
        )
        
        # Log the interaction
        await self._log_ai_interaction(ai_response)
        
        return ai_response
    
    def _generate_fallback_response(self, interaction_type: InteractionType, 
                                  context: StudentContext, 
                                  prompt_variables: Dict[str, Any]) -> str:
        """Generate fallback response when OpenAI is not available"""
        
        fallback_responses = {
            InteractionType.EXPLANATION: f"""
                Entiendo que necesitas una explicación detallada. Basándome en tu nivel actual 
                ({context.difficulty_preference.value}) y tu precisión reciente ({context.recent_accuracy:.1%}), 
                te recomiendo:
                
                1. **Análisis de la pregunta**: Lee cuidadosamente qué te están preguntando
                2. **Identificación de conceptos**: Reconoce los temas principales involucrados
                3. **Aplicación paso a paso**: Sigue un método sistemático
                4. **Verificación**: Revisa tu respuesta antes de confirmar
                
                Para mejorar en este tipo de preguntas, practica ejercicios similares y 
                asegúrate de entender los conceptos fundamentales.
            """,
            
            InteractionType.HINT: f"""
                Aquí tienes una pista personalizada para tu nivel ({context.difficulty_preference.value}):
                
                🔍 **Enfoque sugerido**: Identifica primero qué información te dan y qué te preguntan.
                
                📝 **Estrategia**: {
                    "Empieza con los conceptos más básicos y construye la solución paso a paso." 
                    if context.difficulty_preference == DifficultyLevel.BEGINNER else
                    "Aplica las fórmulas o métodos que conoces, verificando cada paso." 
                    if context.difficulty_preference == DifficultyLevel.INTERMEDIATE else
                    "Considera múltiples enfoques y elige el más eficiente."
                }
                
                ⏰ **Gestión del tiempo**: Dedica máximo 90 segundos a analizar antes de responder.
            """,
            
            InteractionType.CONCEPT: f"""
                Te explico este concepto adaptado a tu nivel ({context.difficulty_preference.value}):
                
                🎯 **Concepto clave**: {prompt_variables.get('concept_name', 'El tema que consultas')}
                
                📚 **Definición simple**: Este concepto es fundamental para entender cómo resolver 
                preguntas relacionadas en el ICFES.
                
                🔗 **Conexión con tus fortalezas**: Puedes relacionarlo con {', '.join(context.strong_areas[:2]) if context.strong_areas else 'conceptos que ya dominas'}.
                
                💡 **Tip para recordar**: Crea una analogía personal que te ayude a recordar este concepto.
                
                📖 **Para profundizar**: Practica ejercicios que combinen este concepto con otros temas.
            """,
            
            InteractionType.STRATEGY: f"""
                Estrategias personalizadas para tu nivel ({context.difficulty_preference.value}):
                
                🎯 **Estrategia principal**: 
                {"Enfócate en dominar los fundamentos antes de avanzar" if context.recent_accuracy < 0.6 else
                 "Practica variedad de ejercicios para consolidar conocimientos" if context.recent_accuracy < 0.8 else
                 "Desafíate con problemas complejos y mejora tu velocidad"}
                
                ⏱️ **Manejo del tiempo**: 
                {"Tómate el tiempo necesario para entender cada pregunta" if context.avg_response_time < 60 else
                 "Practica resolución rápida para mejorar eficiencia"}
                
                📈 **Plan de mejora**:
                1. Identifica patrones en tus errores
                2. Practica 15-20 minutos diarios
                3. Revisa explicaciones de respuestas incorrectas
                4. Realiza simulacros semanales
            """,
            
            InteractionType.CHAT: f"""
                ¡Hola! Como tu tutor de ICFES, estoy aquí para ayudarte. 
                
                Basándome en tu rendimiento reciente ({context.recent_accuracy:.1%} de precisión), 
                veo que {"tienes un buen nivel y puedes enfocarte en perfeccionar detalles" if context.recent_accuracy > 0.7 else
                        "hay oportunidades de mejora que podemos trabajar juntos"}.
                
                {f"Noto que has tenido algunas dificultades en {', '.join(context.problem_areas[:2])}" if context.problem_areas else
                 f"Tus fortalezas en {', '.join(context.strong_areas[:2])} son excelentes" if context.strong_areas else
                 "Estás en un buen camino de aprendizaje"}.
                
                ¿En qué específicamente te gustaría que te ayude hoy?
            """
        }
        
        return fallback_responses.get(interaction_type, fallback_responses[InteractionType.CHAT])
    
    def _generate_follow_up_questions(self, interaction_type: InteractionType, 
                                    context: StudentContext) -> List[str]:
        """Generate contextual follow-up questions"""
        
        base_questions = {
            InteractionType.EXPLANATION: [
                "¿Te queda claro el procedimiento explicado?",
                "¿Quieres que practiquemos con una pregunta similar?",
                "¿Hay algún paso específico que necesites que clarifique?"
            ],
            InteractionType.HINT: [
                "¿Esta pista te ayuda a ver el camino correcto?",
                "¿Necesitas una pista más específica?",
                "¿Quieres intentar resolver la pregunta ahora?"
            ],
            InteractionType.CONCEPT: [
                "¿Quieres ver ejemplos prácticos de este concepto?",
                "¿Te gustaría conocer cómo se aplica en preguntas ICFES?",
                "¿Hay conceptos relacionados que te interesen?"
            ],
            InteractionType.STRATEGY: [
                "¿Quieres que practiquemos esta estrategia con un ejemplo?",
                "¿Te parece útil este enfoque para tus dificultades?",
                "¿Necesitas estrategias para otros tipos de problemas?"
            ],
            InteractionType.CHAT: [
                "¿Te fue útil esta respuesta?",
                "¿Hay algo más específico en lo que pueda ayudarte?",
                "¿Quieres que profundicemos en algún tema?"
            ]
        }
        
        questions = base_questions.get(interaction_type, base_questions[InteractionType.CHAT])
        
        # Personalize based on student context
        if context.recent_accuracy < 0.5:
            questions.append("¿Te gustaría repasar conceptos fundamentales?")
        elif context.recent_accuracy > 0.8:
            questions.append("¿Estás listo para un desafío más avanzado?")
        
        return questions[:3]  # Limit to 3 questions
    
    def _generate_suggested_actions(self, interaction_type: InteractionType, 
                                  context: StudentContext) -> List[str]:
        """Generate personalized suggested actions"""
        
        actions = []
        
        # Base actions by interaction type
        if interaction_type == InteractionType.EXPLANATION:
            actions.append("Practica con preguntas similares")
            actions.append("Revisa conceptos relacionados")
        elif interaction_type == InteractionType.HINT:
            actions.append("Intenta resolver la pregunta con esta guía")
            actions.append("Aplica esta estrategia en futuras preguntas")
        elif interaction_type == InteractionType.CONCEPT:
            actions.append("Busca ejemplos adicionales del concepto")
            actions.append("Conecta este concepto con otros temas")
        elif interaction_type == InteractionType.STRATEGY:
            actions.append("Implementa esta estrategia en tu próxima sesión")
            actions.append("Cronometra tu aplicación de la estrategia")
        
        # Personalize based on performance
        if context.recent_accuracy < 0.6:
            actions.append("Dedica tiempo extra a conceptos fundamentales")
            actions.append("Practica ejercicios de dificultad básica")
        elif context.recent_accuracy > 0.8:
            actions.append("Busca ejercicios más desafiantes")
            actions.append("Practica bajo presión de tiempo")
        
        if context.avg_response_time > 120:
            actions.append("Practica estrategias de lectura rápida")
        
        return actions[:4]  # Limit to 4 actions
    
    async def _find_related_resources(self, context: StudentContext, 
                                    prompt_variables: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find related educational resources"""
        
        if not context.subject_id:
            return []
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Find related videos
            videos = await conn.fetch("""
                SELECT title, url, duration_sec, description
                FROM youtube_catalog 
                WHERE subject_id = $1
                AND duration_sec BETWEEN 180 AND 900
                ORDER BY RANDOM()
                LIMIT 3
            """, context.subject_id)
            
            resources = []
            for video in videos:
                resources.append({
                    "type": "video",
                    "title": video['title'],
                    "url": video['url'],
                    "duration": f"{video['duration_sec']//60}:{video['duration_sec']%60:02d}",
                    "description": video['description'][:100] + "..." if video['description'] else ""
                })
            
            # Add practice resources based on problem areas
            if context.problem_areas:
                resources.append({
                    "type": "practice",
                    "title": f"Ejercicios de refuerzo: {context.problem_areas[0]}",
                    "url": f"/practice?topic={context.problem_areas[0]}",
                    "description": "Ejercicios específicos para mejorar en esta área"
                })
            
            return resources
            
        except Exception as e:
            logger.warning(f"Error finding related resources: {e}")
            return []
        finally:
            await conn.close()
    
    def _generate_learning_objectives(self, interaction_type: InteractionType, 
                                    prompt_variables: Dict[str, Any]) -> List[str]:
        """Generate specific learning objectives for the interaction"""
        
        objectives_map = {
            InteractionType.EXPLANATION: [
                "Comprender por qué la respuesta es correcta",
                "Identificar el método de resolución apropiado",
                "Aplicar el conocimiento en preguntas similares"
            ],
            InteractionType.HINT: [
                "Desarrollar estrategias de análisis de preguntas",
                "Mejorar el razonamiento paso a paso",
                "Ganar confianza en la resolución autónoma"
            ],
            InteractionType.CONCEPT: [
                "Dominar la definición y aplicación del concepto",
                "Conectar el concepto con conocimientos previos",
                "Reconocer el concepto en diferentes contextos"
            ],
            InteractionType.STRATEGY: [
                "Implementar estrategias efectivas de estudio",
                "Mejorar la gestión del tiempo en exámenes",
                "Desarrollar técnicas de autoevaluación"
            ],
            InteractionType.CHAT: [
                "Aclarar dudas específicas sobre el tema",
                "Reforzar la motivación y confianza",
                "Establecer próximos pasos de aprendizaje"
            ]
        }
        
        return objectives_map.get(interaction_type, objectives_map[InteractionType.CHAT])
    
    def _estimate_time_needed(self, interaction_type: InteractionType, response_text: str) -> int:
        """Estimate time needed to process the AI response (in minutes)"""
        
        base_times = {
            InteractionType.EXPLANATION: 5,
            InteractionType.HINT: 2,
            InteractionType.CONCEPT: 8,
            InteractionType.STRATEGY: 10,
            InteractionType.CHAT: 3
        }
        
        base_time = base_times.get(interaction_type, 5)
        
        # Adjust based on response length
        word_count = len(response_text.split())
        if word_count > 200:
            base_time += 2
        elif word_count > 400:
            base_time += 5
        
        return base_time
    
    async def _log_ai_interaction(self, ai_response: AIResponse):
        """Log AI interaction to database"""
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            await conn.execute("""
                INSERT INTO ai_interactions (
                    id, student_id, interaction_type, response_content,
                    confidence_score, tokens_used, response_time_ms, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, 
            ai_response.interaction_id,
            ai_response.student_id,
            ai_response.interaction_type.value,
            ai_response.response_text,
            ai_response.confidence_score,
            ai_response.tokens_used,
            ai_response.response_time_ms,
            ai_response.created_at
            )
            
        except Exception as e:
            logger.warning(f"Error logging AI interaction: {e}")
        finally:
            await conn.close()
    
    # Public interface methods
    
    async def explain_question(self, student_id: str, question_id: str, 
                             student_answer: str, subject_id: Optional[int] = None) -> AIResponse:
        """Generate comprehensive question explanation"""
        
        context = await self.get_student_context(student_id, subject_id)
        
        # Get question details
        conn = await asyncpg.connect(self.database_url)
        try:
            question = await conn.fetchrow("""
                SELECT statement, option_a, option_b, option_c, option_d, 
                       correct_answer, explanation
                FROM questions WHERE id = $1
            """, question_id)
            
            if not question:
                raise ValueError("Question not found")
            
        finally:
            await conn.close()
        
        prompt_variables = {
            'question_text': question['statement'],
            'student_answer': student_answer,
            'correct_answer': question['correct_answer'],
            'option_a': question['option_a'],
            'option_b': question['option_b'],
            'option_c': question['option_c'],
            'option_d': question['option_d'],
            'existing_explanation': question['explanation'] or ""
        }
        
        return await self.generate_ai_response(InteractionType.EXPLANATION, context, prompt_variables)
    
    async def generate_hint(self, student_id: str, question_id: str, 
                          attempt_number: int = 1, time_spent: int = 0,
                          subject_id: Optional[int] = None) -> AIResponse:
        """Generate intelligent, progressive hints"""
        
        context = await self.get_student_context(student_id, subject_id)
        
        # Get question details
        conn = await asyncpg.connect(self.database_url)
        try:
            question = await conn.fetchrow("""
                SELECT statement, option_a, option_b, option_c, option_d, 
                       correct_answer, hint
                FROM questions WHERE id = $1
            """, question_id)
            
            if not question:
                raise ValueError("Question not found")
            
        finally:
            await conn.close()
        
        prompt_variables = {
            'question_text': question['statement'],
            'option_a': question['option_a'],
            'option_b': question['option_b'],
            'option_c': question['option_c'],
            'option_d': question['option_d'],
            'attempt_number': attempt_number,
            'time_spent': time_spent,
            'existing_hint': question['hint'] or ""
        }
        
        return await self.generate_ai_response(InteractionType.HINT, context, prompt_variables)
    
    async def explain_concept(self, student_id: str, concept_name: str, 
                            subject_id: Optional[int] = None, 
                            topic_name: Optional[str] = None) -> AIResponse:
        """Generate comprehensive concept explanation"""
        
        context = await self.get_student_context(student_id, subject_id)
        
        # Get subject and topic names
        conn = await asyncpg.connect(self.database_url)
        try:
            subject_name = "Materia"
            if subject_id:
                result = await conn.fetchrow("SELECT name FROM subjects WHERE id = $1", subject_id)
                if result:
                    subject_name = result['name']
            
        finally:
            await conn.close()
        
        prompt_variables = {
            'concept_name': concept_name,
            'subject_name': subject_name,
            'topic_name': topic_name or "General",
            'related_errors': ', '.join([f for f in context.problem_areas if concept_name.lower() in f.lower()][:3])
        }
        
        return await self.generate_ai_response(InteractionType.CONCEPT, context, prompt_variables)
    
    async def provide_strategy_advice(self, student_id: str, problem_description: str,
                                    subject_id: Optional[int] = None) -> AIResponse:
        """Provide personalized strategy advice"""
        
        context = await self.get_student_context(student_id, subject_id)
        
        # Analyze error patterns
        error_patterns = []
        if context.avg_response_time > 120:
            error_patterns.append("Tiempo excesivo de análisis")
        if context.recent_accuracy < 0.6:
            error_patterns.append("Errores en conceptos fundamentales")
        if len(context.problem_areas) > 3:
            error_patterns.append("Dificultades dispersas en múltiples temas")
        
        prompt_variables = {
            'problem_description': problem_description,
            'error_pattern': '; '.join(error_patterns) if error_patterns else "Patrón no identificado",
            'accuracy': context.recent_accuracy,
            'main_difficulties': ', '.join(context.problem_areas[:3]) or "Ninguna específica identificada"
        }
        
        return await self.generate_ai_response(InteractionType.STRATEGY, context, prompt_variables)
    
    async def chat_with_tutor(self, student_id: str, message: str,
                            subject_id: Optional[int] = None) -> AIResponse:
        """General AI tutoring chat interface"""
        
        context = await self.get_student_context(student_id, subject_id)
        
        prompt_variables = {
            'student_message': message
        }
        
        return await self.generate_ai_response(InteractionType.CHAT, context, prompt_variables)

# Example usage and testing
async def main():
    """Test the AI Training Zone Service"""
    import os

    # Use environment variables for all credentials
    database_url = os.getenv("DATABASE_URL", "")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    openai_api_key = os.getenv("OPENAI_API_KEY")  # Set if available

    if not database_url:
        logger.error("DATABASE_URL environment variable is required")
        return

    service = AITrainingZoneService(database_url, redis_url, openai_api_key)
    
    try:
        logger.info("Testing AI Training Zone Service...")

        # Test chat interaction
        chat_response = await service.chat_with_tutor(
            "test_student_001", 
            "Tengo dificultades con las preguntas de matemáticas, especialmente álgebra"
        )
        
        logger.info(f"Chat Response: {chat_response.response_text[:200]}...")
        logger.debug(f"Follow-up questions: {chat_response.follow_up_questions}")
        logger.debug(f"Suggested actions: {chat_response.suggested_actions}")
        
        # Test concept explanation
        concept_response = await service.explain_concept(
            "test_student_001",
            "Ecuaciones de primer grado",
            subject_id=1
        )
        
        logger.info(f"Concept explanation: {concept_response.response_text[:200]}...")
        logger.debug(f"Learning objectives: {concept_response.learning_objectives}")
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())