"""
Monthly Reassessment and Plan Update System
Automated system for tracking student progress and updating study plans
"""

import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import text

from .personalized_study_plan_generator import PersonalizedStudyPlanGenerator
from .diagnostic_weakness_analyzer import DiagnosticWeaknessAnalyzer
from .study_plan_storage import StudyPlanStorageManager

logger = logging.getLogger(__name__)

@dataclass
class ProgressMetrics:
    """Student progress metrics for reassessment"""
    user_id: str
    subject_id: str
    original_score: float
    current_score: float
    score_improvement: float
    improvement_percentage: float
    
    topics_improved: List[str]
    topics_still_weak: List[str]
    new_weak_areas: List[str]
    mastered_topics: List[str]
    
    study_time_hours: float
    videos_watched: int
    exercises_completed: int
    plan_completion_rate: float
    
    consistency_score: float
    engagement_level: str
    learning_velocity: float

@dataclass
class ReassessmentRecommendation:
    """Recommendation based on reassessment"""
    recommendation_type: str
    priority_level: int
    title: str
    description: str
    action_items: List[str]
    estimated_impact: str
    time_investment: float

@dataclass
class PlanUpdateSummary:
    """Summary of plan updates after reassessment"""
    original_plan_id: str
    new_plan_id: str
    update_type: str
    changes_made: List[str]
    new_focus_areas: List[str]
    removed_areas: List[str]
    estimated_improvement: float
    next_reassessment_date: str

