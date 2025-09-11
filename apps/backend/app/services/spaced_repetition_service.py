"""
Spaced Repetition Service
Implements intelligent spaced repetition system for optimal knowledge retention
Based on scientific algorithms like SM-2, Anki, and modern cognitive science research
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import json
import logging
import math
from enum import Enum
from dataclasses import dataclass

from ..models.user import User
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.topic import Topic
from ..models.question import Question
from ..models.battle import BattleAnswer
from ..core.config import settings
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)

class ReviewResult(Enum):
    AGAIN = 1      # Failed, show again soon
    HARD = 2       # Difficult, shorter interval
    GOOD = 3       # Normal, standard interval
    EASY = 4       # Easy, longer interval

class ItemStatus(Enum):
    NEW = "new"
    LEARNING = "learning"
    REVIEW = "review"
    GRADUATED = "graduated"
    SUSPENDED = "suspended"

@dataclass
class SpacedItem:
    """Represents an item in the spaced repetition system"""
    item_id: str
    user_id: str
    topic_id: str
    content_type: str  # question, concept, formula, etc.
    content_data: Dict[str, Any]
    
    # SM-2 Algorithm parameters
    ease_factor: float = 2.5
    interval: int = 1  # days
    repetitions: int = 0
    due_date: datetime = None
    
    # Additional metrics
    status: ItemStatus = ItemStatus.NEW
    last_reviewed: datetime = None
    total_reviews: int = 0
    success_rate: float = 0.0
    average_response_time: float = 0.0
    difficulty_rating: float = 0.5  # 0-1 scale
    
    # Learning context
    learning_session_id: str = None
    related_items: List[str] = None
    prerequisite_items: List[str] = None

class SpacedRepetitionService:
    """
    Advanced spaced repetition service with AI-enhanced scheduling
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # SM-2 Algorithm constants
        self.MIN_EASE_FACTOR = 1.3
        self.INITIAL_EASE_FACTOR = 2.5
        self.EASE_BONUS = 0.15
        self.EASE_PENALTY = 0.2
        
        # Learning stages
        self.LEARNING_STEPS = [1, 10, 1440]  # 1 min, 10 min, 1 day (in minutes)
        self.GRADUATING_INTERVAL = 1  # 1 day
        self.EASY_INTERVAL = 4  # 4 days
        
    async def create_spaced_repetition_schedule(
        self,
        user_id: str,
        plan_id: str,
        topics: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a comprehensive spaced repetition schedule for a study plan
        """
        try:
            # Get study plan
            study_plan = self.db.query(StudyPlan).filter(
                StudyPlan.id == plan_id,
                StudyPlan.user_id == user_id
            ).first()
            
            if not study_plan:
                raise ValueError(f"Study plan {plan_id} not found")
            
            # Extract topics from plan if not provided
            if not topics:
                topics = await self._extract_topics_from_plan(study_plan)
            
            # Create spaced items for each topic/concept
            spaced_items = await self._create_spaced_items(
                user_id, plan_id, topics
            )
            
            # Initialize review schedule
            review_schedule = await self._initialize_review_schedule(spaced_items)
            
            # Create retention curves
            retention_curves = await self._create_retention_curves(
                user_id, spaced_items
            )
            
            # Generate review calendar
            review_calendar = await self._generate_review_calendar(
                review_schedule, retention_curves
            )
            
            # Create adaptive parameters
            adaptive_params = await self._create_adaptive_parameters(
                user_id, spaced_items
            )
            
            spaced_system = {
                "system_id": f"spaced-{user_id}-{plan_id}",
                "user_id": user_id,
                "plan_id": plan_id,
                "created_at": datetime.now().isoformat(),
                "total_items": len(spaced_items),
                "spaced_items": [item.__dict__ for item in spaced_items],
                "review_schedule": review_schedule,
                "retention_curves": retention_curves,
                "review_calendar": review_calendar,
                "adaptive_parameters": adaptive_params,
                "performance_metrics": {
                    "total_reviews_scheduled": len(review_calendar),
                    "estimated_retention_rate": adaptive_params.get("estimated_retention", 0.85),
                    "optimal_review_frequency": adaptive_params.get("optimal_frequency", "daily"),
                    "difficulty_distribution": await self._analyze_difficulty_distribution(spaced_items)
                },
                "algorithm_settings": {
                    "algorithm_type": "Enhanced SM-2",
                    "ease_factor_range": [self.MIN_EASE_FACTOR, 4.0],
                    "learning_steps": self.LEARNING_STEPS,
                    "graduating_interval": self.GRADUATING_INTERVAL,
                    "easy_interval": self.EASY_INTERVAL
                }
            }
            
            # Cache the system
            cache_key = f"spaced_system:{user_id}:{plan_id}"
            cache_service.set(cache_key, spaced_system, expire=3600 * 24)  # 24 hours
            
            return spaced_system
            
        except Exception as e:
            logger.error(f"Error creating spaced repetition schedule: {str(e)}")
            raise
    
    async def get_daily_reviews(
        self,
        user_id: str,
        date: datetime = None,
        max_reviews: int = 50
    ) -> Dict[str, Any]:
        """
        Get daily review items for spaced repetition
        """
        if not date:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        try:
            # Get all spaced items for user
            spaced_items = await self._get_user_spaced_items(user_id)
            
            # Filter items due for review
            due_items = [
                item for item in spaced_items
                if item.due_date and item.due_date <= date + timedelta(days=1)
            ]
            
            # Separate by type
            new_items = [item for item in due_items if item.status == ItemStatus.NEW]
            learning_items = [item for item in due_items if item.status == ItemStatus.LEARNING]
            review_items = [item for item in due_items if item.status == ItemStatus.REVIEW]
            
            # Prioritize items
            prioritized_items = await self._prioritize_review_items(
                new_items, learning_items, review_items, max_reviews
            )
            
            # Create review session
            review_session = await self._create_review_session(
                user_id, date, prioritized_items
            )
            
            # Add learning context
            context = await self._add_learning_context(prioritized_items)
            
            daily_reviews = {
                "date": date.strftime("%Y-%m-%d"),
                "user_id": user_id,
                "total_due_items": len(due_items),
                "session_items": len(prioritized_items),
                "new_items": len(new_items),
                "learning_items": len(learning_items),
                "review_items": len(review_items),
                "review_session": review_session,
                "learning_context": context,
                "estimated_duration_minutes": await self._estimate_session_duration(
                    prioritized_items
                ),
                "difficulty_balance": await self._calculate_difficulty_balance(
                    prioritized_items
                ),
                "retention_prediction": await self._predict_session_retention(
                    user_id, prioritized_items
                )
            }
            
            return daily_reviews
            
        except Exception as e:
            logger.error(f"Error getting daily reviews: {str(e)}")
            return {"error": str(e)}
    
    async def process_review_result(
        self,
        user_id: str,
        item_id: str,
        result: ReviewResult,
        response_time_ms: int = None,
        additional_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process the result of a spaced repetition review
        """
        try:
            # Get the spaced item
            spaced_item = await self._get_spaced_item(user_id, item_id)
            if not spaced_item:
                raise ValueError(f"Spaced item {item_id} not found")
            
            # Apply SM-2 algorithm
            updated_item = await self._apply_sm2_algorithm(
                spaced_item, result, response_time_ms
            )
            
            # Update learning analytics
            analytics_update = await self._update_learning_analytics(
                updated_item, result, additional_data
            )
            
            # Adjust related items
            related_adjustments = await self._adjust_related_items(
                updated_item, result
            )
            
            # Calculate next review predictions
            next_reviews = await self._calculate_next_review_predictions(
                updated_item
            )
            
            # Save updates
            await self._save_spaced_item_updates(updated_item)
            
            result_data = {
                "success": True,
                "item_id": item_id,
                "result": result.name,
                "updated_item": updated_item.__dict__,
                "next_review_date": updated_item.due_date.isoformat(),
                "interval_days": updated_item.interval,
                "ease_factor": updated_item.ease_factor,
                "analytics_update": analytics_update,
                "related_adjustments": len(related_adjustments),
                "retention_prediction": next_reviews["retention_prediction"],
                "learning_progress": await self._calculate_learning_progress(
                    user_id, updated_item
                )
            }
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error processing review result: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_retention_analytics(
        self,
        user_id: str,
        plan_id: str = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive retention analytics for spaced repetition
        """
        try:
            # Get spaced items data
            spaced_items = await self._get_user_spaced_items(
                user_id, plan_id, days_back
            )
            
            # Calculate retention metrics
            retention_metrics = await self._calculate_retention_metrics(
                spaced_items, days_back
            )
            
            # Analyze forgetting curves
            forgetting_curves = await self._analyze_forgetting_curves(
                user_id, spaced_items
            )
            
            # Get difficulty progression
            difficulty_progression = await self._analyze_difficulty_progression(
                spaced_items
            )
            
            # Calculate efficiency metrics
            efficiency_metrics = await self._calculate_efficiency_metrics(
                spaced_items
            )
            
            # Generate insights
            insights = await self._generate_retention_insights(
                retention_metrics, forgetting_curves, efficiency_metrics
            )
            
            analytics = {
                "user_id": user_id,
                "plan_id": plan_id,
                "analysis_period_days": days_back,
                "analysis_date": datetime.now().isoformat(),
                "total_items_analyzed": len(spaced_items),
                "retention_metrics": retention_metrics,
                "forgetting_curves": forgetting_curves,
                "difficulty_progression": difficulty_progression,
                "efficiency_metrics": efficiency_metrics,
                "insights_and_recommendations": insights,
                "performance_trends": await self._analyze_performance_trends(
                    spaced_items
                ),
                "optimization_suggestions": await self._generate_optimization_suggestions(
                    retention_metrics, efficiency_metrics
                )
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting retention analytics: {str(e)}")
            return {"error": str(e)}
    
    # Private methods implementing SM-2 algorithm and analytics
    
    async def _apply_sm2_algorithm(
        self,
        item: SpacedItem,
        result: ReviewResult,
        response_time_ms: int = None
    ) -> SpacedItem:
        """
        Apply the SM-2 spaced repetition algorithm
        """
        # Update response time
        if response_time_ms:
            if item.average_response_time == 0:
                item.average_response_time = response_time_ms
            else:
                item.average_response_time = (
                    item.average_response_time * 0.8 + response_time_ms * 0.2
                )
        
        # Update review count
        item.total_reviews += 1
        item.last_reviewed = datetime.now()
        
        # Calculate success rate
        if result in [ReviewResult.GOOD, ReviewResult.EASY]:
            success_count = item.success_rate * (item.total_reviews - 1) + 1
        else:
            success_count = item.success_rate * (item.total_reviews - 1)
        item.success_rate = success_count / item.total_reviews
        
        # Apply SM-2 algorithm
        if item.status == ItemStatus.NEW:
            item.status = ItemStatus.LEARNING
            item.repetitions = 1
            if result == ReviewResult.EASY:
                item.interval = self.EASY_INTERVAL
                item.status = ItemStatus.REVIEW
            else:
                item.interval = self._get_learning_step(0)  # First learning step
        
        elif item.status == ItemStatus.LEARNING:
            if result in [ReviewResult.GOOD, ReviewResult.EASY]:
                if item.repetitions >= len(self.LEARNING_STEPS) - 1:
                    item.status = ItemStatus.REVIEW
                    item.interval = self.GRADUATING_INTERVAL if result == ReviewResult.GOOD else self.EASY_INTERVAL
                    item.repetitions += 1
                else:
                    item.interval = self._get_learning_step(item.repetitions)
                    item.repetitions += 1
            else:
                # Failed review, reset to first learning step
                item.repetitions = 1
                item.interval = self._get_learning_step(0)
        
        elif item.status == ItemStatus.REVIEW:
            if result == ReviewResult.AGAIN:
                # Reset to learning
                item.status = ItemStatus.LEARNING
                item.repetitions = 1
                item.interval = self._get_learning_step(0)
                item.ease_factor = max(
                    self.MIN_EASE_FACTOR,
                    item.ease_factor - self.EASE_PENALTY
                )
            else:
                # Calculate new interval
                if result == ReviewResult.HARD:
                    item.ease_factor = max(
                        self.MIN_EASE_FACTOR,
                        item.ease_factor - self.EASE_PENALTY
                    )
                    item.interval = max(1, int(item.interval * 1.2))
                elif result == ReviewResult.GOOD:
                    item.interval = max(1, int(item.interval * item.ease_factor))
                elif result == ReviewResult.EASY:
                    item.ease_factor += self.EASE_BONUS
                    item.interval = max(1, int(item.interval * item.ease_factor * 1.3))
                
                item.repetitions += 1
        
        # Calculate next due date
        if item.interval < 1440:  # Less than a day (in minutes)
            item.due_date = datetime.now() + timedelta(minutes=item.interval)
        else:
            item.due_date = datetime.now() + timedelta(days=item.interval // 1440)
        
        return item
    
    def _get_learning_step(self, step_index: int) -> int:
        """Get learning step interval in minutes"""
        if step_index < len(self.LEARNING_STEPS):
            return self.LEARNING_STEPS[step_index]
        return self.LEARNING_STEPS[-1]
    
    async def _extract_topics_from_plan(self, study_plan: StudyPlan) -> List[Dict[str, Any]]:
        """Extract topics from study plan for spaced repetition"""
        plan_data = study_plan.plan_data
        if isinstance(plan_data, str):
            plan_data = json.loads(plan_data)
        
        topics = []
        for unit in plan_data.get("units", []):
            for topic in unit.get("topics", []):
                if isinstance(topic, dict):
                    topics.append({
                        "topic_id": topic.get("id", f"topic-{len(topics)}"),
                        "name": topic.get("name", "Unknown Topic"),
                        "difficulty": topic.get("difficulty", 2),
                        "unit_id": unit.get("unit_number", 1),
                        "tags": topic.get("tags", [])
                    })
                else:
                    topics.append({
                        "topic_id": f"topic-{len(topics)}",
                        "name": str(topic),
                        "difficulty": 2,
                        "unit_id": unit.get("unit_number", 1),
                        "tags": []
                    })
        
        return topics
    
    async def _create_spaced_items(
        self,
        user_id: str,
        plan_id: str,
        topics: List[Dict[str, Any]]
    ) -> List[SpacedItem]:
        """Create spaced repetition items from topics"""
        spaced_items = []
        
        for i, topic in enumerate(topics):
            # Create main concept item
            concept_item = SpacedItem(
                item_id=f"concept-{plan_id}-{i}",
                user_id=user_id,
                topic_id=topic["topic_id"],
                content_type="concept",
                content_data={
                    "name": topic["name"],
                    "difficulty": topic["difficulty"],
                    "tags": topic["tags"],
                    "unit_id": topic["unit_id"]
                },
                difficulty_rating=topic["difficulty"] / 5.0,  # Normalize to 0-1
                due_date=datetime.now() + timedelta(minutes=1)  # Start immediately
            )
            spaced_items.append(concept_item)
            
            # Get related questions for this topic
            related_questions = await self._get_questions_for_topic(topic["topic_id"])
            
            for question in related_questions:
                question_item = SpacedItem(
                    item_id=f"question-{question.id}",
                    user_id=user_id,
                    topic_id=topic["topic_id"],
                    content_type="question",
                    content_data={
                        "question_id": str(question.id),
                        "question_text": question.question_text,
                        "difficulty": question.difficulty,
                        "topic_name": topic["name"]
                    },
                    difficulty_rating=question.difficulty / 10.0,  # Normalize to 0-1
                    due_date=datetime.now() + timedelta(hours=1),  # Delay questions slightly
                    related_items=[concept_item.item_id],
                    prerequisite_items=[concept_item.item_id]
                )
                spaced_items.append(question_item)
        
        return spaced_items
    
    async def _get_questions_for_topic(self, topic_name: str) -> List[Question]:
        """Get questions related to a topic"""
        # This would ideally use a proper topic mapping
        # For now, search by topic name in tags or similar
        questions = self.db.query(Question).filter(
            or_(
                Question.tags.contains([topic_name]),
                func.lower(Question.question_text).contains(topic_name.lower())
            )
        ).limit(5).all()  # Limit to 5 questions per topic
        
        return questions
    
    async def _prioritize_review_items(
        self,
        new_items: List[SpacedItem],
        learning_items: List[SpacedItem],
        review_items: List[SpacedItem],
        max_reviews: int
    ) -> List[SpacedItem]:
        """Prioritize items for daily review session"""
        
        # Sort by priority (overdue items first, then by difficulty)
        all_items = []
        
        # Learning items have highest priority
        learning_sorted = sorted(
            learning_items,
            key=lambda x: (x.due_date, x.difficulty_rating)
        )
        
        # Review items sorted by how overdue they are
        review_sorted = sorted(
            review_items,
            key=lambda x: (x.due_date, -x.ease_factor)  # Harder items first
        )
        
        # New items sorted by difficulty (easier first)
        new_sorted = sorted(
            new_items,
            key=lambda x: x.difficulty_rating
        )
        
        # Combine with priorities
        all_items.extend(learning_sorted)
        all_items.extend(review_sorted)
        all_items.extend(new_sorted)
        
        # Limit to max_reviews
        return all_items[:max_reviews]
    
    async def _calculate_retention_metrics(
        self, spaced_items: List[SpacedItem], days_back: int
    ) -> Dict[str, Any]:
        """Calculate comprehensive retention metrics"""
        
        if not spaced_items:
            return {
                "overall_retention_rate": 0.0,
                "average_ease_factor": self.INITIAL_EASE_FACTOR,
                "total_reviews": 0,
                "items_graduated": 0
            }
        
        total_items = len(spaced_items)
        graduated_items = len([item for item in spaced_items if item.status == ItemStatus.REVIEW])
        
        # Calculate overall retention rate (weighted by total reviews)
        total_reviews = sum(item.total_reviews for item in spaced_items)
        weighted_success = sum(
            item.success_rate * item.total_reviews for item in spaced_items
        )
        overall_retention = weighted_success / total_reviews if total_reviews > 0 else 0
        
        # Calculate average ease factor
        ease_factors = [item.ease_factor for item in spaced_items if item.ease_factor > 0]
        avg_ease_factor = sum(ease_factors) / len(ease_factors) if ease_factors else self.INITIAL_EASE_FACTOR
        
        return {
            "overall_retention_rate": round(overall_retention, 3),
            "average_ease_factor": round(avg_ease_factor, 2),
            "total_reviews": total_reviews,
            "total_items": total_items,
            "items_graduated": graduated_items,
            "graduation_rate": round(graduated_items / total_items, 3) if total_items > 0 else 0,
            "average_reviews_per_item": round(total_reviews / total_items, 1) if total_items > 0 else 0,
            "difficulty_distribution": await self._analyze_difficulty_distribution(spaced_items),
            "status_distribution": {
                "new": len([item for item in spaced_items if item.status == ItemStatus.NEW]),
                "learning": len([item for item in spaced_items if item.status == ItemStatus.LEARNING]),
                "review": len([item for item in spaced_items if item.status == ItemStatus.REVIEW]),
                "graduated": graduated_items
            }
        }