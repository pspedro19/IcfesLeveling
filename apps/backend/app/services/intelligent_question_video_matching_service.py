#!/usr/bin/env python3
"""
Intelligent Question-Video Matching Service with Contextual Error Analysis
========================================================================

A comprehensive service that intelligently matches failed ICFES questions 
with relevant YouTube educational videos using advanced semantic similarity,
multi-dimensional filtering, difficulty-appropriate selection, and 
contextual error analysis.

Features:
- Failed question contextual analysis
- Error pattern recognition and classification  
- Multi-algorithmic video matching pipeline
- Confidence scoring and explanation generation
- Real-time matching with caching optimization
- Learning analytics and effectiveness tracking
- Adaptive recommendation improvement

Author: Claude Code Assistant (Video Matching Specialist)
Date: 2025-09-11
"""

import asyncio
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
import hashlib
import time

# Import our advanced services
from .advanced_semantic_similarity_engine import (
    AdvancedSemanticSimilarityEngine, ContentItem, SimilarityResult,
    EmbeddingModel, SimilarityMetric, create_similarity_engine
)
from .multidimensional_topic_filter import (
    MultidimensionalTopicFilter, FilterCriteria, FilterResult, 
    StudentProfile, ContentMetadata, ICFESCompetency, CognitiveLevel,
    create_filter_from_failed_question
)
from .difficulty_appropriate_content_selector import (
    DifficultyAppropriateContentSelector, DifficultySelectionCriteria,
    DifficultySelectionResult, StudentAbility, LearningProgression,
    create_default_selection_criteria
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Types of errors students make"""
    CONCEPTUAL = "conceptual"           # Misunderstanding of concepts
    PROCEDURAL = "procedural"           # Wrong procedures or methods
    COMPUTATIONAL = "computational"     # Calculation errors
    INTERPRETIVE = "interpretive"       # Misinterpretation of questions
    ATTENTION = "attention"             # Careless mistakes
    KNOWLEDGE_GAP = "knowledge_gap"     # Missing prerequisite knowledge
    LINGUISTIC = "linguistic"           # Language comprehension issues
    STRATEGIC = "strategic"             # Wrong problem-solving strategy

class MatchingStrategy(Enum):
    """Video matching strategies"""
    DIRECT_REMEDIATION = "direct_remediation"       # Address specific error
    CONCEPT_REVIEW = "concept_review"               # Review underlying concepts  
    SKILL_BUILDING = "skill_building"               # Build related skills
    PREREQUISITE_FILLING = "prerequisite_filling"  # Fill knowledge gaps
    STRATEGIC_TRAINING = "strategic_training"       # Teach problem-solving strategies
    COMPREHENSIVE = "comprehensive"                 # Multiple strategies combined

class MatchingConfidence(Enum):
    """Confidence levels for matches"""
    VERY_HIGH = "very_high"     # 90%+ confidence
    HIGH = "high"               # 75-89% confidence  
    MODERATE = "moderate"       # 60-74% confidence
    LOW = "low"                 # 45-59% confidence
    VERY_LOW = "very_low"       # < 45% confidence

@dataclass
class FailedQuestion:
    """Represents a failed question with context"""
    question_id: Union[int, str]
    student_id: str
    
    # Question content
    question_text: str
    question_type: str  # multiple_choice, open_ended, etc.
    correct_answer: str
    student_answer: str
    distractors: List[str]
    
    # ICFES metadata
    subject_area: str
    topic: str
    subtopic: str
    competency: str
    component: str
    cognitive_level: str
    
    # Context and timing
    time_spent_seconds: int
    attempt_number: int
    failed_at: datetime
    diagnostic_session_id: Optional[str] = None
    
    # Student performance context
    student_theta: float = 0.0
    question_difficulty: float = 0.0
    success_probability: float = 0.0
    
    # Additional metadata
    question_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorAnalysis:
    """Analysis of why a question was answered incorrectly"""
    question_id: Union[int, str]
    student_id: str
    
    # Error classification
    primary_error_type: ErrorType
    secondary_error_types: List[ErrorType]
    error_confidence: float
    
    # Error patterns
    distractor_analysis: Dict[str, Any]
    common_error_pattern: str
    error_frequency: float  # How common this error is
    
    # Contextual factors
    time_pressure_indicator: float  # 0-1 scale
    prerequisite_gaps: List[str]
    conceptual_misunderstandings: List[str]
    
    # Recommendations
    intervention_priority: int  # 1-5, 5 being highest priority
    recommended_strategies: List[MatchingStrategy]
    
    # Analysis metadata
    analysis_timestamp: datetime
    analysis_confidence: float

@dataclass
class VideoMatch:
    """A matched video with detailed scoring"""
    video_id: Union[int, str]
    video_title: str
    video_url: str
    
    # Matching scores from different algorithms
    semantic_similarity_score: float
    topic_relevance_score: float
    difficulty_appropriateness_score: float
    
    # Combined scores
    overall_match_score: float
    confidence_level: MatchingConfidence
    
    # Matching explanations
    match_reasons: List[str]
    addressing_error_types: List[ErrorType]
    matching_strategies: List[MatchingStrategy]
    
    # Predicted outcomes
    expected_learning_impact: float
    estimated_watch_time: int
    success_probability_improvement: float
    
    # Video metadata
    duration_minutes: int
    channel_name: str
    engagement_metrics: Dict[str, float]
    
    # Selection metadata
    matched_at: datetime
    matching_algorithm_version: str

@dataclass
class MatchingRequest:
    """Request for video matching"""
    failed_question: FailedQuestion
    student_profile: Optional[StudentProfile] = None
    
    # Matching preferences
    max_videos: int = 10
    min_confidence: float = 0.4
    preferred_strategies: List[MatchingStrategy] = field(default_factory=list)
    max_duration_minutes: int = 30
    
    # Filters
    exclude_watched_videos: bool = True
    require_high_engagement: bool = False
    language_preference: str = "es"
    
    # Context
    session_context: Dict[str, Any] = field(default_factory=dict)
    request_timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class MatchingResult:
    """Complete result of video matching"""
    request_id: str
    failed_question: FailedQuestion
    error_analysis: ErrorAnalysis
    
    # Matched videos
    video_matches: List[VideoMatch]
    total_matches_found: int
    
    # Performance metrics
    matching_time_ms: float
    algorithms_used: List[str]
    
    # Quality metrics
    average_match_confidence: float
    coverage_score: float  # How well matches address the error
    
    # Recommendations
    recommended_viewing_order: List[Union[int, str]]  # Video IDs in order
    estimated_total_study_time: int
    
    # Result metadata
    result_timestamp: datetime
    cache_hit: bool = False

class ErrorAnalyzer:
    """Analyzes student errors to understand failure patterns"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.error_patterns = self._load_error_patterns()
        self.distractor_analysis_cache = {}
    
    def analyze_failed_question(self, failed_question: FailedQuestion) -> ErrorAnalysis:
        """Analyze why a question was failed"""
        
        # Analyze distractor choice
        distractor_analysis = self._analyze_distractor_choice(failed_question)
        
        # Identify primary error type
        primary_error_type = self._classify_primary_error(failed_question, distractor_analysis)
        
        # Identify secondary error types
        secondary_error_types = self._identify_secondary_errors(failed_question, distractor_analysis)
        
        # Analyze time pressure
        time_pressure = self._analyze_time_pressure(failed_question)
        
        # Identify prerequisite gaps
        prerequisite_gaps = self._identify_prerequisite_gaps(failed_question)
        
        # Identify conceptual misunderstandings
        conceptual_issues = self._identify_conceptual_misunderstandings(
            failed_question, distractor_analysis
        )
        
        # Calculate intervention priority
        priority = self._calculate_intervention_priority(
            primary_error_type, secondary_error_types, failed_question
        )
        
        # Recommend strategies
        strategies = self._recommend_matching_strategies(
            primary_error_type, secondary_error_types, prerequisite_gaps
        )
        
        # Calculate analysis confidence
        confidence = self._calculate_analysis_confidence(
            distractor_analysis, failed_question
        )
        
        return ErrorAnalysis(
            question_id=failed_question.question_id,
            student_id=failed_question.student_id,
            primary_error_type=primary_error_type,
            secondary_error_types=secondary_error_types,
            error_confidence=confidence,
            distractor_analysis=distractor_analysis,
            common_error_pattern=self._identify_error_pattern(failed_question),
            error_frequency=self._calculate_error_frequency(failed_question),
            time_pressure_indicator=time_pressure,
            prerequisite_gaps=prerequisite_gaps,
            conceptual_misunderstandings=conceptual_issues,
            intervention_priority=priority,
            recommended_strategies=strategies,
            analysis_timestamp=datetime.now(),
            analysis_confidence=confidence
        )
    
    def _analyze_distractor_choice(self, failed_question: FailedQuestion) -> Dict[str, Any]:
        """Analyze the chosen distractor to understand the error"""
        
        cache_key = f"{failed_question.question_id}_{failed_question.student_answer}"
        if cache_key in self.distractor_analysis_cache:
            return self.distractor_analysis_cache[cache_key]
        
        analysis = {
            'chosen_distractor': failed_question.student_answer,
            'correct_answer': failed_question.correct_answer,
            'distractor_type': 'unknown',
            'error_attraction_reason': '',
            'difficulty_level': 'moderate'
        }
        
        try:
            # Query distractor analysis from database
            query = text("""
                SELECT 
                    da.distractor_option,
                    da.error_type,
                    da.attraction_reason,
                    da.frequency_chosen,
                    da.difficulty_indicator
                FROM distractor_analysis da
                WHERE da.question_id = :question_id 
                    AND da.distractor_option = :student_answer
            """)
            
            result = self.db.execute(query, {
                'question_id': failed_question.question_id,
                'student_answer': failed_question.student_answer
            }).fetchone()
            
            if result:
                analysis.update({
                    'distractor_type': result.error_type or 'unknown',
                    'error_attraction_reason': result.attraction_reason or '',
                    'frequency_chosen': result.frequency_chosen or 0.0,
                    'difficulty_level': result.difficulty_indicator or 'moderate'
                })
            
        except Exception as e:
            logger.warning(f"Could not analyze distractor: {e}")
        
        # Apply heuristic analysis if no database data
        if analysis['distractor_type'] == 'unknown':
            analysis = self._heuristic_distractor_analysis(failed_question, analysis)
        
        self.distractor_analysis_cache[cache_key] = analysis
        return analysis
    
    def _heuristic_distractor_analysis(self, failed_question: FailedQuestion, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Apply heuristic rules to analyze distractors"""
        
        student_answer = failed_question.student_answer
        correct_answer = failed_question.correct_answer
        
        # Numeric answer analysis
        try:
            student_num = float(student_answer)
            correct_num = float(correct_answer)
            
            ratio = student_num / correct_num if correct_num != 0 else 1
            
            if 0.9 <= ratio <= 1.1:
                analysis['distractor_type'] = 'computational'
                analysis['error_attraction_reason'] = 'minor calculation error'
            elif ratio > 2 or ratio < 0.5:
                analysis['distractor_type'] = 'conceptual'
                analysis['error_attraction_reason'] = 'major conceptual misunderstanding'
            else:
                analysis['distractor_type'] = 'procedural'
                analysis['error_attraction_reason'] = 'procedural error'
        
        except ValueError:
            # Non-numeric answers
            if len(student_answer) == 1 and len(correct_answer) == 1:
                # Multiple choice
                analysis['distractor_type'] = 'interpretive'
                analysis['error_attraction_reason'] = 'misinterpretation of question or options'
            else:
                analysis['distractor_type'] = 'conceptual'
                analysis['error_attraction_reason'] = 'conceptual misunderstanding'
        
        return analysis
    
    def _classify_primary_error(self, failed_question: FailedQuestion, distractor_analysis: Dict[str, Any]) -> ErrorType:
        """Classify the primary type of error"""
        
        distractor_type = distractor_analysis.get('distractor_type', 'unknown')
        time_spent = failed_question.time_spent_seconds
        expected_time = self._get_expected_time(failed_question)
        
        # Map distractor analysis to error types
        distractor_error_map = {
            'computational': ErrorType.COMPUTATIONAL,
            'conceptual': ErrorType.CONCEPTUAL,
            'procedural': ErrorType.PROCEDURAL,
            'interpretive': ErrorType.INTERPRETIVE
        }
        
        if distractor_type in distractor_error_map:
            primary_error = distractor_error_map[distractor_type]
        else:
            # Use time-based heuristics
            if time_spent < expected_time * 0.5:
                primary_error = ErrorType.ATTENTION
            elif time_spent > expected_time * 2:
                primary_error = ErrorType.KNOWLEDGE_GAP
            else:
                primary_error = ErrorType.CONCEPTUAL
        
        return primary_error
    
    def _identify_secondary_errors(self, failed_question: FailedQuestion, distractor_analysis: Dict[str, Any]) -> List[ErrorType]:
        """Identify secondary error types"""
        
        secondary_errors = []
        
        # Check for time pressure
        if self._analyze_time_pressure(failed_question) > 0.7:
            secondary_errors.append(ErrorType.ATTENTION)
        
        # Check for linguistic issues (if available)
        if failed_question.question_metadata.get('linguistic_complexity', 0) > 0.7:
            secondary_errors.append(ErrorType.LINGUISTIC)
        
        # Check for strategic errors
        if failed_question.cognitive_level in ['aplicar', 'analizar', 'evaluar']:
            secondary_errors.append(ErrorType.STRATEGIC)
        
        return secondary_errors
    
    def _analyze_time_pressure(self, failed_question: FailedQuestion) -> float:
        """Analyze if time pressure contributed to the error"""
        
        time_spent = failed_question.time_spent_seconds
        expected_time = self._get_expected_time(failed_question)
        
        if expected_time == 0:
            return 0.0
        
        time_ratio = time_spent / expected_time
        
        # Time pressure indicator (0-1 scale)
        if time_ratio < 0.3:
            return 0.9  # Very rushed
        elif time_ratio < 0.5:
            return 0.7  # Somewhat rushed
        elif time_ratio < 0.8:
            return 0.3  # Slightly rushed
        else:
            return 0.0  # Adequate time
    
    def _get_expected_time(self, failed_question: FailedQuestion) -> int:
        """Get expected time for question based on type and difficulty"""
        
        base_times = {
            'multiple_choice': 90,  # seconds
            'numerical': 120,
            'short_answer': 150,
            'essay': 300
        }
        
        base_time = base_times.get(failed_question.question_type, 120)
        
        # Adjust for difficulty
        difficulty_factor = 1.0 + (failed_question.question_difficulty * 0.5)
        
        return int(base_time * difficulty_factor)
    
    def _identify_prerequisite_gaps(self, failed_question: FailedQuestion) -> List[str]:
        """Identify missing prerequisite knowledge"""
        
        try:
            query = text("""
                SELECT DISTINCT pt.prerequisite_topic
                FROM prerequisite_topics pt
                JOIN topics t ON pt.topic_id = t.id
                WHERE t.name = :topic AND t.subject_id = (
                    SELECT id FROM subjects WHERE name = :subject
                )
            """)
            
            results = self.db.execute(query, {
                'topic': failed_question.topic,
                'subject': failed_question.subject_area
            }).fetchall()
            
            return [row.prerequisite_topic for row in results]
            
        except Exception as e:
            logger.warning(f"Could not identify prerequisites: {e}")
            return []
    
    def _identify_conceptual_misunderstandings(self, failed_question: FailedQuestion, distractor_analysis: Dict[str, Any]) -> List[str]:
        """Identify conceptual misunderstandings"""
        
        misunderstandings = []
        
        # Based on distractor analysis
        if distractor_analysis.get('distractor_type') == 'conceptual':
            reason = distractor_analysis.get('error_attraction_reason', '')
            if reason:
                misunderstandings.append(reason)
        
        # Subject-specific heuristics
        if failed_question.subject_area == 'Matemáticas':
            if 'algebra' in failed_question.topic.lower():
                misunderstandings.append('confusión entre variables y constantes')
            elif 'geometria' in failed_question.topic.lower():
                misunderstandings.append('confusión en propiedades geométricas')
        
        return misunderstandings
    
    def _calculate_intervention_priority(self, primary_error: ErrorType, secondary_errors: List[ErrorType], failed_question: FailedQuestion) -> int:
        """Calculate intervention priority (1-5)"""
        
        # Base priority by error type
        error_priorities = {
            ErrorType.KNOWLEDGE_GAP: 5,
            ErrorType.CONCEPTUAL: 4,
            ErrorType.PROCEDURAL: 3,
            ErrorType.STRATEGIC: 3,
            ErrorType.INTERPRETIVE: 2,
            ErrorType.COMPUTATIONAL: 2,
            ErrorType.LINGUISTIC: 2,
            ErrorType.ATTENTION: 1
        }
        
        base_priority = error_priorities.get(primary_error, 3)
        
        # Adjust for secondary errors
        if len(secondary_errors) >= 2:
            base_priority = min(5, base_priority + 1)
        
        # Adjust for question importance (competency weight)
        if failed_question.competency in ['razonamiento', 'uso comprensivo', 'interpretacion']:
            base_priority = min(5, base_priority + 1)
        
        return base_priority
    
    def _recommend_matching_strategies(self, primary_error: ErrorType, secondary_errors: List[ErrorType], prerequisites: List[str]) -> List[MatchingStrategy]:
        """Recommend video matching strategies"""
        
        strategies = []
        
        # Primary strategy based on error type
        error_strategy_map = {
            ErrorType.CONCEPTUAL: MatchingStrategy.CONCEPT_REVIEW,
            ErrorType.PROCEDURAL: MatchingStrategy.SKILL_BUILDING,
            ErrorType.KNOWLEDGE_GAP: MatchingStrategy.PREREQUISITE_FILLING,
            ErrorType.STRATEGIC: MatchingStrategy.STRATEGIC_TRAINING,
            ErrorType.COMPUTATIONAL: MatchingStrategy.SKILL_BUILDING,
            ErrorType.INTERPRETIVE: MatchingStrategy.DIRECT_REMEDIATION,
            ErrorType.LINGUISTIC: MatchingStrategy.DIRECT_REMEDIATION,
            ErrorType.ATTENTION: MatchingStrategy.STRATEGIC_TRAINING
        }
        
        primary_strategy = error_strategy_map.get(primary_error, MatchingStrategy.CONCEPT_REVIEW)
        strategies.append(primary_strategy)
        
        # Add strategies for secondary errors
        for secondary_error in secondary_errors:
            secondary_strategy = error_strategy_map.get(secondary_error)
            if secondary_strategy and secondary_strategy not in strategies:
                strategies.append(secondary_strategy)
        
        # Add prerequisite strategy if needed
        if prerequisites and MatchingStrategy.PREREQUISITE_FILLING not in strategies:
            strategies.append(MatchingStrategy.PREREQUISITE_FILLING)
        
        # Add comprehensive strategy for complex cases
        if len(strategies) >= 3:
            strategies.append(MatchingStrategy.COMPREHENSIVE)
        
        return strategies[:3]  # Limit to top 3 strategies
    
    def _identify_error_pattern(self, failed_question: FailedQuestion) -> str:
        """Identify common error pattern"""
        
        # This would use historical data to identify patterns
        # For now, return a simple pattern based on subject and error
        
        subject = failed_question.subject_area.lower()
        topic = failed_question.topic.lower()
        
        pattern_templates = {
            'matemáticas': {
                'algebra': 'error_algebraic_manipulation',
                'geometria': 'error_spatial_reasoning',
                'estadistica': 'error_probability_interpretation'
            },
            'física': {
                'mecanica': 'error_force_analysis',
                'termodinamica': 'error_energy_conservation'
            },
            'química': {
                'estequiometria': 'error_molar_calculations',
                'equilibrio': 'error_equilibrium_concepts'
            }
        }
        
        return pattern_templates.get(subject, {}).get(topic, 'general_error_pattern')
    
    def _calculate_error_frequency(self, failed_question: FailedQuestion) -> float:
        """Calculate how common this error is"""
        
        try:
            query = text("""
                SELECT COUNT(*) as error_count,
                       (SELECT COUNT(*) FROM responses WHERE question_id = :question_id) as total_responses
                FROM responses 
                WHERE question_id = :question_id 
                    AND is_correct = false 
                    AND selected_option = :student_answer
            """)
            
            result = self.db.execute(query, {
                'question_id': failed_question.question_id,
                'student_answer': failed_question.student_answer
            }).fetchone()
            
            if result and result.total_responses > 0:
                return result.error_count / result.total_responses
            else:
                return 0.5  # Default frequency
                
        except Exception as e:
            logger.warning(f"Could not calculate error frequency: {e}")
            return 0.5
    
    def _calculate_analysis_confidence(self, distractor_analysis: Dict[str, Any], failed_question: FailedQuestion) -> float:
        """Calculate confidence in error analysis"""
        
        confidence = 0.5  # Base confidence
        
        # Boost confidence if we have distractor analysis
        if distractor_analysis.get('distractor_type') != 'unknown':
            confidence += 0.2
        
        # Boost confidence if we have timing data
        if failed_question.time_spent_seconds > 0:
            confidence += 0.1
        
        # Boost confidence if we have multiple attempts
        if failed_question.attempt_number > 1:
            confidence += 0.1
        
        # Boost confidence if we have complete metadata
        if failed_question.question_metadata:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _load_error_patterns(self) -> Dict[str, Any]:
        """Load common error patterns from database or configuration"""
        
        # This would load from database in a real implementation
        return {
            'mathematical_errors': {
                'sign_errors': 0.15,
                'operation_errors': 0.12,
                'algebraic_manipulation': 0.18
            },
            'scientific_errors': {
                'unit_confusion': 0.10,
                'formula_application': 0.14,
                'concept_mixing': 0.16
            },
            'language_errors': {
                'misinterpretation': 0.20,
                'vocabulary_confusion': 0.08
            }
        }

class IntelligentQuestionVideoMatchingService:
    """Main service for intelligent question-video matching"""
    
    def __init__(
        self, 
        db_session: Session,
        openai_api_key: Optional[str] = None,
        enable_caching: bool = True
    ):
        self.db = db_session
        self.enable_caching = enable_caching
        
        # Initialize component services
        self.error_analyzer = ErrorAnalyzer(db_session)
        self.similarity_engine = create_similarity_engine(
            openai_api_key=openai_api_key,
            enable_caching=enable_caching
        )
        self.topic_filter = MultidimensionalTopicFilter(db_session)
        self.difficulty_selector = DifficultyAppropriateContentSelector(db_session)
        
        # Matching configuration
        self.algorithm_weights = {
            'semantic_similarity': 0.35,
            'topic_relevance': 0.30,
            'difficulty_appropriateness': 0.25,
            'error_addressing': 0.10
        }
        
        # Cache for repeated requests
        self.match_cache = {}
        
    async def match_videos_for_failed_question(
        self, 
        matching_request: MatchingRequest
    ) -> MatchingResult:
        """Main method to match videos for a failed question"""
        
        start_time = time.time()
        request_id = self._generate_request_id(matching_request)
        
        # Check cache first
        if self.enable_caching and request_id in self.match_cache:
            cached_result = self.match_cache[request_id]
            cached_result.cache_hit = True
            logger.info(f"Cache hit for request {request_id}")
            return cached_result
        
        failed_question = matching_request.failed_question
        
        logger.info(f"Matching videos for failed question {failed_question.question_id} "
                   f"by student {failed_question.student_id}")
        
        # Step 1: Analyze the error
        error_analysis = self.error_analyzer.analyze_failed_question(failed_question)
        
        # Step 2: Get candidate videos using multiple algorithms
        candidate_videos = await self._get_candidate_videos(matching_request, error_analysis)
        
        if not candidate_videos:
            logger.warning("No candidate videos found")
            return self._create_empty_result(request_id, failed_question, error_analysis)
        
        # Step 3: Score and rank videos
        video_matches = await self._score_and_rank_videos(
            candidate_videos, matching_request, error_analysis
        )
        
        # Step 4: Apply final filters and limits
        final_matches = self._apply_final_filters(video_matches, matching_request)
        
        # Step 5: Generate viewing recommendations
        viewing_order = self._generate_viewing_order(final_matches, error_analysis)
        
        # Step 6: Calculate performance metrics
        matching_time = (time.time() - start_time) * 1000
        
        # Create result
        result = MatchingResult(
            request_id=request_id,
            failed_question=failed_question,
            error_analysis=error_analysis,
            video_matches=final_matches,
            total_matches_found=len(candidate_videos),
            matching_time_ms=matching_time,
            algorithms_used=['semantic', 'topic', 'difficulty', 'error_analysis'],
            average_match_confidence=np.mean([m.overall_match_score for m in final_matches]) if final_matches else 0.0,
            coverage_score=self._calculate_coverage_score(final_matches, error_analysis),
            recommended_viewing_order=viewing_order,
            estimated_total_study_time=sum(m.duration_minutes for m in final_matches[:3]),  # Top 3 videos
            result_timestamp=datetime.now(),
            cache_hit=False
        )
        
        # Cache result
        if self.enable_caching:
            self.match_cache[request_id] = result
        
        logger.info(f"Found {len(final_matches)} video matches in {matching_time:.2f}ms")
        return result
    
    async def _get_candidate_videos(
        self, 
        matching_request: MatchingRequest, 
        error_analysis: ErrorAnalysis
    ) -> List[ContentItem]:
        """Get candidate videos using multiple strategies"""
        
        failed_question = matching_request.failed_question
        candidates = set()  # Use set to avoid duplicates
        
        # Strategy 1: Semantic similarity
        semantic_candidates = await self._get_semantic_candidates(failed_question)
        candidates.update(semantic_candidates)
        
        # Strategy 2: Topic-based filtering
        topic_candidates = await self._get_topic_candidates(failed_question, matching_request)
        candidates.update(topic_candidates)
        
        # Strategy 3: Error-specific targeting
        error_candidates = await self._get_error_specific_candidates(failed_question, error_analysis)
        candidates.update(error_candidates)
        
        # Strategy 4: Difficulty-appropriate selection
        difficulty_candidates = await self._get_difficulty_candidates(failed_question, matching_request)
        candidates.update(difficulty_candidates)
        
        return list(candidates)
    
    async def _get_semantic_candidates(self, failed_question: FailedQuestion) -> List[ContentItem]:
        """Get candidates using semantic similarity"""
        
        # Create content item from failed question
        question_item = ContentItem(
            id=failed_question.question_id,
            title=f"Pregunta de {failed_question.subject_area}",
            description=failed_question.question_text,
            content_type="question",
            subject_area=failed_question.subject_area,
            topic=failed_question.topic,
            competency=failed_question.competency,
            difficulty_level=str(int(failed_question.question_difficulty))
        )
        
        # Get video candidates from database
        video_candidates = await self._load_video_candidates(failed_question.subject_area)
        
        if not video_candidates:
            return []
        
        # Find similar content
        similarity_results = await self.similarity_engine.find_most_similar_content(
            query_item=question_item,
            candidate_items=video_candidates,
            top_k=20  # Get top 20 semantic matches
        )
        
        # Convert similarity results to content items
        semantic_candidates = []
        for result in similarity_results:
            if result.similarity_score >= 0.3:  # Minimum similarity threshold
                for candidate in video_candidates:
                    if candidate.id == result.content_id:
                        semantic_candidates.append(candidate)
                        break
        
        logger.info(f"Found {len(semantic_candidates)} semantic candidates")
        return semantic_candidates
    
    async def _get_topic_candidates(
        self, 
        failed_question: FailedQuestion, 
        matching_request: MatchingRequest
    ) -> List[ContentItem]:
        """Get candidates using topic-based filtering"""
        
        # Create filter criteria from failed question
        filter_criteria = create_filter_from_failed_question(
            {
                'subject': failed_question.subject_area,
                'topic': failed_question.topic,
                'competency': failed_question.competency,
                'difficulty': failed_question.question_difficulty,
                'text': failed_question.question_text
            },
            matching_request.student_profile
        )
        
        # Get candidate content metadata
        content_metadata = await self._load_content_metadata(failed_question.subject_area)
        
        if not content_metadata:
            return []
        
        # Apply topic filter
        filter_results = self.topic_filter.apply_filter(content_metadata, filter_criteria)
        
        # Convert to content items
        topic_candidates = []
        for result in filter_results:
            if result.relevance_score >= 0.4:  # Minimum relevance threshold
                content_item = ContentItem(
                    id=result.content_metadata.content_id,
                    title=result.content_metadata.title,
                    description=result.content_metadata.description,
                    content_type=result.content_metadata.content_type.value,
                    subject_area=result.content_metadata.subject_hierarchy.subject_name,
                    topic=result.content_metadata.subject_hierarchy.topic,
                    competency=result.content_metadata.icfes_competency.value,
                    difficulty_level=str(int(result.content_metadata.difficulty_score))
                )
                topic_candidates.append(content_item)
        
        logger.info(f"Found {len(topic_candidates)} topic-based candidates")
        return topic_candidates
    
    async def _get_error_specific_candidates(
        self, 
        failed_question: FailedQuestion, 
        error_analysis: ErrorAnalysis
    ) -> List[ContentItem]:
        """Get candidates that specifically address the identified errors"""
        
        # Query videos that address specific error types
        error_keywords = {
            ErrorType.CONCEPTUAL: ['concepto', 'fundamento', 'definición', 'teoría'],
            ErrorType.PROCEDURAL: ['procedimiento', 'método', 'algoritmo', 'pasos'],
            ErrorType.COMPUTATIONAL: ['cálculo', 'operación', 'aritmética', 'numérico'],
            ErrorType.STRATEGIC: ['estrategia', 'resolución', 'problema', 'enfoque']
        }
        
        primary_error = error_analysis.primary_error_type
        keywords = error_keywords.get(primary_error, ['general'])
        
        try:
            # Query database for videos with relevant keywords
            keywords_str = "', '".join(keywords)
            query = text(f"""
                SELECT DISTINCT
                    yc.id,
                    yc.title,
                    yc.description,
                    yc.subject_id,
                    yc.topic_id,
                    s.name as subject_name,
                    t.name as topic_name,
                    yc.competencias
                FROM youtube_catalog yc
                JOIN subjects s ON yc.subject_id = s.id
                LEFT JOIN topics t ON yc.topic_id = t.id
                WHERE yc.is_processed = true
                    AND s.name = :subject_area
                    AND (
                        yc.title ILIKE ANY(ARRAY['{keywords_str}'])
                        OR yc.description ILIKE ANY(ARRAY['{keywords_str}'])
                        OR yc.tema_principal ILIKE ANY(ARRAY['{keywords_str}'])
                    )
                LIMIT 15
            """)
            
            results = self.db.execute(query, {
                'subject_area': failed_question.subject_area
            }).fetchall()
            
            error_candidates = []
            for row in results:
                content_item = ContentItem(
                    id=row.id,
                    title=row.title,
                    description=row.description or '',
                    content_type="video",
                    subject_area=row.subject_name,
                    topic=row.topic_name or failed_question.topic,
                    competency=failed_question.competency,
                    difficulty_level=str(int(failed_question.question_difficulty))
                )
                error_candidates.append(content_item)
            
            logger.info(f"Found {len(error_candidates)} error-specific candidates")
            return error_candidates
            
        except Exception as e:
            logger.error(f"Error getting error-specific candidates: {e}")
            return []
    
    async def _get_difficulty_candidates(
        self, 
        failed_question: FailedQuestion, 
        matching_request: MatchingRequest
    ) -> List[ContentItem]:
        """Get candidates using difficulty-appropriate selection"""
        
        # Create student ability from failed question context
        student_ability = StudentAbility(
            student_id=failed_question.student_id,
            subject_area=failed_question.subject_area,
            theta=failed_question.student_theta,
            theta_se=0.3,  # Reasonable uncertainty
            theta_ci_lower=failed_question.student_theta - 0.6,
            theta_ci_upper=failed_question.student_theta + 0.6,
            n_responses=10  # Assume some responses
        )
        
        # Create selection criteria
        criteria = DifficultySelectionCriteria(
            student_ability=student_ability,
            learning_progression=LearningProgression.OPTIMAL,
            target_success_rate=0.7,
            max_content_items=15,
            subject_filters=[failed_question.subject_area]
        )
        
        # Get difficulty-appropriate content
        selection_results = self.difficulty_selector.select_appropriate_content(criteria)
        
        # Convert to content items
        difficulty_candidates = []
        for result in selection_results:
            if result.selection_confidence >= 0.4:
                profile = result.content_profile
                content_item = ContentItem(
                    id=profile.content_id,
                    title=profile.title,
                    description="",  # Will be filled from database if needed
                    content_type=profile.content_type,
                    subject_area=profile.subject_area,
                    topic=profile.topic,
                    competency=failed_question.competency,
                    difficulty_level=str(int(profile.difficulty_score))
                )
                difficulty_candidates.append(content_item)
        
        logger.info(f"Found {len(difficulty_candidates)} difficulty-appropriate candidates")
        return difficulty_candidates
    
    async def _score_and_rank_videos(
        self,
        candidate_videos: List[ContentItem],
        matching_request: MatchingRequest,
        error_analysis: ErrorAnalysis
    ) -> List[VideoMatch]:
        """Score and rank video candidates"""
        
        video_matches = []
        failed_question = matching_request.failed_question
        
        for video in candidate_videos:
            # Get detailed video information
            video_details = await self._get_video_details(video.id)
            
            if not video_details:
                continue
            
            # Calculate individual scores
            semantic_score = await self._calculate_semantic_score(video, failed_question)
            topic_score = self._calculate_topic_relevance_score(video, failed_question)
            difficulty_score = self._calculate_difficulty_score(video, failed_question)
            error_addressing_score = self._calculate_error_addressing_score(video, error_analysis)
            
            # Calculate overall match score
            overall_score = (
                semantic_score * self.algorithm_weights['semantic_similarity'] +
                topic_score * self.algorithm_weights['topic_relevance'] +
                difficulty_score * self.algorithm_weights['difficulty_appropriateness'] +
                error_addressing_score * self.algorithm_weights['error_addressing']
            )
            
            # Determine confidence level
            confidence_level = self._determine_confidence_level(overall_score)
            
            # Generate match reasons
            match_reasons = self._generate_match_reasons(
                video, failed_question, semantic_score, topic_score, difficulty_score, error_addressing_score
            )
            
            # Identify addressing error types
            addressing_errors = self._identify_addressing_errors(video, error_analysis)
            
            # Identify matching strategies
            matching_strategies = self._identify_matching_strategies(video, error_analysis)
            
            # Calculate expected outcomes
            learning_impact = self._calculate_learning_impact(video, failed_question, overall_score)
            watch_time = video_details.get('duration_minutes', 15)
            success_improvement = self._calculate_success_improvement(overall_score, error_analysis)
            
            # Create video match
            video_match = VideoMatch(
                video_id=video.id,
                video_title=video.title,
                video_url=video_details.get('url', ''),
                semantic_similarity_score=semantic_score,
                topic_relevance_score=topic_score,
                difficulty_appropriateness_score=difficulty_score,
                overall_match_score=overall_score,
                confidence_level=confidence_level,
                match_reasons=match_reasons,
                addressing_error_types=addressing_errors,
                matching_strategies=matching_strategies,
                expected_learning_impact=learning_impact,
                estimated_watch_time=watch_time,
                success_probability_improvement=success_improvement,
                duration_minutes=watch_time,
                channel_name=video_details.get('channel', ''),
                engagement_metrics=video_details.get('engagement', {}),
                matched_at=datetime.now(),
                matching_algorithm_version="1.0"
            )
            
            video_matches.append(video_match)
        
        # Sort by overall match score
        video_matches.sort(key=lambda x: x.overall_match_score, reverse=True)
        
        return video_matches
    
    async def _load_video_candidates(self, subject_area: str) -> List[ContentItem]:
        """Load video candidates from database"""
        
        try:
            query = text("""
                SELECT 
                    yc.id,
                    yc.title,
                    yc.description,
                    yc.tema_principal,
                    s.name as subject_name,
                    t.name as topic_name,
                    yc.competencias,
                    yc.irt_b
                FROM youtube_catalog yc
                JOIN subjects s ON yc.subject_id = s.id
                LEFT JOIN topics t ON yc.topic_id = t.id
                WHERE yc.is_processed = true
                    AND s.name = :subject_area
                    AND yc.irt_b IS NOT NULL
                ORDER BY RANDOM()
                LIMIT 100
            """)
            
            results = self.db.execute(query, {'subject_area': subject_area}).fetchall()
            
            candidates = []
            for row in results:
                content_item = ContentItem(
                    id=row.id,
                    title=row.title,
                    description=row.description or '',
                    content_type="video",
                    subject_area=row.subject_name,
                    topic=row.topic_name or row.tema_principal or 'General',
                    competency=row.competencias or 'general',
                    difficulty_level=str(int(row.irt_b or 0))
                )
                candidates.append(content_item)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error loading video candidates: {e}")
            return []
    
    async def _load_content_metadata(self, subject_area: str) -> List[ContentMetadata]:
        """Load content metadata for topic filtering"""
        # This would be implemented to load metadata
        # For now, return empty list
        return []
    
    async def _get_video_details(self, video_id: Union[int, str]) -> Dict[str, Any]:
        """Get detailed video information"""
        
        try:
            query = text("""
                SELECT 
                    yc.youtube_url,
                    yc.channel_name,
                    yc.duration_seconds,
                    COALESCE(vs.ctr_7d, 0.1) as ctr,
                    COALESCE(vs.completion_rate_7d, 0.7) as completion_rate,
                    COALESCE(vs.avg_watch_sec_7d, yc.duration_seconds * 0.6) as avg_watch_time
                FROM youtube_catalog yc
                LEFT JOIN video_stats vs ON yc.id = vs.video_id
                WHERE yc.id = :video_id
            """)
            
            result = self.db.execute(query, {'video_id': video_id}).fetchone()
            
            if result:
                return {
                    'url': result.youtube_url,
                    'channel': result.channel_name or 'Unknown',
                    'duration_minutes': int((result.duration_seconds or 900) / 60),
                    'engagement': {
                        'ctr': result.ctr,
                        'completion_rate': result.completion_rate,
                        'avg_watch_ratio': (result.avg_watch_time / result.duration_seconds) if result.duration_seconds else 0.6
                    }
                }
            
        except Exception as e:
            logger.error(f"Error getting video details: {e}")
        
        return {'url': '', 'channel': 'Unknown', 'duration_minutes': 15, 'engagement': {}}
    
    async def _calculate_semantic_score(self, video: ContentItem, failed_question: FailedQuestion) -> float:
        """Calculate semantic similarity score"""
        
        # Create items for similarity comparison
        question_item = ContentItem(
            id=failed_question.question_id,
            title="Pregunta fallada",
            description=failed_question.question_text,
            content_type="question",
            subject_area=failed_question.subject_area,
            topic=failed_question.topic,
            competency=failed_question.competency
        )
        
        # Use the similarity engine
        results = await self.similarity_engine.find_most_similar_content(
            query_item=question_item,
            candidate_items=[video],
            top_k=1
        )
        
        if results:
            return results[0].similarity_score
        else:
            return 0.0
    
    def _calculate_topic_relevance_score(self, video: ContentItem, failed_question: FailedQuestion) -> float:
        """Calculate topic relevance score"""
        
        score = 0.0
        
        # Subject match
        if video.subject_area == failed_question.subject_area:
            score += 0.4
        
        # Topic match
        if video.topic.lower() in failed_question.topic.lower() or failed_question.topic.lower() in video.topic.lower():
            score += 0.3
        
        # Competency match
        if video.competency.lower() in failed_question.competency.lower():
            score += 0.2
        
        # Subtopic match (if available)
        if hasattr(failed_question, 'subtopic') and failed_question.subtopic:
            if failed_question.subtopic.lower() in video.title.lower():
                score += 0.1
        
        return min(1.0, score)
    
    def _calculate_difficulty_score(self, video: ContentItem, failed_question: FailedQuestion) -> float:
        """Calculate difficulty appropriateness score"""
        
        try:
            video_difficulty = float(video.difficulty_level)
            question_difficulty = failed_question.question_difficulty
            
            # Calculate distance
            difficulty_distance = abs(video_difficulty - question_difficulty)
            
            # Convert to similarity score (closer = higher score)
            if difficulty_distance == 0:
                return 1.0
            elif difficulty_distance <= 1:
                return 0.8
            elif difficulty_distance <= 2:
                return 0.6
            else:
                return 0.3
                
        except (ValueError, AttributeError):
            return 0.5  # Default score
    
    def _calculate_error_addressing_score(self, video: ContentItem, error_analysis: ErrorAnalysis) -> float:
        """Calculate how well video addresses the specific error"""
        
        score = 0.0
        
        # Check if video title/description contains error-related keywords
        video_text = f"{video.title} {video.description}".lower()
        
        error_keywords = {
            ErrorType.CONCEPTUAL: ['concepto', 'fundamento', 'teoría', 'definición'],
            ErrorType.PROCEDURAL: ['procedimiento', 'método', 'pasos', 'algoritmo'],
            ErrorType.COMPUTATIONAL: ['cálculo', 'operación', 'aritmética'],
            ErrorType.STRATEGIC: ['estrategia', 'resolución', 'problema']
        }
        
        primary_keywords = error_keywords.get(error_analysis.primary_error_type, [])
        
        # Primary error addressing
        matching_keywords = sum(1 for keyword in primary_keywords if keyword in video_text)
        if matching_keywords > 0:
            score += 0.6 * min(1.0, matching_keywords / len(primary_keywords))
        
        # Secondary error addressing
        for secondary_error in error_analysis.secondary_error_types:
            secondary_keywords = error_keywords.get(secondary_error, [])
            secondary_matches = sum(1 for keyword in secondary_keywords if keyword in video_text)
            if secondary_matches > 0:
                score += 0.2 * min(1.0, secondary_matches / len(secondary_keywords))
        
        return min(1.0, score)
    
    def _determine_confidence_level(self, overall_score: float) -> MatchingConfidence:
        """Determine confidence level from overall score"""
        
        if overall_score >= 0.9:
            return MatchingConfidence.VERY_HIGH
        elif overall_score >= 0.75:
            return MatchingConfidence.HIGH
        elif overall_score >= 0.6:
            return MatchingConfidence.MODERATE
        elif overall_score >= 0.45:
            return MatchingConfidence.LOW
        else:
            return MatchingConfidence.VERY_LOW
    
    def _generate_match_reasons(self, video: ContentItem, failed_question: FailedQuestion, 
                              semantic_score: float, topic_score: float, 
                              difficulty_score: float, error_score: float) -> List[str]:
        """Generate human-readable match reasons"""
        
        reasons = []
        
        if semantic_score > 0.7:
            reasons.append("Alta similitud semántica con la pregunta")
        elif semantic_score > 0.5:
            reasons.append("Similitud semántica moderada")
        
        if topic_score > 0.8:
            reasons.append("Coincidencia exacta de tema y competencia")
        elif topic_score > 0.5:
            reasons.append("Tema relacionado")
        
        if difficulty_score > 0.8:
            reasons.append("Nivel de dificultad apropiado")
        
        if error_score > 0.6:
            reasons.append("Aborda específicamente el tipo de error cometido")
        
        if not reasons:
            reasons.append("Contenido relacionado al área de estudio")
        
        return reasons
    
    def _identify_addressing_errors(self, video: ContentItem, error_analysis: ErrorAnalysis) -> List[ErrorType]:
        """Identify which error types the video addresses"""
        
        addressing = [error_analysis.primary_error_type]
        
        # Simple heuristic based on video title
        video_text = video.title.lower()
        
        if any(word in video_text for word in ['concepto', 'teoría', 'fundamento']):
            if ErrorType.CONCEPTUAL not in addressing:
                addressing.append(ErrorType.CONCEPTUAL)
        
        if any(word in video_text for word in ['procedimiento', 'método', 'pasos']):
            if ErrorType.PROCEDURAL not in addressing:
                addressing.append(ErrorType.PROCEDURAL)
        
        if any(word in video_text for word in ['cálculo', 'operación']):
            if ErrorType.COMPUTATIONAL not in addressing:
                addressing.append(ErrorType.COMPUTATIONAL)
        
        return addressing
    
    def _identify_matching_strategies(self, video: ContentItem, error_analysis: ErrorAnalysis) -> List[MatchingStrategy]:
        """Identify which matching strategies the video supports"""
        
        strategies = []
        
        # Map from error analysis recommendations
        for strategy in error_analysis.recommended_strategies:
            if strategy not in strategies:
                strategies.append(strategy)
        
        # Add default based on video type
        video_text = video.title.lower()
        
        if any(word in video_text for word in ['concepto', 'teoría']):
            if MatchingStrategy.CONCEPT_REVIEW not in strategies:
                strategies.append(MatchingStrategy.CONCEPT_REVIEW)
        
        if any(word in video_text for word in ['ejercicio', 'problema']):
            if MatchingStrategy.SKILL_BUILDING not in strategies:
                strategies.append(MatchingStrategy.SKILL_BUILDING)
        
        return strategies[:3]  # Limit to top 3
    
    def _calculate_learning_impact(self, video: ContentItem, failed_question: FailedQuestion, match_score: float) -> float:
        """Calculate expected learning impact"""
        
        # Base impact from match score
        base_impact = match_score
        
        # Adjust for video engagement (if available)
        engagement_adjustment = 1.0  # Default
        
        # Adjust for topic importance
        if failed_question.competency in ['razonamiento', 'uso comprensivo']:
            importance_adjustment = 1.2
        else:
            importance_adjustment = 1.0
        
        learning_impact = base_impact * engagement_adjustment * importance_adjustment
        
        return min(1.0, learning_impact)
    
    def _calculate_success_improvement(self, match_score: float, error_analysis: ErrorAnalysis) -> float:
        """Calculate expected improvement in success probability"""
        
        # Base improvement from match quality
        base_improvement = match_score * 0.3  # Max 30% improvement
        
        # Adjust for error priority
        if error_analysis.intervention_priority >= 4:
            priority_adjustment = 1.3
        elif error_analysis.intervention_priority >= 2:
            priority_adjustment = 1.1
        else:
            priority_adjustment = 0.9
        
        improvement = base_improvement * priority_adjustment
        
        return min(0.5, improvement)  # Cap at 50% improvement
    
    def _apply_final_filters(self, video_matches: List[VideoMatch], matching_request: MatchingRequest) -> List[VideoMatch]:
        """Apply final filters to video matches"""
        
        filtered_matches = []
        
        for match in video_matches:
            # Confidence filter
            if match.overall_match_score < matching_request.min_confidence:
                continue
            
            # Duration filter
            if match.duration_minutes > matching_request.max_duration_minutes:
                continue
            
            # Engagement filter (if required)
            if matching_request.require_high_engagement:
                engagement = match.engagement_metrics
                if engagement.get('ctr', 0) < 0.1 or engagement.get('completion_rate', 0) < 0.6:
                    continue
            
            filtered_matches.append(match)
        
        return filtered_matches[:matching_request.max_videos]
    
    def _generate_viewing_order(self, video_matches: List[VideoMatch], error_analysis: ErrorAnalysis) -> List[Union[int, str]]:
        """Generate recommended viewing order"""
        
        if not video_matches:
            return []
        
        # Sort by strategy priority for the specific error
        strategy_priority = {
            ErrorType.KNOWLEDGE_GAP: [MatchingStrategy.PREREQUISITE_FILLING, MatchingStrategy.CONCEPT_REVIEW],
            ErrorType.CONCEPTUAL: [MatchingStrategy.CONCEPT_REVIEW, MatchingStrategy.DIRECT_REMEDIATION],
            ErrorType.PROCEDURAL: [MatchingStrategy.SKILL_BUILDING, MatchingStrategy.DIRECT_REMEDIATION],
            ErrorType.STRATEGIC: [MatchingStrategy.STRATEGIC_TRAINING, MatchingStrategy.SKILL_BUILDING]
        }
        
        primary_error = error_analysis.primary_error_type
        preferred_strategies = strategy_priority.get(primary_error, [MatchingStrategy.CONCEPT_REVIEW])
        
        # Sort matches by strategy alignment and score
        def sort_key(match):
            strategy_score = 0
            for i, strategy in enumerate(preferred_strategies):
                if strategy in match.matching_strategies:
                    strategy_score = len(preferred_strategies) - i
                    break
            
            return (strategy_score, match.overall_match_score)
        
        sorted_matches = sorted(video_matches, key=sort_key, reverse=True)
        
        return [match.video_id for match in sorted_matches]
    
    def _calculate_coverage_score(self, video_matches: List[VideoMatch], error_analysis: ErrorAnalysis) -> float:
        """Calculate how well the matches cover the identified errors"""
        
        if not video_matches:
            return 0.0
        
        # Check coverage of primary error
        primary_covered = any(
            error_analysis.primary_error_type in match.addressing_error_types
            for match in video_matches
        )
        
        # Check coverage of secondary errors
        secondary_coverage = 0
        if error_analysis.secondary_error_types:
            for secondary_error in error_analysis.secondary_error_types:
                if any(secondary_error in match.addressing_error_types for match in video_matches):
                    secondary_coverage += 1
            secondary_coverage /= len(error_analysis.secondary_error_types)
        
        # Check strategy coverage
        strategy_coverage = 0
        if error_analysis.recommended_strategies:
            for strategy in error_analysis.recommended_strategies:
                if any(strategy in match.matching_strategies for match in video_matches):
                    strategy_coverage += 1
            strategy_coverage /= len(error_analysis.recommended_strategies)
        
        # Weighted coverage score
        coverage_score = (
            (1.0 if primary_covered else 0.0) * 0.5 +
            secondary_coverage * 0.3 +
            strategy_coverage * 0.2
        )
        
        return coverage_score
    
    def _generate_request_id(self, matching_request: MatchingRequest) -> str:
        """Generate unique request ID for caching"""
        
        request_data = {
            'question_id': matching_request.failed_question.question_id,
            'student_id': matching_request.failed_question.student_id,
            'student_answer': matching_request.failed_question.student_answer,
            'max_videos': matching_request.max_videos,
            'min_confidence': matching_request.min_confidence
        }
        
        request_json = json.dumps(request_data, sort_keys=True)
        return hashlib.md5(request_json.encode()).hexdigest()
    
    def _create_empty_result(self, request_id: str, failed_question: FailedQuestion, error_analysis: ErrorAnalysis) -> MatchingResult:
        """Create empty result when no matches found"""
        
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

# Utility functions
def create_failed_question_from_response(response_data: Dict[str, Any]) -> FailedQuestion:
    """Create FailedQuestion from response data"""
    
    return FailedQuestion(
        question_id=response_data['question_id'],
        student_id=response_data['student_id'],
        question_text=response_data.get('question_text', ''),
        question_type=response_data.get('question_type', 'multiple_choice'),
        correct_answer=response_data.get('correct_answer', ''),
        student_answer=response_data.get('student_answer', ''),
        distractors=response_data.get('distractors', []),
        subject_area=response_data.get('subject_area', ''),
        topic=response_data.get('topic', ''),
        subtopic=response_data.get('subtopic', ''),
        competency=response_data.get('competency', ''),
        component=response_data.get('component', ''),
        cognitive_level=response_data.get('cognitive_level', ''),
        time_spent_seconds=response_data.get('time_spent_seconds', 0),
        attempt_number=response_data.get('attempt_number', 1),
        failed_at=response_data.get('failed_at', datetime.now()),
        student_theta=response_data.get('student_theta', 0.0),
        question_difficulty=response_data.get('question_difficulty', 0.0),
        success_probability=response_data.get('success_probability', 0.0),
        question_metadata=response_data.get('metadata', {})
    )

if __name__ == "__main__":
    # Example usage and testing
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Mock database for testing
    class MockSession:
        def execute(self, query, params=None):
            class MockResult:
                def fetchone(self): return None
                def fetchall(self): return []
            return MockResult()
    
    async def test_matching_service():
        """Test the matching service"""
        
        db = MockSession()
        service = IntelligentQuestionVideoMatchingService(db)
        
        # Create test failed question
        failed_question = FailedQuestion(
            question_id=1,
            student_id="test_student",
            question_text="Resolver el sistema de ecuaciones: 2x + y = 5, x - y = 1",
            question_type="multiple_choice",
            correct_answer="x=2, y=1",
            student_answer="x=1, y=3",
            distractors=["x=1, y=3", "x=3, y=-1", "x=2, y=1", "x=0, y=5"],
            subject_area="Matemáticas",
            topic="Álgebra",
            subtopic="Sistemas de ecuaciones",
            competency="Razonamiento matemático",
            component="Algebraico",
            cognitive_level="aplicar",
            time_spent_seconds=120,
            attempt_number=1,
            failed_at=datetime.now(),
            student_theta=-0.5,
            question_difficulty=0.2,
            success_probability=0.6
        )
        
        # Create matching request
        request = MatchingRequest(
            failed_question=failed_question,
            max_videos=5,
            min_confidence=0.4
        )
        
        print("Testing Intelligent Question-Video Matching Service...")
        print(f"Failed Question: {failed_question.question_text}")
        print(f"Student Answer: {failed_question.student_answer}")
        print(f"Correct Answer: {failed_question.correct_answer}")
        print(f"Subject: {failed_question.subject_area}")
        print(f"Topic: {failed_question.topic}")
        
        print("Service initialized successfully!")
    
    # Run the test
    asyncio.run(test_matching_service())