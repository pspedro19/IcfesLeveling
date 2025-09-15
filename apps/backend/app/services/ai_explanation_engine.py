"""
AI Explanation Engine - Advanced intelligent tutoring system for failed questions
Provides contextual hints, step-by-step solutions, and personalized explanations.
"""

import openai
from typing import Dict, Any, List, Optional, Tuple
import json
import logging
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import math
import re

from ..core.config import settings
from .cache_service import cache_service
from .llm_service import llm_service
from ..models.user import User
from ..models.question import Question
from ..models.ai_explanation import AIExplanation

logger = logging.getLogger(__name__)

class StudentLevelAnalyzer:
    """Analyzes student level and learning patterns for personalized explanations"""
    
    @staticmethod
    def analyze_student_level(user: User, db: Session) -> Dict[str, Any]:
        """Analyze student's academic level and learning patterns"""
        
        # Get user's recent performance
        recent_answers = db.query(AIExplanation).filter(
            and_(
                AIExplanation.user_id == user.id,
                AIExplanation.created_at > datetime.now() - timedelta(days=30)
            )
        ).limit(100).all()
        
        # Calculate basic metrics
        total_questions = len(recent_answers)
        level_indicators = {
            "user_level": user.level or 1,
            "total_questions_attempted": total_questions,
            "experience": user.experience or 0,
            "estimated_academic_level": "intermediate"
        }
        
        # Determine academic level based on user level and performance
        if user.level <= 5:
            level_indicators["estimated_academic_level"] = "beginner"
            level_indicators["explanation_complexity"] = "simple"
            level_indicators["vocabulary_level"] = "basic"
        elif user.level <= 15:
            level_indicators["estimated_academic_level"] = "intermediate"
            level_indicators["explanation_complexity"] = "moderate"
            level_indicators["vocabulary_level"] = "standard"
        else:
            level_indicators["estimated_academic_level"] = "advanced"
            level_indicators["explanation_complexity"] = "detailed"
            level_indicators["vocabulary_level"] = "advanced"
        
        # Add learning style preferences (mock implementation)
        level_indicators["preferred_learning_style"] = "visual_textual"  # Could be enhanced with actual tracking
        level_indicators["attention_span"] = "medium"  # Could be calculated from response times
        
        return level_indicators

class ConceptMapper:
    """Maps questions to related concepts and resources"""
    
    @staticmethod
    def get_related_concepts(question: Question) -> List[Dict[str, Any]]:
        """Extract related concepts from question metadata"""
        concepts = []
        
        # Add main concept from competencia
        if question.competencia:
            concepts.append({
                "type": "competency",
                "name": question.competencia,
                "relevance": "high"
            })
        
        # Add component concept
        if question.componente:
            concepts.append({
                "type": "component", 
                "name": question.componente,
                "relevance": "high"
            })
        
        # Add cognitive process
        if question.proceso_cognitivo:
            concepts.append({
                "type": "cognitive_process",
                "name": question.proceso_cognitivo,
                "relevance": "medium"
            })
        
        return concepts
    
    @staticmethod
    def get_related_resources(question: Question, student_level: str) -> List[Dict[str, Any]]:
        """Generate related learning resources based on question and student level"""
        resources = []
        
        # Study materials based on subject
        if question.subject:
            if student_level == "beginner":
                resources.append({
                    "type": "video",
                    "title": f"Conceptos básicos de {question.subject.name if hasattr(question.subject, 'name') else 'la materia'}",
                    "description": "Video explicativo con fundamentos",
                    "estimated_time": "10-15 minutos"
                })
                resources.append({
                    "type": "practice",
                    "title": "Ejercicios de práctica básicos",
                    "description": "Problemas similares de nivel principiante",
                    "estimated_time": "15-20 minutos"
                })
            elif student_level == "intermediate":
                resources.append({
                    "type": "article",
                    "title": "Guía completa del tema",
                    "description": "Artículo detallado con ejemplos",
                    "estimated_time": "20-25 minutos"
                })
                resources.append({
                    "type": "practice",
                    "title": "Ejercicios progresivos",
                    "description": "Problemas de dificultad creciente",
                    "estimated_time": "25-30 minutos"
                })
            else:  # advanced
                resources.append({
                    "type": "research",
                    "title": "Análisis avanzado del tema",
                    "description": "Material de profundización",
                    "estimated_time": "30-40 minutos"
                })
                resources.append({
                    "type": "challenge",
                    "title": "Problemas desafiantes",
                    "description": "Ejercicios de alta complejidad",
                    "estimated_time": "40-50 minutos"
                })
        
        return resources

