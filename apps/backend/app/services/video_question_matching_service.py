"""
Comprehensive Video-Question Matching Service
Advanced matching algorithm between failed questions and relevant educational videos
"""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text, desc, func
from datetime import datetime, timedelta
import json
import math
from dataclasses import dataclass

from ..models.youtube_catalog import YoutubeCatalog
from ..models.question_video_recommendations import QuestionVideoRecommendations, RecommendationMetrics
from ..models.question import Question
from ..models.user import User
from ..models.quiz import QuizAnswer
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)

@dataclass
class MatchingScore:
    """Data class for video-question matching scores"""
    exact_match: float = 0.0
    semantic_similarity: float = 0.0
    difficulty_proximity: float = 0.0
    popularity: float = 0.0
    error_targeting: float = 0.0
    content_completeness: float = 0.0
    total_score: float = 0.0

@dataclass
class StudentWeakness:
    """Data class for student weakness analysis"""
    question_id: str
    topic_id: Optional[int]
    subject_id: Optional[int]
    error_pattern: str
    distractor_chosen: str
    difficulty_level: float
    frequency: int
    last_failed: datetime

class VideoQuestionMatchingService:
    """
    Advanced service for matching educational videos with failed questions
    Analyzes student weaknesses and recommends targeted video content
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.matching_weights = {
            'semantic': 0.40,
            'exact_match': 0.25,
            'difficulty': 0.15,
            'popularity': 0.10,
            'error_targeting': 0.10
        }
    
    async def analyze_student_weaknesses(self, user_id: str, days_lookback: int = 30) -> List[StudentWeakness]:
        """
        Analyze student's failed questions to identify patterns and weaknesses
        
        Args:
            user_id: Student ID
            days_lookback: Number of days to analyze
            
        Returns:
            List of identified weaknesses with metadata
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_lookback)
            
            # Query failed questions with patterns
            query = text("""
                SELECT 
                    q.id as question_id,
                    q.topic_id,
                    q.subject_id,
                    qa.selected_option as distractor_chosen,
                    q.correct_option,
                    q.difficulty_level,
                    COUNT(*) as failure_count,
                    MAX(qa.answered_at) as last_failed,
                    q.text as question_text,
                    q.explanation
                FROM quiz_answers qa
                JOIN questions q ON qa.question_id = q.id
                WHERE qa.user_id = :user_id 
                    AND qa.is_correct = false
                    AND qa.answered_at >= :cutoff_date
                GROUP BY q.id, q.topic_id, q.subject_id, qa.selected_option, 
                         q.correct_option, q.difficulty_level, q.text, q.explanation
                ORDER BY failure_count DESC, last_failed DESC
                LIMIT 50
            """)
            
            result = self.db.execute(query, {
                'user_id': user_id,
                'cutoff_date': cutoff_date
            })
            
            weaknesses = []
            for row in result:
                # Identify error pattern
                error_pattern = self._classify_error_pattern(
                    row.question_text,
                    row.distractor_chosen,
                    row.correct_option,
                    row.explanation
                )
                
                weakness = StudentWeakness(
                    question_id=str(row.question_id),
                    topic_id=row.topic_id,
                    subject_id=row.subject_id,
                    error_pattern=error_pattern,
                    distractor_chosen=row.distractor_chosen,
                    difficulty_level=float(row.difficulty_level or 0.5),
                    frequency=row.failure_count,
                    last_failed=row.last_failed
                )
                weaknesses.append(weakness)
            
            logger.info(f"Identified {len(weaknesses)} weaknesses for user {user_id}")
            return weaknesses
            
        except Exception as e:
            logger.error(f"Error analyzing student weaknesses: {e}")
            return []
    
    def _classify_error_pattern(self, question_text: str, chosen: str, correct: str, explanation: str) -> str:
        """
        Classify the type of error made by the student
        
        Args:
            question_text: The question text
            chosen: Student's chosen option
            correct: Correct option
            explanation: Question explanation
            
        Returns:
            Error pattern classification
        """
        # Basic error pattern classification
        # This could be enhanced with NLP analysis
        
        patterns = {
            'conceptual_misunderstanding': ['concepto', 'definición', 'principio'],
            'procedural_error': ['procedimiento', 'método', 'pasos'],
            'calculation_error': ['cálculo', 'operación', 'resultado'],
            'interpretation_error': ['interpretación', 'lectura', 'comprensión'],
            'application_error': ['aplicación', 'uso', 'implementación']
        }
        
        text_lower = (question_text + ' ' + explanation).lower()
        
        for pattern, keywords in patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return pattern
        
        return 'general_error'
    
    async def find_matching_videos(
        self, 
        weakness: StudentWeakness, 
        limit: int = 10
    ) -> List[Tuple[YoutubeCatalog, MatchingScore]]:
        """
        Find videos that match a specific student weakness
        
        Args:
            weakness: Student weakness to address
            limit: Maximum number of videos to return
            
        Returns:
            List of tuples (video, matching_score)
        """
        try:
            # Get candidate videos based on topic/subject
            candidates = self.db.query(YoutubeCatalog).filter(
                and_(
                    YoutubeCatalog.is_processed == True,
                    or_(
                        YoutubeCatalog.subject_id == weakness.subject_id,
                        YoutubeCatalog.topic_id == weakness.topic_id
                    )
                )
            ).all()
            
            if not candidates:
                # Fallback to subject-only matching
                candidates = self.db.query(YoutubeCatalog).filter(
                    and_(
                        YoutubeCatalog.is_processed == True,
                        YoutubeCatalog.subject_id == weakness.subject_id
                    )
                ).limit(50).all()
            
            # Score each candidate video
            scored_videos = []
            for video in candidates:
                score = await self._calculate_matching_score(video, weakness)
                if score.total_score > 0.3:  # Minimum threshold
                    scored_videos.append((video, score))
            
            # Sort by total score and return top matches
            scored_videos.sort(key=lambda x: x[1].total_score, reverse=True)
            return scored_videos[:limit]
            
        except Exception as e:
            logger.error(f"Error finding matching videos: {e}")
            return []
    
    async def _calculate_matching_score(
        self, 
        video: YoutubeCatalog, 
        weakness: StudentWeakness
    ) -> MatchingScore:
        """
        Calculate comprehensive matching score between video and weakness
        
        Args:
            video: Candidate video
            weakness: Student weakness
            
        Returns:
            Detailed matching score
        """
        score = MatchingScore()
        
        try:
            # 1. Exact match score (topic/subject alignment)
            score.exact_match = self._calculate_exact_match_score(video, weakness)
            
            # 2. Semantic similarity (would use embeddings in production)
            score.semantic_similarity = await self._calculate_semantic_similarity(video, weakness)
            
            # 3. Difficulty proximity
            score.difficulty_proximity = self._calculate_difficulty_proximity(video, weakness)
            
            # 4. Popularity/engagement score
            score.popularity = self._calculate_popularity_score(video)
            
            # 5. Error targeting score
            score.error_targeting = self._calculate_error_targeting_score(video, weakness)
            
            # 6. Content completeness
            score.content_completeness = self._calculate_content_completeness(video)
            
            # Calculate weighted total score
            score.total_score = (
                score.exact_match * self.matching_weights['exact_match'] +
                score.semantic_similarity * self.matching_weights['semantic'] +
                score.difficulty_proximity * self.matching_weights['difficulty'] +
                score.popularity * self.matching_weights['popularity'] +
                score.error_targeting * self.matching_weights['error_targeting']
            )
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating matching score: {e}")
            return score
    
    def _calculate_exact_match_score(self, video: YoutubeCatalog, weakness: StudentWeakness) -> float:
        """Calculate exact match score based on topic/subject alignment"""
        score = 0.0
        
        # Perfect topic match
        if video.topic_id and video.topic_id == weakness.topic_id:
            score += 0.8
        
        # Subject match
        if video.subject_id and video.subject_id == weakness.subject_id:
            score += 0.6
        
        # Area match (fallback)
        if video.codigo_tema and hasattr(weakness, 'area_code'):
            if video.codigo_tema.startswith(getattr(weakness, 'area_code', '')[:2]):
                score += 0.4
        
        return min(1.0, score)
    
    async def _calculate_semantic_similarity(self, video: YoutubeCatalog, weakness: StudentWeakness) -> float:
        """
        Calculate semantic similarity between video content and question
        In production, this would use actual embeddings
        """
        # Placeholder implementation - would use actual embeddings in production
        # For now, use keyword matching as approximation
        
        try:
            video_text = f"{video.title} {video.description or ''} {video.transcript or ''}"
            
            # Get question text from weakness
            question = self.db.query(Question).filter(
                Question.id == weakness.question_id
            ).first()
            
            if not question:
                return 0.0
            
            question_text = f"{question.text} {question.explanation or ''}"
            
            # Simple keyword overlap (placeholder for actual semantic similarity)
            return self._calculate_text_overlap(video_text, question_text)
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def _calculate_text_overlap(self, text1: str, text2: str) -> float:
        """Calculate simple text overlap as approximation for semantic similarity"""
        try:
            # Normalize and tokenize
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            # Remove common stop words
            stop_words = {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le'}
            words1 = words1 - stop_words
            words2 = words2 - stop_words
            
            if not words1 or not words2:
                return 0.0
            
            # Calculate Jaccard similarity
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_difficulty_proximity(self, video: YoutubeCatalog, weakness: StudentWeakness) -> float:
        """Calculate how well video difficulty matches student's level"""
        try:
            # Map video nivel to difficulty scale
            video_difficulty = self._map_video_difficulty(video.nivel)
            
            # Calculate proximity (closer = higher score)
            diff = abs(video_difficulty - weakness.difficulty_level)
            
            # Score decreases as difference increases
            if diff <= 0.1:
                return 1.0
            elif diff <= 0.3:
                return 0.8
            elif diff <= 0.5:
                return 0.6
            else:
                return max(0.0, 1.0 - diff)
                
        except Exception:
            return 0.5  # Default moderate score
    
    def _map_video_difficulty(self, nivel: Optional[str]) -> float:
        """Map video difficulty level to numeric scale"""
        mapping = {
            'básico': 0.2,
            'intermedio': 0.5,
            'avanzado': 0.8,
            'básico-intermedio': 0.35,
            'intermedio-avanzado': 0.65
        }
        
        if not nivel:
            return 0.5
        
        return mapping.get(nivel.lower(), 0.5)
    
    def _calculate_popularity_score(self, video: YoutubeCatalog) -> float:
        """Calculate video popularity/engagement score"""
        try:
            # Normalize view and like counts
            views = video.view_count or 0
            likes = video.like_count or 0
            
            # Log scale for views (to handle large numbers)
            view_score = min(1.0, math.log10(max(1, views)) / 7.0)  # 10M views = 1.0
            
            # Like ratio score
            like_ratio = likes / max(1, views) if views > 0 else 0
            like_score = min(1.0, like_ratio * 1000)  # 0.1% like ratio = 1.0
            
            # Quality score from our analysis
            quality_score = video.educational_rating / 5.0 if video.educational_rating else 0.5
            
            # Combined popularity score
            return (view_score * 0.4 + like_score * 0.3 + quality_score * 0.3)
            
        except Exception:
            return 0.5
    
    def _calculate_error_targeting_score(self, video: YoutubeCatalog, weakness: StudentWeakness) -> float:
        """Calculate how well video addresses specific error patterns"""
        try:
            video_content = f"{video.title} {video.description or ''}"
            
            # Check if video addresses common error patterns
            error_keywords = {
                'conceptual_misunderstanding': ['concepto', 'definición', 'teoría', 'fundamento'],
                'procedural_error': ['paso a paso', 'procedimiento', 'método', 'técnica'],
                'calculation_error': ['cálculo', 'operación', 'resolver', 'ejercicio'],
                'interpretation_error': ['interpretación', 'análisis', 'comprensión'],
                'application_error': ['aplicación', 'ejemplo', 'práctica', 'uso']
            }
            
            keywords = error_keywords.get(weakness.error_pattern, [])
            
            if not keywords:
                return 0.3  # Default score
            
            # Count keyword matches
            content_lower = video_content.lower()
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            
            return min(1.0, matches / len(keywords))
            
        except Exception:
            return 0.3
    
    def _calculate_content_completeness(self, video: YoutubeCatalog) -> float:
        """Calculate how complete/comprehensive the video content is"""
        try:
            score = 0.0
            
            # Has transcript
            if video.transcript and len(video.transcript) > 100:
                score += 0.3
            
            # Has good description
            if video.description and len(video.description) > 50:
                score += 0.2
            
            # Reasonable duration (not too short, not too long)
            duration = video.duration_seconds or 0
            if 300 <= duration <= 1800:  # 5-30 minutes
                score += 0.3
            elif 120 <= duration <= 3600:  # 2-60 minutes
                score += 0.2
            
            # Has educational metadata
            if video.nivel or video.competencias:
                score += 0.2
            
            return min(1.0, score)
            
        except Exception:
            return 0.5
    
    async def create_video_recommendations(
        self, 
        user_id: str,
        weaknesses: List[StudentWeakness],
        max_recommendations: int = 5
    ) -> List[QuestionVideoRecommendations]:
        """
        Create and store video recommendations for student weaknesses
        
        Args:
            user_id: Student ID
            weaknesses: Identified weaknesses
            max_recommendations: Maximum recommendations per weakness
            
        Returns:
            List of created recommendations
        """
        try:
            recommendations = []
            
            for weakness in weaknesses[:10]:  # Process top 10 weaknesses
                matching_videos = await self.find_matching_videos(weakness, max_recommendations)
                
                for video, score in matching_videos:
                    # Check if recommendation already exists
                    existing = self.db.query(QuestionVideoRecommendations).filter(
                        and_(
                            QuestionVideoRecommendations.question_id == weakness.question_id,
                            QuestionVideoRecommendations.video_id == video.id
                        )
                    ).first()
                    
                    if existing:
                        # Update existing recommendation
                        existing.update_score_components(
                            exact_match=score.exact_match,
                            semantic_similarity=score.semantic_similarity,
                            difficulty_proximity=score.difficulty_proximity,
                            popularity=score.popularity
                        )
                        existing.error_pattern_addressed = weakness.error_pattern
                        existing.distractor_focus = weakness.distractor_chosen
                        existing.targets_common_error = True
                        existing.updated_at = datetime.utcnow()
                        
                        recommendations.append(existing)
                    else:
                        # Create new recommendation
                        recommendation_type = self._determine_recommendation_type(weakness, score)
                        
                        rec = QuestionVideoRecommendations(
                            question_id=weakness.question_id,
                            video_id=video.id,
                            exact_match_score=score.exact_match,
                            semantic_similarity_score=score.semantic_similarity,
                            difficulty_proximity_score=score.difficulty_proximity,
                            popularity_score=score.popularity,
                            total_score=score.total_score,
                            recommendation_type=recommendation_type,
                            error_pattern_addressed=weakness.error_pattern,
                            distractor_focus=weakness.distractor_chosen,
                            targets_common_error=True,
                            content_completeness=score.content_completeness,
                            is_active=True
                        )
                        
                        self.db.add(rec)
                        recommendations.append(rec)
            
            # Commit all recommendations
            self.db.commit()
            
            logger.info(f"Created {len(recommendations)} video recommendations for user {user_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error creating video recommendations: {e}")
            self.db.rollback()
            return []
    
    def _determine_recommendation_type(self, weakness: StudentWeakness, score: MatchingScore) -> str:
        """Determine the type of recommendation based on weakness and score"""
        
        if weakness.error_pattern in ['conceptual_misunderstanding']:
            return 'concept_review'
        elif weakness.frequency > 2:
            return 'error_remediation'
        elif score.difficulty_proximity > 0.8:
            return 'skill_building'
        else:
            return 'concept_review'
    
    async def get_recommendations_for_student(
        self, 
        user_id: str,
        limit: int = 20,
        min_score: float = 0.6
    ) -> List[Dict]:
        """
        Get personalized video recommendations for a student
        
        Args:
            user_id: Student ID
            limit: Maximum recommendations to return
            min_score: Minimum recommendation score
            
        Returns:
            List of recommendation data
        """
        try:
            # Analyze recent weaknesses
            weaknesses = await self.analyze_student_weaknesses(user_id)
            
            if not weaknesses:
                return []
            
            # Create/update recommendations
            await self.create_video_recommendations(user_id, weaknesses)
            
            # Get top recommendations
            query = text("""
                SELECT DISTINCT
                    qvr.*,
                    yc.title,
                    yc.description,
                    yc.youtube_id,
                    yc.url,
                    yc.duration_seconds,
                    yc.channel_name,
                    yc.thumbnail_url,
                    yc.area_evaluada,
                    yc.tema_principal,
                    q.text as question_text
                FROM question_video_recommendations qvr
                JOIN youtube_catalog yc ON qvr.video_id = yc.id
                JOIN questions q ON qvr.question_id = q.id
                JOIN quiz_answers qa ON qa.question_id = q.id
                WHERE qa.user_id = :user_id
                    AND qa.is_correct = false
                    AND qvr.is_active = true
                    AND qvr.total_score >= :min_score
                ORDER BY qvr.total_score DESC, qvr.created_at DESC
                LIMIT :limit
            """)
            
            result = self.db.execute(query, {
                'user_id': user_id,
                'min_score': min_score,
                'limit': limit
            })
            
            recommendations = []
            for row in result:
                rec_data = {
                    'id': row.id,
                    'question_id': str(row.question_id),
                    'video_id': row.video_id,
                    'video_title': row.title,
                    'video_description': row.description,
                    'youtube_id': row.youtube_id,
                    'youtube_url': row.url,
                    'duration_seconds': row.duration_seconds,
                    'channel_name': row.channel_name,
                    'thumbnail_url': row.thumbnail_url,
                    'area_evaluada': row.area_evaluada,
                    'tema_principal': row.tema_principal,
                    'question_text': row.question_text[:200] + '...' if len(row.question_text) > 200 else row.question_text,
                    'total_score': float(row.total_score),
                    'recommendation_type': row.recommendation_type,
                    'error_pattern': row.error_pattern_addressed,
                    'targets_common_error': row.targets_common_error,
                    'confidence_level': row.confidence_level,
                    'created_at': row.created_at.isoformat()
                }
                recommendations.append(rec_data)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations for student: {e}")
            return []
    
    async def track_recommendation_interaction(
        self,
        recommendation_id: int,
        user_id: str,
        interaction_type: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Track student interaction with video recommendations
        
        Args:
            recommendation_id: Recommendation ID
            user_id: Student ID
            interaction_type: Type of interaction (click, watch, complete, rate)
            metadata: Additional interaction data
            
        Returns:
            Success status
        """
        try:
            # Find or create metrics record
            metrics = self.db.query(RecommendationMetrics).filter(
                and_(
                    RecommendationMetrics.recommendation_id == recommendation_id,
                    RecommendationMetrics.student_id == user_id
                )
            ).first()
            
            if not metrics:
                metrics = RecommendationMetrics(
                    recommendation_id=recommendation_id,
                    student_id=user_id
                )
                self.db.add(metrics)
            
            # Update based on interaction type
            if interaction_type == 'click':
                metrics.was_clicked = True
            elif interaction_type == 'watch':
                if metadata:
                    metrics.watch_time_seconds = metadata.get('watch_time_seconds', 0)
                    metrics.completion_rate = metadata.get('completion_rate', 0.0)
            elif interaction_type == 'complete':
                metrics.completion_rate = 100.0
            elif interaction_type == 'rate':
                if metadata:
                    metrics.student_rating = metadata.get('rating', 0)
                    metrics.found_helpful = metadata.get('helpful', False)
                    metrics.feedback_text = metadata.get('feedback', '')
            
            metrics.interaction_timestamp = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error tracking recommendation interaction: {e}")
            self.db.rollback()
            return False