"""
Learning Styles Support Service
Implements comprehensive support for different learning styles and preferences
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import json
import logging
from enum import Enum
from dataclasses import dataclass, asdict

from ..models.user import User
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.video_tracking import VideoTracking
from ..models.battle import Battle, BattleAnswer
from ..core.config import settings
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)

class LearningStyle(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MULTIMODAL = "multimodal"

class ContentType(Enum):
    VIDEO = "video"
    TEXT = "text"
    INTERACTIVE = "interactive"
    AUDIO = "audio"
    VISUAL_AID = "visual_aid"
    PRACTICE = "practice"

class DifficultyPreference(Enum):
    GRADUAL = "gradual"
    CHALLENGING = "challenging"
    MIXED = "mixed"
    ADAPTIVE = "adaptive"

@dataclass
class LearningPreference:
    """Represents a learning preference for a user"""
    preference_id: str
    category: str
    value: Any
    confidence: float  # 0-1, how confident we are about this preference
    source: str  # "detected", "declared", "adaptive"
    last_updated: datetime

@dataclass
class ContentAdaptation:
    """Represents how content should be adapted for a learning style"""
    adaptation_id: str
    original_content: Dict[str, Any]
    adapted_content: Dict[str, Any]
    learning_style: LearningStyle
    adaptation_reasons: List[str]
    effectiveness_score: float

class LearningStylesService:
    """
    Service for detecting, tracking, and adapting to different learning styles
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Learning style detection weights
        self.DETECTION_WEIGHTS = {
            "video_engagement": 0.3,
            "reading_speed": 0.2,
            "practice_performance": 0.25,
            "interaction_patterns": 0.15,
            "time_preferences": 0.1
        }
        
    async def detect_learning_style(
        self,
        user_id: str,
        analysis_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Detect user's learning style based on behavioral patterns
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Analyze video engagement patterns
            video_analysis = await self._analyze_video_engagement_patterns(
                user_id, analysis_period_days
            )
            
            # Analyze reading/text interaction patterns
            reading_analysis = await self._analyze_reading_patterns(
                user_id, analysis_period_days
            )
            
            # Analyze practice and interaction preferences
            practice_analysis = await self._analyze_practice_patterns(
                user_id, analysis_period_days
            )
            
            # Analyze time and session preferences
            time_analysis = await self._analyze_time_preferences(
                user_id, analysis_period_days
            )
            
            # Analyze performance by content type
            performance_analysis = await self._analyze_performance_by_content_type(
                user_id, analysis_period_days
            )
            
            # Calculate learning style scores
            style_scores = await self._calculate_learning_style_scores(
                video_analysis, reading_analysis, practice_analysis,
                time_analysis, performance_analysis
            )
            
            # Determine primary and secondary styles
            primary_style, secondary_style = await self._determine_learning_styles(
                style_scores
            )
            
            # Generate learning preferences
            preferences = await self._generate_learning_preferences(
                user_id, primary_style, secondary_style, {
                    "video": video_analysis,
                    "reading": reading_analysis,
                    "practice": practice_analysis,
                    "time": time_analysis,
                    "performance": performance_analysis
                }
            )
            
            # Create adaptation recommendations
            adaptations = await self._create_adaptation_recommendations(
                primary_style, secondary_style, preferences
            )
            
            detection_result = {
                "user_id": user_id,
                "analysis_period_days": analysis_period_days,
                "detection_date": datetime.now().isoformat(),
                "primary_learning_style": primary_style.value,
                "secondary_learning_style": secondary_style.value if secondary_style else None,
                "confidence_score": style_scores[primary_style],
                "all_style_scores": {style.value: score for style, score in style_scores.items()},
                "behavioral_analysis": {
                    "video_patterns": video_analysis,
                    "reading_patterns": reading_analysis,
                    "practice_patterns": practice_analysis,
                    "time_preferences": time_analysis,
                    "performance_patterns": performance_analysis
                },
                "learning_preferences": [asdict(pref) for pref in preferences],
                "adaptation_recommendations": adaptations,
                "reliability_indicators": await self._calculate_reliability_indicators(
                    style_scores, analysis_period_days
                )
            }
            
            # Cache the result
            cache_key = f"learning_style_detection:{user_id}"
            cache_service.set(cache_key, detection_result, ttl=3600 * 24)  # 24 hours
            
            return detection_result
            
        except Exception as e:
            logger.error(f"Error detecting learning style: {str(e)}")
            raise
    
    async def adapt_content_for_learning_style(
        self,
        content: Dict[str, Any],
        user_id: str,
        learning_style: LearningStyle = None
    ) -> Dict[str, Any]:
        """
        Adapt content based on user's learning style
        """
        try:
            # Get user's learning style if not provided
            if not learning_style:
                detection_result = await self.detect_learning_style(user_id)
                learning_style = LearningStyle(detection_result["primary_learning_style"])
            
            # Get user preferences
            preferences = await self._get_user_learning_preferences(user_id)
            
            # Apply style-specific adaptations
            adapted_content = await self._apply_learning_style_adaptations(
                content, learning_style, preferences
            )
            
            # Add supplementary resources
            supplementary = await self._add_supplementary_resources(
                content, learning_style
            )
            
            # Optimize presentation order
            optimized_order = await self._optimize_content_order(
                adapted_content, learning_style
            )
            
            # Create engagement enhancers
            engagement_enhancers = await self._create_engagement_enhancers(
                content, learning_style
            )
            
            adaptation_result = {
                "original_content": content,
                "adapted_content": optimized_order,
                "learning_style": learning_style.value,
                "supplementary_resources": supplementary,
                "engagement_enhancers": engagement_enhancers,
                "adaptation_metadata": {
                    "adaptations_applied": await self._list_adaptations_applied(
                        content, optimized_order, learning_style
                    ),
                    "confidence_score": await self._calculate_adaptation_confidence(
                        learning_style, preferences
                    ),
                    "expected_effectiveness": await self._predict_content_effectiveness(
                        optimized_order, learning_style, user_id
                    )
                }
            }
            
            return adaptation_result
            
        except Exception as e:
            logger.error(f"Error adapting content for learning style: {str(e)}")
            return {"error": str(e), "original_content": content}
    
    async def create_personalized_study_approach(
        self,
        user_id: str,
        subject_id: str,
        learning_objectives: List[str]
    ) -> Dict[str, Any]:
        """
        Create a personalized study approach based on learning style
        """
        try:
            # Detect learning style
            style_detection = await self.detect_learning_style(user_id)
            primary_style = LearningStyle(style_detection["primary_learning_style"])
            
            # Get subject-specific adaptations
            subject_adaptations = await self._get_subject_specific_adaptations(
                subject_id, primary_style
            )
            
            # Create study methodology
            study_methodology = await self._create_study_methodology(
                primary_style, learning_objectives, subject_adaptations
            )
            
            # Design session structure
            session_structure = await self._design_session_structure(
                primary_style, style_detection["time_preferences"]
            )
            
            # Create resource recommendations
            resource_recommendations = await self._create_resource_recommendations(
                primary_style, subject_id, learning_objectives
            )
            
            # Generate practice strategies
            practice_strategies = await self._generate_practice_strategies(
                primary_style, subject_id
            )
            
            # Create assessment preferences
            assessment_preferences = await self._create_assessment_preferences(
                primary_style, style_detection["behavioral_analysis"]
            )
            
            personalized_approach = {
                "user_id": user_id,
                "subject_id": subject_id,
                "primary_learning_style": primary_style.value,
                "learning_objectives": learning_objectives,
                "study_methodology": study_methodology,
                "session_structure": session_structure,
                "resource_recommendations": resource_recommendations,
                "practice_strategies": practice_strategies,
                "assessment_preferences": assessment_preferences,
                "adaptation_tips": await self._generate_adaptation_tips(primary_style),
                "effectiveness_prediction": await self._predict_approach_effectiveness(
                    user_id, primary_style, study_methodology
                ),
                "alternative_approaches": await self._suggest_alternative_approaches(
                    primary_style, style_detection["all_style_scores"]
                )
            }
            
            return personalized_approach
            
        except Exception as e:
            logger.error(f"Error creating personalized study approach: {str(e)}")
            return {"error": str(e)}
    
    async def track_learning_style_effectiveness(
        self,
        user_id: str,
        adaptation_id: str,
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track the effectiveness of learning style adaptations
        """
        try:
            # Get original adaptation data
            adaptation_data = await self._get_adaptation_data(adaptation_id)
            
            # Calculate effectiveness metrics
            effectiveness_metrics = await self._calculate_effectiveness_metrics(
                adaptation_data, performance_data
            )
            
            # Compare with baseline performance
            baseline_comparison = await self._compare_with_baseline(
                user_id, adaptation_data, performance_data
            )
            
            # Update learning style confidence
            style_confidence_update = await self._update_style_confidence(
                user_id, effectiveness_metrics
            )
            
            # Generate insights
            insights = await self._generate_effectiveness_insights(
                effectiveness_metrics, baseline_comparison
            )
            
            # Create improvement recommendations
            improvements = await self._suggest_adaptation_improvements(
                adaptation_data, effectiveness_metrics
            )
            
            tracking_result = {
                "user_id": user_id,
                "adaptation_id": adaptation_id,
                "tracking_date": datetime.now().isoformat(),
                "effectiveness_metrics": effectiveness_metrics,
                "baseline_comparison": baseline_comparison,
                "style_confidence_update": style_confidence_update,
                "insights": insights,
                "improvement_recommendations": improvements,
                "overall_effectiveness_score": effectiveness_metrics.get("overall_score", 0),
                "recommendation": await self._generate_overall_recommendation(
                    effectiveness_metrics, baseline_comparison
                )
            }
            
            # Cache the tracking data
            cache_key = f"style_effectiveness:{user_id}:{adaptation_id}"
            cache_service.set(cache_key, tracking_result, ttl=3600 * 12)  # 12 hours
            
            return tracking_result
            
        except Exception as e:
            logger.error(f"Error tracking learning style effectiveness: {str(e)}")
            return {"error": str(e)}
    
    # Private helper methods
    
    async def _analyze_video_engagement_patterns(
        self, user_id: str, days: int
    ) -> Dict[str, Any]:
        """Analyze user's video watching patterns"""
        
        video_data = self.db.query(VideoTracking).filter(
            VideoTracking.user_id == user_id,
            VideoTracking.watched_at >= datetime.now() - timedelta(days=days)
        ).all()
        
        if not video_data:
            return {
                "engagement_level": 0.5,
                "completion_rate": 0.5,
                "preferred_duration": 600,  # 10 minutes default
                "rewatch_frequency": 0,
                "interaction_patterns": []
            }
        
        total_videos = len(video_data)
        completed_videos = sum(1 for v in video_data if v.completion_percentage >= 80)
        avg_completion = sum(v.completion_percentage for v in video_data) / total_videos
        
        # Analyze preferred video duration
        duration_preferences = {}
        for video in video_data:
            duration_bucket = self._get_duration_bucket(video.watch_time_seconds)
            duration_preferences[duration_bucket] = duration_preferences.get(duration_bucket, 0) + 1
        
        preferred_duration = max(duration_preferences.items(), key=lambda x: x[1])[0] if duration_preferences else 600
        
        return {
            "engagement_level": completed_videos / total_videos,
            "completion_rate": avg_completion / 100,
            "preferred_duration": preferred_duration,
            "total_videos_watched": total_videos,
            "rewatch_frequency": await self._calculate_rewatch_frequency(video_data),
            "interaction_patterns": await self._analyze_video_interaction_patterns(video_data),
            "optimal_video_length": await self._determine_optimal_video_length(video_data)
        }
    
    async def _analyze_reading_patterns(
        self, user_id: str, days: int
    ) -> Dict[str, Any]:
        """Analyze user's reading and text interaction patterns"""
        
        # This would analyze text-based content interaction
        # For now, return estimated patterns based on available data
        battles = self.db.query(Battle).filter(
            Battle.user_id == user_id,
            Battle.created_at >= datetime.now() - timedelta(days=days)
        ).all()
        
        if not battles:
            return {
                "reading_speed": "medium",
                "text_preference": "moderate",
                "comprehension_rate": 0.7,
                "preferred_text_length": "medium"
            }
        
        # Analyze question reading patterns
        total_response_time = 0
        total_questions = 0
        
        for battle in battles:
            answers = self.db.query(BattleAnswer).filter(
                BattleAnswer.battle_id == battle.id
            ).all()
            
            for answer in answers:
                if answer.response_time_ms:
                    total_response_time += answer.response_time_ms
                    total_questions += 1
        
        avg_response_time = total_response_time / total_questions if total_questions > 0 else 30000
        
        # Classify reading speed
        if avg_response_time < 20000:  # < 20 seconds
            reading_speed = "fast"
        elif avg_response_time < 40000:  # < 40 seconds
            reading_speed = "medium"
        else:
            reading_speed = "slow"
        
        return {
            "reading_speed": reading_speed,
            "average_response_time_ms": avg_response_time,
            "text_preference": "high" if avg_response_time < 25000 else "medium",
            "comprehension_rate": await self._estimate_reading_comprehension(battles),
            "preferred_text_length": await self._determine_preferred_text_length(battles)
        }
    
    async def _analyze_practice_patterns(
        self, user_id: str, days: int
    ) -> Dict[str, Any]:
        """Analyze user's practice and hands-on learning patterns"""
        
        battles = self.db.query(Battle).filter(
            Battle.user_id == user_id,
            Battle.created_at >= datetime.now() - timedelta(days=days)
        ).all()
        
        if not battles:
            return {
                "practice_frequency": 0,
                "hands_on_preference": 0.5,
                "trial_error_comfort": 0.5,
                "repetition_tolerance": 0.5
            }
        
        total_battles = len(battles)
        
        # Calculate practice frequency (battles per day)
        practice_frequency = total_battles / days
        
        # Analyze trial-and-error patterns
        trial_error_score = 0
        repetition_score = 0
        
        for battle in battles:
            answers = self.db.query(BattleAnswer).filter(
                BattleAnswer.battle_id == battle.id
            ).all()
            
            # Multiple attempts on same questions indicate trial-error comfort
            question_attempts = {}
            for answer in answers:
                q_id = answer.question_id
                question_attempts[q_id] = question_attempts.get(q_id, 0) + 1
            
            repeat_attempts = sum(1 for attempts in question_attempts.values() if attempts > 1)
            if len(question_attempts) > 0:
                trial_error_score += repeat_attempts / len(question_attempts)
                repetition_score += repeat_attempts / len(question_attempts)
        
        trial_error_comfort = trial_error_score / total_battles if total_battles > 0 else 0.5
        repetition_tolerance = repetition_score / total_battles if total_battles > 0 else 0.5
        
        return {
            "practice_frequency": practice_frequency,
            "hands_on_preference": min(1.0, practice_frequency / 2),  # Normalize to 0-1
            "trial_error_comfort": trial_error_comfort,
            "repetition_tolerance": repetition_tolerance,
            "interactive_engagement": await self._calculate_interactive_engagement(battles)
        }
    
    async def _calculate_learning_style_scores(
        self,
        video_analysis: Dict,
        reading_analysis: Dict,
        practice_analysis: Dict,
        time_analysis: Dict,
        performance_analysis: Dict
    ) -> Dict[LearningStyle, float]:
        """Calculate scores for each learning style based on behavioral analysis"""
        
        scores = {style: 0.0 for style in LearningStyle}
        
        # Visual learners: high video engagement, moderate reading
        scores[LearningStyle.VISUAL] = (
            video_analysis["engagement_level"] * 0.4 +
            (1 - reading_analysis.get("text_preference_score", 0.5)) * 0.3 +
            performance_analysis.get("visual_content_performance", 0.5) * 0.3
        )
        
        # Auditory learners: moderate video (for audio), low reading speed preference
        scores[LearningStyle.AUDITORY] = (
            video_analysis["engagement_level"] * 0.3 +
            (reading_analysis["reading_speed"] == "slow") * 0.4 +
            performance_analysis.get("audio_content_performance", 0.5) * 0.3
        )
        
        # Kinesthetic learners: high practice frequency, hands-on preference
        scores[LearningStyle.KINESTHETIC] = (
            practice_analysis["hands_on_preference"] * 0.4 +
            practice_analysis["trial_error_comfort"] * 0.3 +
            practice_analysis["interactive_engagement"] * 0.3
        )
        
        # Reading/Writing learners: high text preference, good reading comprehension
        scores[LearningStyle.READING_WRITING] = (
            reading_analysis.get("text_preference_score", 0.5) * 0.4 +
            reading_analysis["comprehension_rate"] * 0.3 +
            (reading_analysis["reading_speed"] == "fast") * 0.3
        )
        
        # Multimodal learners: balanced across all modalities
        multimodal_balance = 1 - max(scores.values()) + min(scores.values())  # Higher when scores are balanced
        scores[LearningStyle.MULTIMODAL] = multimodal_balance
        
        # Normalize scores to 0-1 range
        max_score = max(scores.values()) if max(scores.values()) > 0 else 1
        for style in scores:
            scores[style] = scores[style] / max_score
        
        return scores
    
    async def _determine_learning_styles(
        self, style_scores: Dict[LearningStyle, float]
    ) -> Tuple[LearningStyle, Optional[LearningStyle]]:
        """Determine primary and secondary learning styles"""
        
        sorted_styles = sorted(style_scores.items(), key=lambda x: x[1], reverse=True)
        
        primary_style = sorted_styles[0][0]
        
        # Secondary style if score is close to primary (within 20%)
        secondary_style = None
        if len(sorted_styles) > 1:
            primary_score = sorted_styles[0][1]
            secondary_score = sorted_styles[1][1]
            if secondary_score >= primary_score * 0.8:
                secondary_style = sorted_styles[1][0]
        
        return primary_style, secondary_style
    
    async def _apply_learning_style_adaptations(
        self,
        content: Dict[str, Any],
        learning_style: LearningStyle,
        preferences: List[LearningPreference]
    ) -> Dict[str, Any]:
        """Apply learning style-specific adaptations to content"""
        
        adapted_content = content.copy()
        
        if learning_style == LearningStyle.VISUAL:
            adapted_content = await self._adapt_for_visual_learner(adapted_content)
        elif learning_style == LearningStyle.AUDITORY:
            adapted_content = await self._adapt_for_auditory_learner(adapted_content)
        elif learning_style == LearningStyle.KINESTHETIC:
            adapted_content = await self._adapt_for_kinesthetic_learner(adapted_content)
        elif learning_style == LearningStyle.READING_WRITING:
            adapted_content = await self._adapt_for_reading_writing_learner(adapted_content)
        elif learning_style == LearningStyle.MULTIMODAL:
            adapted_content = await self._adapt_for_multimodal_learner(adapted_content)
        
        # Apply user-specific preferences
        for preference in preferences:
            adapted_content = await self._apply_preference_adaptation(
                adapted_content, preference
            )
        
        return adapted_content
    
    async def _adapt_for_visual_learner(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt content for visual learners"""
        
        # Prioritize visual elements
        if "resources" not in content:
            content["resources"] = []
        
        # Add visual aids
        visual_resources = [
            {"type": "diagram", "description": "Visual representation of concepts"},
            {"type": "infographic", "description": "Key points in visual format"},
            {"type": "mind_map", "description": "Concept relationships visualization"},
            {"type": "flowchart", "description": "Process visualization"}
        ]
        
        content["resources"].extend(visual_resources)
        
        # Emphasize visual learning techniques
        content["learning_techniques"] = content.get("learning_techniques", [])
        content["learning_techniques"].extend([
            "Use color coding for different concepts",
            "Create visual summaries",
            "Draw concept maps",
            "Use spatial organization"
        ])
        
        # Modify content presentation
        content["presentation_style"] = "visual_heavy"
        content["recommended_tools"] = ["mind mapping software", "diagram creators", "visual note-taking apps"]
        
        return content
    
    async def _adapt_for_kinesthetic_learner(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt content for kinesthetic learners"""
        
        # Add hands-on activities
        if "activities" not in content:
            content["activities"] = []
        
        hands_on_activities = [
            {"type": "simulation", "description": "Interactive problem-solving scenarios"},
            {"type": "practice_lab", "description": "Hands-on practice exercises"},
            {"type": "role_play", "description": "Act out concepts"},
            {"type": "building_models", "description": "Create physical or digital models"}
        ]
        
        content["activities"].extend(hands_on_activities)
        
        # Emphasize movement and interaction
        content["learning_techniques"] = content.get("learning_techniques", [])
        content["learning_techniques"].extend([
            "Take frequent breaks to move around",
            "Use manipulatives and tools",
            "Practice by doing",
            "Use trial and error approach"
        ])
        
        # Modify session structure
        content["session_structure"] = {
            "warm_up": "5 min movement/activation",
            "main_content": "broken into 15-20 min chunks",
            "practice_breaks": "hands-on practice every 20 minutes",
            "cool_down": "reflective activity"
        }
        
        return content