class IntelligentHintSystem:
    """Provides progressive, contextual hints based on student needs"""
    
    @staticmethod
    def generate_progressive_hints(question: Question, user_answer: str, attempt_number: int, student_level: str) -> List[str]:
        """Generate progressive hints based on attempt number and student level"""
        hints = []
        
        # Use existing question hints if available
        if question.pista_1 and attempt_number >= 1:
            hints.append(question.pista_1)
        if question.pista_2 and attempt_number >= 2:
            hints.append(question.pista_2)
        if question.pista_3 and attempt_number >= 3:
            hints.append(question.pista_3)
        
        # Generate additional contextual hints based on student level
        if not hints or len(hints) < attempt_number:
            if student_level == "beginner":
                hints.extend([
                    "Comienza identificando los datos que te proporciona el problema",
                    "¿Qué concepto o fórmula crees que necesitas aplicar?",
                    "Revisa las opciones una por una y descarta las que no tienen sentido"
                ])
            elif student_level == "intermediate":
                hints.extend([
                    "Analiza la relación entre los elementos del problema",
                    "Considera si hay pasos intermedios necesarios",
                    "Verifica tu razonamiento paso a paso"
                ])
            else:  # advanced
                hints.extend([
                    "Examina si hay múltiples enfoques para resolver este problema",
                    "Considera las implicaciones teóricas del problema",
                    "Analiza críticamente cada opción desde diferentes perspectivas"
                ])
        
        return hints[:attempt_number]
    
    @staticmethod
    def analyze_error_type(question: Question, user_answer: str, correct_answer: str) -> str:
        """Analyze the type of error made by the student"""
        if not user_answer or user_answer == correct_answer:
            return "none"
        
        # Simple heuristic for error classification
        # In a real implementation, this could use more sophisticated analysis
        if question.error_comun and user_answer in question.error_comun:
            return "common_misconception"
        elif abs(ord(user_answer.lower()) - ord(correct_answer.lower())) == 1:
            return "adjacent_choice"  # Chose adjacent option
        else:
            return "conceptual"

