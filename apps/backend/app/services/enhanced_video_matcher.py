"""
Enhanced YouTube Video Recommendation Matching System
Advanced matching of failed questions to YouTube videos using multiple algorithms
"""

import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

@dataclass
class VideoRecommendation:
    """Enhanced video recommendation with detailed matching metadata"""
    video_id: str
    youtube_id: str
    title: str
    url: str
    channel_name: str
    duration_seconds: int
    topic: str
    difficulty_level: int
    quality_score: float
    
    # Matching scores
    content_match_score: float
    difficulty_match_score: float
    topic_relevance_score: float
    semantic_similarity_score: float
    popularity_score: float
    composite_score: float
    
    # Recommendation metadata
    recommendation_type: str
    confidence_level: str
    learning_objective: str
    target_error_pattern: str
    prerequisite_concepts: List[str]
    follow_up_topics: List[str]
    
    # Learning context
    estimated_watch_time: int
    xp_value: int
    difficulty_progression: str
    cognitive_load: str

@dataclass
class QuestionAnalysis:
    """Analysis of a failed question for video matching"""
    question_id: str
    question_text: str
    topic: str
    difficulty_theta: float
    cognitive_level: str
    competency: str
    component: str
    error_indicators: List[str]
    content_keywords: List[str]
    concept_tags: List[str]

