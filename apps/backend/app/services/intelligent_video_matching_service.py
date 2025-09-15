"""
Intelligent Video Matching Service
Combines IRT + Vector Embeddings + LLM for advanced video recommendations
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
from datetime import datetime
import math

logger = logging.getLogger(__name__)

# Optional imports with fallbacks
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not available, using fallback calculations")

try:
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("SentenceTransformers not available, using text-based similarity")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available, using fallback ranking")

class IntelligentVideoMatchingService:
    """
    Advanced video recommendation service that uses:
    1. IRT (Item Response Theory) for student ability analysis
    2. Vector Embeddings for semantic similarity between topics and videos
    3. LLM for intelligent decision making and ranking
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_model = None
        self.openai_client = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize embedding model and OpenAI client"""
        try:
            # Initialize sentence transformer for embeddings if available
            if TRANSFORMERS_AVAILABLE:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Embedding model initialized successfully")
            else:
                self.embedding_model = None
                logger.info("📝 Using text-based similarity instead of embeddings")
            
            # Initialize OpenAI client if API key is available
            if OPENAI_AVAILABLE:
                openai_key = os.getenv('OPENAI_API_KEY')
                if openai_key:
                    openai.api_key = openai_key
                    self.openai_client = openai
                    logger.info("✅ OpenAI client initialized")
                else:
                    self.openai_client = None
                    logger.info("📝 Using intelligent fallback ranking")
            else:
                self.openai_client = None
                logger.info("📝 Using intelligent fallback ranking")
                
        except Exception as e:
            logger.error(f"❌ Error initializing models: {e}")
            # Fallback to basic matching if models fail
            self.embedding_model = None
            self.openai_client = None
    
    def get_student_irt_profile(self, test_id: str) -> Dict[str, Any]:
        """
        Extract IRT-based student ability profile from diagnostic test results
        """
        try:
            # Get test data and calculate IRT-like parameters from available data
            irt_query = text("""
                SELECT 
                    dt.id,
                    dt.user_id,
                    dt.subject_id,
                    dt.score_percentage,
                    dt.correct_answers,
                    dt.total_questions,
                    dt.time_taken_seconds,
                    dt.questions_answered,
                    dt.weaknesses,
                    dt.strengths,
                    dt.score_by_topic
                FROM diagnostic_tests dt
                WHERE dt.id = :test_id
            """)
            
            result = self.db.execute(irt_query, {'test_id': test_id}).first()
            
            if not result:
                logger.warning(f"No IRT data found for test {test_id}")
                return self._default_irt_profile()
            
            # Extract available data and convert to proper types
            score_percentage = float(result[3]) if result[3] is not None else 50.0
            correct_answers = int(result[4]) if result[4] is not None else 0
            total_questions = int(result[5]) if result[5] is not None else 1
            time_taken = int(result[6]) if result[6] is not None else 1800
            questions_answered = int(result[7]) if result[7] is not None else total_questions
            weaknesses_json = result[8] if result[8] is not None else []
            strengths_json = result[9] if result[9] is not None else []
            score_by_topic = result[10] if result[10] is not None else {}
            
            # Calculate IRT-like metrics from available data
            accuracy = correct_answers / total_questions if total_questions > 0 else 0.5
            
            # Convert score to IRT ability scale (-3 to +3)
            ability = (float(score_percentage) / 100.0 * 6.0) - 3.0 if score_percentage else -1.0
            
            # Estimate confidence based on consistency
            confidence = accuracy if accuracy > 0.3 else 0.3
            
            # Calculate derived metrics
            optimal_difficulty = self._calculate_optimal_difficulty(ability, confidence)
            avg_time_per_question = time_taken / questions_answered if questions_answered > 0 else 30.0
            learning_speed = self._estimate_learning_speed(avg_time_per_question, None)
            
            irt_profile = {
                'student_ability': ability,
                'confidence_level': confidence,
                'accuracy_rate': accuracy,
                'optimal_difficulty': optimal_difficulty,
                'learning_speed': learning_speed,
                'total_responses': questions_answered,
                'avg_response_time': avg_time_per_question,
                'response_consistency': confidence,
                'recommended_content_level': self._get_content_level_recommendation(ability),
                'study_intensity': self._calculate_study_intensity(ability, accuracy),
                'score_percentage': score_percentage,
                'weaknesses_data': weaknesses_json,
                'strengths_data': strengths_json,
                'topic_scores': score_by_topic
            }
            
            logger.info(f"📊 IRT Profile calculated for test {test_id}: ability={ability:.3f}, difficulty={optimal_difficulty:.3f}")
            return irt_profile
            
        except Exception as e:
            logger.error(f"❌ Error calculating IRT profile: {e}")
            return self._default_irt_profile()
    
    def get_weakness_embeddings(self, weaknesses: List[str]) -> Dict[str, Any]:
        """
        Generate vector embeddings for identified weakness topics
        """
        if not weaknesses:
            return {}
        
        try:
            weakness_embeddings = {}
            
            for weakness in weaknesses:
                # Clean weakness text
                topic = weakness.replace('Necesita reforzar ', '').strip()
                
                if self.embedding_model:
                    # Create rich context for embedding
                    context_text = f"Matemáticas educación {topic} conceptos fundamentales ejercicios práctica"
                    
                    # Generate embedding
                    embedding = self.embedding_model.encode([context_text])[0]
                    weakness_embeddings[topic] = embedding
                    
                    logger.info(f"🔍 Generated embedding for weakness: {topic}")
                else:
                    # Text-based fallback representation
                    weakness_embeddings[topic] = {
                        'text': topic.lower(),
                        'keywords': topic.lower().split(),
                        'context': f"matemáticas educación {topic.lower()} conceptos fundamentales"
                    }
                    logger.info(f"📝 Generated text representation for weakness: {topic}")
            
            return weakness_embeddings
            
        except Exception as e:
            logger.error(f"❌ Error generating weakness embeddings: {e}")
            return {}
    
    def get_video_embeddings(self, subject_id: str) -> List[Dict[str, Any]]:
        """
        Get or generate embeddings for YouTube videos in the catalog
        """
        try:
            # Get videos from catalog
            video_query = text("""
                SELECT 
                    video_id, title, description, tema_principal, 
                    duration_seconds, educational_value, quality_score,
                    url, thumbnail_url, channel, difficulty_level,
                    title_embedding, description_embedding, combined_embedding
                FROM youtube_catalog
                WHERE subject_id = :subject_id AND is_active = true
                ORDER BY quality_score DESC NULLS LAST, educational_value DESC NULLS LAST
            """)
            
            videos = self.db.execute(video_query, {'subject_id': subject_id}).fetchall()
            
            if not videos:
                logger.warning(f"No videos found for subject {subject_id}")
                return []
            
            video_data = []
            
            for video in videos:
                video_dict = {
                    'video_id': video[0],
                    'title': video[1],
                    'description': video[2] or '',
                    'tema_principal': video[3] or '',
                    'duration_seconds': int(video[4]) if video[4] else 0,
                    'educational_value': float(video[5]) if video[5] else 0.5,
                    'quality_score': float(video[6]) if video[6] else 0.5,
                    'url': video[7] or f"https://www.youtube.com/watch?v={video[0]}",
                    'thumbnail_url': video[8] or '',
                    'channel': video[9] or '',
                    'difficulty_level': video[10] or 'Intermedio'
                }
                
                # Generate or use existing embeddings
                if self.embedding_model:
                    video_content = f"{video[1]} {video[2] or ''} {video[3] or ''}"
                    if video_content.strip():
                        try:
                            embedding = self.embedding_model.encode([video_content])[0]
                            video_dict['embedding'] = embedding
                        except:
                            if NUMPY_AVAILABLE:
                                video_dict['embedding'] = np.zeros(384)  # Default embedding size
                            else:
                                video_dict['embedding'] = None
                    else:
                        if NUMPY_AVAILABLE:
                            video_dict['embedding'] = np.zeros(384)
                        else:
                            video_dict['embedding'] = None
                else:
                    # Text-based fallback
                    video_content = f"{video[1]} {video[2] or ''} {video[3] or ''}"
                    video_dict['embedding'] = {
                        'text': video_content.lower(),
                        'keywords': video_content.lower().split(),
                        'title': (video[1] or '').lower(),
                        'tema_principal': (video[3] or '').lower()
                    }
                
                video_data.append(video_dict)
            
            logger.info(f"📹 Retrieved {len(video_data)} videos with embeddings")
            return video_data
            
        except Exception as e:
            logger.error(f"❌ Error getting video embeddings: {e}")
            return []
    
    def calculate_semantic_similarity(self, weakness_embeddings: Dict[str, Any], 
                                    video_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate semantic similarity between weaknesses and videos using embeddings or text similarity
        """
        recommendations = []
        
        try:
            for weakness_topic, weakness_embedding in weakness_embeddings.items():
                for video in video_data:
                    video_embedding = video.get('embedding')
                    
                    # Calculate similarity based on available data
                    if self.embedding_model and NUMPY_AVAILABLE:
                        # Vector-based similarity
                        if hasattr(weakness_embedding, 'shape') and hasattr(video_embedding, 'shape'):
                            if np.linalg.norm(weakness_embedding) > 0 and np.linalg.norm(video_embedding) > 0:
                                similarity = np.dot(weakness_embedding, video_embedding) / (
                                    np.linalg.norm(weakness_embedding) * np.linalg.norm(video_embedding)
                                )
                            else:
                                similarity = 0.0
                        else:
                            similarity = self._calculate_text_similarity(weakness_topic, video)
                    else:
                        # Text-based similarity fallback
                        similarity = self._calculate_text_similarity(weakness_topic, video)
                    
                    # Create recommendation entry
                    recommendation = {
                        'weakness_topic': weakness_topic,
                        'video': video,
                        'semantic_similarity': float(similarity),
                        'content_match_score': self._calculate_content_match(weakness_topic, video),
                        'title_relevance': self._calculate_title_relevance(weakness_topic, video['title']),
                        'topic_relevance': self._calculate_topic_relevance(weakness_topic, video['tema_principal'])
                    }
                    
                    recommendations.append(recommendation)
            
            # Sort by semantic similarity
            recommendations.sort(key=lambda x: x['semantic_similarity'], reverse=True)
            
            method = "vector embeddings" if self.embedding_model and NUMPY_AVAILABLE else "text similarity"
            logger.info(f"🎯 Calculated semantic similarities using {method} for {len(recommendations)} video-weakness pairs")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error calculating semantic similarity: {e}")
            return []
    
    def llm_intelligent_ranking(self, recommendations: List[Dict[str, Any]], 
                              irt_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Use LLM to make intelligent final ranking decisions
        """
        if not recommendations:
            return []
        
        try:
            # Prepare data for LLM analysis
            top_candidates = recommendations[:15]  # Analyze top 15 candidates
            
            if self.openai_client:
                return self._openai_ranking(top_candidates, irt_profile)
            else:
                return self._fallback_intelligent_ranking(top_candidates, irt_profile)
            
        except Exception as e:
            logger.error(f"❌ Error in LLM ranking: {e}")
            return self._fallback_intelligent_ranking(recommendations[:10], irt_profile)
    
    def _openai_ranking(self, candidates: List[Dict[str, Any]], 
                       irt_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Use OpenAI GPT for intelligent ranking
        """
        try:
            # Prepare prompt for GPT
            prompt = self._create_ranking_prompt(candidates, irt_profile)
            
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un experto en educación matemática y recomendación de contenido educativo. Analiza las debilidades del estudiante y recomienda los mejores videos."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse GPT response
            gpt_rankings = self._parse_gpt_response(response.choices[0].message.content)
            
            # Apply GPT rankings to recommendations
            ranked_recommendations = self._apply_gpt_rankings(candidates, gpt_rankings, irt_profile)
            
            logger.info("🤖 Used OpenAI GPT for intelligent video ranking")
            return ranked_recommendations
            
        except Exception as e:
            logger.error(f"❌ OpenAI ranking failed: {e}")
            return self._fallback_intelligent_ranking(candidates, irt_profile)
    
    def _fallback_intelligent_ranking(self, candidates: List[Dict[str, Any]], 
                                    irt_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fallback intelligent ranking without external LLM
        """
        try:
            for candidate in candidates:
                # Multi-factor scoring
                semantic_score = candidate['semantic_similarity']
                content_score = candidate['content_match_score']
                title_score = candidate['title_relevance']
                topic_score = candidate['topic_relevance']
                
                # IRT-based adjustments
                video = candidate['video']
                difficulty_match = self._calculate_difficulty_match(
                    video.get('difficulty_level', 'Intermedio'),
                    irt_profile['recommended_content_level']
                )
                
                quality_bonus = video.get('quality_score', 0.5) * 0.3
                educational_bonus = video.get('educational_value', 0.5) * 0.3
                duration_fit = self._calculate_duration_fitness(
                    video.get('duration_seconds', 0),
                    irt_profile['learning_speed']
                )
                
                # Combined intelligent score
                intelligent_score = (
                    semantic_score * 0.35 +
                    content_score * 0.25 +
                    title_score * 0.15 +
                    topic_score * 0.15 +
                    difficulty_match * 0.20 +
                    quality_bonus * 0.15 +
                    educational_bonus * 0.15 +
                    duration_fit * 0.10
                ) / 1.5  # Normalize
                
                candidate['intelligent_score'] = intelligent_score
                candidate['difficulty_match'] = difficulty_match
                candidate['quality_bonus'] = quality_bonus
                candidate['duration_fitness'] = duration_fit
                
                # Add reasoning
                candidate['recommendation_reasoning'] = self._generate_recommendation_reasoning(
                    candidate, irt_profile
                )
            
            # Sort by intelligent score
            candidates.sort(key=lambda x: x['intelligent_score'], reverse=True)
            
            logger.info("🧠 Applied fallback intelligent ranking algorithm")
            return candidates
            
        except Exception as e:
            logger.error(f"❌ Error in fallback ranking: {e}")
            return candidates
    
    def generate_final_recommendations(self, test_id: str, max_videos: int = 9) -> Dict[str, Any]:
        """
        Main method to generate intelligent video recommendations
        """
        try:
            logger.info(f"🚀 Starting intelligent video recommendation for test {test_id}")
            
            # Step 1: Get IRT profile
            irt_profile = self.get_student_irt_profile(test_id)
            
            # Step 2: Get weaknesses from diagnostic results
            weaknesses = self._extract_weaknesses_from_test(test_id)
            if not weaknesses:
                logger.warning("No weaknesses found, using general recommendations")
                weaknesses = ['Conceptos fundamentales', 'Práctica general']
            
            # Step 3: Generate embeddings for weaknesses
            weakness_embeddings = self.get_weakness_embeddings(weaknesses)
            
            # Step 4: Get subject and video data
            subject_id = self._get_test_subject(test_id)
            video_data = self.get_video_embeddings(subject_id)
            
            if not video_data:
                logger.error("No videos found for recommendations")
                return self._generate_fallback_recommendations(test_id, weaknesses)
            
            # Step 5: Calculate semantic similarities
            similarity_results = self.calculate_semantic_similarity(weakness_embeddings, video_data)
            
            # Step 6: Apply LLM intelligent ranking
            ranked_recommendations = self.llm_intelligent_ranking(similarity_results, irt_profile)
            
            # Step 7: Format final recommendations
            final_recommendations = self._format_final_recommendations(
                ranked_recommendations[:max_videos], irt_profile, test_id
            )
            
            logger.info(f"✅ Generated {len(final_recommendations['recommendations'])} intelligent recommendations")
            
            return final_recommendations
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendations: {e}")
            return self._generate_fallback_recommendations(test_id, ['Repaso general'])
    
    # Helper methods
    def _default_irt_profile(self) -> Dict[str, Any]:
        return {
            'student_ability': -1.0,
            'confidence_level': 0.5,
            'accuracy_rate': 0.5,
            'optimal_difficulty': 0.0,
            'learning_speed': 'medium',
            'total_responses': 0,
            'avg_response_time': 30.0,
            'response_consistency': 0.5,
            'recommended_content_level': 'Intermedio',
            'study_intensity': 'moderate'
        }
    
    def _calculate_optimal_difficulty(self, ability: float, confidence: float) -> float:
        """Calculate optimal difficulty using IRT principles"""
        return ability + (0.5 * confidence)
    
    def _estimate_learning_speed(self, avg_time: Optional[float], time_variance: Optional[float]) -> str:
        """Estimate learning speed from response patterns"""
        if not avg_time:
            return 'medium'
        
        if avg_time < 20:
            return 'fast'
        elif avg_time > 45:
            return 'slow'
        else:
            return 'medium'
    
    def _get_content_level_recommendation(self, ability: float) -> str:
        """Map IRT ability to content difficulty level"""
        if ability < -1.5:
            return 'Básico'
        elif ability < 0:
            return 'Intermedio'
        else:
            return 'Avanzado'
    
    def _calculate_study_intensity(self, ability: float, accuracy: float) -> str:
        """Recommend study intensity based on performance"""
        if accuracy < 0.4 or ability < -2.0:
            return 'intensive'
        elif accuracy > 0.7 and ability > 0:
            return 'light'
        else:
            return 'moderate'
    
    def _calculate_content_match(self, weakness: str, video: Dict[str, Any]) -> float:
        """Calculate content matching score"""
        video_title = video.get('title', '').lower()
        video_topic = video.get('tema_principal', '').lower()
        weakness_lower = weakness.lower()
        
        title_match = len(set(weakness_lower.split()) & set(video_title.split())) / max(len(weakness_lower.split()), 1)
        topic_match = len(set(weakness_lower.split()) & set(video_topic.split())) / max(len(weakness_lower.split()), 1)
        
        return (title_match + topic_match) / 2
    
    def _calculate_title_relevance(self, weakness: str, title: str) -> float:
        """Calculate title relevance score"""
        if not title:
            return 0.0
        
        weakness_words = set(weakness.lower().split())
        title_words = set(title.lower().split())
        
        if not weakness_words:
            return 0.0
        
        intersection = weakness_words & title_words
        return len(intersection) / len(weakness_words)
    
    def _calculate_topic_relevance(self, weakness: str, topic: str) -> float:
        """Calculate topic relevance score"""
        if not topic:
            return 0.0
        
        return 1.0 if weakness.lower() in topic.lower() or topic.lower() in weakness.lower() else 0.0
    
    def _extract_weaknesses_from_test(self, test_id: str) -> List[str]:
        """Extract weaknesses from diagnostic test results"""
        try:
            # Get weaknesses from the diagnostic test table
            query = text("""
                SELECT dt.weaknesses, dt.score_by_topic
                FROM diagnostic_tests dt
                WHERE dt.id = :test_id
            """)
            
            result = self.db.execute(query, {'test_id': test_id}).first()
            
            if result:
                weaknesses = result[0] if result[0] else []
                score_by_topic = result[1] if result[1] else {}
                
                # If weaknesses is a list, use it directly
                if isinstance(weaknesses, list) and weaknesses:
                    return weaknesses
                
                # If score_by_topic exists, find low-scoring topics
                if isinstance(score_by_topic, dict) and score_by_topic:
                    weak_topics = []
                    for topic, score in score_by_topic.items():
                        if isinstance(score, (int, float)) and score < 60:  # Below 60%
                            weak_topics.append(topic)
                    
                    if weak_topics:
                        return weak_topics
            
            # Fallback: return common mathematical weakness topics
            logger.info(f"No specific weaknesses found for test {test_id}, using default topics")
            return ['Álgebra básica', 'Geometría', 'Aritmética']
            
        except Exception as e:
            logger.error(f"Error extracting weaknesses: {e}")
            return ['Conceptos fundamentales', 'Matemáticas básicas']
    
    def _get_test_subject(self, test_id: str) -> str:
        """Get subject ID for the test"""
        try:
            query = text("SELECT subject_id FROM diagnostic_tests WHERE id = :test_id")
            result = self.db.execute(query, {'test_id': test_id}).first()
            return result[0] if result else '550e8400-e29b-41d4-a716-446655440001'
        except:
            return '550e8400-e29b-41d4-a716-446655440001'  # Default math subject
    
    def _generate_recommendation_reasoning(self, candidate: Dict[str, Any], 
                                         irt_profile: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for recommendation"""
        video = candidate['video']
        weakness = candidate['weakness_topic']
        
        reasons = []
        
        if candidate['semantic_similarity'] > 0.7:
            reasons.append("Alta similitud semántica con tu área de mejora")
        
        if candidate['difficulty_match'] > 0.8:
            reasons.append(f"Nivel de dificultad apropiado para tu perfil ({irt_profile['recommended_content_level']})")
        
        if video.get('quality_score', 0) > 0.7:
            reasons.append("Video de alta calidad educativa")
        
        if candidate['title_relevance'] > 0.6:
            reasons.append(f"Título directamente relacionado con {weakness}")
        
        if not reasons:
            reasons.append(f"Recomendado para reforzar {weakness}")
        
        return " | ".join(reasons)
    
    def _format_final_recommendations(self, ranked_results: List[Dict[str, Any]], 
                                    irt_profile: Dict[str, Any], test_id: str) -> Dict[str, Any]:
        """Format final recommendations for API response"""
        
        recommendations = []
        
        for result in ranked_results:
            video = result['video']
            
            recommendation = {
                'id': video['video_id'],
                'title': video['title'],
                'url': video['url'],
                'duration_minutes': round(video.get('duration_seconds', 0) / 60) if video.get('duration_seconds') else 15,
                'xp': min(150, max(50, round(video.get('duration_seconds', 900) / 60) * 4)),
                'topic': result['weakness_topic'],
                'difficulty': video.get('difficulty_level', 'Intermedio'),
                'recommendation_score': result['intelligent_score'],
                'reasoning': result['recommendation_reasoning'],
                'difficulty_match': result.get('difficulty_match', 'appropriate'),
                'semantic_similarity': result['semantic_similarity'],
                'educational_value': video.get('educational_value', 0.5),
                'quality_score': video.get('quality_score', 0.5),
                'channel': video.get('channel', ''),
                'thumbnail_url': video.get('thumbnail_url', ''),
                'youtube_id': video['video_id'],
                'is_real_video': True,
                'irt_optimized': True
            }
            
            recommendations.append(recommendation)
        
        # Calculate aggregate metrics
        if recommendations:
            scores = [r['recommendation_score'] for r in recommendations]
            similarities = [r['semantic_similarity'] for r in recommendations]
            avg_score = sum(scores) / len(scores)
            avg_similarity = sum(similarities) / len(similarities)
        else:
            avg_score = 0
            avg_similarity = 0
        
        return {
            'success': True,
            'recommendations': recommendations,
            'total_recommendations': len(recommendations),
            'irt_profile': irt_profile,
            'algorithm_info': {
                'method': 'IRT + Vector Embeddings + LLM Intelligence',
                'avg_recommendation_score': round(avg_score, 3),
                'avg_semantic_similarity': round(avg_similarity, 3),
                'confidence_level': 'high' if avg_score > 0.7 else 'medium',
                'personalization_level': 'advanced_irt_optimized'
            },
            'generated_at': datetime.utcnow().isoformat(),
            'test_id': test_id
        }
    
    def _generate_fallback_recommendations(self, test_id: str, weaknesses: List[str]) -> Dict[str, Any]:
        """Generate fallback recommendations if main system fails"""
        return {
            'success': False,
            'error': 'Advanced recommendation system unavailable',
            'recommendations': [],
            'fallback_used': True,
            'test_id': test_id
        }
    
    def _calculate_difficulty_match(self, video_difficulty: str, recommended_level: str) -> float:
        """Calculate how well video difficulty matches student's recommended level"""
        difficulty_map = {'Básico': 1, 'Intermedio': 2, 'Avanzado': 3}
        
        video_level = difficulty_map.get(video_difficulty, 2)
        rec_level = difficulty_map.get(recommended_level, 2)
        
        diff = abs(video_level - rec_level)
        
        if diff == 0:
            return 1.0
        elif diff == 1:
            return 0.7
        else:
            return 0.3
    
    def _calculate_duration_fitness(self, duration_seconds: int, learning_speed: str) -> float:
        """Calculate how well video duration fits student's learning speed"""
        duration_minutes = duration_seconds / 60 if duration_seconds else 15
        
        if learning_speed == 'fast':
            # Fast learners prefer shorter, focused content
            if duration_minutes <= 10:
                return 1.0
            elif duration_minutes <= 20:
                return 0.8
            else:
                return 0.5
        elif learning_speed == 'slow':
            # Slow learners need more comprehensive content
            if 15 <= duration_minutes <= 30:
                return 1.0
            elif 10 <= duration_minutes <= 40:
                return 0.8
            else:
                return 0.6
        else:  # medium
            # Medium learners are flexible
            if 10 <= duration_minutes <= 25:
                return 1.0
            else:
                return 0.7
    
    def _calculate_text_similarity(self, weakness_topic: str, video: Dict[str, Any]) -> float:
        """Calculate text-based similarity when embeddings are not available"""
        try:
            weakness_words = set(weakness_topic.lower().split())
            
            # Get video text content
            video_title = (video.get('title') or '').lower()
            video_tema = (video.get('tema_principal') or '').lower()
            video_desc = (video.get('description') or '').lower()
            
            all_video_words = set()
            all_video_words.update(video_title.split())
            all_video_words.update(video_tema.split())
            all_video_words.update(video_desc.split())
            
            if not weakness_words or not all_video_words:
                return 0.0
            
            # Calculate Jaccard similarity
            intersection = weakness_words & all_video_words
            union = weakness_words | all_video_words
            
            jaccard_similarity = len(intersection) / len(union) if union else 0.0
            
            # Boost for exact topic matches
            if weakness_topic.lower() in video_tema:
                jaccard_similarity += 0.3
            
            if weakness_topic.lower() in video_title:
                jaccard_similarity += 0.2
            
            # Normalize to [0, 1]
            return min(1.0, jaccard_similarity)
            
        except Exception as e:
            logger.error(f"Error calculating text similarity: {e}")
            return 0.0