class AIExplanationEngine:
    """Main AI Explanation Engine with intelligent tutoring capabilities"""
    
    def __init__(self):
        self.client = None
        self.student_analyzer = StudentLevelAnalyzer()
        self.concept_mapper = ConceptMapper()
        self.hint_system = IntelligentHintSystem()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client if available"""
        if settings.OPENAI_API_KEY:
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("AI Explanation Engine initialized with OpenAI")
        else:
            logger.warning("AI Explanation Engine using fallback mode (no OpenAI key)")
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key for AI responses"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float)):
                key_parts.append(f"{k}:{v}")
            else:
                key_parts.append(f"{k}:{hash(str(v))}")
        return ":".join(key_parts)
    
    async def generate_comprehensive_explanation(
        self,
        question: Question,
        user_answer: str,
        user: User,
        db: Session,
        attempt_number: int = 1,
        previous_hints_used: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive AI-powered explanation with tutoring features
        """
        # Analyze student level and learning patterns
        student_analysis = self.student_analyzer.analyze_student_level(user, db)
        
        # Determine if answer is correct
        is_correct = user_answer.lower() == question.respuesta_correcta.lower()
        
        # Analyze error type if incorrect
        error_type = "none" if is_correct else self.hint_system.analyze_error_type(
            question, user_answer, question.respuesta_correcta
        )
        
        # Generate cache key
        cache_key = self._generate_cache_key(
            "ai_comprehensive_explanation",
            question_id=str(question.id),
            user_answer=user_answer,
            student_level=student_analysis["estimated_academic_level"],
            attempt=attempt_number
        )
        
        # Check cache
        cached_result = cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        # Generate explanation components
        explanation_data = {
            "is_correct": is_correct,
            "correct_answer": question.respuesta_correcta,
            "error_type": error_type,
            "student_level": student_analysis["estimated_academic_level"],
            "attempt_number": attempt_number
        }
        
        if self.client and not is_correct:
            # Generate AI-powered step-by-step explanation
            explanation_data.update(await self._generate_ai_explanation(
                question, user_answer, student_analysis, error_type
            ))
        else:
            # Use fallback explanation
            explanation_data.update(self._generate_fallback_explanation(
                question, user_answer, is_correct, student_analysis
            ))
        
        # Add progressive hints
        explanation_data["hints"] = self.hint_system.generate_progressive_hints(
            question, user_answer, attempt_number, student_analysis["estimated_academic_level"]
        )
        
        # Add related concepts and resources
        explanation_data["related_concepts"] = self.concept_mapper.get_related_concepts(question)
        explanation_data["recommended_resources"] = self.concept_mapper.get_related_resources(
            question, student_analysis["estimated_academic_level"]
        )
        
        # Add suggested next actions
        explanation_data["suggested_actions"] = self._generate_suggested_actions(
            is_correct, error_type, student_analysis, attempt_number
        )
        
        # Cache the result
        cache_service.set(cache_key, explanation_data, ttl=3600)
        
        return explanation_data
    
    async def _generate_ai_explanation(
        self,
        question: Question,
        user_answer: str,
        student_analysis: Dict[str, Any],
        error_type: str
    ) -> Dict[str, Any]:
        """Generate AI-powered detailed explanation"""
        try:
            # Prepare context for AI
            complexity_level = student_analysis["explanation_complexity"]
            vocabulary_level = student_analysis["vocabulary_level"]
            academic_level = student_analysis["estimated_academic_level"]
            
            # Build question context
            question_context = {
                "text": question.pregunta_texto or question.question_text,
                "options": question.get_options_dict(),
                "correct_answer": question.respuesta_correcta,
                "user_answer": user_answer,
                "competency": question.competencia,
                "component": question.componente,
                "existing_explanation": question.explicacion_respuesta
            }
            
            prompt = f"""
            Eres un tutor experto en preparación ICFES con capacidades de enseñanza personalizada.
            
            CONTEXTO DEL ESTUDIANTE:
            - Nivel académico: {academic_level}
            - Complejidad de explicación: {complexity_level}
            - Vocabulario: {vocabulary_level}
            - Tipo de error: {error_type}
            
            PREGUNTA:
            {question_context['text']}
            
            OPCIONES:
            {json.dumps(question_context['options'], ensure_ascii=False, indent=2)}
            
            RESPUESTA DEL ESTUDIANTE: {user_answer}
            RESPUESTA CORRECTA: {question_context['correct_answer']}
            COMPETENCIA ICFES: {question_context['competency']}
            COMPONENTE: {question_context['component']}
            
            GENERA UNA EXPLICACIÓN EDUCATIVA QUE INCLUYA:
            
            1. **Análisis del error**: Explica específicamente por qué la respuesta del estudiante es incorrecta
            2. **Explicación paso a paso**: Muestra el proceso correcto de razonamiento
            3. **Conceptos clave**: Identifica y explica los conceptos fundamentales
            4. **Consejos para evitar el error**: Estrategias para no cometer el mismo error
            5. **Conexiones**: Relaciona con otros temas o conceptos
            
            REQUIREMENTS:
            - Usa un tono empático y motivador
            - Adapta el lenguaje al nivel {vocabulary_level}
            - Proporciona explicaciones {complexity_level}
            - Máximo 300 palabras
            - Usa ejemplos si es necesario
            - Enfócate en el aprendizaje, no en el error
            
            Responde en formato JSON con las claves:
            "error_analysis", "step_by_step", "key_concepts", "tips", "connections"
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un tutor experto en ICFES especializado en explicaciones personalizadas. Responde siempre en JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            try:
                ai_explanation = json.loads(response.choices[0].message.content)
                return {
                    "explanation_type": "ai_generated",
                    "detailed_explanation": ai_explanation,
                    "confidence_score": 0.85
                }
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI response as JSON, using fallback")
                return self._parse_ai_text_response(response.choices[0].message.content)
                
        except Exception as e:
            logger.error(f"Error generating AI explanation: {e}")
            return {"explanation_type": "fallback", "confidence_score": 0.5}
    
    def _parse_ai_text_response(self, text_response: str) -> Dict[str, Any]:
        """Parse AI text response into structured format"""
        return {
            "explanation_type": "ai_text",
            "detailed_explanation": {
                "error_analysis": text_response[:100],
                "step_by_step": text_response,
                "key_concepts": ["Revisar conceptos fundamentales"],
                "tips": ["Analizar cuidadosamente cada opción"],
                "connections": ["Relacionar con temas anteriores"]
            },
            "confidence_score": 0.6
        }
    
    def _generate_fallback_explanation(
        self,
        question: Question,
        user_answer: str,
        is_correct: bool,
        student_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured fallback explanation without AI"""
        if is_correct:
            return {
                "explanation_type": "correct_answer",
                "main_explanation": f"¡Excelente! Tu respuesta '{user_answer}' es correcta.",
                "detailed_explanation": {
                    "error_analysis": "No hay errores en tu respuesta.",
                    "step_by_step": question.explicacion_respuesta or "Has aplicado correctamente los conceptos.",
                    "key_concepts": [question.competencia] if question.competencia else ["Concepto aplicado correctamente"],
                    "tips": ["Mantén este nivel de análisis en futuras preguntas"],
                    "connections": ["Este conocimiento te ayudará en preguntas similares"]
                },
                "confidence_score": 0.9
            }
        else:
            academic_level = student_analysis["estimated_academic_level"]
            
            if academic_level == "beginner":
                explanation = f"Tu respuesta '{user_answer}' no es correcta. La respuesta correcta es '{question.respuesta_correcta}'. Te recomiendo revisar los conceptos básicos del tema."
            elif academic_level == "intermediate":
                explanation = f"La respuesta '{user_answer}' presenta un error conceptual. La opción correcta es '{question.respuesta_correcta}'. Analiza paso a paso el procedimiento."
            else:
                explanation = f"Tu elección '{user_answer}' no corresponde a la respuesta óptima '{question.respuesta_correcta}'. Considera revisar el enfoque utilizado."
            
            return {
                "explanation_type": "fallback",
                "main_explanation": explanation,
                "detailed_explanation": {
                    "error_analysis": f"La opción {user_answer} presenta errores conceptuales",
                    "step_by_step": question.explicacion_respuesta or "Revisa el procedimiento paso a paso",
                    "key_concepts": [question.competencia or "Concepto principal"],
                    "tips": ["Analiza cuidadosamente cada opción", "Revisa los conceptos fundamentales"],
                    "connections": ["Relaciona con temas similares estudiados"]
                },
                "confidence_score": 0.7
            }
    
    def _generate_suggested_actions(
        self,
        is_correct: bool,
        error_type: str,
        student_analysis: Dict[str, Any],
        attempt_number: int
    ) -> List[str]:
        """Generate personalized suggested actions"""
        actions = []
        
        if is_correct:
            if student_analysis["estimated_academic_level"] == "beginner":
                actions.extend([
                    "¡Excelente trabajo! Intenta preguntas de mayor dificultad",
                    "Refuerza este conocimiento con ejercicios similares"
                ])
            else:
                actions.extend([
                    "¡Muy bien! Mantén este nivel de análisis",
                    "Considera ayudar a otros estudiantes con dudas similares"
                ])
        else:
            if attempt_number == 1:
                actions.extend([
                    "Revisa los conceptos fundamentales",
                    "Intenta nuevamente con más tiempo",
                    "Analiza cada opción cuidadosamente"
                ])
            elif attempt_number >= 2:
                actions.extend([
                    "Busca recursos adicionales sobre este tema",
                    "Practica con ejercicios similares",
                    "Considera formar un grupo de estudio"
                ])
            
            if error_type == "common_misconception":
                actions.append("Este es un error común, revisa el concepto específico")
            elif error_type == "conceptual":
                actions.append("Enfócate en comprender la teoría antes de resolver")
        
        return actions
    
    async def get_contextual_hint(
        self,
        question: Question,
        user: User,
        hint_level: int,
        previous_attempts: int = 0
    ) -> Dict[str, Any]:
        """Get contextual hint based on student level and attempt number"""
        
        student_analysis = self.student_analyzer.analyze_student_level(user, Session())
        
        hints = self.hint_system.generate_progressive_hints(
            question, "", hint_level, student_analysis["estimated_academic_level"]
        )
        
        if hint_level <= len(hints):
            current_hint = hints[hint_level - 1]
        else:
            current_hint = "Has agotado todas las pistas disponibles. Revisa los conceptos fundamentales."
        
        return {
            "hint": current_hint,
            "hint_level": hint_level,
            "max_hints": len(hints),
            "student_level": student_analysis["estimated_academic_level"],
            "estimated_remaining_attempts": max(0, 3 - previous_attempts)
        }

# Singleton instance
ai_explanation_engine = AIExplanationEngine()