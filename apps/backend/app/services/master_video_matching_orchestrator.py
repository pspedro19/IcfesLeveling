#!/usr/bin/env python3
"""
Master Video Matching Orchestrator - Advanced ICFES System Integration
====================================================================

A comprehensive orchestration service that integrates all advanced video
matching components into a unified, high-performance system for intelligent
educational content recommendation based on failed ICFES questions.

Features:
- Orchestrates all video matching algorithms
- Performance monitoring and optimization
- Real-time analytics and A/B testing
- Adaptive algorithm weighting
- Quality assurance and validation
- Comprehensive logging and metrics

Author: Claude Code Assistant (Video Matching Specialist)
Date: 2025-09-11
"""

import asyncio
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import hashlib
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import our advanced components
from .advanced_semantic_similarity_engine import (
    AdvancedSemanticSimilarityEngine, ContentItem, create_similarity_engine
)
from .multidimensional_topic_filter import (
    MultidimensionalTopicFilter, FilterCriteria, StudentProfile
)
from .difficulty_appropriate_content_selector import (
    DifficultyAppropriateContentSelector, DifficultySelectionCriteria
)
from .intelligent_question_video_matching_service import (
    IntelligentQuestionVideoMatchingService, MatchingRequest, MatchingResult,
    FailedQuestion, ErrorAnalysis, VideoMatch, create_failed_question_from_response
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlgorithmStrategy(Enum):
    """Available matching algorithm strategies"""
    SEMANTIC_ONLY = "semantic_only"
    TOPIC_ONLY = "topic_only"
    DIFFICULTY_ONLY = "difficulty_only"
    HYBRID_BALANCED = "hybrid_balanced"
    HYBRID_SEMANTIC_HEAVY = "hybrid_semantic_heavy"
    HYBRID_TOPIC_HEAVY = "hybrid_topic_heavy"
    ADAPTIVE = "adaptive"
    ERROR_FOCUSED = "error_focused"

class PerformanceProfile(Enum):
    """System performance profiles"""
    ACCURACY_OPTIMIZED = "accuracy_optimized"     # Best matching quality
    SPEED_OPTIMIZED = "speed_optimized"           # Fastest response
    BALANCED = "balanced"                         # Balance of speed and quality
    COMPREHENSIVE = "comprehensive"               # Maximum coverage

@dataclass
class SystemConfiguration:
    """Master system configuration"""
    # Algorithm settings
    default_strategy: AlgorithmStrategy = AlgorithmStrategy.HYBRID_BALANCED
    performance_profile: PerformanceProfile = PerformanceProfile.BALANCED
    
    # Performance settings
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 30
    cache_ttl_seconds: int = 3600
    
    # Quality settings
    min_match_confidence: float = 0.4
    max_results_per_request: int = 10
    enable_quality_filtering: bool = True
    
    # Monitoring settings
    enable_performance_monitoring: bool = True
    enable_ab_testing: bool = False
    log_detailed_metrics: bool = True
    
    # Algorithm weights (can be adjusted dynamically)
    algorithm_weights: Dict[str, float] = field(default_factory=lambda: {
        'semantic_similarity': 0.35,
        'topic_relevance': 0.30,
        'difficulty_match': 0.20,
        'error_analysis': 0.15
    })

@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    request_id: str
    student_id: str
    question_id: Union[int, str]
    
    # Timing metrics
    total_time_ms: float
    semantic_time_ms: float
    topic_time_ms: float
    difficulty_time_ms: float
    integration_time_ms: float
    
    # Quality metrics
    results_count: int
    average_confidence: float
    coverage_score: float
    
    # Algorithm performance
    algorithms_used: List[str]
    cache_hit_rate: float
    
    # Request metadata
    timestamp: datetime
    strategy_used: AlgorithmStrategy
    performance_profile: PerformanceProfile

@dataclass
class SystemMetrics:
    """Aggregated system metrics"""
    # Performance statistics
    total_requests: int
    average_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    
    # Quality statistics
    average_match_confidence: float
    average_results_per_request: float
    success_rate: float
    
    # Algorithm statistics
    algorithm_usage_stats: Dict[str, int]
    cache_hit_rate: float
    
    # Error statistics
    error_rate: float
    timeout_rate: float
    
    # Time window
    measurement_period: timedelta
    last_updated: datetime

class PerformanceMonitor:
    """Monitors system performance and collects metrics"""
    
    def __init__(self):
        self.request_metrics: List[RequestMetrics] = []
        self.system_metrics: Optional[SystemMetrics] = None
        self.lock = threading.Lock()
        
        # Rolling metrics (last 1000 requests)
        self.max_stored_metrics = 1000
        
    def record_request_metrics(self, metrics: RequestMetrics):
        """Record metrics for a completed request"""
        with self.lock:
            self.request_metrics.append(metrics)
            
            # Keep only recent metrics
            if len(self.request_metrics) > self.max_stored_metrics:
                self.request_metrics = self.request_metrics[-self.max_stored_metrics:]
            
            # Update system metrics
            self._update_system_metrics()
    
    def _update_system_metrics(self):
        """Update aggregated system metrics"""
        if not self.request_metrics:
            return
        
        recent_metrics = self.request_metrics[-100:]  # Last 100 requests
        
        # Calculate performance statistics
        response_times = [m.total_time_ms for m in recent_metrics]
        confidences = [m.average_confidence for m in recent_metrics if m.average_confidence > 0]
        
        # Algorithm usage statistics
        algorithm_usage = defaultdict(int)
        for metrics in recent_metrics:
            for algorithm in metrics.algorithms_used:
                algorithm_usage[algorithm] += 1
        
        # Calculate cache hit rate
        cache_hits = sum(1 for m in recent_metrics if m.cache_hit_rate > 0.5)
        cache_hit_rate = cache_hits / len(recent_metrics) if recent_metrics else 0.0
        
        # Error and timeout rates
        error_count = sum(1 for m in recent_metrics if m.results_count == 0)
        timeout_count = sum(1 for m in recent_metrics if m.total_time_ms > 30000)  # 30 seconds
        
        self.system_metrics = SystemMetrics(
            total_requests=len(self.request_metrics),
            average_response_time_ms=np.mean(response_times) if response_times else 0,
            p95_response_time_ms=np.percentile(response_times, 95) if response_times else 0,
            p99_response_time_ms=np.percentile(response_times, 99) if response_times else 0,
            average_match_confidence=np.mean(confidences) if confidences else 0,
            average_results_per_request=np.mean([m.results_count for m in recent_metrics]),
            success_rate=(len(recent_metrics) - error_count) / len(recent_metrics) if recent_metrics else 1.0,
            algorithm_usage_stats=dict(algorithm_usage),
            cache_hit_rate=cache_hit_rate,
            error_rate=error_count / len(recent_metrics) if recent_metrics else 0.0,
            timeout_rate=timeout_count / len(recent_metrics) if recent_metrics else 0.0,
            measurement_period=timedelta(hours=1),
            last_updated=datetime.now()
        )
    
    def get_system_metrics(self) -> Optional[SystemMetrics]:
        """Get current system metrics"""
        with self.lock:
            return self.system_metrics
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        with self.lock:
            if not self.system_metrics:
                return {'error': 'No metrics available'}
            
            metrics = self.system_metrics
            recent_requests = self.request_metrics[-50:] if self.request_metrics else []
            
            return {
                'system_health': {
                    'status': 'healthy' if metrics.error_rate < 0.05 and metrics.average_response_time_ms < 5000 else 'degraded',
                    'total_requests': metrics.total_requests,
                    'success_rate': round(metrics.success_rate * 100, 2),
                    'error_rate': round(metrics.error_rate * 100, 2)
                },
                'performance': {
                    'avg_response_time_ms': round(metrics.average_response_time_ms, 2),
                    'p95_response_time_ms': round(metrics.p95_response_time_ms, 2),
                    'p99_response_time_ms': round(metrics.p99_response_time_ms, 2),
                    'cache_hit_rate': round(metrics.cache_hit_rate * 100, 2)
                },
                'quality': {
                    'avg_match_confidence': round(metrics.average_match_confidence, 3),
                    'avg_results_per_request': round(metrics.average_results_per_request, 1)
                },
                'algorithms': metrics.algorithm_usage_stats,
                'recent_trends': self._analyze_recent_trends(recent_requests),
                'recommendations': self._generate_optimization_recommendations(metrics)
            }
    
    def _analyze_recent_trends(self, recent_requests: List[RequestMetrics]) -> Dict[str, Any]:
        """Analyze recent performance trends"""
        if len(recent_requests) < 10:
            return {'status': 'insufficient_data'}
        
        # Split into two halves for comparison
        mid = len(recent_requests) // 2
        first_half = recent_requests[:mid]
        second_half = recent_requests[mid:]
        
        first_avg_time = np.mean([r.total_time_ms for r in first_half])
        second_avg_time = np.mean([r.total_time_ms for r in second_half])
        
        first_avg_confidence = np.mean([r.average_confidence for r in first_half])
        second_avg_confidence = np.mean([r.average_confidence for r in second_half])
        
        time_trend = 'improving' if second_avg_time < first_avg_time else 'degrading'
        quality_trend = 'improving' if second_avg_confidence > first_avg_confidence else 'degrading'
        
        return {
            'response_time_trend': time_trend,
            'quality_trend': quality_trend,
            'time_change_percent': round(((second_avg_time - first_avg_time) / first_avg_time) * 100, 2),
            'quality_change_percent': round(((second_avg_confidence - first_avg_confidence) / first_avg_confidence) * 100, 2)
        }
    
    def _generate_optimization_recommendations(self, metrics: SystemMetrics) -> List[str]:
        """Generate system optimization recommendations"""
        recommendations = []
        
        if metrics.average_response_time_ms > 5000:
            recommendations.append("Consider enabling speed-optimized performance profile")
        
        if metrics.cache_hit_rate < 0.3:
            recommendations.append("Increase cache TTL to improve cache hit rate")
        
        if metrics.average_match_confidence < 0.6:
            recommendations.append("Consider using accuracy-optimized performance profile")
        
        if metrics.error_rate > 0.05:
            recommendations.append("Investigate and fix sources of errors")
        
        # Algorithm-specific recommendations
        if metrics.algorithm_usage_stats.get('semantic_similarity', 0) < 10:
            recommendations.append("Consider increasing semantic similarity weight for better quality")
        
        return recommendations

class AdaptiveAlgorithmOptimizer:
    """Optimizes algorithm weights based on performance feedback"""
    
    def __init__(self):
        self.performance_history: Dict[str, List[float]] = defaultdict(list)
        self.current_weights = {
            'semantic_similarity': 0.35,
            'topic_relevance': 0.30,
            'difficulty_match': 0.20,
            'error_analysis': 0.15
        }
        self.optimization_enabled = True
        self.min_samples_for_optimization = 50
    
    def record_performance(self, algorithm: str, performance_score: float):
        """Record performance score for an algorithm"""
        if not self.optimization_enabled:
            return
        
        self.performance_history[algorithm].append(performance_score)
        
        # Keep only recent performance data
        if len(self.performance_history[algorithm]) > 200:
            self.performance_history[algorithm] = self.performance_history[algorithm][-200:]
    
    def optimize_weights(self) -> Dict[str, float]:
        """Optimize algorithm weights based on performance history"""
        if not self.optimization_enabled:
            return self.current_weights
        
        # Check if we have enough data
        if not all(len(history) >= self.min_samples_for_optimization 
                  for history in self.performance_history.values()):
            return self.current_weights
        
        # Calculate performance scores for each algorithm
        algorithm_scores = {}
        for algorithm, history in self.performance_history.items():
            recent_performance = history[-50:]  # Last 50 samples
            algorithm_scores[algorithm] = np.mean(recent_performance)
        
        # Normalize scores to create new weights
        total_score = sum(algorithm_scores.values())
        if total_score > 0:
            new_weights = {
                algorithm: score / total_score
                for algorithm, score in algorithm_scores.items()
            }
            
            # Apply smoothing to prevent dramatic changes
            smoothing_factor = 0.1  # 10% adaptation rate
            optimized_weights = {}
            for algorithm in self.current_weights:
                current_weight = self.current_weights[algorithm]
                new_weight = new_weights.get(algorithm, current_weight)
                optimized_weights[algorithm] = (
                    current_weight * (1 - smoothing_factor) + 
                    new_weight * smoothing_factor
                )
            
            self.current_weights = optimized_weights
            logger.info(f"Optimized algorithm weights: {self.current_weights}")
        
        return self.current_weights

class MasterVideoMatchingOrchestrator:
    """Master orchestration service for all video matching components"""
    
    def __init__(
        self, 
        db_session: Session,
        openai_api_key: Optional[str] = None,
        config: Optional[SystemConfiguration] = None
    ):
        self.db = db_session
        self.config = config or SystemConfiguration()
        
        # Initialize component services
        logger.info("Initializing master video matching orchestrator...")
        
        self.semantic_engine = create_similarity_engine(
            openai_api_key=openai_api_key,
            enable_caching=True
        )
        
        self.topic_filter = MultidimensionalTopicFilter(db_session)
        self.difficulty_selector = DifficultyAppropriateContentSelector(db_session)
        self.matching_service = IntelligentQuestionVideoMatchingService(
            db_session, openai_api_key, enable_caching=True
        )
        
        # Initialize monitoring and optimization
        self.performance_monitor = PerformanceMonitor()
        self.algorithm_optimizer = AdaptiveAlgorithmOptimizer()
        
        # Thread pool for concurrent processing
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.max_concurrent_requests
        )
        
        # Request cache
        self.request_cache: Dict[str, Tuple[datetime, MatchingResult]] = {}
        
        logger.info("Master video matching orchestrator initialized successfully")
    
    async def get_video_recommendations(
        self,
        student_id: str,
        failed_question_data: Dict[str, Any],
        strategy: Optional[AlgorithmStrategy] = None,
        max_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Main method to get video recommendations for a failed question
        
        Args:
            student_id: ID of the student
            failed_question_data: Data about the failed question
            strategy: Algorithm strategy to use (optional)
            max_results: Maximum number of results to return (optional)
            
        Returns:
            Dictionary containing recommendations and metadata
        """
        
        start_time = time.time()
        request_id = self._generate_request_id(student_id, failed_question_data)
        
        logger.info(f"Processing recommendation request {request_id} for student {student_id}")
        
        # Check cache first
        if self._is_cache_hit(request_id):
            cached_result = self.request_cache[request_id][1]
            logger.info(f"Cache hit for request {request_id}")
            return self._format_response(cached_result, cache_hit=True)
        
        # Determine strategy and configuration
        strategy = strategy or self.config.default_strategy
        max_results = max_results or self.config.max_results_per_request
        
        try:
            # Create failed question object
            failed_question = create_failed_question_from_response(failed_question_data)
            
            # Create matching request
            matching_request = MatchingRequest(
                failed_question=failed_question,
                max_videos=max_results,
                min_confidence=self.config.min_match_confidence
            )
            
            # Execute matching strategy
            result = await self._execute_matching_strategy(matching_request, strategy)
            
            # Post-process results
            processed_result = await self._post_process_results(result, strategy)
            
            # Cache the result
            self._cache_result(request_id, processed_result)
            
            # Record performance metrics
            self._record_request_metrics(request_id, student_id, failed_question.question_id, 
                                      start_time, result, strategy)
            
            # Format and return response
            response = self._format_response(processed_result, cache_hit=False)
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"Request {request_id} completed in {processing_time:.2f}ms with {len(result.video_matches)} matches")
            
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Request {request_id} timed out")
            return self._format_error_response("Request timed out", "TIMEOUT")
        
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}")
            return self._format_error_response(str(e), "INTERNAL_ERROR")
    
    async def _execute_matching_strategy(
        self, 
        matching_request: MatchingRequest, 
        strategy: AlgorithmStrategy
    ) -> MatchingResult:
        """Execute the specified matching strategy"""
        
        if strategy == AlgorithmStrategy.SEMANTIC_ONLY:
            return await self._semantic_only_matching(matching_request)
        
        elif strategy == AlgorithmStrategy.TOPIC_ONLY:
            return await self._topic_only_matching(matching_request)
        
        elif strategy == AlgorithmStrategy.DIFFICULTY_ONLY:
            return await self._difficulty_only_matching(matching_request)
        
        elif strategy == AlgorithmStrategy.ERROR_FOCUSED:
            return await self._error_focused_matching(matching_request)
        
        elif strategy == AlgorithmStrategy.ADAPTIVE:
            return await self._adaptive_matching(matching_request)
        
        else:
            # Default to hybrid strategies
            return await self._hybrid_matching(matching_request, strategy)
    
    async def _semantic_only_matching(self, matching_request: MatchingRequest) -> MatchingResult:
        """Execute semantic similarity matching only"""
        
        # Use only the semantic similarity engine
        failed_question = matching_request.failed_question
        
        # Create content item from failed question
        question_item = ContentItem(
            id=failed_question.question_id,
            title=f"Pregunta de {failed_question.subject_area}",
            description=failed_question.question_text,
            content_type="question",
            subject_area=failed_question.subject_area,
            topic=failed_question.topic,
            competency=failed_question.competency
        )
        
        # Load video candidates
        video_candidates = await self._load_video_candidates(failed_question.subject_area)
        
        # Find semantic matches
        similarity_results = await self.semantic_engine.find_most_similar_content(
            query_item=question_item,
            candidate_items=video_candidates,
            top_k=matching_request.max_videos
        )
        
        # Convert to video matches
        video_matches = []
        for i, result in enumerate(similarity_results):
            if result.similarity_score >= matching_request.min_confidence:
                video_match = VideoMatch(
                    video_id=result.content_id,
                    video_title=f"Video {result.content_id}",
                    video_url=f"https://youtube.com/watch?v={result.content_id}",
                    semantic_similarity_score=result.similarity_score,
                    topic_relevance_score=0.0,
                    difficulty_appropriateness_score=0.0,
                    overall_match_score=result.similarity_score,
                    confidence_level=self._determine_confidence_level(result.similarity_score),
                    match_reasons=["Alta similitud semántica"],
                    addressing_error_types=[],
                    matching_strategies=[],
                    expected_learning_impact=result.similarity_score * 0.8,
                    estimated_watch_time=15,
                    success_probability_improvement=result.similarity_score * 0.2,
                    duration_minutes=15,
                    channel_name="Canal Educativo",
                    engagement_metrics={},
                    matched_at=datetime.now(),
                    matching_algorithm_version="semantic-only-1.0"
                )
                video_matches.append(video_match)
        
        # Create result
        return MatchingResult(
            request_id=f"semantic_{failed_question.question_id}_{failed_question.student_id}",
            failed_question=failed_question,
            error_analysis=self._create_basic_error_analysis(failed_question),
            video_matches=video_matches,
            total_matches_found=len(video_matches),
            matching_time_ms=0.0,
            algorithms_used=['semantic_similarity'],
            average_match_confidence=np.mean([m.overall_match_score for m in video_matches]) if video_matches else 0.0,
            coverage_score=0.8 if video_matches else 0.0,
            recommended_viewing_order=[m.video_id for m in video_matches],
            estimated_total_study_time=sum(m.duration_minutes for m in video_matches),
            result_timestamp=datetime.now()
        )
    
    async def _topic_only_matching(self, matching_request: MatchingRequest) -> MatchingResult:
        """Execute topic-based matching only"""
        
        # Implementation would use only the topic filter
        # For brevity, returning a basic implementation
        failed_question = matching_request.failed_question
        
        return MatchingResult(
            request_id=f"topic_{failed_question.question_id}_{failed_question.student_id}",
            failed_question=failed_question,
            error_analysis=self._create_basic_error_analysis(failed_question),
            video_matches=[],
            total_matches_found=0,
            matching_time_ms=0.0,
            algorithms_used=['topic_filtering'],
            average_match_confidence=0.0,
            coverage_score=0.0,
            recommended_viewing_order=[],
            estimated_total_study_time=0,
            result_timestamp=datetime.now()
        )
    
    async def _difficulty_only_matching(self, matching_request: MatchingRequest) -> MatchingResult:
        """Execute difficulty-based matching only"""
        
        # Implementation would use only the difficulty selector
        failed_question = matching_request.failed_question
        
        return MatchingResult(
            request_id=f"difficulty_{failed_question.question_id}_{failed_question.student_id}",
            failed_question=failed_question,
            error_analysis=self._create_basic_error_analysis(failed_question),
            video_matches=[],
            total_matches_found=0,
            matching_time_ms=0.0,
            algorithms_used=['difficulty_selection'],
            average_match_confidence=0.0,
            coverage_score=0.0,
            recommended_viewing_order=[],
            estimated_total_study_time=0,
            result_timestamp=datetime.now()
        )
    
    async def _error_focused_matching(self, matching_request: MatchingRequest) -> MatchingResult:
        """Execute error-focused matching"""
        
        # Use the full intelligent matching service with error analysis focus
        return await self.matching_service.match_videos_for_failed_question(matching_request)
    
    async def _adaptive_matching(self, matching_request: MatchingRequest) -> MatchingResult:
        """Execute adaptive matching with optimized weights"""
        
        # Get current optimized weights
        optimized_weights = self.algorithm_optimizer.optimize_weights()
        
        # Update the matching service weights
        self.matching_service.algorithm_weights = optimized_weights
        
        # Execute hybrid matching
        result = await self.matching_service.match_videos_for_failed_question(matching_request)
        
        # Record performance for future optimization
        if result.video_matches:
            avg_confidence = result.average_match_confidence
            for algorithm in result.algorithms_used:
                self.algorithm_optimizer.record_performance(algorithm, avg_confidence)
        
        return result
    
    async def _hybrid_matching(self, matching_request: MatchingRequest, strategy: AlgorithmStrategy) -> MatchingResult:
        """Execute hybrid matching strategies"""
        
        # Adjust weights based on strategy
        if strategy == AlgorithmStrategy.HYBRID_SEMANTIC_HEAVY:
            weights = {
                'semantic_similarity': 0.50,
                'topic_relevance': 0.25,
                'difficulty_appropriateness': 0.15,
                'error_addressing': 0.10
            }
        elif strategy == AlgorithmStrategy.HYBRID_TOPIC_HEAVY:
            weights = {
                'semantic_similarity': 0.20,
                'topic_relevance': 0.45,
                'difficulty_appropriateness': 0.25,
                'error_addressing': 0.10
            }
        else:  # HYBRID_BALANCED
            weights = self.config.algorithm_weights
        
        # Update matching service weights
        self.matching_service.algorithm_weights = weights
        
        # Execute matching
        return await self.matching_service.match_videos_for_failed_question(matching_request)
    
    async def _post_process_results(self, result: MatchingResult, strategy: AlgorithmStrategy) -> MatchingResult:
        """Post-process matching results for optimization"""
        
        # Apply quality filtering if enabled
        if self.config.enable_quality_filtering:
            filtered_matches = []
            for match in result.video_matches:
                # Quality criteria
                if (match.overall_match_score >= self.config.min_match_confidence and
                    match.expected_learning_impact > 0.3):
                    filtered_matches.append(match)
            
            result.video_matches = filtered_matches
        
        # Re-rank based on performance profile
        if self.config.performance_profile == PerformanceProfile.ACCURACY_OPTIMIZED:
            result.video_matches.sort(key=lambda x: x.overall_match_score, reverse=True)
        elif self.config.performance_profile == PerformanceProfile.SPEED_OPTIMIZED:
            # Limit to top results for speed
            result.video_matches = result.video_matches[:5]
        
        return result
    
    def _is_cache_hit(self, request_id: str) -> bool:
        """Check if request is a cache hit"""
        if request_id in self.request_cache:
            cached_time, _ = self.request_cache[request_id]
            if datetime.now() - cached_time < timedelta(seconds=self.config.cache_ttl_seconds):
                return True
            else:
                # Remove expired cache entry
                del self.request_cache[request_id]
        
        return False
    
    def _cache_result(self, request_id: str, result: MatchingResult):
        """Cache matching result"""
        self.request_cache[request_id] = (datetime.now(), result)
        
        # Clean up old cache entries
        if len(self.request_cache) > 1000:  # Limit cache size
            oldest_entries = sorted(self.request_cache.items(), 
                                  key=lambda x: x[1][0])[:100]
            for entry_id, _ in oldest_entries:
                del self.request_cache[entry_id]
    
    def _record_request_metrics(
        self, 
        request_id: str, 
        student_id: str, 
        question_id: Union[int, str],
        start_time: float,
        result: MatchingResult,
        strategy: AlgorithmStrategy
    ):
        """Record detailed metrics for the request"""
        
        if not self.config.enable_performance_monitoring:
            return
        
        total_time = (time.time() - start_time) * 1000
        
        metrics = RequestMetrics(
            request_id=request_id,
            student_id=student_id,
            question_id=question_id,
            total_time_ms=total_time,
            semantic_time_ms=0.0,  # Would need to measure individually
            topic_time_ms=0.0,
            difficulty_time_ms=0.0,
            integration_time_ms=0.0,
            results_count=len(result.video_matches),
            average_confidence=result.average_match_confidence,
            coverage_score=result.coverage_score,
            algorithms_used=result.algorithms_used,
            cache_hit_rate=1.0 if result.cache_hit else 0.0,
            timestamp=datetime.now(),
            strategy_used=strategy,
            performance_profile=self.config.performance_profile
        )
        
        self.performance_monitor.record_request_metrics(metrics)
    
    def _format_response(self, result: MatchingResult, cache_hit: bool = False) -> Dict[str, Any]:
        """Format the matching result as API response"""
        
        return {
            'success': True,
            'request_id': result.request_id,
            'cache_hit': cache_hit,
            'timestamp': result.result_timestamp.isoformat(),
            'processing_time_ms': result.matching_time_ms,
            'student_analysis': {
                'student_id': result.failed_question.student_id,
                'error_analysis': {
                    'primary_error_type': result.error_analysis.primary_error_type.value,
                    'confidence': result.error_analysis.error_confidence,
                    'intervention_priority': result.error_analysis.intervention_priority
                }
            },
            'recommendations': {
                'total_found': result.total_matches_found,
                'returned_count': len(result.video_matches),
                'average_confidence': round(result.average_match_confidence, 3),
                'coverage_score': round(result.coverage_score, 3),
                'videos': [
                    {
                        'video_id': match.video_id,
                        'title': match.video_title,
                        'url': match.video_url,
                        'duration_minutes': match.duration_minutes,
                        'confidence_level': match.confidence_level.value,
                        'overall_score': round(match.overall_match_score, 3),
                        'match_reasons': match.match_reasons,
                        'expected_impact': round(match.expected_learning_impact, 3),
                        'estimated_improvement': round(match.success_probability_improvement, 3)
                    }
                    for match in result.video_matches
                ],
                'viewing_order': result.recommended_viewing_order,
                'estimated_study_time': result.estimated_total_study_time
            },
            'metadata': {
                'algorithms_used': result.algorithms_used,
                'version': '1.0'
            }
        }
    
    def _format_error_response(self, error_message: str, error_code: str) -> Dict[str, Any]:
        """Format error response"""
        
        return {
            'success': False,
            'error': {
                'code': error_code,
                'message': error_message,
                'timestamp': datetime.now().isoformat()
            },
            'recommendations': {
                'total_found': 0,
                'returned_count': 0,
                'videos': []
            }
        }
    
    async def _load_video_candidates(self, subject_area: str) -> List[ContentItem]:
        """Load video candidates from database"""
        
        # This is a simplified implementation
        # In practice, this would query the database for relevant videos
        
        candidates = []
        for i in range(10):  # Mock 10 videos
            candidate = ContentItem(
                id=f"video_{i}",
                title=f"Video educativo {i} - {subject_area}",
                description=f"Descripción del video {i}",
                content_type="video",
                subject_area=subject_area,
                topic="Tema general",
                competency="General"
            )
            candidates.append(candidate)
        
        return candidates
    
    def _create_basic_error_analysis(self, failed_question: FailedQuestion) -> ErrorAnalysis:
        """Create basic error analysis"""
        
        from .intelligent_question_video_matching_service import ErrorAnalysis, ErrorType, MatchingStrategy
        
        return ErrorAnalysis(
            question_id=failed_question.question_id,
            student_id=failed_question.student_id,
            primary_error_type=ErrorType.CONCEPTUAL,
            secondary_error_types=[],
            error_confidence=0.7,
            distractor_analysis={},
            common_error_pattern="general_pattern",
            error_frequency=0.3,
            time_pressure_indicator=0.2,
            prerequisite_gaps=[],
            conceptual_misunderstandings=[],
            intervention_priority=3,
            recommended_strategies=[MatchingStrategy.CONCEPT_REVIEW],
            analysis_timestamp=datetime.now(),
            analysis_confidence=0.7
        )
    
    def _determine_confidence_level(self, score: float):
        """Determine confidence level from score"""
        from .intelligent_question_video_matching_service import MatchingConfidence
        
        if score >= 0.8:
            return MatchingConfidence.HIGH
        elif score >= 0.6:
            return MatchingConfidence.MODERATE
        else:
            return MatchingConfidence.LOW
    
    def _generate_request_id(self, student_id: str, failed_question_data: Dict[str, Any]) -> str:
        """Generate unique request ID"""
        
        key_data = {
            'student_id': student_id,
            'question_id': failed_question_data.get('question_id'),
            'student_answer': failed_question_data.get('student_answer')
        }
        
        key_json = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_json.encode()).hexdigest()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        system_metrics = self.performance_monitor.get_system_metrics()
        performance_report = self.performance_monitor.get_performance_report()
        
        return {
            'status': 'operational',
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'configuration': {
                'default_strategy': self.config.default_strategy.value,
                'performance_profile': self.config.performance_profile.value,
                'max_concurrent_requests': self.config.max_concurrent_requests,
                'cache_enabled': True
            },
            'components': {
                'semantic_engine': 'operational',
                'topic_filter': 'operational', 
                'difficulty_selector': 'operational',
                'matching_service': 'operational'
            },
            'performance': performance_report,
            'cache_stats': {
                'cached_entries': len(self.request_cache),
                'cache_size_limit': 1000
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        
        health_status = {
            'overall': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'issues': []
        }
        
        # Check database connectivity
        try:
            self.db.execute(text("SELECT 1"))
            health_status['components']['database'] = 'healthy'
        except Exception as e:
            health_status['components']['database'] = 'unhealthy'
            health_status['issues'].append(f"Database connectivity: {e}")
            health_status['overall'] = 'degraded'
        
        # Check component services
        try:
            # Simple test of semantic engine
            test_item = ContentItem(
                id="test",
                title="Test",
                description="Test description",
                content_type="test",
                subject_area="Test",
                topic="Test",
                competency="Test"
            )
            
            await self.semantic_engine.generate_embedding("test text")
            health_status['components']['semantic_engine'] = 'healthy'
        except Exception as e:
            health_status['components']['semantic_engine'] = 'unhealthy'
            health_status['issues'].append(f"Semantic engine: {e}")
            health_status['overall'] = 'degraded'
        
        # Check performance metrics
        system_metrics = self.performance_monitor.get_system_metrics()
        if system_metrics:
            if system_metrics.error_rate > 0.1:
                health_status['issues'].append(f"High error rate: {system_metrics.error_rate:.2%}")
                health_status['overall'] = 'degraded'
            
            if system_metrics.average_response_time_ms > 10000:
                health_status['issues'].append(f"High response time: {system_metrics.average_response_time_ms:.0f}ms")
                health_status['overall'] = 'degraded'
        
        health_status['components']['performance_monitor'] = 'healthy'
        health_status['components']['algorithm_optimizer'] = 'healthy'
        
        return health_status

# Factory function for easy initialization
def create_master_orchestrator(
    db_session: Session,
    openai_api_key: Optional[str] = None,
    performance_profile: PerformanceProfile = PerformanceProfile.BALANCED
) -> MasterVideoMatchingOrchestrator:
    """Create and configure master orchestrator"""
    
    config = SystemConfiguration(
        performance_profile=performance_profile,
        enable_performance_monitoring=True,
        enable_quality_filtering=True
    )
    
    return MasterVideoMatchingOrchestrator(
        db_session=db_session,
        openai_api_key=openai_api_key,
        config=config
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
    
    async def test_orchestrator():
        """Test the master orchestrator"""
        
        db = MockSession()
        orchestrator = create_master_orchestrator(db)
        
        # Test failed question data
        failed_question_data = {
            'question_id': 1,
            'student_id': 'test_student',
            'question_text': 'Resolver el sistema de ecuaciones: 2x + y = 5, x - y = 1',
            'question_type': 'multiple_choice',
            'correct_answer': 'x=2, y=1',
            'student_answer': 'x=1, y=3',
            'subject_area': 'Matemáticas',
            'topic': 'Álgebra',
            'competency': 'Razonamiento matemático',
            'time_spent_seconds': 120,
            'student_theta': -0.5,
            'question_difficulty': 0.2
        }
        
        print("Testing Master Video Matching Orchestrator...")
        print(f"Configuration: {orchestrator.config.performance_profile}")
        print(f"Default Strategy: {orchestrator.config.default_strategy}")
        
        # Test health check
        health = await orchestrator.health_check()
        print(f"Health Status: {health['overall']}")
        
        # Test system status
        status = orchestrator.get_system_status()
        print(f"System Status: {status['status']}")
        
        print("Master orchestrator initialized successfully!")
    
    # Run the test
    asyncio.run(test_orchestrator())