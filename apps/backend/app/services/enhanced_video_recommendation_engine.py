"""
Enhanced Video Recommendation Engine with Semantic Matching
Advanced system for matching failed questions to YouTube video content
"""

import asyncio
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from ..models.youtube_catalog import YoutubeCatalog, VideoStats, StudentVideoInteraction
from ..models.question_video_recommendations import QuestionVideoRecommendations, RecommendationMetrics
from ..models.user import User
from ..models.question import Question
from ..models.response import Response

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False


class EnhancedVideoRecommendationEngine:
    """Enhanced video recommendation engine with semantic matching and AI"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_client = openai.OpenAI(api_key=openai_api_key) if openai_api_key and OPENAI_AVAILABLE else None
        
        # Recommendation weights (can be tuned)
        self.weights = {
            'semantic_similarity': 0.50,
            'difficulty_match': 0.20,
            'exact_match': 0.15,
            'popularity': 0.15
        }
        
        # Thresholds
        self.min_similarity_threshold = 0.75
        self.max_recommendations_per_question = 5
        self.embedding_cache = {}
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get text embedding using OpenAI API with caching"""
        # Use cache to avoid redundant API calls
        text_hash = hash(text)
        if text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]
        
        if not self.openai_client:
            logger.warning("OpenAI client not available, returning dummy embedding")
            # Return a dummy embedding for development
            embedding = np.random.random(1536).tolist()
            self.embedding_cache[text_hash] = embedding
            return embedding
        
        try:
            response = await self.openai_client.embeddings.acreate(
                model="text-embedding-ada-002",
                input=text[:8000]  # Limit text length for API
            )
            embedding = response.data[0].embedding
            self.embedding_cache[text_hash] = embedding
            return embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None
    
    def calculate_semantic_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Handle empty or invalid embeddings
            if len(vec1) == 0 or len(vec2) == 0:
                return 0.0
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(max(0.0, min(1.0, similarity)))  # Clamp between 0 and 1
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def calculate_difficulty_match(self, student_theta: float, video_irt_b: Optional[float]) -> float:
        """Calculate difficulty match score based on IRT parameters"""
        if video_irt_b is None:
            return 0.5  # Neutral if no IRT data
        
        # Calculate absolute distance between student ability and video difficulty
        distance = abs(student_theta - video_irt_b)
        
        # Convert distance to similarity score (closer = better match)
        if distance > 2.0:
            return 0.1  # Poor match for large differences
        else:
            return max(0.1, 1.0 - (distance / 2.0))
    
    def calculate_popularity_score(self, video: YoutubeCatalog) -> float:
        """Calculate popularity score from video stats and metrics"""
        if hasattr(video, 'stats') and video.stats:
            stats = video.stats
            ctr = float(stats.ctr_7d or 0)
            completion = float(stats.completion_rate_7d or 0)
            improvement = float(stats.avg_improvement_score or 0)
            
            # Weighted combination: CTR, completion, and learning improvement
            return (ctr * 0.3) + (completion * 0.4) + (improvement * 0.3)
        
        # Fallback to basic video metrics
        if video.view_count and video.like_count:
            like_ratio = video.like_count / max(video.view_count, 1)
            return min(1.0, like_ratio * 100)  # Scale to 0-1
        
        return 0.3  # Default medium popularity
    
    async def find_videos_for_failed_question(
        self, 
        db: Session,
        question_id: str,
        student_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find relevant videos for a failed question using semantic matching"""
        
        # Get question details
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            logger.error(f"Question {question_id} not found")
            return []
        
        # Get student's theta estimate (ability level)
        student_theta = await self._get_student_theta(db, student_id, question.subject_id)
        
        # Generate question embedding for semantic matching
        question_text = self._generate_question_text(question)
        question_embedding = await self.get_embedding(question_text)
        
        if not question_embedding:
            logger.error("Failed to generate question embedding")
            # Fallback to basic matching without semantic similarity
            return await self._get_basic_video_recommendations(db, question, limit)
        
        # Find candidate videos
        candidate_videos = await self._get_candidate_videos(
            db, question.subject_id, question.topic_id
        )
        
        if not candidate_videos:
            logger.warning(f"No candidate videos found for subject {question.subject_id}")
            return []
        
        # Score and rank videos
        scored_videos = []
        for video in candidate_videos:
            score_data = await self._score_video_for_question(
                video, question, question_embedding, student_theta
            )
            
            if score_data['total_score'] >= self.min_similarity_threshold:
                scored_videos.append({
                    'video': video,
                    'scores': score_data,
                    'recommendation_data': self._build_recommendation_data(
                        video, question, score_data
                    )
                })
        
        # Sort by total score and return top results
        scored_videos.sort(key=lambda x: x['scores']['total_score'], reverse=True)
        return [item['recommendation_data'] for item in scored_videos[:limit]]
    
    async def _get_student_theta(self, db: Session, student_id: str, subject_id: int) -> float:
        """Get student's ability estimate (theta) for the subject"""
        try:
            # Query recent diagnostic attempts for theta estimate
            result = db.execute(
                text("""
                    SELECT theta FROM diagnostic_attempts 
                    WHERE student_id = :student_id 
                    AND subject_id = :subject_id 
                    AND finished_at IS NOT NULL
                    ORDER BY finished_at DESC 
                    LIMIT 1
                """),
                {'student_id': student_id, 'subject_id': subject_id}
            ).fetchone()
            
            return float(result[0]) if result else 0.0
        except Exception as e:
            logger.error(f"Error getting student theta: {e}")
            return 0.0
    
    def _generate_question_text(self, question: Question) -> str:
        """Generate text representation of question for embedding"""
        parts = [
            question.text or "",
            question.subject.name if hasattr(question, 'subject') and question.subject else "",
            question.topic.name if hasattr(question, 'topic') and question.topic else "",
            question.competence or "",
            question.component or ""
        ]
        return " | ".join(filter(None, parts))
    
    async def _get_candidate_videos(
        self, 
        db: Session, 
        subject_id: int, 
        topic_id: Optional[int] = None
    ) -> List[YoutubeCatalog]:
        """Get candidate videos for recommendation"""
        query = db.query(YoutubeCatalog).filter(
            and_(
                YoutubeCatalog.subject_id == subject_id,
                YoutubeCatalog.is_processed == True,
                YoutubeCatalog.processing_status == 'completed'
            )
        )
        
        if topic_id:
            # Prefer exact topic match but also include subject-level videos
            query = query.filter(
                or_(
                    YoutubeCatalog.topic_id == topic_id,
                    YoutubeCatalog.topic_id.is_(None)  # Subject-level videos
                )
            )
        
        # Order by quality and processing status
        query = query.order_by(
            YoutubeCatalog.has_embeddings.desc(),
            YoutubeCatalog.relevance_score.desc(),
            YoutubeCatalog.quality_score.desc()
        )
        
        return query.limit(50).all()  # Get top 50 candidates for scoring
    
    async def _score_video_for_question(
        self, 
        video: YoutubeCatalog,
        question: Question,
        question_embedding: List[float],
        student_theta: float
    ) -> Dict[str, float]:
        """Score a video for a specific question"""
        
        # 1. Semantic similarity (most important factor)
        semantic_score = 0.0
        if video.combined_embedding:
            try:
                # Handle different embedding storage formats
                video_embedding = video.combined_embedding
                if isinstance(video_embedding, str):
                    # If stored as string, try to parse it
                    try:
                        video_embedding = eval(video_embedding)
                    except:
                        video_embedding = []
                
                if video_embedding and len(video_embedding) > 0:
                    semantic_score = self.calculate_semantic_similarity(
                        question_embedding, video_embedding
                    )
            except Exception as e:
                logger.error(f"Error calculating semantic similarity: {e}")
        
        # 2. Exact match score (subject/topic alignment)
        exact_match_score = 0.0
        if video.subject_id == question.subject_id:
            exact_match_score += 0.5
        if hasattr(question, 'topic_id') and video.topic_id == question.topic_id:
            exact_match_score += 0.5
        exact_match_score = min(1.0, exact_match_score)
        
        # 3. Difficulty match based on IRT parameters
        difficulty_score = self.calculate_difficulty_match(student_theta, video.irt_b)
        
        # 4. Popularity score based on video stats
        popularity_score = self.calculate_popularity_score(video)
        
        # Calculate total weighted score
        total_score = (
            semantic_score * self.weights['semantic_similarity'] +
            difficulty_score * self.weights['difficulty_match'] +
            exact_match_score * self.weights['exact_match'] +
            popularity_score * self.weights['popularity']
        )
        
        return {
            'semantic_similarity': semantic_score,
            'difficulty_match': difficulty_score,
            'exact_match': exact_match_score,
            'popularity': popularity_score,
            'total_score': min(1.0, total_score)  # Ensure score doesn't exceed 1.0
        }
    
    def _build_recommendation_data(
        self, 
        video: YoutubeCatalog, 
        question: Question, 
        score_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """Build comprehensive recommendation data structure"""
        
        # Determine recommendation type based on scores
        recommendation_type = 'concept_review'
        if score_data['semantic_similarity'] > 0.8:
            recommendation_type = 'error_remediation'
        elif score_data['difficulty_match'] > 0.8:
            recommendation_type = 'skill_building'
        elif score_data['exact_match'] > 0.9:
            recommendation_type = 'direct_practice'
        
        # Determine confidence level
        confidence_level = 'low'
        if score_data['total_score'] >= 0.8:
            confidence_level = 'high'
        elif score_data['total_score'] >= 0.6:
            confidence_level = 'medium'
        
        return {
            'video_id': video.id,
            'youtube_id': video.youtube_id,
            'title': video.title,
            'description': video.description,
            'url': video.get_watch_url(),
            'embed_url': video.get_embed_url(),
            'duration_seconds': video.duration_seconds,
            'channel': video.channel_name,
            'thumbnail_url': video.thumbnail_url,
            'subject_id': video.subject_id,
            'topic_id': video.topic_id,
            'area_evaluada': video.area_evaluada,
            'tema_principal': video.tema_principal,
            'nivel': video.nivel,
            'recommendation_type': recommendation_type,
            'confidence_level': confidence_level,
            'scores': score_data,
            'learning_objectives': self._extract_learning_objectives(video, question),
            'estimated_study_time': video.duration_seconds // 60 if video.duration_seconds else 15,
            'quality_score': float(video.quality_score) if video.quality_score else 0.0,
            'relevance_score': float(video.relevance_score) if video.relevance_score else 0.0
        }
    
    def _extract_learning_objectives(
        self, 
        video: YoutubeCatalog, 
        question: Question
    ) -> List[str]:
        """Extract learning objectives based on video and question content"""
        objectives = []
        
        if hasattr(question, 'competence') and question.competence:
            objectives.append(f"Develop {question.competence.lower()} skills")
        
        if hasattr(question, 'component') and question.component:
            objectives.append(f"Understand {question.component.lower()} concepts")
        
        if video.tema_principal:
            objectives.append(f"Master {video.tema_principal.lower()}")
        
        if video.area_evaluada:
            objectives.append(f"Strengthen {video.area_evaluada.lower()} knowledge")
        
        return objectives[:3]  # Limit to top 3 objectives
    
    async def _get_basic_video_recommendations(
        self, 
        db: Session, 
        question: Question, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fallback method for basic video recommendations without embeddings"""
        try:
            videos = db.query(YoutubeCatalog).filter(
                and_(
                    YoutubeCatalog.subject_id == question.subject_id,
                    YoutubeCatalog.is_processed == True
                )
            ).order_by(
                YoutubeCatalog.relevance_score.desc()
            ).limit(limit).all()
            
            return [
                {
                    'video_id': video.id,
                    'youtube_id': video.youtube_id,
                    'title': video.title,
                    'url': video.get_watch_url(),
                    'embed_url': video.get_embed_url(),
                    'duration_seconds': video.duration_seconds,
                    'channel': video.channel_name,
                    'recommendation_type': 'basic_match',
                    'confidence_level': 'low',
                    'scores': {'total_score': 0.5},
                    'estimated_study_time': video.duration_seconds // 60 if video.duration_seconds else 15
                }
                for video in videos
            ]
        except Exception as e:
            logger.error(f"Error getting basic recommendations: {e}")
            return []
    
    async def get_personalized_video_list(
        self,
        db: Session,
        student_id: str,
        subject_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get personalized video recommendations for a student based on failed questions"""
        
        # Get student's recent failed questions
        failed_questions = await self._get_recent_failed_questions(
            db, student_id, subject_id
        )
        
        if not failed_questions:
            # Return popular videos for the subject as fallback
            return await self._get_popular_videos(db, subject_id, limit)
        
        # Get recommendations for each failed question
        all_recommendations = []
        for question in failed_questions[:5]:  # Top 5 recent failures
            try:
                recommendations = await self.find_videos_for_failed_question(
                    db, str(question.id), student_id, 3
                )
                all_recommendations.extend(recommendations)
            except Exception as e:
                logger.error(f"Error getting recommendations for question {question.id}: {e}")
                continue
        
        # Remove duplicates and rank by score
        unique_videos = {}
        for rec in all_recommendations:
            video_id = rec['video_id']
            if video_id not in unique_videos:
                unique_videos[video_id] = rec
            else:
                # Keep the one with higher score
                if rec['scores']['total_score'] > unique_videos[video_id]['scores']['total_score']:
                    unique_videos[video_id] = rec
        
        # Sort by score and return
        ranked_videos = list(unique_videos.values())
        ranked_videos.sort(key=lambda x: x['scores']['total_score'], reverse=True)
        
        return ranked_videos[:limit]
    
    async def _get_recent_failed_questions(
        self,
        db: Session,
        student_id: str,
        subject_id: Optional[int] = None,
        days: int = 30
    ) -> List[Question]:
        """Get student's recent failed questions"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Query recent incorrect responses
            query = db.query(Question).join(Response).filter(
                and_(
                    Response.student_id == student_id,
                    Response.is_correct == False,
                    Response.answered_at >= cutoff_date
                )
            )
            
            if subject_id:
                query = query.filter(Question.subject_id == subject_id)
            
            questions = query.order_by(Response.answered_at.desc()).limit(10).all()
            return questions
            
        except Exception as e:
            logger.error(f"Error getting recent failed questions: {e}")
            return []
    
    async def _get_popular_videos(
        self,
        db: Session,
        subject_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get popular videos as fallback recommendations"""
        try:
            query = db.query(YoutubeCatalog).filter(
                and_(
                    YoutubeCatalog.is_processed == True,
                    YoutubeCatalog.processing_status == 'completed'
                )
            )
            
            if subject_id:
                query = query.filter(YoutubeCatalog.subject_id == subject_id)
            
            videos = query.order_by(
                YoutubeCatalog.relevance_score.desc(),
                YoutubeCatalog.view_count.desc()
            ).limit(limit).all()
            
            return [
                {
                    'video_id': video.id,
                    'youtube_id': video.youtube_id,
                    'title': video.title,
                    'description': video.description,
                    'url': video.get_watch_url(),
                    'embed_url': video.get_embed_url(),
                    'duration_seconds': video.duration_seconds,
                    'channel': video.channel_name,
                    'thumbnail_url': video.thumbnail_url,
                    'area_evaluada': video.area_evaluada,
                    'tema_principal': video.tema_principal,
                    'recommendation_type': 'popular',
                    'confidence_level': 'medium',
                    'scores': {'total_score': float(video.relevance_score or 0.5)},
                    'estimated_study_time': video.duration_seconds // 60 if video.duration_seconds else 15,
                    'quality_score': float(video.quality_score) if video.quality_score else 0.0
                }
                for video in videos
            ]
        except Exception as e:
            logger.error(f"Error getting popular videos: {e}")
            return []
    
    async def track_video_interaction(
        self,
        db: Session,
        student_id: str,
        video_id: int,
        interaction_data: Dict[str, Any]
    ) -> bool:
        """Track student video interaction for analytics and improving recommendations"""
        try:
            interaction = StudentVideoInteraction(
                student_id=student_id,
                video_id=video_id,
                watch_start_time=interaction_data.get('watch_start_time'),
                watch_end_time=interaction_data.get('watch_end_time'),
                total_watch_seconds=interaction_data.get('total_watch_seconds', 0),
                completion_percentage=interaction_data.get('completion_percentage', 0.0),
                question_id=interaction_data.get('question_id'),
                session_id=interaction_data.get('session_id'),
                recommendation_source=interaction_data.get('recommendation_source', 'enhanced_engine'),
                was_helpful=interaction_data.get('was_helpful'),
                difficulty_rating=interaction_data.get('difficulty_rating'),
                quality_rating=interaction_data.get('quality_rating'),
                feedback_text=interaction_data.get('feedback_text'),
                performance_before=interaction_data.get('performance_before'),
                performance_after=interaction_data.get('performance_after')
            )
            
            # Calculate improvement delta if both before and after scores are available
            if interaction.performance_before and interaction.performance_after:
                interaction.improvement_delta = interaction.performance_after - interaction.performance_before
            
            db.add(interaction)
            db.commit()
            
            logger.info(f"Tracked video interaction: student={student_id}, video={video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking video interaction: {e}")
            db.rollback()
            return False


# Global service instance
enhanced_video_recommendation_engine = EnhancedVideoRecommendationEngine()