class MonthlyReassessmentSystem:
    """
    Comprehensive system for monthly student reassessment and plan updates
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.plan_generator = PersonalizedStudyPlanGenerator(db)
        self.weakness_analyzer = DiagnosticWeaknessAnalyzer(db)
        self.storage_manager = StudyPlanStorageManager(db)
        
        # Reassessment thresholds
        self.improvement_thresholds = {
            'excellent': 20.0,
            'good': 10.0,
            'moderate': 5.0,
            'minimal': 2.0
        }
        
        # Plan update triggers
        self.update_triggers = {
            'major_improvement': 15.0,
            'stagnation': -2.0,
            'new_weaknesses': 3,  # Number of new weak areas
            'completion_rate_low': 0.3
        }
    
    async def conduct_monthly_reassessment(
        self,
        user_id: str,
        subject_id: str,
        original_plan_id: str,
        reassessment_test_id: str
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive monthly reassessment
        """
        try:
            logger.info(f"🔄 Starting monthly reassessment for user {user_id}, subject {subject_id}")
            
            # 1. Calculate progress metrics
            progress_metrics = await self._calculate_progress_metrics(
                user_id, subject_id, original_plan_id, reassessment_test_id
            )
            
            if not progress_metrics:
                return {
                    'success': False,
                    'error': 'Could not calculate progress metrics'
                }
            
            # 2. Analyze reassessment test results
            reassessment_analysis = await self.weakness_analyzer.analyze_diagnostic_results(
                user_id, subject_id, reassessment_test_id
            )
            
            if not reassessment_analysis['success']:
                return reassessment_analysis
            
            # 3. Compare with original baseline
            comparison_analysis = await self._compare_with_baseline(
                user_id, subject_id, original_plan_id, reassessment_analysis
            )
            
            # 4. Generate recommendations
            recommendations = await self._generate_reassessment_recommendations(
                progress_metrics, comparison_analysis
            )
            
            # 5. Determine if plan update is needed
            update_decision = await self._determine_plan_update_decision(
                progress_metrics, comparison_analysis, recommendations
            )
            
            # 6. Update plan if necessary
            plan_update_result = None
            if update_decision['should_update']:
                plan_update_result = await self._update_study_plan(
                    user_id, subject_id, original_plan_id, 
                    reassessment_analysis, progress_metrics
                )
            
            # 7. Schedule next reassessment
            next_reassessment = await self._schedule_next_reassessment(
                user_id, subject_id, plan_update_result['new_plan_id'] if plan_update_result else original_plan_id
            )
            
            # 8. Save reassessment results
            reassessment_record = await self._save_reassessment_record(
                user_id, subject_id, original_plan_id, reassessment_test_id,
                progress_metrics, comparison_analysis, recommendations,
                update_decision, plan_update_result
            )
            
            return {
                'success': True,
                'reassessment_id': reassessment_record['id'],
                'progress_metrics': asdict(progress_metrics),
                'comparison_analysis': comparison_analysis,
                'recommendations': [asdict(r) for r in recommendations],
                'update_decision': update_decision,
                'plan_update_result': plan_update_result,
                'next_reassessment_date': next_reassessment['date'],
                'overall_assessment': self._generate_overall_assessment(progress_metrics, recommendations)
            }
            
        except Exception as e:
            logger.error(f"❌ Error in monthly reassessment: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to conduct monthly reassessment'
            }
    
    async def _calculate_progress_metrics(
        self,
        user_id: str,
        subject_id: str,
        plan_id: str,
        reassessment_test_id: str
    ) -> Optional[ProgressMetrics]:
        """Calculate comprehensive progress metrics"""
        try:
            # Get original diagnostic score
            original_score_query = text("""
                SELECT dt.score_percentage, dt.created_at
                FROM diagnostic_tests dt
                JOIN study_plans sp ON sp.user_id = dt.user_id AND sp.subject_id = dt.subject_id
                WHERE sp.id = :plan_id
                AND dt.test_type = 'real_icfes'
                AND dt.is_monthly_reassessment = false
                ORDER BY dt.created_at ASC
                LIMIT 1
            """)
            
            original_result = self.db.execute(original_score_query, {'plan_id': plan_id}).first()
            original_score = original_result[0] if original_result else 0.0
            
            # Get reassessment score
            reassessment_query = text("""
                SELECT score_percentage FROM diagnostic_tests
                WHERE id = :test_id AND user_id = :user_id
            """)
            
            reassessment_result = self.db.execute(reassessment_query, {
                'test_id': reassessment_test_id,
                'user_id': user_id
            }).first()
            
            current_score = reassessment_result[0] if reassessment_result else 0.0
            
            # Calculate topic-level improvements
            topic_analysis = await self._analyze_topic_level_progress(
                user_id, subject_id, plan_id, reassessment_test_id
            )
            
            # Get study activity metrics
            activity_metrics = await self._get_study_activity_metrics(
                user_id, subject_id, plan_id
            )
            
            # Calculate derived metrics
            score_improvement = current_score - original_score
            improvement_percentage = (score_improvement / original_score * 100) if original_score > 0 else 0
            
            # Calculate consistency and engagement
            consistency_score = await self._calculate_consistency_score(user_id, subject_id, plan_id)
            engagement_level = self._determine_engagement_level(activity_metrics)
            learning_velocity = self._calculate_learning_velocity(
                score_improvement, activity_metrics['study_time_hours']
            )
            
            return ProgressMetrics(
                user_id=user_id,
                subject_id=subject_id,
                original_score=original_score,
                current_score=current_score,
                score_improvement=score_improvement,
                improvement_percentage=improvement_percentage,
                
                topics_improved=topic_analysis['improved'],
                topics_still_weak=topic_analysis['still_weak'],
                new_weak_areas=topic_analysis['new_weak'],
                mastered_topics=topic_analysis['mastered'],
                
                study_time_hours=activity_metrics['study_time_hours'],
                videos_watched=activity_metrics['videos_watched'],
                exercises_completed=activity_metrics['exercises_completed'],
                plan_completion_rate=activity_metrics['completion_rate'],
                
                consistency_score=consistency_score,
                engagement_level=engagement_level,
                learning_velocity=learning_velocity
            )
            
        except Exception as e:
            logger.error(f"Error calculating progress metrics: {e}")
            return None
    
    async def _analyze_topic_level_progress(
        self,
        user_id: str,
        subject_id: str,
        plan_id: str,
        reassessment_test_id: str
    ) -> Dict[str, List[str]]:
        """Analyze progress at topic level"""
        try:
            # Get original weaknesses from plan
            plan_data = self.storage_manager.get_study_plan(plan_id)
            if not plan_data['success']:
                return {'improved': [], 'still_weak': [], 'new_weak': [], 'mastered': []}
            
            original_weaknesses = set()
            if 'plan_data' in plan_data and 'metadata' in plan_data['plan_data']:
                original_weaknesses = set(plan_data['plan_data']['metadata'].get('weakness_areas', []))
            
            # Get current weak areas from reassessment
            reassessment_query = text("""
                SELECT 
                    t.name as topic_name,
                    COUNT(*) as total_questions,
                    SUM(CASE WHEN dta.is_correct THEN 1 ELSE 0 END) as correct_answers
                FROM diagnostic_test_answers dta
                JOIN questions q ON dta.question_id = q.id
                JOIN topics t ON dta.topic_id = t.id
                WHERE dta.diagnostic_test_id = :test_id
                GROUP BY t.name
            """)
            
            topic_results = self.db.execute(reassessment_query, {'test_id': reassessment_test_id}).fetchall()
            
            current_weak_topics = set()
            current_strong_topics = set()
            
            for row in topic_results:
                topic_name = row[0]
                accuracy = row[2] / row[1] if row[1] > 0 else 0
                
                if accuracy < 0.6:  # Below 60% considered weak
                    current_weak_topics.add(topic_name)
                elif accuracy >= 0.8:  # Above 80% considered strong
                    current_strong_topics.add(topic_name)
            
            # Analyze changes
            improved = list(original_weaknesses - current_weak_topics)
            still_weak = list(original_weaknesses & current_weak_topics)
            new_weak = list(current_weak_topics - original_weaknesses)
            mastered = list(current_strong_topics)
            
            return {
                'improved': improved,
                'still_weak': still_weak,
                'new_weak': new_weak,
                'mastered': mastered
            }
            
        except Exception as e:
            logger.error(f"Error analyzing topic progress: {e}")
            return {'improved': [], 'still_weak': [], 'new_weak': [], 'mastered': []}
    
    async def _get_study_activity_metrics(
        self,
        user_id: str,
        subject_id: str,
        plan_id: str
    ) -> Dict[str, Any]:
        """Get student study activity metrics"""
        try:
            # Get plan creation date for time range
            plan_query = text("SELECT created_at FROM study_plans WHERE id = :plan_id")
            plan_result = self.db.execute(plan_query, {'plan_id': plan_id}).first()
            plan_start_date = plan_result[0] if plan_result else datetime.now() - timedelta(days=30)
            
            # Video watching activity
            video_query = text("""
                SELECT COUNT(DISTINCT youtube_id) as videos_watched,
                       SUM(watch_time_seconds) as total_watch_time
                FROM video_tracking
                WHERE user_id = :user_id 
                AND plan_id = :plan_id
                AND created_at >= :start_date
            """)
            
            video_result = self.db.execute(video_query, {
                'user_id': user_id,
                'plan_id': plan_id,
                'start_date': plan_start_date
            }).first()
            
            videos_watched = video_result[0] or 0
            watch_time_seconds = video_result[1] or 0
            
            # Exercise completion activity
            exercise_query = text("""
                SELECT COUNT(*) as exercises_completed
                FROM practice_sessions
                WHERE user_id = :user_id 
                AND subject_id = :subject_id
                AND created_at >= :start_date
            """)
            
            exercise_result = self.db.execute(exercise_query, {
                'user_id': user_id,
                'subject_id': subject_id,
                'start_date': plan_start_date
            }).first()
            
            exercises_completed = exercise_result[0] or 0
            
            # Plan completion rate
            completion_query = text("""
                SELECT completed_units, total_units
                FROM study_plans
                WHERE id = :plan_id
            """)
            
            completion_result = self.db.execute(completion_query, {'plan_id': plan_id}).first()
            completion_rate = 0.0
            if completion_result and completion_result[1] > 0:
                completion_rate = completion_result[0] / completion_result[1]
            
            return {
                'videos_watched': videos_watched,
                'study_time_hours': watch_time_seconds / 3600,
                'exercises_completed': exercises_completed,
                'completion_rate': completion_rate
            }
            
        except Exception as e:
            logger.error(f"Error getting activity metrics: {e}")
            return {
                'videos_watched': 0,
                'study_time_hours': 0.0,
                'exercises_completed': 0,
                'completion_rate': 0.0
            }
    
    async def _calculate_consistency_score(
        self,
        user_id: str,
        subject_id: str,
        plan_id: str
    ) -> float:
        """Calculate learning consistency score"""
        try:
            # Get daily activity over the last 30 days
            activity_query = text("""
                SELECT DATE(created_at) as activity_date,
                       COUNT(*) as daily_activity
                FROM (
                    SELECT created_at FROM video_tracking 
                    WHERE user_id = :user_id AND plan_id = :plan_id
                    AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                    UNION ALL
                    SELECT created_at FROM practice_sessions
                    WHERE user_id = :user_id AND subject_id = :subject_id
                    AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                ) activities
                GROUP BY DATE(created_at)
                ORDER BY activity_date
            """)
            
            activity_results = self.db.execute(activity_query, {
                'user_id': user_id,
                'plan_id': plan_id,
                'subject_id': subject_id
            }).fetchall()
            
            if not activity_results:
                return 0.0
            
            # Calculate consistency based on regular activity
            active_days = len(activity_results)
            total_days = 30
            consistency_score = active_days / total_days
            
            # Bonus for regular daily activity
            if active_days >= 20:  # 20+ days out of 30
                consistency_score += 0.2
            elif active_days >= 15:  # 15+ days out of 30
                consistency_score += 0.1
            
            return min(1.0, consistency_score)
            
        except Exception as e:
            logger.error(f"Error calculating consistency score: {e}")
            return 0.0
    
    def _determine_engagement_level(self, activity_metrics: Dict[str, Any]) -> str:
        """Determine student engagement level"""
        videos_watched = activity_metrics['videos_watched']
        study_time = activity_metrics['study_time_hours']
        exercises = activity_metrics['exercises_completed']
        completion_rate = activity_metrics['completion_rate']
        
        # Calculate engagement score
        engagement_score = 0
        
        if videos_watched >= 15:
            engagement_score += 3
        elif videos_watched >= 10:
            engagement_score += 2
        elif videos_watched >= 5:
            engagement_score += 1
        
        if study_time >= 20:
            engagement_score += 3
        elif study_time >= 10:
            engagement_score += 2
        elif study_time >= 5:
            engagement_score += 1
        
        if exercises >= 50:
            engagement_score += 3
        elif exercises >= 25:
            engagement_score += 2
        elif exercises >= 10:
            engagement_score += 1
        
        if completion_rate >= 0.8:
            engagement_score += 2
        elif completion_rate >= 0.5:
            engagement_score += 1
        
        # Determine level
        if engagement_score >= 9:
            return 'very_high'
        elif engagement_score >= 6:
            return 'high'
        elif engagement_score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_learning_velocity(self, score_improvement: float, study_time: float) -> float:
        """Calculate learning velocity (improvement per hour of study)"""
        if study_time <= 0:
            return 0.0
        
        return score_improvement / study_time
    
    async def _compare_with_baseline(
        self,
        user_id: str,
        subject_id: str,
        original_plan_id: str,
        reassessment_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare reassessment with original baseline"""
        try:
            # Get original analysis if available
            original_diagnostic_query = text("""
                SELECT dt.id 
                FROM diagnostic_tests dt
                JOIN study_plans sp ON sp.user_id = dt.user_id AND sp.subject_id = dt.subject_id
                WHERE sp.id = :plan_id
                AND dt.test_type = 'real_icfes'
                AND dt.is_monthly_reassessment = false
                ORDER BY dt.created_at ASC
                LIMIT 1
            """)
            
            original_diagnostic_result = self.db.execute(original_diagnostic_query, {
                'plan_id': original_plan_id
            }).first()
            
            if not original_diagnostic_result:
                return {'comparison_available': False}
            
            original_diagnostic_id = original_diagnostic_result[0]
            original_analysis = await self.weakness_analyzer.get_saved_analysis(original_diagnostic_id)
            
            if not original_analysis['success']:
                return {'comparison_available': False}
            
            original_data = original_analysis['analysis']
            current_data = reassessment_analysis
            
            # Compare weakness patterns
            original_weaknesses = {wp['topic_name']: wp for wp in original_data.get('weakness_patterns', [])}
            current_weaknesses = {wp['topic_name']: wp for wp in current_data.get('weakness_patterns', [])}
            
            resolved_weaknesses = set(original_weaknesses.keys()) - set(current_weaknesses.keys())
            persistent_weaknesses = set(original_weaknesses.keys()) & set(current_weaknesses.keys())
            new_weaknesses = set(current_weaknesses.keys()) - set(original_weaknesses.keys())
            
            # Compare scores for persistent weaknesses
            weakness_improvements = {}
            for topic in persistent_weaknesses:
                original_severity = original_weaknesses[topic]['severity_score']
                current_severity = current_weaknesses[topic]['severity_score']
                improvement = original_severity - current_severity
                weakness_improvements[topic] = {
                    'original_severity': original_severity,
                    'current_severity': current_severity,
                    'improvement': improvement,
                    'improvement_percentage': (improvement / original_severity * 100) if original_severity > 0 else 0
                }
            
            # Compare overall metrics
            original_overall = original_data.get('overall_metrics', {})
            current_overall = current_data.get('overall_metrics', {})
            
            metric_changes = {}
            for metric in ['accuracy_rate', 'avg_response_time']:
                if metric in original_overall and metric in current_overall:
                    original_value = original_overall[metric]
                    current_value = current_overall[metric]
                    change = current_value - original_value
                    metric_changes[metric] = {
                        'original': original_value,
                        'current': current_value,
                        'change': change,
                        'change_percentage': (change / original_value * 100) if original_value != 0 else 0
                    }
            
            return {
                'comparison_available': True,
                'resolved_weaknesses': list(resolved_weaknesses),
                'persistent_weaknesses': list(persistent_weaknesses),
                'new_weaknesses': list(new_weaknesses),
                'weakness_improvements': weakness_improvements,
                'metric_changes': metric_changes,
                'overall_improvement_trend': self._assess_improvement_trend(
                    len(resolved_weaknesses), len(new_weaknesses), weakness_improvements
                )
            }
            
        except Exception as e:
            logger.error(f"Error comparing with baseline: {e}")
            return {'comparison_available': False, 'error': str(e)}
    
    def _assess_improvement_trend(
        self,
        resolved_count: int,
        new_weakness_count: int,
        weakness_improvements: Dict[str, Dict]
    ) -> str:
        """Assess overall improvement trend"""
        
        # Calculate improvement indicators
        net_weakness_reduction = resolved_count - new_weakness_count
        avg_severity_improvement = 0
        
        if weakness_improvements:
            avg_severity_improvement = sum(
                wi['improvement'] for wi in weakness_improvements.values()
            ) / len(weakness_improvements)
        
        # Determine trend
        if net_weakness_reduction > 2 and avg_severity_improvement > 0.1:
            return 'excellent'
        elif net_weakness_reduction > 0 and avg_severity_improvement > 0.05:
            return 'good'
        elif net_weakness_reduction >= 0 and avg_severity_improvement >= 0:
            return 'stable'
        elif net_weakness_reduction < 0 or avg_severity_improvement < -0.05:
            return 'declining'
        else:
            return 'mixed'
    
    async def _generate_reassessment_recommendations(
        self,
        progress_metrics: ProgressMetrics,
        comparison_analysis: Dict[str, Any]
    ) -> List[ReassessmentRecommendation]:
        """Generate recommendations based on reassessment"""
        recommendations = []
        
        # Recommendation based on score improvement
        if progress_metrics.score_improvement >= self.improvement_thresholds['excellent']:
            recommendations.append(ReassessmentRecommendation(
                recommendation_type='acceleration',
                priority_level=1,
                title='Accelerate Learning Path',
                description='Excellent progress! Consider advancing to more challenging content.',
                action_items=[
                    'Move to advanced difficulty levels',
                    'Add enrichment activities',
                    'Consider peer tutoring opportunities'
                ],
                estimated_impact='high',
                time_investment=2.0
            ))
        elif progress_metrics.score_improvement <= self.improvement_thresholds['minimal']:
            recommendations.append(ReassessmentRecommendation(
                recommendation_type='intervention',
                priority_level=1,
                title='Intensive Support Needed',
                description='Limited progress detected. Implement intensive support strategies.',
                action_items=[
                    'Increase study time allocation',
                    'Add one-on-one tutoring sessions',
                    'Revisit fundamental concepts',
                    'Adjust learning methodology'
                ],
                estimated_impact='high',
                time_investment=8.0
            ))
        
        # Recommendation based on engagement
        if progress_metrics.engagement_level == 'low':
            recommendations.append(ReassessmentRecommendation(
                recommendation_type='engagement',
                priority_level=2,
                title='Boost Student Engagement',
                description='Low engagement detected. Implement strategies to increase motivation.',
                action_items=[
                    'Add gamification elements',
                    'Diversify content types',
                    'Set smaller, achievable goals',
                    'Provide regular positive feedback'
                ],
                estimated_impact='medium',
                time_investment=3.0
            ))
        
        # Recommendation based on consistency
        if progress_metrics.consistency_score < 0.5:
            recommendations.append(ReassessmentRecommendation(
                recommendation_type='consistency',
                priority_level=2,
                title='Improve Study Consistency',
                description='Irregular study patterns detected. Focus on building consistent habits.',
                action_items=[
                    'Create structured study schedule',
                    'Set daily study reminders',
                    'Track daily progress',
                    'Implement accountability measures'
                ],
                estimated_impact='medium',
                time_investment=1.0
            ))
        
        # Recommendation for new weaknesses
        if len(progress_metrics.new_weak_areas) > 2:
            recommendations.append(ReassessmentRecommendation(
                recommendation_type='weakness_management',
                priority_level=1,
                title='Address New Weakness Areas',
                description=f'New weak areas identified: {", ".join(progress_metrics.new_weak_areas)}',
                action_items=[
                    'Prioritize new weakness areas in study plan',
                    'Add targeted practice for new weak topics',
                    'Review prerequisites for new weak areas',
                    'Adjust time allocation'
                ],
                estimated_impact='high',
                time_investment=5.0
            ))
        
        # Recommendation for persistent weaknesses
        if len(progress_metrics.topics_still_weak) > 3:
            recommendations.append(ReassessmentRecommendation(
                recommendation_type='persistence',
                priority_level=1,
                title='Intensive Focus on Persistent Weaknesses',
                description='Multiple areas still require attention despite study time.',
                action_items=[
                    'Change learning approach for persistent topics',
                    'Seek alternative explanations and resources',
                    'Increase practice intensity',
                    'Consider different learning modalities'
                ],
                estimated_impact='high',
                time_investment=6.0
            ))
        
        # Positive reinforcement recommendation
        if len(progress_metrics.topics_improved) > 0 or progress_metrics.score_improvement > 0:
            recommendations.append(ReassessmentRecommendation(
                recommendation_type='reinforcement',
                priority_level=3,
                title='Celebrate and Reinforce Progress',
                description=f'Great improvement in: {", ".join(progress_metrics.topics_improved)}',
                action_items=[
                    'Acknowledge achievements',
                    'Use successful strategies in other areas',
                    'Build confidence for challenging topics',
                    'Share success with support network'
                ],
                estimated_impact='medium',
                time_investment=0.5
            ))
        
        # Sort by priority
        recommendations.sort(key=lambda x: x.priority_level)
        
        return recommendations
    
    async def _determine_plan_update_decision(
        self,
        progress_metrics: ProgressMetrics,
        comparison_analysis: Dict[str, Any],
        recommendations: List[ReassessmentRecommendation]
    ) -> Dict[str, Any]:
        """Determine if study plan should be updated"""
        
        update_reasons = []
        should_update = False
        
        # Check update triggers
        if progress_metrics.score_improvement >= self.update_triggers['major_improvement']:
            update_reasons.append('Major improvement - advance to next level')
            should_update = True
        
        if progress_metrics.score_improvement <= self.update_triggers['stagnation']:
            update_reasons.append('Stagnation detected - change approach')
            should_update = True
        
        if len(progress_metrics.new_weak_areas) >= self.update_triggers['new_weaknesses']:
            update_reasons.append('New weaknesses identified - adjust focus')
            should_update = True
        
        if progress_metrics.plan_completion_rate <= self.update_triggers['completion_rate_low']:
            update_reasons.append('Low completion rate - simplify plan')
            should_update = True
        
        # Check high-priority recommendations
        high_priority_recs = [r for r in recommendations if r.priority_level == 1]
        if len(high_priority_recs) >= 2:
            update_reasons.append('Multiple high-priority interventions needed')
            should_update = True
        
        # Determine update type
        update_type = 'none'
        if should_update:
            if progress_metrics.score_improvement >= 15:
                update_type = 'advancement'
            elif progress_metrics.score_improvement <= -2:
                update_type = 'remediation'
            elif len(progress_metrics.new_weak_areas) > 2:
                update_type = 'focus_shift'
            else:
                update_type = 'optimization'
        
        return {
            'should_update': should_update,
            'update_type': update_type,
            'reasons': update_reasons,
            'confidence_level': 'high' if len(update_reasons) >= 2 else 'medium' if update_reasons else 'low'
        }
    
    async def _update_study_plan(
        self,
        user_id: str,
        subject_id: str,
        original_plan_id: str,
        reassessment_analysis: Dict[str, Any],
        progress_metrics: ProgressMetrics
    ) -> Dict[str, Any]:
        """Update study plan based on reassessment"""
        try:
            logger.info(f"📚 Updating study plan for user {user_id}")
            
            # Mark original plan as inactive
            self.storage_manager.archive_plan(original_plan_id)
            
            # Generate new plan based on reassessment
            # Use the reassessment as a new diagnostic test
            new_plan_result = await self.plan_generator.generate_personalized_plan(
                user_id=user_id,
                subject_id=subject_id,
                diagnostic_test_id=reassessment_analysis.get('diagnostic_test_id', ''),
                target_weeks=6  # Shorter duration for reassessment plans
            )
            
            if not new_plan_result['success']:
                return new_plan_result
            
            # Analyze changes made
            changes_analysis = await self._analyze_plan_changes(
                original_plan_id, new_plan_result['plan_id'], progress_metrics
            )
            
            # Create update summary
            update_summary = PlanUpdateSummary(
                original_plan_id=original_plan_id,
                new_plan_id=new_plan_result['plan_id'],
                update_type=self._determine_update_type(progress_metrics),
                changes_made=changes_analysis['changes'],
                new_focus_areas=changes_analysis['new_focus'],
                removed_areas=changes_analysis['removed_focus'],
                estimated_improvement=self._estimate_improvement_potential(progress_metrics),
                next_reassessment_date=(datetime.now() + timedelta(days=30)).isoformat()
            )
            
            return {
                'success': True,
                'new_plan_id': new_plan_result['plan_id'],
                'update_summary': asdict(update_summary),
                'changes_analysis': changes_analysis,
                'message': 'Study plan successfully updated based on reassessment'
            }
            
        except Exception as e:
            logger.error(f"Error updating study plan: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _analyze_plan_changes(
        self,
        original_plan_id: str,
        new_plan_id: str,
        progress_metrics: ProgressMetrics
    ) -> Dict[str, Any]:
        """Analyze changes between original and new plan"""
        try:
            # Get both plans
            original_plan = self.storage_manager.get_study_plan(original_plan_id)
            new_plan = self.storage_manager.get_study_plan(new_plan_id)
            
            changes = []
            new_focus = []
            removed_focus = []
            
            if original_plan['success'] and new_plan['success']:
                # Compare focus areas
                original_metadata = original_plan.get('plan_data', {}).get('metadata', {})
                new_metadata = new_plan.get('plan_data', {}).get('metadata', {})
                
                original_weaknesses = set(original_metadata.get('weakness_areas', []))
                new_weaknesses = set(new_metadata.get('weakness_areas', []))
                
                new_focus = list(new_weaknesses - original_weaknesses)
                removed_focus = list(original_weaknesses - new_weaknesses)
                
                # Identify types of changes
                if new_focus:
                    changes.append(f"Added focus on {len(new_focus)} new areas")
                if removed_focus:
                    changes.append(f"Removed focus from {len(removed_focus)} mastered areas")
                if len(progress_metrics.topics_improved) > 0:
                    changes.append(f"Reduced emphasis on {len(progress_metrics.topics_improved)} improved topics")
                if len(progress_metrics.new_weak_areas) > 0:
                    changes.append(f"Increased support for {len(progress_metrics.new_weak_areas)} new challenge areas")
            
            return {
                'changes': changes,
                'new_focus': new_focus,
                'removed_focus': removed_focus
            }
            
        except Exception as e:
            logger.error(f"Error analyzing plan changes: {e}")
            return {
                'changes': ['Plan structure updated'],
                'new_focus': [],
                'removed_focus': []
            }
    
    def _determine_update_type(self, progress_metrics: ProgressMetrics) -> str:
        """Determine the type of plan update"""
        if progress_metrics.score_improvement >= 15:
            return 'advancement'
        elif progress_metrics.score_improvement <= -2:
            return 'remediation'
        elif len(progress_metrics.new_weak_areas) > 2:
            return 'focus_adjustment'
        elif progress_metrics.engagement_level == 'low':
            return 'engagement_boost'
        else:
            return 'optimization'
    
    def _estimate_improvement_potential(self, progress_metrics: ProgressMetrics) -> float:
        """Estimate potential improvement from plan update"""
        base_improvement = 10.0  # Base 10 point improvement
        
        # Adjust based on current velocity
        if progress_metrics.learning_velocity > 1.0:
            base_improvement += 5.0
        elif progress_metrics.learning_velocity < 0.5:
            base_improvement -= 2.0
        
        # Adjust based on engagement
        if progress_metrics.engagement_level == 'high':
            base_improvement += 3.0
        elif progress_metrics.engagement_level == 'low':
            base_improvement -= 3.0
        
        return max(5.0, min(25.0, base_improvement))
    
    async def _schedule_next_reassessment(
        self,
        user_id: str,
        subject_id: str,
        plan_id: str
    ) -> Dict[str, Any]:
        """Schedule the next monthly reassessment"""
        try:
            next_date = datetime.now() + timedelta(days=30)
            
            # Save to notifications table
            query = text("""
                INSERT INTO notifications (
                    id, user_id, title, message, type, scheduled_for,
                    metadata, is_active
                ) VALUES (
                    :id, :user_id, :title, :message, 'monthly_reassessment',
                    :scheduled_for, :metadata, true
                )
            """)
            
            notification_id = str(uuid.uuid4())
            metadata = json.dumps({
                'plan_id': plan_id,
                'subject_id': subject_id,
                'reassessment_type': 'monthly_progress'
            })
            
            self.db.execute(query, {
                'id': notification_id,
                'user_id': user_id,
                'title': 'Monthly Progress Assessment Due',
                'message': 'Time for your monthly progress assessment! Take a new diagnostic test to update your study plan.',
                'scheduled_for': next_date,
                'metadata': metadata
            })
            
            self.db.commit()
            
            return {
                'success': True,
                'notification_id': notification_id,
                'date': next_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling next reassessment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _save_reassessment_record(
        self,
        user_id: str,
        subject_id: str,
        original_plan_id: str,
        reassessment_test_id: str,
        progress_metrics: ProgressMetrics,
        comparison_analysis: Dict[str, Any],
        recommendations: List[ReassessmentRecommendation],
        update_decision: Dict[str, Any],
        plan_update_result: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Save comprehensive reassessment record"""
        try:
            reassessment_id = str(uuid.uuid4())
            
            record_data = {
                'user_id': user_id,
                'subject_id': subject_id,
                'original_plan_id': original_plan_id,
                'reassessment_test_id': reassessment_test_id,
                'progress_metrics': asdict(progress_metrics),
                'comparison_analysis': comparison_analysis,
                'recommendations': [asdict(r) for r in recommendations],
                'update_decision': update_decision,
                'plan_update_result': plan_update_result,
                'created_at': datetime.now().isoformat()
            }
            
            # Save to database (assuming a reassessment_records table exists)
            query = text("""
                INSERT INTO reassessment_records (
                    id, user_id, subject_id, original_plan_id, 
                    reassessment_test_id, record_data, created_at
                ) VALUES (
                    :id, :user_id, :subject_id, :original_plan_id,
                    :reassessment_test_id, :record_data, CURRENT_TIMESTAMP
                )
            """)
            
            self.db.execute(query, {
                'id': reassessment_id,
                'user_id': user_id,
                'subject_id': subject_id,
                'original_plan_id': original_plan_id,
                'reassessment_test_id': reassessment_test_id,
                'record_data': json.dumps(record_data)
            })
            
            self.db.commit()
            logger.info(f"✅ Reassessment record saved: {reassessment_id}")
            
            return {'id': reassessment_id}
            
        except Exception as e:
            logger.error(f"Error saving reassessment record: {e}")
            self.db.rollback()
            return {'id': f'error_{uuid.uuid4()}'}
    
    def _generate_overall_assessment(
        self,
        progress_metrics: ProgressMetrics,
        recommendations: List[ReassessmentRecommendation]
    ) -> Dict[str, Any]:
        """Generate overall assessment summary"""
        
        # Determine overall performance level
        if progress_metrics.score_improvement >= 15:
            performance_level = 'excellent'
        elif progress_metrics.score_improvement >= 10:
            performance_level = 'good'
        elif progress_metrics.score_improvement >= 5:
            performance_level = 'satisfactory'
        elif progress_metrics.score_improvement >= 0:
            performance_level = 'minimal'
        else:
            performance_level = 'needs_attention'
        
        # Count high-priority recommendations
        urgent_actions = len([r for r in recommendations if r.priority_level == 1])
        
        # Generate summary message
        summary_messages = {
            'excellent': 'Outstanding progress! You\'re exceeding expectations.',
            'good': 'Great progress! Continue with current approach.',
            'satisfactory': 'Good progress. Some areas need attention.',
            'minimal': 'Limited progress. Consider adjusting study approach.',
            'needs_attention': 'Progress below expectations. Intervention needed.'
        }
        
        return {
            'performance_level': performance_level,
            'summary_message': summary_messages[performance_level],
            'score_change': progress_metrics.score_improvement,
            'topics_mastered': len(progress_metrics.topics_improved),
            'urgent_actions_needed': urgent_actions,
            'next_milestone': f"Target: {progress_metrics.current_score + 10:.1f}% in next assessment",
            'confidence_level': 'high' if progress_metrics.consistency_score > 0.7 else 'medium'
        }