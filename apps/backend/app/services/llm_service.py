import openai
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime
import asyncio
from functools import lru_cache

from ..core.config import settings
from .cache_service import cache_service

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize OpenAI client if API key is available"""
        if settings.OPENAI_API_KEY:
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized successfully")
        else:
            logger.warning("OpenAI API key not found - using mock responses")
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate a unique cache key for LLM responses"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float)):
                key_parts.append(f"{k}:{v}")
            else:
                key_parts.append(f"{k}:{hash(str(v))}")
        return ":".join(key_parts)
    
    async def get_battle_tips(
        self,
        user_performance: Dict[str, Any],
        battle_context: Dict[str, Any]
    ) -> List[str]:
        """Get personalized battle tips based on performance"""
        cache_key = self._generate_cache_key(
            "llm:battle_tips",
            accuracy=round(user_performance.get('accuracy', 0), 1),
            topic=battle_context.get('topic', 'general')
        )
        
        # Check cache first
        cached_tips = cache_service.get(cache_key)
        if cached_tips:
            logger.debug(f"Cache hit for battle tips: {cache_key}")
            return cached_tips
        
        if not self.client:
            # Mock tips if no OpenAI client
            return self._get_mock_battle_tips(user_performance, battle_context)
        
        try:
            # Prepare context for LLM
            accuracy = user_performance.get('accuracy', 0)
            weakest_topics = user_performance.get('weakest_topics', [])
            current_topic = battle_context.get('topic', 'general')
            difficulty = battle_context.get('difficulty', 5)
            
            prompt = f"""
            Eres un tutor experto en preparación ICFES. Genera 3 tips concisos y personalizados 
            para un estudiante con las siguientes características:
            
            - Precisión actual: {accuracy}%
            - Temas débiles: {', '.join(weakest_topics[:3]) if weakest_topics else 'Ninguno identificado'}
            - Tema actual: {current_topic}
            - Dificultad: {difficulty}/10
            
            Los tips deben ser:
            1. Específicos para mejorar en el tema actual
            2. Prácticos y accionables
            3. Motivadores y en español
            4. Máximo 50 palabras cada uno
            
            Formato: Lista numerada sin introducción ni conclusión.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un tutor experto en ICFES."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            # Parse response
            tips_text = response.choices[0].message.content.strip()
            tips = [tip.strip() for tip in tips_text.split('\n') if tip.strip() and tip[0].isdigit()]
            
            # Clean tips (remove numbering)
            clean_tips = []
            for tip in tips[:3]:  # Max 3 tips
                # Remove leading numbers and dots
                clean_tip = tip.lstrip('0123456789. ')
                if clean_tip:
                    clean_tips.append(clean_tip)
            
            # Cache the result
            cache_service.set(cache_key, clean_tips, ttl=3600)  # 1 hour cache
            
            return clean_tips
            
        except Exception as e:
            logger.error(f"Error generating battle tips: {e}")
            return self._get_mock_battle_tips(user_performance, battle_context)
    
    def _get_mock_battle_tips(
        self,
        user_performance: Dict[str, Any],
        battle_context: Dict[str, Any]
    ) -> List[str]:
        """Generate mock tips when LLM is not available"""
        accuracy = user_performance.get('accuracy', 0)
        topic = battle_context.get('topic', 'general')
        
        if accuracy < 60:
            return [
                f"Tómate más tiempo para analizar cada pregunta de {topic}",
                "Revisa los conceptos fundamentales antes de intentar problemas complejos",
                "Practica con ejercicios similares para ganar confianza"
            ]
        elif accuracy < 80:
            return [
                f"Buen progreso en {topic}! Enfócate en los detalles",
                "Identifica patrones comunes en las preguntas",
                "Practica problemas de mayor dificultad gradualmente"
            ]
        else:
            return [
                f"¡Excelente dominio de {topic}! Mantén el ritmo",
                "Intenta resolver problemas más rápido sin perder precisión",
                "Ayuda a otros compañeros para reforzar tu conocimiento"
            ]
    
    async def get_question_explanation(
        self,
        question: Dict[str, Any],
        user_answer: str,
        is_correct: bool
    ) -> str:
        """Get detailed explanation for a question"""
        cache_key = self._generate_cache_key(
            "llm:explanation",
            question_id=question.get('id'),
            user_answer=user_answer
        )
        
        # Check cache
        cached_explanation = cache_service.get(cache_key)
        if cached_explanation:
            return cached_explanation
        
        if not self.client:
            return self._get_mock_explanation(question, user_answer, is_correct)
        
        try:
            prompt = f"""
            Explica la siguiente pregunta ICFES y por qué la respuesta es correcta o incorrecta:
            
            Pregunta: {question.get('text')}
            Opciones: {json.dumps(question.get('options', {}), ensure_ascii=False)}
            Respuesta del usuario: {user_answer}
            Respuesta correcta: {question.get('correct_answer')}
            Es correcta: {'Sí' if is_correct else 'No'}
            
            Proporciona una explicación clara y educativa en español (máximo 150 palabras).
            Si la respuesta es incorrecta, explica por qué y da la respuesta correcta.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un profesor experto en ICFES."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.5
            )
            
            explanation = response.choices[0].message.content.strip()
            
            # Cache the result
            cache_service.set(cache_key, explanation, ttl=86400)  # 24 hours
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return self._get_mock_explanation(question, user_answer, is_correct)
    
    def _get_mock_explanation(
        self,
        question: Dict[str, Any],
        user_answer: str,
        is_correct: bool
    ) -> str:
        """Generate mock explanation when LLM is not available"""
        if is_correct:
            return (
                f"¡Correcto! Has seleccionado '{user_answer}'. "
                f"{question.get('explanation', 'Esta es la respuesta correcta según el contexto de la pregunta.')}"
            )
        else:
            return (
                f"Tu respuesta '{user_answer}' no es correcta. "
                f"La respuesta correcta es '{question.get('correct_answer')}'. "
                f"{question.get('explanation', 'Revisa el concepto y vuelve a intentarlo.')}"
            )
    
    async def generate_personalized_study_tips(
        self,
        user_stats: Dict[str, Any],
        weak_areas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comprehensive personalized study recommendations"""
        cache_key = self._generate_cache_key(
            "llm:study_tips",
            level=user_stats.get('level', 1),
            weak_count=len(weak_areas)
        )
        
        cached_tips = cache_service.get(cache_key)
        if cached_tips:
            return cached_tips
        
        if not self.client:
            return self._get_mock_study_tips(user_stats, weak_areas)
        
        try:
            weak_topics_summary = "\n".join([
                f"- {area['topic']}: {area['accuracy']}% de precisión"
                for area in weak_areas[:5]
            ])
            
            prompt = f"""
            Genera un plan de estudio personalizado para un estudiante ICFES con:
            
            Nivel: {user_stats.get('level', 1)}
            Experiencia: {user_stats.get('experience', 0)}
            Precisión general: {user_stats.get('overall_accuracy', 0)}%
            Racha de días: {user_stats.get('streak_days', 0)}
            
            Áreas débiles:
            {weak_topics_summary}
            
            Proporciona:
            1. 3 objetivos específicos a corto plazo (1 semana)
            2. 3 estrategias de estudio recomendadas
            3. Tiempo sugerido de estudio diario
            4. 2 recursos o técnicas específicas
            
            Formato: JSON con las claves "objetivos", "estrategias", "tiempo_diario", "recursos"
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un tutor experto en preparación ICFES. Responde solo en formato JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            try:
                study_plan = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                study_plan = self._get_mock_study_tips(user_stats, weak_areas)
            
            # Cache the result
            cache_service.set(cache_key, study_plan, ttl=86400)  # 24 hours
            
            return study_plan
            
        except Exception as e:
            logger.error(f"Error generating study tips: {e}")
            return self._get_mock_study_tips(user_stats, weak_areas)
    
    def _get_mock_study_tips(
        self,
        user_stats: Dict[str, Any],
        weak_areas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate mock study tips when LLM is not available"""
        return {
            "objetivos": [
                "Mejorar precisión en los temas débiles en un 15%",
                "Completar al menos 50 preguntas esta semana",
                "Mantener una racha de estudio de 7 días"
            ],
            "estrategias": [
                "Enfócate en un tema débil por día",
                "Revisa las explicaciones de todas las respuestas incorrectas",
                "Practica con temporizador para mejorar velocidad"
            ],
            "tiempo_diario": "45-60 minutos",
            "recursos": [
                "Usa mapas conceptuales para visualizar relaciones",
                "Forma un grupo de estudio virtual con otros jugadores"
            ]
        }
    
    async def analyze_learning_pattern(
        self,
        user_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze user's learning patterns and provide insights"""
        if not user_history:
            return {
                "pattern": "insufficient_data",
                "insights": ["Necesitamos más datos para analizar tu patrón de aprendizaje"],
                "recommendations": ["Continúa practicando regularmente"]
            }
        
        # Simple pattern analysis without LLM
        total_questions = len(user_history)
        correct_answers = sum(1 for h in user_history if h.get('is_correct', False))
        accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Time analysis
        avg_response_time = sum(h.get('response_time', 0) for h in user_history) / total_questions
        
        # Difficulty progression
        difficulty_progression = [h.get('difficulty', 5) for h in user_history[-20:]]
        is_improving = len(difficulty_progression) > 10 and \
                      sum(difficulty_progression[-5:]) > sum(difficulty_progression[:5])
        
        pattern = {
            "pattern": "improving" if is_improving else "stable",
            "metrics": {
                "total_questions": total_questions,
                "accuracy": round(accuracy, 1),
                "avg_response_time": round(avg_response_time / 1000, 1),  # Convert to seconds
                "difficulty_trend": "increasing" if is_improving else "stable"
            },
            "insights": [],
            "recommendations": []
        }
        
        # Generate insights
        if accuracy < 60:
            pattern["insights"].append("Tu precisión está por debajo del promedio")
            pattern["recommendations"].append("Reduce la dificultad temporalmente para ganar confianza")
        elif accuracy > 85:
            pattern["insights"].append("¡Excelente precisión! Estás dominando el material")
            pattern["recommendations"].append("Aumenta la dificultad para seguir mejorando")
        
        if avg_response_time > 30000:  # 30 seconds
            pattern["insights"].append("Tomas más tiempo del promedio en responder")
            pattern["recommendations"].append("Practica con temporizador para mejorar velocidad")
        
        return pattern
    
    async def generate_motivational_message(
        self,
        context: str,
        user_stats: Dict[str, Any]
    ) -> str:
        """Generate motivational messages based on context"""
        messages = {
            "level_up": [
                "¡Felicidades Hunter! Has subido al nivel {level}. ¡El conocimiento es tu mayor poder!",
                "¡Nivel {level} desbloqueado! Cada batalla te hace más fuerte. ¡Sigue así!",
                "¡Impresionante! Nivel {level} alcanzado. Los S-Rank Hunters comenzaron como tú."
            ],
            "streak": [
                "¡{days} días de racha! Tu dedicación es admirable, futuro S-Rank Hunter.",
                "¡Increíble! {days} días consecutivos. La consistencia es la clave del éxito.",
                "¡{days} días sin parar! Tienes la determinación de un verdadero Hunter."
            ],
            "battle_won": [
                "¡Victoria épica! Has demostrado tu valía en el campo de batalla del conocimiento.",
                "¡Excelente batalla! Cada victoria te acerca más a convertirte en S-Rank.",
                "¡Has triunfado! Los monstruos del desconocimiento tiemblan ante ti."
            ],
            "achievement": [
                "¡Nuevo logro desbloqueado! Tu leyenda crece con cada hazaña.",
                "¡Achievement obtenido! Eres un verdadero Hunter del conocimiento.",
                "¡Logro conseguido! Tu historia se escribe con cada victoria."
            ]
        }
        
        message_list = messages.get(context, ["¡Sigue adelante, Hunter!"])
        message = message_list[hash(str(user_stats)) % len(message_list)]
        
        # Format with user stats
        return message.format(
            level=user_stats.get('level', 1),
            days=user_stats.get('streak_days', 0),
            rank=user_stats.get('rank', 'E')
        )
    
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.client is not None

# Singleton instance
llm_service = LLMService()