class EnhancedVideoMatcher:
    """
    Advanced system for matching failed questions to optimal YouTube videos
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Matching algorithm weights
        self.matching_weights = {
            'content_match': 0.30,      # Direct content similarity
            'difficulty_match': 0.25,    # Difficulty level alignment
            'topic_relevance': 0.20,     # Topic/subject relevance
            'semantic_similarity': 0.15, # Semantic content similarity
            'popularity_score': 0.10     # Video quality/popularity
        }
        
        # Error pattern to learning objective mapping
        self.error_to_objective = {
            'conceptual_misunderstanding': 'Understand fundamental concepts',
            'procedural_error': 'Master step-by-step procedures',
            'calculation_error': 'Improve computational accuracy',
            'reading_comprehension': 'Enhance text interpretation skills',
            'time_management': 'Develop efficient problem-solving strategies',
            'knowledge_gap': 'Build foundational knowledge'
        }
        
        # Cognitive load levels
        self.cognitive_levels = {
            'remember': 'low',
            'understand': 'medium',
            'apply': 'medium',
            'analyze': 'high',
            'evaluate': 'high',
            'create': 'very_high'
        }
    
    async def get_matched_video_recommendations(
        self,
        failed_questions: List[Dict[str, Any]],
        subject_id: str,
        max_videos_per_question: int = 3,
        total_video_limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get comprehensive video recommendations for failed questions
        """
        try:
            logger.info(f"🎯 Matching videos for {len(failed_questions)} failed questions")
            
            # 1. Analyze each failed question
            question_analyses = await self._analyze_failed_questions(failed_questions)
            
            # 2. Get candidate videos for each question
            all_recommendations = []
            question_video_map = {}
            
            for analysis in question_analyses:
                videos = await self._find_matching_videos(
                    analysis, subject_id, max_videos_per_question
                )
                
                question_video_map[analysis.question_id] = videos
                all_recommendations.extend(videos)
            
            # 3. Remove duplicates and apply global ranking
            unique_videos = await self._deduplicate_and_rank_videos(
                all_recommendations, total_video_limit
            )
            
            # 4. Organize by learning progression
            learning_path = await self._organize_learning_progression(
                unique_videos, question_analyses
            )
            
            # 5. Generate metadata and insights
            matching_metadata = await self._generate_matching_metadata(
                question_analyses, unique_videos, question_video_map
            )
            
            return {
                'success': True,
                'total_questions_analyzed': len(failed_questions),
                'total_videos_recommended': len(unique_videos),
                'question_video_mapping': {
                    q_id: [asdict(v) for v in videos] 
                    for q_id, videos in question_video_map.items()
                },
                'recommended_videos': [asdict(v) for v in unique_videos],
                'learning_progression': learning_path,
                'matching_metadata': matching_metadata,
                'confidence_summary': self._calculate_confidence_summary(unique_videos)
            }
            
        except Exception as e:
            logger.error(f"❌ Error in video matching: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to match videos to questions'
            }
    
    async def _analyze_failed_questions(
        self,
        failed_questions: List[Dict[str, Any]]
    ) -> List[QuestionAnalysis]:
        """Analyze failed questions to extract matching criteria"""
        analyses = []
        
        for question in failed_questions:
            # Extract content keywords from question text
            content_keywords = self._extract_content_keywords(
                question.get('question_text', '')
            )
            
            # Identify error indicators
            error_indicators = self._identify_error_indicators(question)
            
            # Extract concept tags
            concept_tags = self._extract_concept_tags(
                question.get('question_text', ''),
                question.get('topic_name', ''),
                question.get('competency', '')
            )
            
            analysis = QuestionAnalysis(
                question_id=question['question_id'],
                question_text=question.get('question_text', ''),
                topic=question.get('topic_name', ''),
                difficulty_theta=question.get('difficulty_theta', 0),
                cognitive_level=question.get('cognitive_level', 'understand'),
                competency=question.get('competency', ''),
                component=question.get('component', ''),
                error_indicators=error_indicators,
                content_keywords=content_keywords,
                concept_tags=concept_tags
            )
            
            analyses.append(analysis)
        
        return analyses
    
    def _extract_content_keywords(self, question_text: str) -> List[str]:
        """Extract relevant keywords from question text"""
        if not question_text:
            return []
        
        # Common math/science/language keywords
        keyword_patterns = {
            'math': r'\b(equation|function|graph|derivative|integral|algebra|geometry|triangle|circle|polynomial|matrix|vector|probability|statistics)\b',
            'science': r'\b(molecule|atom|cell|DNA|evolution|force|energy|velocity|acceleration|reaction|element|compound|ecosystem)\b',
            'language': r'\b(metaphor|simile|protagonist|theme|setting|plot|grammar|syntax|verb|noun|adjective|paragraph|essay)\b'
        }
        
        keywords = []
        text_lower = question_text.lower()
        
        for category, pattern in keyword_patterns.items():
            matches = re.findall(pattern, text_lower)
            keywords.extend(matches)
        
        # Add numerical indicators
        if re.search(r'\d+', question_text):
            keywords.append('numerical_calculation')
        
        # Add question type indicators
        if '?' in question_text:
            if 'why' in text_lower or 'explain' in text_lower:
                keywords.append('conceptual_explanation')
            elif 'how' in text_lower or 'calculate' in text_lower:
                keywords.append('procedural_solution')
            elif 'what' in text_lower:
                keywords.append('factual_recall')
        
        return list(set(keywords))
    
    def _identify_error_indicators(self, question: Dict[str, Any]) -> List[str]:
        """Identify potential error patterns from question metadata"""
        indicators = []
        
        # Based on response time
        response_time = question.get('response_time_ms', 0)
        if response_time < 30000:  # Less than 30 seconds
            indicators.append('rushed_answer')
        elif response_time > 300000:  # More than 5 minutes
            indicators.append('struggled_with_concept')
        
        # Based on hints used
        hints_used = question.get('hints_used', 0)
        if hints_used > 2:
            indicators.append('knowledge_gap')
        elif hints_used == 0 and not question.get('is_correct', False):
            indicators.append('overconfidence')
        
        # Based on difficulty
        difficulty = question.get('difficulty_theta', 0)
        if difficulty < -1 and not question.get('is_correct', False):
            indicators.append('careless_mistake')
        elif difficulty > 1:
            indicators.append('advanced_concept_challenge')
        
        # Based on cognitive level
        cognitive_level = question.get('cognitive_level', '')
        if cognitive_level in ['analyze', 'evaluate', 'create']:
            indicators.append('higher_order_thinking')
        
        return indicators
    
    def _extract_concept_tags(
        self,
        question_text: str,
        topic: str,
        competency: str
    ) -> List[str]:
        """Extract specific concept tags for better matching"""
        tags = []
        
        # Add topic as primary tag
        if topic:
            tags.append(topic.lower().replace(' ', '_'))
        
        # Add competency-based tags
        if competency:
            tags.append(competency.lower().replace(' ', '_'))
        
        # Extract specific mathematical concepts
        math_concepts = {
            'linear_equation': r'\b(linear|slope|y\s*=|mx\s*\+\s*b)\b',
            'quadratic': r'\b(quadratic|parabola|x\^2|x²)\b',
            'geometry': r'\b(triangle|circle|angle|area|perimeter|volume)\b',
            'probability': r'\b(probability|chance|odds|random)\b',
            'statistics': r'\b(mean|median|mode|standard\s+deviation|average)\b'
        }
        
        text_lower = question_text.lower()
        for concept, pattern in math_concepts.items():
            if re.search(pattern, text_lower):
                tags.append(concept)
        
        return list(set(tags))
    
    async def _find_matching_videos(
        self,
        question_analysis: QuestionAnalysis,
        subject_id: str,
        max_videos: int
    ) -> List[VideoRecommendation]:
        """Find matching videos for a specific question analysis"""
        try:
            # Get subject name
            subject_query = text("SELECT name FROM subjects WHERE id = :subject_id")
            subject_result = self.db.execute(subject_query, {'subject_id': subject_id}).first()
            subject_name = subject_result[0] if subject_result else 'Mathematics'
            
            # First, try to get videos from question_video_recommendations table
            direct_matches = await self._get_direct_video_matches(question_analysis.question_id)
            
            # If no direct matches, find by content similarity
            if not direct_matches:
                content_matches = await self._find_content_similar_videos(
                    question_analysis, subject_name, max_videos * 2
                )
            else:
                content_matches = direct_matches
            
            # Score and rank videos
            scored_videos = []
            for video_data in content_matches:
                recommendation = await self._score_video_match(
                    video_data, question_analysis
                )
                if recommendation.composite_score > 0.3:  # Minimum threshold
                    scored_videos.append(recommendation)
            
            # Sort by composite score and return top matches
            scored_videos.sort(key=lambda x: x.composite_score, reverse=True)
            return scored_videos[:max_videos]
            
        except Exception as e:
            logger.error(f"Error finding matching videos: {e}")
            return []
    
    async def _get_direct_video_matches(self, question_id: str) -> List[Dict[str, Any]]:
        """Get videos from the question_video_recommendations table"""
        try:
            query = text("""
                SELECT 
                    yc.id,
                    yc.youtube_id,
                    yc.title,
                    yc.url,
                    yc.channel_name,
                    yc.duration_seconds,
                    yc.tema_principal,
                    yc.quality_score,
                    yc.educational_rating,
                    yc.view_count,
                    qvr.total_score,
                    qvr.recommendation_type,
                    qvr.confidence_level,
                    qvr.learning_objective
                FROM question_video_recommendations qvr
                JOIN youtube_catalog yc ON qvr.video_id = yc.id
                WHERE qvr.question_id = :question_id
                AND qvr.is_active = true
                AND qvr.total_score >= 0.5
                ORDER BY qvr.total_score DESC
                LIMIT 5
            """)
            
            results = self.db.execute(query, {'question_id': question_id}).fetchall()
            
            videos = []
            for row in results:
                videos.append({
                    'video_id': row[0],
                    'youtube_id': row[1],
                    'title': row[2],
                    'url': row[3],
                    'channel_name': row[4],
                    'duration_seconds': row[5],
                    'topic': row[6],
                    'quality_score': float(row[7]) if row[7] else 0.5,
                    'educational_rating': float(row[8]) if row[8] else 0.5,
                    'view_count': row[9] or 0,
                    'match_score': float(row[10]),
                    'recommendation_type': row[11],
                    'confidence_level': row[12],
                    'learning_objective': row[13],
                    'source': 'direct_match'
                })
            
            return videos
            
        except Exception as e:
            logger.error(f"Error getting direct video matches: {e}")
            return []
    
    async def _find_content_similar_videos(
        self,
        question_analysis: QuestionAnalysis,
        subject_name: str,
        max_videos: int
    ) -> List[Dict[str, Any]]:
        """Find videos by content similarity"""
        try:
            # Build search criteria
            topic_pattern = f"%{question_analysis.topic}%" if question_analysis.topic else "%"
            
            # Create keyword search pattern
            keyword_patterns = []
            for keyword in question_analysis.content_keywords[:3]:  # Top 3 keywords
                keyword_patterns.append(f"%{keyword}%")
            
            query = text("""
                SELECT 
                    id, youtube_id, title, url, channel_name, duration_seconds,
                    tema_principal, quality_score, educational_rating, view_count,
                    area_evaluada, nivel
                FROM youtube_catalog
                WHERE area_evaluada = :subject_name
                AND processing_status = 'completed'
                AND (
                    LOWER(tema_principal) LIKE LOWER(:topic_pattern)
                    OR LOWER(title) LIKE LOWER(:topic_pattern)
                    {}
                )
                ORDER BY quality_score DESC, educational_rating DESC, view_count DESC
                LIMIT :limit
            """.format(
                ' OR ' + ' OR '.join([
                    f"LOWER(title) LIKE LOWER(:keyword_{i})" 
                    for i in range(len(keyword_patterns))
                ]) if keyword_patterns else ''
            ))
            
            params = {
                'subject_name': subject_name,
                'topic_pattern': topic_pattern,
                'limit': max_videos
            }
            
            # Add keyword parameters
            for i, pattern in enumerate(keyword_patterns):
                params[f'keyword_{i}'] = pattern
            
            results = self.db.execute(query, params).fetchall()
            
            videos = []
            for row in results:
                videos.append({
                    'video_id': row[0],
                    'youtube_id': row[1],
                    'title': row[2],
                    'url': row[3],
                    'channel_name': row[4],
                    'duration_seconds': row[5],
                    'topic': row[6],
                    'quality_score': float(row[7]) if row[7] else 0.5,
                    'educational_rating': float(row[8]) if row[8] else 0.5,
                    'view_count': row[9] or 0,
                    'area_evaluada': row[10],
                    'nivel': row[11],
                    'source': 'content_similarity'
                })
            
            return videos
            
        except Exception as e:
            logger.error(f"Error finding content similar videos: {e}")
            return []
    
    async def _score_video_match(
        self,
        video_data: Dict[str, Any],
        question_analysis: QuestionAnalysis
    ) -> VideoRecommendation:
        """Score how well a video matches a question analysis"""
        
        # Calculate individual scores
        content_score = self._calculate_content_match_score(video_data, question_analysis)
        difficulty_score = self._calculate_difficulty_match_score(video_data, question_analysis)
        topic_score = self._calculate_topic_relevance_score(video_data, question_analysis)
        semantic_score = self._calculate_semantic_similarity_score(video_data, question_analysis)
        popularity_score = self._calculate_popularity_score(video_data)
        
        # Calculate composite score
        composite_score = (
            content_score * self.matching_weights['content_match'] +
            difficulty_score * self.matching_weights['difficulty_match'] +
            topic_score * self.matching_weights['topic_relevance'] +
            semantic_score * self.matching_weights['semantic_similarity'] +
            popularity_score * self.matching_weights['popularity_score']
        )
        
        # Determine recommendation metadata
        recommendation_type = self._determine_recommendation_type(question_analysis, video_data)
        confidence_level = self._determine_confidence_level(composite_score)
        learning_objective = self._generate_learning_objective(question_analysis, video_data)
        target_error_pattern = self._identify_target_error_pattern(question_analysis)
        
        # Calculate additional metadata
        xp_value = self._calculate_xp_value(video_data, composite_score)
        difficulty_progression = self._determine_difficulty_progression(question_analysis, video_data)
        cognitive_load = self.cognitive_levels.get(question_analysis.cognitive_level, 'medium')
        
        return VideoRecommendation(
            video_id=video_data['video_id'],
            youtube_id=video_data['youtube_id'],
            title=video_data['title'],
            url=video_data['url'],
            channel_name=video_data['channel_name'],
            duration_seconds=video_data['duration_seconds'],
            topic=video_data['topic'],
            difficulty_level=self._map_difficulty_level(video_data),
            quality_score=video_data['quality_score'],
            
            content_match_score=content_score,
            difficulty_match_score=difficulty_score,
            topic_relevance_score=topic_score,
            semantic_similarity_score=semantic_score,
            popularity_score=popularity_score,
            composite_score=composite_score,
            
            recommendation_type=recommendation_type,
            confidence_level=confidence_level,
            learning_objective=learning_objective,
            target_error_pattern=target_error_pattern,
            prerequisite_concepts=self._identify_prerequisites(question_analysis),
            follow_up_topics=self._identify_follow_up_topics(question_analysis),
            
            estimated_watch_time=video_data['duration_seconds'],
            xp_value=xp_value,
            difficulty_progression=difficulty_progression,
            cognitive_load=cognitive_load
        )
    
    def _calculate_content_match_score(
        self,
        video_data: Dict[str, Any],
        question_analysis: QuestionAnalysis
    ) -> float:
        """Calculate content similarity score"""
        video_title = video_data.get('title', '').lower()
        video_topic = video_data.get('topic', '').lower()
        
        # Check for keyword matches
        keyword_matches = 0
        for keyword in question_analysis.content_keywords:
            if keyword.lower() in video_title or keyword.lower() in video_topic:
                keyword_matches += 1
        
        # Check for concept tag matches
        concept_matches = 0
        for concept in question_analysis.concept_tags:
            concept_clean = concept.replace('_', ' ')
            if concept_clean in video_title or concept_clean in video_topic:
                concept_matches += 1
        
        # Calculate score based on matches
        total_terms = len(question_analysis.content_keywords) + len(question_analysis.concept_tags)
        if total_terms == 0:
            return 0.5  # Default score
        
        match_ratio = (keyword_matches + concept_matches) / total_terms
        return min(1.0, match_ratio)
    
    def _calculate_difficulty_match_score(
        self,
        video_data: Dict[str, Any],
        question_analysis: QuestionAnalysis
    ) -> float:
        """Calculate difficulty alignment score"""
        question_difficulty = question_analysis.difficulty_theta
        
        # Map video level to difficulty scale
        video_level = video_data.get('nivel', 'medio').lower()
        video_difficulty_map = {
            'básico': -1.0,
            'basico': -1.0,
            'intermedio': 0.0,
            'medio': 0.0,
            'avanzado': 1.0,
            'advanced': 1.0
        }
        
        video_difficulty = video_difficulty_map.get(video_level, 0.0)
        
        # Calculate proximity score
        difficulty_diff = abs(question_difficulty - video_difficulty)
        
        # Score decreases as difference increases
        if difficulty_diff <= 0.5:
            return 1.0
        elif difficulty_diff <= 1.0:
            return 0.8
        elif difficulty_diff <= 1.5:
            return 0.6
        else:
            return 0.4
    
    def _calculate_topic_relevance_score(
        self,
        video_data: Dict[str, Any],
        question_analysis: QuestionAnalysis
    ) -> float:
        """Calculate topic relevance score"""
        video_topic = video_data.get('topic', '').lower()
        question_topic = question_analysis.topic.lower()
        
        if not video_topic or not question_topic:
            return 0.5
        
        # Direct topic match
        if question_topic in video_topic or video_topic in question_topic:
            return 1.0
        
        # Partial topic match using sequence matcher
        similarity = SequenceMatcher(None, question_topic, video_topic).ratio()
        return similarity
    
    def _calculate_semantic_similarity_score(
        self,
        video_data: Dict[str, Any],
        question_analysis: QuestionAnalysis
    ) -> float:
        """Calculate semantic similarity (simplified version)"""
        # This would ideally use embeddings or more sophisticated NLP
        # For now, use basic text similarity
        
        video_text = f"{video_data.get('title', '')} {video_data.get('topic', '')}".lower()
        question_text = question_analysis.question_text.lower()
        
        # Calculate word overlap
        video_words = set(video_text.split())
        question_words = set(question_text.split())
        
        if not video_words or not question_words:
            return 0.3
        
        intersection = video_words.intersection(question_words)
        union = video_words.union(question_words)
        
        jaccard_similarity = len(intersection) / len(union) if union else 0
        return jaccard_similarity
    
    def _calculate_popularity_score(self, video_data: Dict[str, Any]) -> float:
        """Calculate video popularity/quality score"""
        quality_score = float(video_data.get('quality_score', 0.5))
        educational_rating = float(video_data.get('educational_rating', 0.5))
        view_count = int(video_data.get('view_count', 0))
        
        # Normalize view count (log scale) - handle edge cases
        try:
            if view_count <= 0:
                view_score = 0.1
            else:
                log_views = np.log10(view_count)
                if np.isinf(log_views) or np.isnan(log_views):
                    view_score = 0.5
                else:
                    view_score = min(1.0, max(0.0, log_views / 6.0))
        except (ValueError, TypeError):
            view_score = 0.1
        
        # Combine scores - ensure no NaN or inf values
        quality_score = min(1.0, max(0.0, quality_score))
        educational_rating = min(1.0, max(0.0, educational_rating))
        
        popularity = (quality_score * 0.4 + educational_rating * 0.4 + view_score * 0.2)
        return min(1.0, max(0.0, popularity))
    
    def _determine_recommendation_type(
        self,
        question_analysis: QuestionAnalysis,
        video_data: Dict[str, Any]
    ) -> str:
        """Determine the type of recommendation"""
        if 'knowledge_gap' in question_analysis.error_indicators:
            return 'concept_introduction'
        elif 'procedural_error' in question_analysis.error_indicators:
            return 'step_by_step_solution'
        elif 'careless_mistake' in question_analysis.error_indicators:
            return 'practice_reinforcement'
        elif question_analysis.difficulty_theta > 0.5:
            return 'advanced_concept_building'
        else:
            return 'concept_review'
    
    def _determine_confidence_level(self, composite_score: float) -> str:
        """Determine confidence level based on composite score"""
        if composite_score >= 0.8:
            return 'high'
        elif composite_score >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _generate_learning_objective(
        self,
        question_analysis: QuestionAnalysis,
        video_data: Dict[str, Any]
    ) -> str:
        """Generate specific learning objective for the video"""
        topic = question_analysis.topic or video_data.get('topic', 'the concept')
        
        # Based on error patterns
        for error in question_analysis.error_indicators:
            if error in self.error_to_objective:
                return f"{self.error_to_objective[error]} in {topic}"
        
        # Default objective
        return f"Master {topic} concepts and applications"
    
    def _identify_target_error_pattern(self, question_analysis: QuestionAnalysis) -> str:
        """Identify the primary error pattern this video should address"""
        if question_analysis.error_indicators:
            return question_analysis.error_indicators[0]
        return 'general_understanding'
    
    def _identify_prerequisites(self, question_analysis: QuestionAnalysis) -> List[str]:
        """Identify prerequisite concepts"""
        topic = question_analysis.topic
        
        prerequisite_map = {
            'Quadratic Functions': ['Linear equations', 'Basic algebra'],
            'Trigonometry': ['Geometry basics', 'Angle measurement'],
            'Derivatives': ['Functions', 'Limits', 'Algebra'],
            'Stoichiometry': ['Chemical equations', 'Mole concept'],
            'Reading Comprehension': ['Vocabulary', 'Basic grammar']
        }
        
        return prerequisite_map.get(topic, ['Basic concepts'])
    
    def _identify_follow_up_topics(self, question_analysis: QuestionAnalysis) -> List[str]:
        """Identify follow-up topics to explore"""
        topic = question_analysis.topic
        
        followup_map = {
            'Linear Equations': ['Quadratic functions', 'Systems of equations'],
            'Basic Geometry': ['Coordinate geometry', 'Trigonometry'],
            'Algebra Basics': ['Functions', 'Polynomials'],
            'Cell Biology': ['Genetics', 'Evolution'],
            'Grammar': ['Writing techniques', 'Literature analysis']
        }
        
        return followup_map.get(topic, ['Advanced applications'])
    
    def _calculate_xp_value(self, video_data: Dict[str, Any], composite_score: float) -> int:
        """Calculate XP value for watching the video"""
        duration = video_data.get('duration_seconds', 0)
        quality = video_data.get('quality_score', 0.5)
        
        # Base XP from duration (5 XP per minute)
        base_xp = (duration // 60) * 5
        
        # Quality multiplier
        quality_multiplier = 0.5 + (quality * 0.5)
        
        # Match quality multiplier
        match_multiplier = 0.5 + (composite_score * 0.5)
        
        total_xp = int(base_xp * quality_multiplier * match_multiplier)
        return max(10, min(100, total_xp))  # Between 10-100 XP
    
    def _determine_difficulty_progression(
        self,
        question_analysis: QuestionAnalysis,
        video_data: Dict[str, Any]
    ) -> str:
        """Determine if video is prerequisite, at-level, or advanced"""
        question_difficulty = question_analysis.difficulty_theta
        video_level = video_data.get('nivel', 'medio').lower()
        
        if video_level in ['básico', 'basico'] and question_difficulty > -0.5:
            return 'prerequisite'
        elif video_level == 'avanzado' and question_difficulty < 0.5:
            return 'advanced'
        else:
            return 'at_level'
    
    def _map_difficulty_level(self, video_data: Dict[str, Any]) -> int:
        """Map video difficulty to numeric level"""
        nivel = video_data.get('nivel', 'medio').lower()
        
        level_map = {
            'básico': 1,
            'basico': 1,
            'intermedio': 2,
            'medio': 2,
            'avanzado': 3,
            'advanced': 3
        }
        
        return level_map.get(nivel, 2)
    
    async def _deduplicate_and_rank_videos(
        self,
        all_recommendations: List[VideoRecommendation],
        limit: int
    ) -> List[VideoRecommendation]:
        """Remove duplicates and rank videos globally"""
        # Remove duplicates by youtube_id
        seen_ids = set()
        unique_videos = []
        
        for video in all_recommendations:
            if video.youtube_id not in seen_ids:
                seen_ids.add(video.youtube_id)
                unique_videos.append(video)
        
        # Sort by composite score
        unique_videos.sort(key=lambda x: x.composite_score, reverse=True)
        
        return unique_videos[:limit]
    
    async def _organize_learning_progression(
        self,
        videos: List[VideoRecommendation],
        question_analyses: List[QuestionAnalysis]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Organize videos into learning progression"""
        progression = {
            'foundation': [],
            'skill_building': [],
            'mastery': [],
            'advanced': []
        }
        
        for video in videos:
            video_dict = asdict(video)
            
            if video.difficulty_progression == 'prerequisite':
                progression['foundation'].append(video_dict)
            elif video.recommendation_type in ['concept_introduction', 'concept_review']:
                progression['skill_building'].append(video_dict)
            elif video.recommendation_type == 'step_by_step_solution':
                progression['mastery'].append(video_dict)
            else:
                progression['advanced'].append(video_dict)
        
        return progression
    
    async def _generate_matching_metadata(
        self,
        question_analyses: List[QuestionAnalysis],
        videos: List[VideoRecommendation],
        question_video_map: Dict[str, List[VideoRecommendation]]
    ) -> Dict[str, Any]:
        """Generate comprehensive matching metadata"""
        
        # Calculate coverage statistics
        topics_covered = set()
        error_patterns_addressed = set()
        
        for analysis in question_analyses:
            topics_covered.add(analysis.topic)
            error_patterns_addressed.update(analysis.error_indicators)
        
        # Calculate confidence distribution
        confidence_dist = {'high': 0, 'medium': 0, 'low': 0}
        for video in videos:
            confidence_dist[video.confidence_level] += 1
        
        # Calculate recommendation type distribution
        rec_type_dist = {}
        for video in videos:
            rec_type_dist[video.recommendation_type] = rec_type_dist.get(video.recommendation_type, 0) + 1
        
        return {
            'coverage_analysis': {
                'topics_covered': list(topics_covered),
                'error_patterns_addressed': list(error_patterns_addressed),
                'questions_with_videos': len([q for q in question_video_map.values() if q]),
                'coverage_percentage': len([q for q in question_video_map.values() if q]) / len(question_analyses) * 100
            },
            'quality_metrics': {
                'average_composite_score': sum([v.composite_score for v in videos]) / len(videos) if videos else 0.0,
                'confidence_distribution': confidence_dist,
                'recommendation_type_distribution': rec_type_dist,
                'average_xp_value': sum([v.xp_value for v in videos]) / len(videos) if videos else 0.0
            },
            'learning_metrics': {
                'total_watch_time_minutes': sum(v.estimated_watch_time for v in videos) // 60,
                'difficulty_spread': {
                    'prerequisite': len([v for v in videos if v.difficulty_progression == 'prerequisite']),
                    'at_level': len([v for v in videos if v.difficulty_progression == 'at_level']),
                    'advanced': len([v for v in videos if v.difficulty_progression == 'advanced'])
                }
            }
        }
    
    def _calculate_confidence_summary(self, videos: List[VideoRecommendation]) -> Dict[str, Any]:
        """Calculate overall confidence summary"""
        if not videos:
            return {'overall_confidence': 'low', 'confidence_score': 0.0}
        
        # Calculate weighted confidence score
        confidence_weights = {'high': 1.0, 'medium': 0.6, 'low': 0.3}
        total_score = sum(confidence_weights[v.confidence_level] for v in videos)
        avg_score = total_score / len(videos)
        
        overall_confidence = 'high' if avg_score > 0.8 else 'medium' if avg_score > 0.5 else 'low'
        
        return {
            'overall_confidence': overall_confidence,
            'confidence_score': round(avg_score, 3),
            'high_confidence_count': len([v for v in videos if v.confidence_level == 'high']),
            'total_videos': len(videos)
        }