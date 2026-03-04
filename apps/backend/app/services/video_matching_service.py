"""
Unified Video Matching Service
Consolidates logic from various 'intelligent_video_*' services into a single,
pedagogically-driven video matching system. This service focuses on intelligently
matching failed questions with relevant video content.
"""

import asyncio
import logging
import json
import hashlib
import numpy as np
import time
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func
from difflib import SequenceMatcher # For fuzzy matching

# Import models
from ..models.question import Question
from ..models.youtube_catalog import YoutubeCatalog
from ..models.response import Response # For getting student's failed questions
from ..models.subject import Subject # For getting subject name
from ..models.topic import Topic # For getting topic name

# Import schemas (dataclasses and enums)
from ..schemas.video_matching import (
    FailedQuestion, ErrorAnalysis, VideoMatch, MatchingRequest, MatchingResult,
    ErrorType, MatchingStrategy, MatchingConfidence
)

# Placeholder for semantic similarity engine (will be part of this service)
# Placeholder for difficulty selector (will be part of this service)

logger = logging.getLogger(__name__)

# --- Configuration Constants (Can be moved to settings.py) ---
MIN_SIMILARITY_THRESHOLD = 0.3 # Minimum semantic similarity for a video to be considered
MAX_RECOMMENDATIONS_PER_QUESTION = 5 # Max videos to return per failed question
MAX_SEARCH_CANDIDATES = 100 # Max videos to retrieve from DB for scoring
EMBEDDING_MODEL_NAME = "text-embedding-ada-002"
EMBEDDING_DIMENSIONS = 1536 # OpenAI ada-002 model output dimension
FUZZY_MATCHING_THRESHOLD = 70 # Score for fuzzy matching (0-100)

# OpenAI and PGVector availability (from intelligent_video_mapper.py)
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

