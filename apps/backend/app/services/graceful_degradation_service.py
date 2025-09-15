"""
Graceful Degradation Service
Provides fallback functionality when services fail, ensuring system continues working
even when components are unavailable.
"""

import asyncio
import json
import logging
import random
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..core.cache_manager import cache_manager
from ..core.database import get_db
from ..models.question import Question
from ..models.user import User

logger = logging.getLogger(__name__)


@dataclass
class FallbackData:
    """Structure for fallback data"""
    service_name: str
    data: Dict[str, Any]
    cache_duration: int = 300  # 5 minutes default
    last_updated: datetime = None
    is_stale: bool = False


class GracefulDegradationService:
    """
    Service that provides fallback functionality when primary services fail.
    Implements various degradation strategies to maintain system functionality.
    """
    
    def __init__(self):
        self.fallback_data: Dict[str, FallbackData] = {}
        self.service_status: Dict[str, bool] = {}
        self.degradation_strategies: Dict[str, Callable] = {
            'database_unavailable': self._database_fallback_strategy,
            'ai_service_unavailable': self._ai_service_fallback_strategy,
            'external_api_unavailable': self._external_api_fallback_strategy,
            'cache_unavailable': self._cache_fallback_strategy,
            'websocket_unavailable': self._websocket_fallback_strategy
        }
        self._initialize_fallback_data()
    
    def _initialize_fallback_data(self):
        """Initialize default fallback data for critical services"""
        self.fallback_data.update({
            'questions': FallbackData(
                service_name='questions',
                data={
                    'sample_questions': [
                        {
                            'id': 'fallback_math_1',
                            'subject': 'Matemáticas',
                            'topic': 'Aritmética básica',
                            'question_text': '¿Cuál es el resultado de 15 + 28?',
                            'options': ['41', '42', '43', '44'],
                            'correct_answer': 'B',
                            'explanation': 'Sumando 15 + 28 = 43',
                            'difficulty': 'facil'
                        },
                        {
                            'id': 'fallback_spanish_1',
                            'subject': 'Lenguaje',
                            'topic': 'Comprensión lectora',
                            'question_text': 'En el texto "El gato saltó sobre la mesa", ¿cuál es el sujeto?',
                            'options': ['El gato', 'saltó', 'la mesa', 'sobre'],
                            'correct_answer': 'A',
                            'explanation': 'El sujeto es quien realiza la acción, en este caso "El gato"',
                            'difficulty': 'facil'
                        }
                    ]
                }
            ),
            'ai_explanations': FallbackData(
                service_name='ai_explanations',
                data={
                    'default_explanation': {
                        'explanation': 'La respuesta correcta ha sido marcada. Te recomendamos revisar el tema para fortalecer tu comprensión.',
                        'tips': [
                            'Revisa los conceptos fundamentales del tema',
                            'Practica con ejercicios similares',
                            'Consulta material de apoyo adicional'
                        ],
                        'related_concepts': ['Conceptos básicos'],
                        'difficulty_adjustment': 'maintain'
                    }
                }
            ),
            'study_plans': FallbackData(
                service_name='study_plans',
                data={
                    'default_plan': {
                        'plan': {
                            'daily_sessions': 2,
                            'session_duration': 25,
                            'focus_subjects': ['Matemáticas', 'Lenguaje'],
                            'practice_subjects': ['Ciencias'],
                            'weekly_goals': [
                                'Completar 15 preguntas diarias',
                                'Mantener racha de estudio',
                                'Revisar errores cometidos'
                            ]
                        },
                        'recommendations': [
                            'Dedica tiempo constante al estudio',
                            'Enfócate en tus materias más débiles',
                            'Practica regularmente'
                        ],
                        'estimated_improvement': 10.0
                    }
                }
            ),
            'leaderboard': FallbackData(
                service_name='leaderboard',
                data={
                    'cached_leaderboard': [
                        {'rank': 1, 'username': 'Estudiante Top', 'score': 9500, 'level': 25},
                        {'rank': 2, 'username': 'Super Learner', 'score': 9200, 'level': 24},
                        {'rank': 3, 'username': 'Math Master', 'score': 8800, 'level': 23}
                    ],
                    'user_rank': {'rank': '50+', 'score': 1200, 'level': 5}
                }
            )
        })
    
    async def get_fallback_questions(self, subject: str = None, count: int = 10) -> List[Dict]:
        """Get fallback questions when database is unavailable"""
        try:
            # First try to get from cache
            cache_key = f"fallback_questions:{subject}:{count}"
            cached_questions = await cache_manager.get_cached_data(cache_key)
            
            if cached_questions:
                logger.info(f"Using cached fallback questions for {subject}")
                return cached_questions
            
            # Use predefined fallback questions
            fallback_questions = self.fallback_data['questions'].data['sample_questions']
            
            # Filter by subject if specified
            if subject:
                filtered_questions = [
                    q for q in fallback_questions 
                    if q.get('subject', '').lower() == subject.lower()
                ]
                if filtered_questions:
                    fallback_questions = filtered_questions
            
            # Duplicate and randomize to meet count requirement
            result_questions = []
            for i in range(count):
                base_question = fallback_questions[i % len(fallback_questions)].copy()
                base_question['id'] = f"{base_question['id']}_copy_{i}"
                result_questions.append(base_question)
            
            # Cache for future use
            await cache_manager.cache_data(cache_key, result_questions, ttl=300)
            
            logger.info(f"Provided {len(result_questions)} fallback questions")
            return result_questions
            
        except Exception as error:
            logger.error(f"Error in fallback questions: {error}")
            # Return minimal questions as last resort
            return [{
                'id': 'emergency_question_1',
                'subject': subject or 'General',
                'topic': 'Conocimiento básico',
                'question_text': 'Esta es una pregunta de ejemplo mientras se restaura el servicio.',
                'options': ['Opción A', 'Opción B', 'Opción C', 'Opción D'],
                'correct_answer': 'A',
                'explanation': 'Servicio en mantenimiento.',
                'difficulty': 'facil'
            }]
    
    async def get_fallback_ai_explanation(self, question_data: Dict = None) -> Dict:
        """Get fallback AI explanation when AI service is unavailable"""
        try:
            base_explanation = self.fallback_data['ai_explanations'].data['default_explanation']
            
            # Customize explanation based on question data if available
            if question_data:
                subject = question_data.get('subject', 'la materia')
                topic = question_data.get('topic', 'este tema')
                
                customized_explanation = {
                    'explanation': f'La respuesta correcta para esta pregunta de {subject} es importante. Te recomendamos estudiar más sobre {topic} para mejorar tu comprensión.',
                    'tips': [
                        f'Repasa los conceptos de {topic}',
                        f'Practica más ejercicios de {subject}',
                        'Consulta material adicional sobre el tema'
                    ],
                    'related_concepts': [topic],
                    'difficulty_adjustment': 'maintain',
                    'fallback_mode': True
                }
                return customized_explanation
            
            return {**base_explanation, 'fallback_mode': True}
            
        except Exception as error:
            logger.error(f"Error in fallback AI explanation: {error}")
            return {
                'explanation': 'Explicación temporalmente no disponible. Por favor intenta más tarde.',
                'tips': ['Consulta tu material de estudio', 'Practica ejercicios similares'],
                'related_concepts': ['Conceptos generales'],
                'difficulty_adjustment': 'maintain',
                'fallback_mode': True,
                'error_occurred': True
            }
    
    async def get_fallback_study_plan(self, user_data: Dict = None) -> Dict:
        """Get fallback study plan when AI service is unavailable"""
        try:
            base_plan = self.fallback_data['study_plans'].data['default_plan']
            
            # Customize based on user data if available
            if user_data:
                weak_subjects = user_data.get('weak_subjects', ['Matemáticas'])
                strong_subjects = user_data.get('strong_subjects', ['Lenguaje'])
                
                customized_plan = {
                    'plan': {
                        **base_plan['plan'],
                        'focus_subjects': weak_subjects[:2],  # Focus on top 2 weak subjects
                        'practice_subjects': strong_subjects[:1]  # Maintain 1 strong subject
                    },
                    'recommendations': [
                        f'Dedica más tiempo a {", ".join(weak_subjects[:2])}',
                        'Mantén práctica en materias fuertes',
                        'Establece horarios regulares de estudio'
                    ],
                    'estimated_improvement': 8.0,
                    'fallback_mode': True
                }
                return customized_plan
            
            return {**base_plan, 'fallback_mode': True}
            
        except Exception as error:
            logger.error(f"Error in fallback study plan: {error}")
            return {
                'plan': {
                    'daily_sessions': 2,
                    'session_duration': 20,
                    'focus_subjects': ['Matemáticas'],
                    'practice_subjects': [],
                    'weekly_goals': ['Estudiar diariamente']
                },
                'recommendations': ['Mantén constancia en el estudio'],
                'estimated_improvement': 5.0,
                'fallback_mode': True,
                'error_occurred': True
            }
    
    async def get_fallback_leaderboard(self, user_id: str = None) -> Dict:
        """Get fallback leaderboard when database is unavailable"""
        try:
            base_leaderboard = self.fallback_data['leaderboard'].data
            
            # Add some randomization to make it feel more dynamic
            leaderboard = base_leaderboard['cached_leaderboard'].copy()
            for entry in leaderboard:
                # Add small random variations
                score_variation = random.randint(-50, 50)
                entry['score'] = max(0, entry['score'] + score_variation)
            
            result = {
                'leaderboard': leaderboard,
                'user_rank': base_leaderboard['user_rank'],
                'total_participants': len(leaderboard) + random.randint(100, 500),
                'last_updated': datetime.now().isoformat(),
                'fallback_mode': True
            }
            
            return result
            
        except Exception as error:
            logger.error(f"Error in fallback leaderboard: {error}")
            return {
                'leaderboard': [],
                'user_rank': {'rank': 'N/A', 'score': 0, 'level': 1},
                'total_participants': 0,
                'fallback_mode': True,
                'error_occurred': True
            }
    
    async def get_fallback_user_progress(self, user_id: str) -> Dict:
        """Get fallback user progress data"""
        try:
            # Try to get from cache first
            cache_key = f"user_progress_fallback:{user_id}"
            cached_progress = await cache_manager.get_cached_data(cache_key)
            
            if cached_progress:
                return {**cached_progress, 'fallback_mode': True}
            
            # Generate reasonable fallback progress
            fallback_progress = {
                'user_id': user_id,
                'level': random.randint(1, 10),
                'xp': random.randint(100, 2000),
                'subjects_progress': {
                    'Matemáticas': {'completed': 15, 'total': 50, 'accuracy': 0.72},
                    'Lenguaje': {'completed': 12, 'total': 45, 'accuracy': 0.68},
                    'Ciencias': {'completed': 8, 'total': 40, 'accuracy': 0.65},
                    'Sociales': {'completed': 10, 'total': 35, 'accuracy': 0.70},
                    'Inglés': {'completed': 5, 'total': 30, 'accuracy': 0.60}
                },
                'streak_days': random.randint(1, 15),
                'achievements': [
                    {'id': 'first_steps', 'name': 'Primeros Pasos', 'earned_at': datetime.now().isoformat()},
                    {'id': 'week_warrior', 'name': 'Guerrero de la Semana', 'earned_at': datetime.now().isoformat()}
                ],
                'last_activity': datetime.now().isoformat(),
                'fallback_mode': True
            }
            
            # Cache for a short time
            await cache_manager.cache_data(cache_key, fallback_progress, ttl=180)
            
            return fallback_progress
            
        except Exception as error:
            logger.error(f"Error in fallback user progress: {error}")
            return {
                'user_id': user_id,
                'level': 1,
                'xp': 0,
                'subjects_progress': {},
                'streak_days': 0,
                'achievements': [],
                'last_activity': datetime.now().isoformat(),
                'fallback_mode': True,
                'error_occurred': True
            }
    
    async def check_service_health(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        try:
            # Implement health checks for different services
            if service_name == 'database':
                return await self._check_database_health()
            elif service_name == 'ai_service':
                return await self._check_ai_service_health()
            elif service_name == 'cache':
                return await self._check_cache_health()
            elif service_name == 'websocket':
                return await self._check_websocket_health()
            else:
                return True  # Assume healthy if unknown service
                
        except Exception as error:
            logger.error(f"Health check failed for {service_name}: {error}")
            return False
    
    async def _check_database_health(self) -> bool:
        """Check database health"""
        try:
            db = next(get_db())
            # Simple query to test connection
            result = db.execute("SELECT 1").fetchone()
            return result is not None
        except Exception:
            return False
    
    async def _check_ai_service_health(self) -> bool:
        """Check AI service health"""
        try:
            # This would make an actual call to the AI service health endpoint
            # For now, we'll simulate
            return True
        except Exception:
            return False
    
    async def _check_cache_health(self) -> bool:
        """Check cache health"""
        try:
            # Test cache connectivity
            test_key = "health_check_test"
            await cache_manager.cache_data(test_key, "test", ttl=1)
            result = await cache_manager.get_cached_data(test_key)
            return result == "test"
        except Exception:
            return False
    
    async def _check_websocket_health(self) -> bool:
        """Check WebSocket service health"""
        try:
            # This would check WebSocket service availability
            # For now, we'll simulate
            return True
        except Exception:
            return False
    
    async def update_service_status(self, service_name: str, is_healthy: bool):
        """Update service status and trigger degradation if needed"""
        previous_status = self.service_status.get(service_name, True)
        self.service_status[service_name] = is_healthy
        
        if previous_status and not is_healthy:
            logger.warning(f"Service {service_name} became unhealthy - activating degradation")
            await self._activate_degradation(service_name)
        elif not previous_status and is_healthy:
            logger.info(f"Service {service_name} recovered - deactivating degradation")
            await self._deactivate_degradation(service_name)
    
    async def _activate_degradation(self, service_name: str):
        """Activate degradation strategies for a service"""
        try:
            degradation_key = f"{service_name}_unavailable"
            if degradation_key in self.degradation_strategies:
                await self.degradation_strategies[degradation_key]()
                logger.info(f"Activated degradation strategy for {service_name}")
        except Exception as error:
            logger.error(f"Failed to activate degradation for {service_name}: {error}")
    
    async def _deactivate_degradation(self, service_name: str):
        """Deactivate degradation strategies for a service"""
        try:
            # Clear degradation-specific caches
            cache_keys = [
                f"fallback_questions:*",
                f"user_progress_fallback:*",
                f"degradation_{service_name}:*"
            ]
            
            for pattern in cache_keys:
                keys = await cache_manager.get_keys_by_pattern(pattern)
                for key in keys:
                    await cache_manager.delete(key)
            
            logger.info(f"Deactivated degradation strategy for {service_name}")
            
        except Exception as error:
            logger.error(f"Failed to deactivate degradation for {service_name}: {error}")
    
    # Degradation strategy implementations
    async def _database_fallback_strategy(self):
        """Strategy when database is unavailable"""
        logger.info("Implementing database fallback strategy")
        # Could implement more specific strategies here
    
    async def _ai_service_fallback_strategy(self):
        """Strategy when AI service is unavailable"""
        logger.info("Implementing AI service fallback strategy")
        # Could implement more specific strategies here
    
    async def _external_api_fallback_strategy(self):
        """Strategy when external APIs are unavailable"""
        logger.info("Implementing external API fallback strategy")
        # Could implement more specific strategies here
    
    async def _cache_fallback_strategy(self):
        """Strategy when cache is unavailable"""
        logger.info("Implementing cache fallback strategy")
        # Could implement more specific strategies here
    
    async def _websocket_fallback_strategy(self):
        """Strategy when WebSocket service is unavailable"""
        logger.info("Implementing WebSocket fallback strategy")
        # Could implement more specific strategies here
    
    def is_service_degraded(self, service_name: str) -> bool:
        """Check if a service is currently in degraded mode"""
        return not self.service_status.get(service_name, True)
    
    async def get_system_degradation_status(self) -> Dict:
        """Get overall system degradation status"""
        return {
            'services': self.service_status,
            'degraded_services': [
                service for service, healthy in self.service_status.items() 
                if not healthy
            ],
            'overall_health': all(self.service_status.values()) if self.service_status else True,
            'timestamp': datetime.now().isoformat()
        }


# Global instance
graceful_degradation_service = GracefulDegradationService()