"""
Adaptive Learning Service
Implements dynamic learning path adjustments based on real-time performance data
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import json
import logging
import math
from enum import Enum

from ..models.user import User
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.topic import Topic
from ..models.question import Question
from ..models.battle import Battle, BattleAnswer
from ..models.video_tracking import VideoTracking
from ..core.config import settings
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)

class AdaptationTrigger(Enum):
    PERFORMANCE_DROP = "performance_drop"
    MASTERY_ACHIEVED = "mastery_achieved"
    STRUGGLING_TOPIC = "struggling_topic"
    RAPID_PROGRESS = "rapid_progress"
    ENGAGEMENT_LOW = "engagement_low"
    TIME_CONSTRAINT = "time_constraint"

class AdaptiveAction(Enum):
    REDUCE_DIFFICULTY = "reduce_difficulty"
    INCREASE_DIFFICULTY = "increase_difficulty"
    ADD_REVIEW_SESSIONS = "add_review_sessions"
    SKIP_REDUNDANT_CONTENT = "skip_redundant_content"
    ADD_PRACTICE_EXERCISES = "add_practice_exercises"
    CHANGE_CONTENT_TYPE = "change_content_type"
    ADJUST_PACING = "adjust_pacing"
    ADD_MOTIVATION_BOOST = "add_motivation_boost"

class AdaptiveLearningService:
    """
    Service for implementing adaptive learning path adjustments
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    async def evaluate_learning_progress(
        self,
        user_id: str,
        plan_id: str,
        current_unit: int = None
    ) -> Dict[str, Any]:
        """
        Evaluate current learning progress and identify adaptation needs
        """
        try:
            # Get current study plan
            study_plan = self.db.query(StudyPlan).filter(
                StudyPlan.id == plan_id,
                StudyPlan.user_id == user_id
            ).first()
            
            if not study_plan:
                raise ValueError(f"Study plan {plan_id} not found")
            
            # Analyze performance trends
            performance_analysis = await self._analyze_performance_trends(user_id, plan_id)
            
            # Detect learning patterns
            learning_patterns = await self._detect_learning_patterns(user_id, plan_id)
            
            # Identify adaptation triggers
            triggers = await self._identify_adaptation_triggers(
                performance_analysis, learning_patterns
            )
            
            # Generate adaptation recommendations
            adaptations = await self._generate_adaptations(
                triggers, performance_analysis, learning_patterns
            )
            
            evaluation = {
                "plan_id": plan_id,
                "evaluation_timestamp": datetime.now().isoformat(),
                "performance_analysis": performance_analysis,
                "learning_patterns": learning_patterns,
                "adaptation_triggers": triggers,
                "recommended_adaptations": adaptations,
                "overall_health_score": self._calculate_plan_health_score(
                    performance_analysis, learning_patterns
                ),
                "intervention_urgency": self._assess_intervention_urgency(triggers)
            }
            
            # Cache the evaluation
            cache_key = f"adaptive_eval:{user_id}:{plan_id}"
            cache_service.set(cache_key, evaluation, ttl=1800)  # 30 minutes
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating learning progress: {str(e)}")
            raise
    
    async def apply_adaptations(
        self,
        user_id: str,
        plan_id: str,
        adaptations: List[Dict[str, Any]],
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """
        Apply adaptive learning adjustments to study plan
        """
        try:
            study_plan = self.db.query(StudyPlan).filter(
                StudyPlan.id == plan_id,
                StudyPlan.user_id == user_id
            ).first()
            
            if not study_plan:
                raise ValueError(f"Study plan {plan_id} not found")
            
            applied_adaptations = []
            failed_adaptations = []
            
            plan_data = study_plan.plan_data
            if isinstance(plan_data, str):
                plan_data = json.loads(plan_data)
            
            for adaptation in adaptations:
                try:
                    if auto_apply or adaptation.get("approved", False):
                        result = await self._apply_single_adaptation(
                            plan_data, adaptation
                        )
                        if result["success"]:
                            applied_adaptations.append(adaptation)
                        else:
                            failed_adaptations.append({
                                "adaptation": adaptation,
                                "error": result["error"]
                            })
                except Exception as e:
                    failed_adaptations.append({
                        "adaptation": adaptation,
                        "error": str(e)
                    })
            
            # Update the study plan with adaptations
            if applied_adaptations:
                study_plan.plan_data = plan_data
                study_plan.updated_at = datetime.now()
                self.db.commit()
                
                # Log the adaptations
                await self._log_adaptations(user_id, plan_id, applied_adaptations)
            
            return {
                "success": True,
                "applied_adaptations": len(applied_adaptations),
                "failed_adaptations": len(failed_adaptations),
                "adaptations_applied": applied_adaptations,
                "adaptations_failed": failed_adaptations,
                "updated_plan": plan_data if applied_adaptations else None
            }
            
        except Exception as e:
            logger.error(f"Error applying adaptations: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_real_time_adjustments(
        self,
        user_id: str,
        plan_id: str,
        current_activity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get real-time adjustments during study session
        """
        try:
            # Analyze current session performance
            session_analysis = await self._analyze_current_session(
                user_id, current_activity
            )
            
            # Generate immediate adjustments
            immediate_adjustments = await self._generate_immediate_adjustments(
                session_analysis
            )
            
            # Get motivational interventions if needed
            motivational_interventions = await self._get_motivational_interventions(
                session_analysis
            )
            
            return {
                "session_analysis": session_analysis,
                "immediate_adjustments": immediate_adjustments,
                "motivational_interventions": motivational_interventions,
                "continue_current_approach": session_analysis["performance_trend"] == "positive"
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time adjustments: {str(e)}")
            return {"error": str(e)}
    
    # Private methods for analysis and adaptation
    
    async def _analyze_performance_trends(
        self, user_id: str, plan_id: str
    ) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        
        # Get recent progress data
        progress_records = self.db.query(PlanProgress).filter(
            PlanProgress.plan_id == plan_id
        ).all()
        
        # Get recent battle/quiz results
        recent_battles = self.db.query(Battle).filter(
            Battle.user_id == user_id,
            Battle.created_at >= datetime.now() - timedelta(days=14)
        ).order_by(Battle.created_at.desc()).all()
        
        if not recent_battles:
            return {
                "trend": "insufficient_data",
                "average_score": 0,
                "improvement_rate": 0,
                "consistency": 0
            }
        
        # Calculate trends
        scores = []
        for battle in recent_battles:
            answers = self.db.query(BattleAnswer).filter(
                BattleAnswer.battle_id == battle.id
            ).all()
            
            if answers:
                correct_answers = sum(1 for answer in answers if answer.is_correct)
                battle_score = (correct_answers / len(answers)) * 100
                scores.append({
                    "score": battle_score,
                    "timestamp": battle.created_at,
                    "total_questions": len(answers)
                })
        
        if len(scores) < 2:
            return {
                "trend": "insufficient_data",
                "average_score": scores[0]["score"] if scores else 0,
                "improvement_rate": 0,
                "consistency": 0
            }
        
        # Calculate metrics
        recent_scores = [s["score"] for s in scores[-5:]]  # Last 5 sessions
        older_scores = [s["score"] for s in scores[:-5]] if len(scores) > 5 else recent_scores
        
        avg_recent = sum(recent_scores) / len(recent_scores)
        avg_older = sum(older_scores) / len(older_scores)
        improvement_rate = ((avg_recent - avg_older) / avg_older) * 100 if avg_older > 0 else 0
        
        # Calculate consistency (standard deviation)
        import statistics
        consistency = 1 - (statistics.stdev(recent_scores) / max(avg_recent, 1))
        consistency = max(0, min(1, consistency))
        
        # Determine trend
        if improvement_rate > 10:
            trend = "strong_improvement"
        elif improvement_rate > 3:
            trend = "improvement"
        elif improvement_rate > -3:
            trend = "stable"
        elif improvement_rate > -10:
            trend = "decline"
        else:
            trend = "strong_decline"
        
        return {
            "trend": trend,
            "average_score": avg_recent,
            "improvement_rate": improvement_rate,
            "consistency": consistency,
            "total_sessions": len(scores),
            "recent_sessions": len(recent_scores),
            "score_variance": statistics.variance(recent_scores) if len(recent_scores) > 1 else 0
        }
    
    async def _detect_learning_patterns(
        self, user_id: str, plan_id: str
    ) -> Dict[str, Any]:
        """Detect learning patterns and behaviors"""
        
        # Analyze study time patterns
        study_sessions = await self._get_study_sessions(user_id, plan_id)
        
        # Analyze content engagement
        video_engagement = await self._analyze_video_engagement(user_id)
        
        # Analyze topic performance
        topic_performance = await self._analyze_topic_performance(user_id)
        
        # Detect learning preferences
        learning_preferences = await self._detect_learning_preferences(
            study_sessions, video_engagement, topic_performance
        )
        
        return {
            "study_patterns": study_sessions,
            "video_engagement": video_engagement,
            "topic_performance": topic_performance,
            "learning_preferences": learning_preferences,
            "engagement_level": self._calculate_engagement_level(
                study_sessions, video_engagement
            ),
            "learning_velocity": self._calculate_learning_velocity(topic_performance),
            "retention_indicators": await self._analyze_retention_patterns(user_id)
        }
    
    async def _identify_adaptation_triggers(
        self,
        performance_analysis: Dict[str, Any],
        learning_patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify triggers that require adaptation"""
        
        triggers = []
        
        # Performance-based triggers
        if performance_analysis["trend"] == "strong_decline":
            triggers.append({
                "type": AdaptationTrigger.PERFORMANCE_DROP,
                "severity": "high",
                "details": {
                    "improvement_rate": performance_analysis["improvement_rate"],
                    "consistency": performance_analysis["consistency"]
                }
            })
        elif performance_analysis["trend"] == "decline":
            triggers.append({
                "type": AdaptationTrigger.PERFORMANCE_DROP,
                "severity": "medium",
                "details": performance_analysis
            })
        
        # Mastery-based triggers
        if performance_analysis["average_score"] > 85 and performance_analysis["consistency"] > 0.8:
            triggers.append({
                "type": AdaptationTrigger.MASTERY_ACHIEVED,
                "severity": "low",
                "details": {
                    "average_score": performance_analysis["average_score"],
                    "consistency": performance_analysis["consistency"]
                }
            })
        
        # Engagement-based triggers
        if learning_patterns["engagement_level"] < 0.3:
            triggers.append({
                "type": AdaptationTrigger.ENGAGEMENT_LOW,
                "severity": "high",
                "details": learning_patterns["engagement_level"]
            })
        
        # Topic-specific struggles
        struggling_topics = []
        for topic, perf in learning_patterns["topic_performance"].items():
            if perf.get("success_rate", 0) < 0.4:
                struggling_topics.append(topic)
        
        if struggling_topics:
            triggers.append({
                "type": AdaptationTrigger.STRUGGLING_TOPIC,
                "severity": "medium",
                "details": {"topics": struggling_topics}
            })
        
        # Rapid progress trigger
        if performance_analysis["improvement_rate"] > 20:
            triggers.append({
                "type": AdaptationTrigger.RAPID_PROGRESS,
                "severity": "low",
                "details": performance_analysis
            })
        
        return triggers
    
    async def _generate_adaptations(
        self,
        triggers: List[Dict[str, Any]],
        performance_analysis: Dict[str, Any],
        learning_patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate adaptation recommendations based on triggers"""
        
        adaptations = []
        
        for trigger in triggers:
            trigger_type = AdaptationTrigger(trigger["type"])
            severity = trigger["severity"]
            
            if trigger_type == AdaptationTrigger.PERFORMANCE_DROP:
                if severity == "high":
                    adaptations.extend([
                        {
                            "action": AdaptiveAction.REDUCE_DIFFICULTY,
                            "priority": "high",
                            "description": "Reduce difficulty level to rebuild confidence",
                            "parameters": {"difficulty_reduction": 1}
                        },
                        {
                            "action": AdaptiveAction.ADD_REVIEW_SESSIONS,
                            "priority": "high",
                            "description": "Add extra review sessions for struggling topics",
                            "parameters": {"review_frequency": "daily"}
                        }
                    ])
                else:
                    adaptations.append({
                        "action": AdaptiveAction.ADD_PRACTICE_EXERCISES,
                        "priority": "medium",
                        "description": "Add more practice exercises",
                        "parameters": {"additional_exercises": 5}
                    })
            
            elif trigger_type == AdaptationTrigger.MASTERY_ACHIEVED:
                adaptations.extend([
                    {
                        "action": AdaptiveAction.INCREASE_DIFFICULTY,
                        "priority": "medium",
                        "description": "Increase difficulty to maintain challenge",
                        "parameters": {"difficulty_increase": 1}
                    },
                    {
                        "action": AdaptiveAction.SKIP_REDUNDANT_CONTENT,
                        "priority": "low",
                        "description": "Skip basic content and move to advanced topics",
                        "parameters": {"skip_threshold": 0.85}
                    }
                ])
            
            elif trigger_type == AdaptationTrigger.ENGAGEMENT_LOW:
                adaptations.extend([
                    {
                        "action": AdaptiveAction.CHANGE_CONTENT_TYPE,
                        "priority": "high",
                        "description": "Switch to more engaging content types",
                        "parameters": {"preferred_type": "interactive"}
                    },
                    {
                        "action": AdaptiveAction.ADD_MOTIVATION_BOOST,
                        "priority": "high",
                        "description": "Add motivational elements and rewards",
                        "parameters": {"motivation_type": "gamification"}
                    }
                ])
            
            elif trigger_type == AdaptationTrigger.STRUGGLING_TOPIC:
                topics = trigger["details"]["topics"]
                adaptations.append({
                    "action": AdaptiveAction.ADD_REVIEW_SESSIONS,
                    "priority": "high",
                    "description": f"Add focused review for struggling topics: {', '.join(topics)}",
                    "parameters": {
                        "topics": topics,
                        "review_intensity": "high"
                    }
                })
            
            elif trigger_type == AdaptationTrigger.RAPID_PROGRESS:
                adaptations.append({
                    "action": AdaptiveAction.ADJUST_PACING,
                    "priority": "medium",
                    "description": "Accelerate pacing due to rapid progress",
                    "parameters": {"pacing_multiplier": 1.3}
                })
        
        # Prioritize adaptations
        adaptations.sort(key=lambda x: {
            "high": 3, "medium": 2, "low": 1
        }.get(x["priority"], 0), reverse=True)
        
        return adaptations
    
    async def _apply_single_adaptation(
        self,
        plan_data: Dict[str, Any],
        adaptation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a single adaptation to the plan data"""
        
        try:
            action = AdaptiveAction(adaptation["action"])
            parameters = adaptation.get("parameters", {})
            
            if action == AdaptiveAction.REDUCE_DIFFICULTY:
                await self._reduce_difficulty(plan_data, parameters)
            elif action == AdaptiveAction.INCREASE_DIFFICULTY:
                await self._increase_difficulty(plan_data, parameters)
            elif action == AdaptiveAction.ADD_REVIEW_SESSIONS:
                await self._add_review_sessions(plan_data, parameters)
            elif action == AdaptiveAction.SKIP_REDUNDANT_CONTENT:
                await self._skip_redundant_content(plan_data, parameters)
            elif action == AdaptiveAction.ADD_PRACTICE_EXERCISES:
                await self._add_practice_exercises(plan_data, parameters)
            elif action == AdaptiveAction.CHANGE_CONTENT_TYPE:
                await self._change_content_type(plan_data, parameters)
            elif action == AdaptiveAction.ADJUST_PACING:
                await self._adjust_pacing(plan_data, parameters)
            elif action == AdaptiveAction.ADD_MOTIVATION_BOOST:
                await self._add_motivation_boost(plan_data, parameters)
            
            return {"success": True, "action": action.value}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Helper methods for specific adaptations
    
    async def _reduce_difficulty(self, plan_data: Dict, parameters: Dict):
        """Reduce difficulty of plan content"""
        reduction = parameters.get("difficulty_reduction", 1)
        
        for unit in plan_data.get("units", []):
            current_difficulty = unit.get("difficulty_level", 3)
            unit["difficulty_level"] = max(1, current_difficulty - reduction)
            
            # Also reduce topic difficulties
            for topic in unit.get("topics", []):
                if isinstance(topic, dict) and "difficulty" in topic:
                    topic["difficulty"] = max(1, topic["difficulty"] - reduction)
    
    async def _increase_difficulty(self, plan_data: Dict, parameters: Dict):
        """Increase difficulty of plan content"""
        increase = parameters.get("difficulty_increase", 1)
        
        for unit in plan_data.get("units", []):
            current_difficulty = unit.get("difficulty_level", 3)
            unit["difficulty_level"] = min(5, current_difficulty + increase)
            
            # Also increase topic difficulties
            for topic in unit.get("topics", []):
                if isinstance(topic, dict) and "difficulty" in topic:
                    topic["difficulty"] = min(5, topic["difficulty"] + increase)
    
    async def _add_review_sessions(self, plan_data: Dict, parameters: Dict):
        """Add review sessions to the plan"""
        review_frequency = parameters.get("review_frequency", "weekly")
        topics = parameters.get("topics", [])
        
        # Add review section to plan
        if "review_schedule" not in plan_data:
            plan_data["review_schedule"] = {}
        
        plan_data["review_schedule"][review_frequency] = {
            "frequency": review_frequency,
            "topics": topics,
            "added_at": datetime.now().isoformat()
        }
    
    async def _add_practice_exercises(self, plan_data: Dict, parameters: Dict):
        """Add additional practice exercises"""
        additional_exercises = parameters.get("additional_exercises", 5)
        
        for unit in plan_data.get("units", []):
            current_exercises = unit.get("exercise_count", 0)
            unit["exercise_count"] = current_exercises + additional_exercises
    
    # Additional helper methods would continue here...
    
    def _calculate_plan_health_score(
        self, performance_analysis: Dict, learning_patterns: Dict
    ) -> float:
        """Calculate overall health score of the study plan"""
        
        # Performance component (40%)
        perf_score = min(performance_analysis["average_score"] / 100, 1.0)
        
        # Consistency component (30%)
        consistency_score = performance_analysis["consistency"]
        
        # Engagement component (30%)
        engagement_score = learning_patterns["engagement_level"]
        
        health_score = (perf_score * 0.4 + consistency_score * 0.3 + engagement_score * 0.3)
        
        return round(health_score, 2)
    
    def _assess_intervention_urgency(self, triggers: List[Dict]) -> str:
        """Assess the urgency of intervention needed"""
        if not triggers:
            return "none"
        
        high_severity_count = sum(1 for t in triggers if t["severity"] == "high")
        medium_severity_count = sum(1 for t in triggers if t["severity"] == "medium")
        
        if high_severity_count >= 2:
            return "immediate"
        elif high_severity_count >= 1:
            return "urgent"
        elif medium_severity_count >= 2:
            return "moderate"
        else:
            return "low"
    
    async def _get_study_sessions(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        """Analyze study session patterns"""
        # This would analyze user's study session data
        # Return mock data for now
        return {
            "average_session_length": 45,
            "sessions_per_week": 4,
            "preferred_time_slots": ["19:00-21:00"],
            "completion_rate": 0.75
        }
    
    async def _analyze_video_engagement(self, user_id: str) -> Dict[str, Any]:
        """Analyze video watching engagement"""
        video_tracking = self.db.query(VideoTracking).filter(
            VideoTracking.user_id == user_id,
            VideoTracking.watched_at >= datetime.now() - timedelta(days=14)
        ).all()
        
        if not video_tracking:
            return {"engagement_rate": 0.5, "completion_rate": 0.5}
        
        total_videos = len(video_tracking)
        completed_videos = sum(1 for vt in video_tracking if vt.completion_percentage >= 80)
        avg_completion = sum(vt.completion_percentage for vt in video_tracking) / total_videos
        
        return {
            "engagement_rate": completed_videos / total_videos,
            "completion_rate": avg_completion / 100,
            "total_videos": total_videos
        }
    
    async def _analyze_topic_performance(self, user_id: str) -> Dict[str, Any]:
        """Analyze performance by topic"""
        # This would analyze performance across different topics
        # Return mock data structure
        return {
            "algebra": {"success_rate": 0.75, "attempts": 20},
            "geometry": {"success_rate": 0.45, "attempts": 15},
            "trigonometry": {"success_rate": 0.60, "attempts": 10}
        }