class VideoMatchingService:
    """
    Main service for intelligent video matching. Orchestrates error analysis,
    multi-strategy video search, scoring, and ranking.
    """

    def __init__(self, db: Session, openai_api_key: Optional[str] = None, enable_caching: bool = True):
        self.db = db
        self.openai_api_key = openai_api_key
        self.enable_caching = enable_caching
        self.embedding_cache = {} # Cache for OpenAI embeddings

        logger.info("VideoMatchingService initialized.")
    
    # --- Orchestration (from intelligent_question_video_matching_service.py) ---
    async def match_videos_for_failed_question(self, matching_request: MatchingRequest) -> MatchingResult:
        start_time = time.time()
        request_id = self._generate_request_id(matching_request)

        # Check cache first (simplified)
        if self.enable_caching and request_id in self.embedding_cache: # Using embedding cache for match cache
            cached_result = self.embedding_cache[request_id] # This is not ideal, a proper cache is needed
            cached_result.cache_hit = True
            logger.info(f"Cache hit for request {request_id}")
            return cached_result
        
        failed_question = matching_request.failed_question
        logger.info(f"Matching videos for failed question {failed_question.question_id} by student {failed_question.student_id}")

        # Step 1: Analyze the error (using integrated ErrorAnalyzer logic)
        error_analysis = self._analyze_failed_question(failed_question)
        
        # Step 2: Get candidate videos using cascading search
        candidate_videos = await self._get_candidate_videos_cascading(failed_question)
        
        if not candidate_videos:
            logger.warning("No candidate videos found.")
            return self._create_empty_result(request_id, failed_question, error_analysis)

        # Step 3: Score and rank videos (using integrated ranking logic)
        video_matches = await self._score_and_rank_videos(
            candidate_videos, matching_request, error_analysis, failed_question
        )
        
        # Step 4: Apply final filters and limits
        final_matches = self._apply_final_filters(video_matches, matching_request)
        
        # Step 5: Generate viewing order
        viewing_order = self._generate_viewing_order(final_matches, error_analysis)
        
        matching_time = (time.time() - start_time) * 1000
        
        result = MatchingResult(
            request_id=request_id,
            failed_question=failed_question,
            error_analysis=error_analysis,
            video_matches=final_matches,
            total_matches_found=len(candidate_videos),
            matching_time_ms=matching_time,
            algorithms_used=['semantic', 'topic', 'difficulty', 'error_analysis', 'fuzzy'],
            average_match_confidence=np.mean([m.overall_match_score for m in final_matches]) if final_matches else 0.0,
            coverage_score=self._calculate_coverage_score(final_matches, error_analysis),
            recommended_viewing_order=viewing_order,
            estimated_total_study_time=sum(m.duration_minutes for m in final_matches[:3]),
            result_timestamp=datetime.now(),
            cache_hit=False
        )
        
        if self.enable_caching:
            self.embedding_cache[request_id] = result # This is not ideal, a proper cache is needed
        
        logger.info(f"Found {len(final_matches)} video matches in {matching_time:.2f}ms")
        return result

    def _generate_request_id(self, matching_request: MatchingRequest) -> str:
        """Generate unique request ID for caching"""
        request_data = {
            'question_id': matching_request.failed_question.question_id,
            'student_id': matching_request.failed_question.student_id,
            'student_answer': matching_request.failed_question.student_answer,
            'max_videos': matching_request.max_videos,
            'min_confidence': matching_request.min_confidence
        }
        request_json = json.dumps(request_data, sort_keys=True, default=str) # Use default=str for datetime objects
        return hashlib.md5(request_json.encode()).hexdigest()
    
    def _create_empty_result(self, request_id: str, failed_question: FailedQuestion, error_analysis: ErrorAnalysis) -> MatchingResult:
        return MatchingResult(
            request_id=request_id,
            failed_question=failed_question,
            error_analysis=error_analysis,
            video_matches=[],
            total_matches_found=0,
            matching_time_ms=0.0,
            algorithms_used=[],
            average_match_confidence=0.0,
            coverage_score=0.0,
            recommended_viewing_order=[],
            estimated_total_study_time=0,
            result_timestamp=datetime.now(),
            cache_hit=False
        )

    # --- Error Analysis (integrated from intelligent_question_video_matching_service.py) ---
    def _analyze_failed_question(self, failed_question: FailedQuestion) -> ErrorAnalysis:
        # Simplified error analysis for brevity. Full implementation would integrate
        # the complex logic from the original ErrorAnalyzer class.
        
        primary_error_type = ErrorType.CONCEPTUAL # Default
        if "calculation" in failed_question.question_text.lower():
            primary_error_type = ErrorType.COMPUTATIONAL
        
        return ErrorAnalysis(
            question_id=failed_question.question_id,
            student_id=failed_question.student_id,
            primary_error_type=primary_error_type,
            secondary_error_types=[],
            error_confidence=0.7,
            distractor_analysis={},
            common_error_pattern="general_misunderstanding",
            error_frequency=0.5,
            time_pressure_indicator=0.0,
            prerequisite_gaps=[],
            conceptual_misunderstandings=[],
            intervention_priority=3,
            recommended_strategies=[MatchingStrategy.CONCEPT_REVIEW],
            analysis_timestamp=datetime.now(),
            analysis_confidence=0.7
        )
    
    # --- Video Search Strategy (Cascading - from intelligent_video_recommendation_engine.py) ---
    async def _get_candidate_videos_cascading(self, failed_question: FailedQuestion) -> List[Dict[str, Any]]:
        candidates = []
        
        # Strategy 1: Exact metadata match
        exact_matches = await self._find_exact_matches(failed_question)
        if exact_matches:
            candidates.extend(exact_matches)
            if len(candidates) >= MAX_SEARCH_CANDIDATES: return candidates[:MAX_SEARCH_CANDIDATES]

        # Strategy 2: Fuzzy text match
        fuzzy_matches = await self._find_fuzzy_matches(failed_question)
        if fuzzy_matches:
            candidates.extend(fuzzy_matches)
            if len(candidates) >= MAX_SEARCH_CANDIDATES: return candidates[:MAX_SEARCH_CANDIDATES]
        
        # Strategy 3: Semantic vector search
        semantic_matches = await self._find_semantic_matches(failed_question)
        if semantic_matches:
            candidates.extend(semantic_matches)
        
        # Deduplicate candidates (basic deduplication by youtube_id)
        unique_candidates = {v['youtube_id']: v for v in candidates}.values()
        return list(unique_candidates)[:MAX_SEARCH_CANDIDATES]
    
    async def _find_exact_matches(self, failed_question: FailedQuestion) -> List[Dict[str, Any]]:
        # This part needs to query YoutubeCatalog and filter very precisely
        query = text("""
            SELECT id, youtube_id, title, tema_principal, nivel_dificultad, youtube_url, channel_name, duration_seconds, area_evaluada
            FROM youtube_catalog
            WHERE tema_principal ILIKE :topic
            AND nivel_dificultad = :difficulty
            AND area_evaluada = :subject
            LIMIT 10
        """)
        params = {
            "topic": f"%{failed_question.topic}%",
            "difficulty": int(failed_question.question_difficulty) if failed_question.question_difficulty else 1, # Convert float to int
            "subject": failed_question.subject_area
        }
        results = self.db.execute(query, params).fetchall()
        
        return [self._convert_video_row_to_dict(row) for row in results]

    async def _find_fuzzy_matches(self, failed_question: FailedQuestion) -> List[Dict[str, Any]]:
        # Fuzzy matching using SequenceMatcher (or fuzzywuzzy if installed)
        # This will query a broader set and then filter in Python
        query = text("""
            SELECT id, youtube_id, title, tema_principal, nivel_dificultad, youtube_url, channel_name, duration_seconds, area_evaluada
            FROM youtube_catalog
            WHERE area_evaluada = :subject
            LIMIT 50
        """)
        params = {"subject": failed_question.subject_area}
        results = self.db.execute(query, params).fetchall()
        
        fuzzy_results = []
        for row in results:
            title_similarity = SequenceMatcher(None, failed_question.question_text, row.title).ratio() * 100
            topic_similarity = SequenceMatcher(None, failed_question.topic, row.tema_principal).ratio() * 100
            
            if title_similarity >= FUZZY_MATCHING_THRESHOLD or topic_similarity >= FUZZY_MATCHING_THRESHOLD:
                fuzzy_results.append(self._convert_video_row_to_dict(row))
        return fuzzy_results

    async def _find_semantic_matches(self, failed_question: FailedQuestion) -> List[Dict[str, Any]]:
        # This part needs OpenAI embeddings and pgvector
        # Simplified for now as full implementation requires specific DB setup and API keys
        logger.warning("Semantic search is a placeholder. Requires OpenAI API key and pgvector setup.")
        # Dummy data for semantic matches
        return [] # Implement actual semantic search here

    # --- Video Scoring and Ranking (from _fallback_intelligent_ranking in intelligent_video_matching_service.py) ---
    async def _score_and_rank_videos(
        self, 
        candidate_videos: List[Dict[str, Any]], 
        matching_request: MatchingRequest, 
        error_analysis: ErrorAnalysis,
        failed_question: FailedQuestion
    ) -> List[VideoMatch]:
        
        scored_videos = []
        for video_data in candidate_videos:
            # Calculate individual scores
            content_score = self._calculate_content_match_score(video_data, failed_question)
            difficulty_score = self._calculate_difficulty_match_score(video_data, failed_question)
            topic_score = self._calculate_topic_relevance_score(video_data, failed_question)
            error_addressing_score = self._calculate_error_addressing_score(video_data, error_analysis)
            
            # Combine into overall score (using ranking_weights)
            overall_score = (
                content_score * self.ranking_weights['semantic_similarity'] + # Re-using semantic weight for content
                difficulty_score * self.ranking_weights['difficulty_match'] +
                topic_score * self.ranking_weights['topic_relevance'] +
                error_addressing_score * self.ranking_weights['error_addressing']
            )
            
            confidence = self._determine_confidence_level(overall_score)
            
            # Placeholder for predicted outcomes
            predicted_outcomes = {
                "expected_learning_impact": overall_score * 0.8,
                "estimated_watch_time": video_data.get('duration_seconds', 0),
                "success_probability_improvement": overall_score * 0.2
            }
            
            video_match = VideoMatch(
                video_id=video_data.get('id', ''),
                video_title=video_data.get('title', ''),
                video_url=video_data.get('youtube_url', ''),
                semantic_similarity_score=content_score, # Placeholder
                topic_relevance_score=topic_score,
                difficulty_appropriateness_score=difficulty_score,
                overall_match_score=overall_score,
                confidence_level=confidence,
                match_reasons=[], # Populate based on individual scores
                addressing_error_types=[], # From error_analysis
                matching_strategies=[], # From error_analysis
                predicted_outcomes=predicted_outcomes,
                duration_minutes=video_data.get('duration_seconds', 0) // 60,
                channel_name=video_data.get('channel_name', ''),
                engagement_metrics={}, # Placeholder
                matched_at=datetime.now(),
                matching_algorithm_version="1.0"
            )
            scored_videos.append(video_match)
        
        scored_videos.sort(key=lambda x: x.overall_match_score, reverse=True)
        return scored_videos
    
    # --- Helper methods for scoring (from intelligent_video_matching_service.py) ---
    def _calculate_content_match_score(self, video_data: Dict[str, Any], failed_question: FailedQuestion) -> float:
        # Simplified: check keyword overlap in title/description with question text
        video_text = f"{video_data.get('title', '')} {video_data.get('tema_principal', '')} {video_data.get('description', '')}".lower()
        question_text = failed_question.question_text.lower()
        
        video_words = set(re.findall(r'\b\w+\b', video_text))
        question_words = set(re.findall(r'\b\w+\b', question_text))
        
        if not video_words or not question_words: return 0.0
        
        common_words = len(video_words.intersection(question_words))
        return common_words / max(len(video_words.union(question_words)), 1)
    
    def _calculate_difficulty_match_score(self, video_data: Dict[str, Any], failed_question: FailedQuestion) -> float:
        # Simplified: direct comparison of integer difficulty levels
        video_difficulty = video_data.get('nivel_dificultad', 3) # Assume 1-5 scale
        question_difficulty = int(failed_question.question_difficulty) if failed_question.question_difficulty else 1 # Assuming this is mapped to 1-5
        
        diff = abs(video_difficulty - question_difficulty)
        if diff == 0: return 1.0
        if diff == 1: return 0.7
        if diff == 2: return 0.4
        return 0.1
    
    def _calculate_topic_relevance_score(self, video_data: Dict[str, Any], failed_question: FailedQuestion) -> float:
        # Check if video topic/subject matches question topic/subject
        video_topic = video_data.get('tema_principal', '').lower()
        video_subject = video_data.get('area_evaluada', '').lower()
        
        question_topic = failed_question.topic.lower()
        question_subject = failed_question.subject_area.lower()
        
        score = 0.0
        if question_topic in video_topic: score += 0.5
        if question_subject in video_subject: score += 0.5
        return score
    
    def _calculate_error_addressing_score(self, video_data: Dict[str, Any], error_analysis: ErrorAnalysis) -> float:
        # Placeholder for complex logic. In full implementation, this would
        # check if video content directly addresses error_analysis.primary_error_type
        return 0.5 # Default score
    
    def _determine_confidence_level(self, overall_score: float) -> MatchingConfidence:
        if overall_score >= 0.85: return MatchingConfidence.VERY_HIGH
        if overall_score >= 0.7: return MatchingConfidence.HIGH
        if overall_score >= 0.5: return MatchingConfidence.MODERATE
        return MatchingConfidence.LOW

    # --- Final Filtering and Ordering ---
    def _apply_final_filters(self, video_matches: List[VideoMatch], matching_request: MatchingRequest) -> List[VideoMatch]:
        filtered_matches = [
            match for match in video_matches 
            if match.overall_match_score >= matching_request.min_confidence
            and match.duration_minutes <= matching_request.max_duration_minutes
        ]
        return filtered_matches[:matching_request.max_videos]

    def _generate_viewing_order(self, video_matches: List[VideoMatch], error_analysis: ErrorAnalysis) -> List[Union[int, str]]:
        # For simplicity, just return video IDs sorted by overall_match_score
        return [match.video_id for match in video_matches]
    
    def _calculate_coverage_score(self, video_matches: List[VideoMatch], error_analysis: ErrorAnalysis) -> float:
        # Placeholder for complex coverage score calculation
        return 0.0

    # --- Utility functions ---
    def _convert_video_row_to_dict(self, row: Any) -> Dict[str, Any]:
        # Helper to convert a SQLAlchemy row object to a dictionary
        # Assumes row has attributes like youtube_id, title, tema_principal, etc.
        return {
            "id": str(row.id), # Assuming ID from YoutubeCatalog
            "youtube_id": row.youtube_id,
            "title": row.title,
            "tema_principal": row.tema_principal,
            "nivel_dificultad": row.nivel_dificultad,
            "youtube_url": row.youtube_url, # Assuming it exists
            "channel_name": row.channel_name, # Assuming it exists
            "duration_seconds": row.duration_seconds, # Assuming it exists
            "area_evaluada": row.area_evaluada # Assuming it exists
            # ... other fields as needed
        }

