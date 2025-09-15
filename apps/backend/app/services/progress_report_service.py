"""
Progress Report Service with Learning Trajectory Visualization
Generates comprehensive progress reports showing student learning trajectories,
improvement patterns, and personalized insights.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, text
from datetime import datetime, timedelta, date
import json
import uuid
import statistics
from dataclasses import dataclass
from enum import Enum

from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestResult
from ..models.user import User
from ..models.subject import Subject
from ..models.topic import Topic

logger = logging.getLogger(__name__)

class ReportType(Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMESTER = "semester"
    ANNUAL = "annual"
    CUSTOM = "custom"

class TrajectoryType(Enum):
    OVERALL_PERFORMANCE = "overall_performance"
    TOPIC_MASTERY = "topic_mastery"
    DIFFICULTY_PROGRESSION = "difficulty_progression"
    TIME_EFFICIENCY = "time_efficiency"
    LEARNING_VELOCITY = "learning_velocity"

@dataclass
class LearningTrajectoryPoint:
    """Data structure for a single point in the learning trajectory."""
    date: datetime
    score: float
    assessment_type: str
    topic_scores: Dict[str, float]
    difficulty_level: float
    time_efficiency: float
    confidence_level: float
    improvement_rate: float

class ProgressReportService:
    """
    Service for generating comprehensive progress reports with learning trajectory visualization.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def generate_comprehensive_report(self, user_id: str, subject_id: str = None,
                                    report_type: ReportType = ReportType.MONTHLY,
                                    custom_date_range: Tuple[datetime, datetime] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive progress report with learning trajectories.
        
        Args:
            user_id: User identifier
            subject_id: Optional subject identifier. If None, generates for all subjects.
            report_type: Type of report (monthly, quarterly, etc.)
            custom_date_range: Optional custom date range (start_date, end_date)
            
        Returns:
            Comprehensive progress report with visualizations and insights
        """
        try:
            # Calculate date range
            start_date, end_date = self._calculate_date_range(report_type, custom_date_range)
            
            # Get user information
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Generate report sections
            report = {
                "report_id": str(uuid.uuid4()),
                "user_id": user_id,
                "user_name": user.username,
                "subject_id": subject_id,
                "report_type": report_type.value,
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "generated_at": datetime.utcnow(),
                
                # Core report sections
                "executive_summary": self._generate_executive_summary(user_id, subject_id, start_date, end_date),
                "learning_trajectories": self._generate_learning_trajectories(user_id, subject_id, start_date, end_date),
                "performance_analytics": self._generate_performance_analytics(user_id, subject_id, start_date, end_date),
                "topic_mastery_analysis": self._generate_topic_mastery_analysis(user_id, subject_id, start_date, end_date),
                "improvement_patterns": self._generate_improvement_patterns(user_id, subject_id, start_date, end_date),
                "predictions_and_recommendations": self._generate_predictions_and_recommendations(user_id, subject_id, start_date, end_date),
                "detailed_metrics": self._generate_detailed_metrics(user_id, subject_id, start_date, end_date),
                "visualization_data": self._generate_visualization_data(user_id, subject_id, start_date, end_date),
                "actionable_insights": self._generate_actionable_insights(user_id, subject_id, start_date, end_date)
            }
            
            # Calculate report confidence score
            report["confidence_score"] = self._calculate_report_confidence(report)
            
            # Store report for future reference
            self._store_progress_report(report)
            
            self.logger.info(f"Generated comprehensive progress report for user {user_id}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive progress report: {str(e)}")
            raise
    
    def generate_learning_trajectory_visualization(self, user_id: str, subject_id: str,
                                                 trajectory_type: TrajectoryType,
                                                 time_period: int = 180) -> Dict[str, Any]:
        """
        Generate detailed learning trajectory visualization data.
        
        Args:
            user_id: User identifier
            subject_id: Subject identifier
            trajectory_type: Type of trajectory to visualize
            time_period: Number of days to include in trajectory
            
        Returns:
            Trajectory visualization data and metadata
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=time_period)
            
            # Get trajectory data points
            trajectory_points = self._extract_trajectory_points(user_id, subject_id, start_date, trajectory_type)
            
            # Generate visualization configuration
            visualization_config = self._generate_trajectory_visualization_config(trajectory_type, trajectory_points)
            
            # Calculate trend analysis
            trend_analysis = self._calculate_trajectory_trends(trajectory_points, trajectory_type)
            
            # Generate insights
            trajectory_insights = self._generate_trajectory_insights(trajectory_points, trend_analysis, trajectory_type)
            
            # Create interactive elements
            interactive_elements = self._create_interactive_elements(trajectory_points, trajectory_type)
            
            return {
                "trajectory_id": str(uuid.uuid4()),
                "user_id": user_id,
                "subject_id": subject_id,
                "trajectory_type": trajectory_type.value,
                "time_period_days": time_period,
                "data_points": len(trajectory_points),
                "trajectory_data": {
                    "points": [self._serialize_trajectory_point(point) for point in trajectory_points],
                    "trend_lines": trend_analysis.get("trend_lines", []),
                    "milestones": trend_analysis.get("milestones", []),
                    "annotations": trend_analysis.get("annotations", [])
                },
                "visualization_config": visualization_config,
                "trend_analysis": trend_analysis,
                "insights": trajectory_insights,
                "interactive_elements": interactive_elements,
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating learning trajectory visualization: {str(e)}")
            raise
    
    def generate_comparative_analysis(self, user_id: str, subject_ids: List[str],
                                    comparison_period: int = 90) -> Dict[str, Any]:
        """
        Generate comparative analysis across multiple subjects or time periods.
        
        Args:
            user_id: User identifier
            subject_ids: List of subject identifiers to compare
            comparison_period: Number of days for comparison
            
        Returns:
            Comparative analysis with cross-subject insights
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=comparison_period)
            
            # Generate analysis for each subject
            subject_analyses = {}
            for subject_id in subject_ids:
                subject_analyses[subject_id] = self._generate_subject_analysis(user_id, subject_id, start_date)
            
            # Perform cross-subject comparison
            cross_subject_comparison = self._perform_cross_subject_comparison(subject_analyses)
            
            # Identify patterns and correlations
            pattern_analysis = self._identify_cross_subject_patterns(subject_analyses)
            
            # Generate comparative insights
            comparative_insights = self._generate_comparative_insights(cross_subject_comparison, pattern_analysis)
            
            # Create unified recommendations
            unified_recommendations = self._create_unified_recommendations(subject_analyses, comparative_insights)
            
            return {
                "comparison_id": str(uuid.uuid4()),
                "user_id": user_id,
                "subjects_analyzed": subject_ids,
                "comparison_period_days": comparison_period,
                "generated_at": datetime.utcnow(),
                
                "subject_analyses": subject_analyses,
                "cross_subject_comparison": cross_subject_comparison,
                "pattern_analysis": pattern_analysis,
                "comparative_insights": comparative_insights,
                "unified_recommendations": unified_recommendations,
                
                "performance_ranking": self._rank_subject_performance(subject_analyses),
                "learning_efficiency_comparison": self._compare_learning_efficiency(subject_analyses),
                "improvement_rate_analysis": self._analyze_improvement_rates(subject_analyses)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating comparative analysis: {str(e)}")
            raise
    
    def generate_milestone_report(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """
        Generate milestone achievement report showing learning goals and accomplishments.
        
        Args:
            user_id: User identifier
            subject_id: Subject identifier
            
        Returns:
            Milestone report with achievements and upcoming goals
        """
        try:
            # Get all diagnostic tests for milestone analysis
            diagnostics = self.db.query(DiagnosticTest).filter(
                and_(
                    DiagnosticTest.user_id == user_id,
                    DiagnosticTest.subject_id == subject_id,
                    DiagnosticTest.status == "completed"
                )
            ).order_by(DiagnosticTest.created_at.asc()).all()
            
            # Identify achieved milestones
            achieved_milestones = self._identify_achieved_milestones(diagnostics)
            
            # Calculate progress toward upcoming milestones
            upcoming_milestones = self._calculate_upcoming_milestones(diagnostics)
            
            # Analyze milestone achievement patterns
            achievement_patterns = self._analyze_milestone_patterns(achieved_milestones)
            
            # Generate milestone insights
            milestone_insights = self._generate_milestone_insights(achieved_milestones, upcoming_milestones, achievement_patterns)
            
            # Create achievement timeline
            achievement_timeline = self._create_achievement_timeline(achieved_milestones)
            
            return {
                "milestone_report_id": str(uuid.uuid4()),
                "user_id": user_id,
                "subject_id": subject_id,
                "generated_at": datetime.utcnow(),
                
                "achievement_summary": {
                    "total_milestones_achieved": len(achieved_milestones),
                    "milestones_this_month": len([m for m in achieved_milestones if self._is_recent(m["achieved_date"], 30)]),
                    "achievement_rate": self._calculate_achievement_rate(achieved_milestones),
                    "next_milestone_eta": self._estimate_next_milestone_eta(upcoming_milestones, achievement_patterns)
                },
                
                "achieved_milestones": achieved_milestones,
                "upcoming_milestones": upcoming_milestones,
                "achievement_patterns": achievement_patterns,
                "milestone_insights": milestone_insights,
                "achievement_timeline": achievement_timeline,
                
                "celebration_worthy_achievements": self._identify_celebration_worthy_achievements(achieved_milestones),
                "motivation_boosters": self._generate_motivation_boosters(upcoming_milestones, achievement_patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating milestone report: {str(e)}")
            raise
    
    def export_report_data(self, report_id: str, export_format: str = "json") -> Dict[str, Any]:
        """
        Export report data in various formats for external use.
        
        Args:
            report_id: Report identifier
            export_format: Export format ("json", "csv", "pdf", "excel")
            
        Returns:
            Exported report data and metadata
        """
        try:
            # Get report data
            report_data = self._get_stored_report(report_id)
            if not report_data:
                raise ValueError(f"Report {report_id} not found")
            
            # Format data for export
            if export_format == "json":
                exported_data = self._export_as_json(report_data)
            elif export_format == "csv":
                exported_data = self._export_as_csv(report_data)
            elif export_format == "pdf":
                exported_data = self._export_as_pdf(report_data)
            elif export_format == "excel":
                exported_data = self._export_as_excel(report_data)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            return {
                "export_id": str(uuid.uuid4()),
                "report_id": report_id,
                "export_format": export_format,
                "exported_at": datetime.utcnow(),
                "data": exported_data,
                "metadata": {
                    "file_size": len(str(exported_data)),
                    "data_points": self._count_data_points(report_data),
                    "export_version": "1.0"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting report data: {str(e)}")
            raise
    
    # Private helper methods
    
    def _calculate_date_range(self, report_type: ReportType, 
                            custom_range: Optional[Tuple[datetime, datetime]]) -> Tuple[datetime, datetime]:
        """Calculate date range for report based on type."""
        if custom_range:
            return custom_range
        
        end_date = datetime.utcnow()
        
        if report_type == ReportType.MONTHLY:
            start_date = end_date - timedelta(days=30)
        elif report_type == ReportType.QUARTERLY:
            start_date = end_date - timedelta(days=90)
        elif report_type == ReportType.SEMESTER:
            start_date = end_date - timedelta(days=180)
        elif report_type == ReportType.ANNUAL:
            start_date = end_date - timedelta(days=365)
        else:  # DEFAULT to monthly
            start_date = end_date - timedelta(days=30)
        
        return start_date, end_date
    
    def _generate_executive_summary(self, user_id: str, subject_id: str, 
                                  start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate executive summary section of the report."""
        # Get diagnostic tests in period
        diagnostics = self._get_diagnostics_in_period(user_id, subject_id, start_date, end_date)
        
        if not diagnostics:
            return {"message": "No assessment data available for this period"}
        
        # Calculate key metrics
        current_score = diagnostics[-1].score_percentage if diagnostics else 0
        initial_score = diagnostics[0].score_percentage if diagnostics else 0
        improvement = current_score - initial_score
        
        # Calculate average scores by month
        monthly_averages = self._calculate_monthly_averages(diagnostics)
        
        # Identify key achievements
        key_achievements = self._identify_key_achievements(diagnostics)
        
        # Calculate learning velocity
        learning_velocity = self._calculate_learning_velocity(diagnostics)
        
        return {
            "period_overview": {
                "total_assessments": len(diagnostics),
                "current_performance": current_score,
                "initial_performance": initial_score,
                "overall_improvement": improvement,
                "improvement_percentage": (improvement / max(initial_score, 1)) * 100
            },
            "key_metrics": {
                "average_monthly_score": statistics.mean(monthly_averages) if monthly_averages else 0,
                "consistency_score": self._calculate_consistency_score(diagnostics),
                "learning_velocity": learning_velocity,
                "assessment_frequency": len(diagnostics) / max(1, (end_date - start_date).days / 30)
            },
            "highlights": {
                "key_achievements": key_achievements,
                "biggest_improvement": self._find_biggest_improvement(diagnostics),
                "most_consistent_topic": self._find_most_consistent_topic(diagnostics),
                "learning_streak": self._calculate_learning_streak(diagnostics)
            },
            "period_grade": self._calculate_period_grade(improvement, learning_velocity, len(diagnostics))
        }
    
    def _generate_learning_trajectories(self, user_id: str, subject_id: str,
                                      start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate learning trajectories for all trajectory types."""
        trajectories = {}
        
        for trajectory_type in TrajectoryType:
            try:
                trajectory_data = self.generate_learning_trajectory_visualization(
                    user_id, subject_id, trajectory_type, (end_date - start_date).days
                )
                trajectories[trajectory_type.value] = trajectory_data
            except Exception as e:
                self.logger.warning(f"Failed to generate {trajectory_type.value} trajectory: {str(e)}")
                trajectories[trajectory_type.value] = {"error": str(e)}
        
        return trajectories
    
    def _generate_performance_analytics(self, user_id: str, subject_id: str,
                                      start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate detailed performance analytics."""
        diagnostics = self._get_diagnostics_in_period(user_id, subject_id, start_date, end_date)
        
        # Score distribution analysis
        scores = [d.score_percentage for d in diagnostics]
        score_analysis = {
            "mean": statistics.mean(scores) if scores else 0,
            "median": statistics.median(scores) if scores else 0,
            "std_deviation": statistics.stdev(scores) if len(scores) > 1 else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "score_range": max(scores) - min(scores) if scores else 0
        }
        
        # Performance trends
        performance_trends = self._analyze_performance_trends(diagnostics)
        
        # Time efficiency analysis
        time_efficiency = self._analyze_time_efficiency(diagnostics)
        
        # Difficulty progression
        difficulty_progression = self._analyze_difficulty_progression(diagnostics)
        
        return {
            "score_distribution": score_analysis,
            "performance_trends": performance_trends,
            "time_efficiency": time_efficiency,
            "difficulty_progression": difficulty_progression,
            "performance_stability": self._calculate_performance_stability(scores),
            "improvement_acceleration": self._calculate_improvement_acceleration(diagnostics)
        }
    
    def _generate_topic_mastery_analysis(self, user_id: str, subject_id: str,
                                       start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate topic mastery analysis."""
        diagnostics = self._get_diagnostics_in_period(user_id, subject_id, start_date, end_date)
        
        # Aggregate topic scores across all assessments
        topic_scores = {}
        topic_counts = {}
        
        for diagnostic in diagnostics:
            if diagnostic.score_by_topic:
                for topic, score in diagnostic.score_by_topic.items():
                    if topic not in topic_scores:
                        topic_scores[topic] = []
                    topic_scores[topic].append(score)
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Calculate mastery metrics for each topic
        mastery_analysis = {}
        for topic, scores in topic_scores.items():
            mastery_analysis[topic] = {
                "current_level": scores[-1] if scores else 0,
                "average_score": statistics.mean(scores),
                "improvement": scores[-1] - scores[0] if len(scores) > 1 else 0,
                "consistency": 1 - (statistics.stdev(scores) / max(statistics.mean(scores), 1)) if len(scores) > 1 else 1,
                "mastery_status": self._determine_mastery_status(scores),
                "assessment_count": len(scores),
                "trend": self._calculate_topic_trend(scores)
            }
        
        # Identify mastery patterns
        mastery_patterns = {
            "mastered_topics": [topic for topic, data in mastery_analysis.items() if data["mastery_status"] == "mastered"],
            "developing_topics": [topic for topic, data in mastery_analysis.items() if data["mastery_status"] == "developing"],
            "struggling_topics": [topic for topic, data in mastery_analysis.items() if data["mastery_status"] == "struggling"],
            "fastest_improving": max(mastery_analysis.items(), key=lambda x: x[1]["improvement"])[0] if mastery_analysis else None,
            "most_consistent": max(mastery_analysis.items(), key=lambda x: x[1]["consistency"])[0] if mastery_analysis else None
        }
        
        return {
            "topic_analysis": mastery_analysis,
            "mastery_patterns": mastery_patterns,
            "overall_mastery_score": self._calculate_overall_mastery_score(mastery_analysis),
            "mastery_trajectory": self._calculate_mastery_trajectory(topic_scores)
        }
    
    def _generate_improvement_patterns(self, user_id: str, subject_id: str,
                                     start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate improvement patterns analysis."""
        diagnostics = self._get_diagnostics_in_period(user_id, subject_id, start_date, end_date)
        
        if len(diagnostics) < 2:
            return {"message": "Insufficient data for improvement pattern analysis"}
        
        # Calculate improvement between consecutive assessments
        improvements = []
        for i in range(1, len(diagnostics)):
            improvement = diagnostics[i].score_percentage - diagnostics[i-1].score_percentage
            time_gap = (diagnostics[i].created_at - diagnostics[i-1].created_at).days
            improvements.append({
                "improvement": improvement,
                "time_gap": time_gap,
                "date": diagnostics[i].created_at,
                "from_score": diagnostics[i-1].score_percentage,
                "to_score": diagnostics[i].score_percentage
            })
        
        # Analyze improvement patterns
        patterns = {
            "average_improvement": statistics.mean([imp["improvement"] for imp in improvements]),
            "improvement_consistency": self._calculate_improvement_consistency(improvements),
            "best_improvement_period": max(improvements, key=lambda x: x["improvement"]) if improvements else None,
            "improvement_acceleration": self._calculate_improvement_acceleration_pattern(improvements),
            "plateau_periods": self._identify_plateau_periods(improvements),
            "breakthrough_moments": self._identify_breakthrough_moments(improvements)
        }
        
        # Identify factors correlated with improvement
        improvement_factors = self._analyze_improvement_factors(diagnostics, improvements)
        
        return {
            "improvement_data": improvements,
            "patterns": patterns,
            "improvement_factors": improvement_factors,
            "improvement_prediction": self._predict_future_improvement(improvements)
        }
    
    def _generate_predictions_and_recommendations(self, user_id: str, subject_id: str,
                                                start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate predictions and personalized recommendations."""
        diagnostics = self._get_diagnostics_in_period(user_id, subject_id, start_date, end_date)
        
        # Performance predictions
        performance_predictions = self._generate_performance_predictions(diagnostics)
        
        # Learning recommendations
        learning_recommendations = self._generate_learning_recommendations(diagnostics)
        
        # Study plan suggestions
        study_plan_suggestions = self._generate_study_plan_suggestions(diagnostics)
        
        # Goal setting recommendations
        goal_recommendations = self._generate_goal_recommendations(diagnostics)
        
        return {
            "performance_predictions": performance_predictions,
            "learning_recommendations": learning_recommendations,
            "study_plan_suggestions": study_plan_suggestions,
            "goal_recommendations": goal_recommendations,
            "next_assessment_preparation": self._generate_assessment_preparation_advice(diagnostics),
            "personalized_insights": self._generate_personalized_insights(user_id, diagnostics)
        }
    
    def _generate_detailed_metrics(self, user_id: str, subject_id: str,
                                 start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate detailed metrics for comprehensive analysis."""
        diagnostics = self._get_diagnostics_in_period(user_id, subject_id, start_date, end_date)
        
        return {
            "assessment_metrics": self._calculate_assessment_metrics(diagnostics),
            "learning_efficiency_metrics": self._calculate_learning_efficiency_metrics(diagnostics),
            "engagement_metrics": self._calculate_engagement_metrics(diagnostics),
            "consistency_metrics": self._calculate_consistency_metrics_detailed(diagnostics),
            "comparative_metrics": self._calculate_comparative_metrics(user_id, subject_id, diagnostics)
        }
    
    def _generate_visualization_data(self, user_id: str, subject_id: str,
                                   start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate data for visualizations."""
        diagnostics = self._get_diagnostics_in_period(user_id, subject_id, start_date, end_date)
        
        return {
            "chart_data": {
                "score_timeline": self._prepare_score_timeline_data(diagnostics),
                "topic_performance_radar": self._prepare_topic_radar_data(diagnostics),
                "improvement_bar_chart": self._prepare_improvement_bar_data(diagnostics),
                "consistency_heatmap": self._prepare_consistency_heatmap_data(diagnostics)
            },
            "interactive_elements": {
                "drill_down_data": self._prepare_drill_down_data(diagnostics),
                "filter_options": self._prepare_filter_options(diagnostics),
                "comparison_baselines": self._prepare_comparison_baselines(user_id, subject_id)
            }
        }
    
    def _generate_actionable_insights(self, user_id: str, subject_id: str,
                                    start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate actionable insights based on analysis."""
        diagnostics = self._get_diagnostics_in_period(user_id, subject_id, start_date, end_date)
        
        insights = []
        
        # Performance insights
        if diagnostics:
            latest_score = diagnostics[-1].score_percentage
            if latest_score > 80:
                insights.append({
                    "type": "achievement",
                    "priority": "high",
                    "title": "Excelente Rendimiento",
                    "description": f"Has alcanzado un nivel de rendimiento excepcional con {latest_score:.1f}%",
                    "action": "Mantén tu rutina actual y considera retos más avanzados",
                    "category": "performance"
                })
            elif latest_score < 50:
                insights.append({
                    "type": "improvement_needed",
                    "priority": "high",
                    "title": "Oportunidad de Mejora",
                    "description": f"Tu rendimiento actual es {latest_score:.1f}%, hay espacio para crecer",
                    "action": "Enfócate en conceptos fundamentales y practica regularmente",
                    "category": "performance"
                })
        
        # Add more insights based on patterns
        insights.extend(self._generate_pattern_based_insights(diagnostics))
        insights.extend(self._generate_trend_based_insights(diagnostics))
        insights.extend(self._generate_topic_specific_insights(diagnostics))
        
        # Sort by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        insights.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)
        
        return insights[:10]  # Return top 10 insights
    
    def _extract_trajectory_points(self, user_id: str, subject_id: str, start_date: datetime,
                                 trajectory_type: TrajectoryType) -> List[LearningTrajectoryPoint]:
        """Extract trajectory points for visualization."""
        diagnostics = self._get_diagnostics_in_period(user_id, subject_id, start_date, datetime.utcnow())
        
        trajectory_points = []
        for i, diagnostic in enumerate(diagnostics):
            # Calculate metrics based on trajectory type
            if trajectory_type == TrajectoryType.OVERALL_PERFORMANCE:
                score = diagnostic.score_percentage
            elif trajectory_type == TrajectoryType.TIME_EFFICIENCY:
                score = self._calculate_time_efficiency_score(diagnostic)
            elif trajectory_type == TrajectoryType.DIFFICULTY_PROGRESSION:
                score = self._calculate_difficulty_score(diagnostic)
            else:
                score = diagnostic.score_percentage  # Default
            
            # Calculate additional metrics
            time_efficiency = self._calculate_time_efficiency_score(diagnostic)
            confidence_level = self._estimate_confidence_level(diagnostic)
            improvement_rate = self._calculate_improvement_rate(diagnostics, i)
            
            point = LearningTrajectoryPoint(
                date=diagnostic.created_at,
                score=score,
                assessment_type=diagnostic.test_type,
                topic_scores=diagnostic.score_by_topic or {},
                difficulty_level=self._calculate_difficulty_score(diagnostic),
                time_efficiency=time_efficiency,
                confidence_level=confidence_level,
                improvement_rate=improvement_rate
            )
            trajectory_points.append(point)
        
        return trajectory_points
    
    def _serialize_trajectory_point(self, point: LearningTrajectoryPoint) -> Dict[str, Any]:
        """Serialize trajectory point for JSON output."""
        return {
            "date": point.date.isoformat(),
            "score": point.score,
            "assessment_type": point.assessment_type,
            "topic_scores": point.topic_scores,
            "difficulty_level": point.difficulty_level,
            "time_efficiency": point.time_efficiency,
            "confidence_level": point.confidence_level,
            "improvement_rate": point.improvement_rate
        }
    
    def _get_diagnostics_in_period(self, user_id: str, subject_id: str,
                                 start_date: datetime, end_date: datetime) -> List[DiagnosticTest]:
        """Get diagnostic tests within specified period."""
        query = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.status == "completed",
                DiagnosticTest.created_at >= start_date,
                DiagnosticTest.created_at <= end_date
            )
        )
        
        if subject_id:
            query = query.filter(DiagnosticTest.subject_id == subject_id)
        
        return query.order_by(DiagnosticTest.created_at.asc()).all()
    
    # Additional helper methods for calculations and analysis...
    
    def _calculate_monthly_averages(self, diagnostics: List[DiagnosticTest]) -> List[float]:
        """Calculate monthly average scores."""
        if not diagnostics:
            return []
        
        monthly_scores = {}
        for diagnostic in diagnostics:
            month_key = diagnostic.created_at.strftime("%Y-%m")
            if month_key not in monthly_scores:
                monthly_scores[month_key] = []
            monthly_scores[month_key].append(diagnostic.score_percentage)
        
        return [statistics.mean(scores) for scores in monthly_scores.values()]
    
    def _calculate_consistency_score(self, diagnostics: List[DiagnosticTest]) -> float:
        """Calculate consistency score based on score variance."""
        if len(diagnostics) < 2:
            return 1.0
        
        scores = [d.score_percentage for d in diagnostics]
        mean_score = statistics.mean(scores)
        std_dev = statistics.stdev(scores)
        
        # Consistency score: lower variance = higher consistency
        consistency = max(0, 1 - (std_dev / max(mean_score, 1)))
        return consistency
    
    def _calculate_learning_velocity(self, diagnostics: List[DiagnosticTest]) -> float:
        """Calculate learning velocity (improvement per unit time)."""
        if len(diagnostics) < 2:
            return 0.0
        
        first_score = diagnostics[0].score_percentage
        last_score = diagnostics[-1].score_percentage
        time_span = (diagnostics[-1].created_at - diagnostics[0].created_at).days
        
        if time_span == 0:
            return 0.0
        
        return (last_score - first_score) / time_span
    
    def _identify_key_achievements(self, diagnostics: List[DiagnosticTest]) -> List[Dict[str, Any]]:
        """Identify key achievements from diagnostic history."""
        achievements = []
        
        if not diagnostics:
            return achievements
        
        # Score milestones
        max_score = max(d.score_percentage for d in diagnostics)
        if max_score >= 90:
            achievements.append({"type": "score_milestone", "description": "Alcanzó 90% o más en una evaluación"})
        elif max_score >= 80:
            achievements.append({"type": "score_milestone", "description": "Alcanzó 80% o más en una evaluación"})
        
        # Improvement streaks
        improvements = []
        for i in range(1, len(diagnostics)):
            if diagnostics[i].score_percentage > diagnostics[i-1].score_percentage:
                improvements.append(1)
            else:
                improvements.append(0)
        
        # Find longest improvement streak
        max_streak = 0
        current_streak = 0
        for improvement in improvements:
            if improvement:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        if max_streak >= 3:
            achievements.append({"type": "improvement_streak", "description": f"Racha de mejora de {max_streak} evaluaciones"})
        
        return achievements
    
    def _find_biggest_improvement(self, diagnostics: List[DiagnosticTest]) -> Optional[Dict[str, Any]]:
        """Find the biggest improvement between consecutive tests."""
        if len(diagnostics) < 2:
            return None
        
        biggest_improvement = 0
        best_period = None
        
        for i in range(1, len(diagnostics)):
            improvement = diagnostics[i].score_percentage - diagnostics[i-1].score_percentage
            if improvement > biggest_improvement:
                biggest_improvement = improvement
                best_period = {
                    "improvement": improvement,
                    "from_date": diagnostics[i-1].created_at,
                    "to_date": diagnostics[i].created_at,
                    "from_score": diagnostics[i-1].score_percentage,
                    "to_score": diagnostics[i].score_percentage
                }
        
        return best_period
    
    def _find_most_consistent_topic(self, diagnostics: List[DiagnosticTest]) -> Optional[str]:
        """Find the most consistent topic across assessments."""
        topic_scores = {}
        
        for diagnostic in diagnostics:
            if diagnostic.score_by_topic:
                for topic, score in diagnostic.score_by_topic.items():
                    if topic not in topic_scores:
                        topic_scores[topic] = []
                    topic_scores[topic].append(score)
        
        most_consistent_topic = None
        lowest_variance = float('inf')
        
        for topic, scores in topic_scores.items():
            if len(scores) > 1:
                variance = statistics.variance(scores)
                if variance < lowest_variance:
                    lowest_variance = variance
                    most_consistent_topic = topic
        
        return most_consistent_topic
    
    def _calculate_learning_streak(self, diagnostics: List[DiagnosticTest]) -> int:
        """Calculate current learning streak (consecutive improvements or maintenance)."""
        if len(diagnostics) < 2:
            return 0
        
        streak = 0
        for i in range(len(diagnostics) - 1, 0, -1):
            if diagnostics[i].score_percentage >= diagnostics[i-1].score_percentage:
                streak += 1
            else:
                break
        
        return streak
    
    def _calculate_period_grade(self, improvement: float, learning_velocity: float, assessment_count: int) -> str:
        """Calculate overall grade for the period."""
        # Grade based on multiple factors
        grade_score = 0
        
        # Improvement factor
        if improvement > 20:
            grade_score += 3
        elif improvement > 10:
            grade_score += 2
        elif improvement > 0:
            grade_score += 1
        
        # Learning velocity factor
        if learning_velocity > 1:
            grade_score += 2
        elif learning_velocity > 0.5:
            grade_score += 1
        
        # Engagement factor (assessment frequency)
        if assessment_count >= 4:
            grade_score += 2
        elif assessment_count >= 2:
            grade_score += 1
        
        # Convert to letter grade
        if grade_score >= 6:
            return "A"
        elif grade_score >= 4:
            return "B"
        elif grade_score >= 2:
            return "C"
        else:
            return "D"
    
    def _calculate_report_confidence(self, report: Dict[str, Any]) -> float:
        """Calculate confidence score for the report based on data quality and quantity."""
        confidence_factors = []
        
        # Data quantity factor
        executive_summary = report.get("executive_summary", {})
        assessment_count = executive_summary.get("period_overview", {}).get("total_assessments", 0)
        
        if assessment_count >= 5:
            confidence_factors.append(1.0)
        elif assessment_count >= 3:
            confidence_factors.append(0.8)
        elif assessment_count >= 2:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)
        
        # Data consistency factor
        consistency_score = executive_summary.get("key_metrics", {}).get("consistency_score", 0)
        confidence_factors.append(consistency_score)
        
        # Time span factor (more time = more confidence in trends)
        # This would be calculated based on the actual time span of data
        confidence_factors.append(0.8)  # Placeholder
        
        return statistics.mean(confidence_factors) if confidence_factors else 0.5
    
    def _store_progress_report(self, report: Dict[str, Any]):
        """Store progress report for future reference."""
        # In a real implementation, this would store the report in a database
        self.logger.info(f"Stored progress report {report['report_id']} for user {report['user_id']}")
    
    # Placeholder methods for complex calculations (to be implemented)
    
    def _analyze_performance_trends(self, diagnostics: List[DiagnosticTest]) -> Dict[str, Any]:
        """Analyze performance trends."""
        return {"trend": "improving", "confidence": 0.8}
    
    def _analyze_time_efficiency(self, diagnostics: List[DiagnosticTest]) -> Dict[str, Any]:
        """Analyze time efficiency patterns."""
        return {"efficiency_trend": "stable", "average_time_per_question": 90}
    
    def _analyze_difficulty_progression(self, diagnostics: List[DiagnosticTest]) -> Dict[str, Any]:
        """Analyze difficulty progression."""
        return {"progression": "gradual", "current_level": "intermediate"}
    
    def _calculate_performance_stability(self, scores: List[float]) -> float:
        """Calculate performance stability metric."""
        if len(scores) < 2:
            return 1.0
        return 1 - (statistics.stdev(scores) / max(statistics.mean(scores), 1))
    
    def _calculate_improvement_acceleration(self, diagnostics: List[DiagnosticTest]) -> float:
        """Calculate improvement acceleration."""
        return 0.5  # Placeholder
    
    def _determine_mastery_status(self, scores: List[float]) -> str:
        """Determine mastery status for a topic."""
        if not scores:
            return "unknown"
        
        latest_score = scores[-1]
        average_score = statistics.mean(scores)
        
        if latest_score >= 85 and average_score >= 80:
            return "mastered"
        elif latest_score >= 70 and average_score >= 65:
            return "developing"
        else:
            return "struggling"
    
    def _calculate_topic_trend(self, scores: List[float]) -> str:
        """Calculate trend for a specific topic."""
        if len(scores) < 2:
            return "stable"
        
        recent_avg = statistics.mean(scores[-min(3, len(scores)):])
        early_avg = statistics.mean(scores[:min(3, len(scores))])
        
        if recent_avg > early_avg + 5:
            return "improving"
        elif recent_avg < early_avg - 5:
            return "declining"
        else:
            return "stable"
    
    def _calculate_overall_mastery_score(self, mastery_analysis: Dict[str, Any]) -> float:
        """Calculate overall mastery score across all topics."""
        if not mastery_analysis:
            return 0.0
        
        scores = [data["current_level"] for data in mastery_analysis.values()]
        return statistics.mean(scores) if scores else 0.0
    
    def _calculate_mastery_trajectory(self, topic_scores: Dict[str, List[float]]) -> Dict[str, Any]:
        """Calculate mastery trajectory across topics."""
        return {"overall_trend": "improving", "velocity": 0.5}
    
    # Additional placeholder methods would be implemented here for a complete system
    
    def _generate_performance_predictions(self, diagnostics: List[DiagnosticTest]) -> Dict[str, Any]:
        """Generate performance predictions."""
        return {"predicted_next_score": 75.0, "confidence": 0.7}
    
    def _generate_learning_recommendations(self, diagnostics: List[DiagnosticTest]) -> List[str]:
        """Generate learning recommendations."""
        return ["Enfócate en práctica regular", "Revisa conceptos fundamentales"]
    
    def _generate_study_plan_suggestions(self, diagnostics: List[DiagnosticTest]) -> Dict[str, Any]:
        """Generate study plan suggestions."""
        return {"recommended_frequency": "3 times per week", "session_duration": "45 minutes"}
    
    def _generate_goal_recommendations(self, diagnostics: List[DiagnosticTest]) -> List[Dict[str, Any]]:
        """Generate goal recommendations."""
        return [{"goal": "Alcanzar 80% en próxima evaluación", "timeframe": "2 weeks", "difficulty": "medium"}]
    
    def _generate_assessment_preparation_advice(self, diagnostics: List[DiagnosticTest]) -> List[str]:
        """Generate assessment preparation advice."""
        return ["Repasa temas débiles", "Practica gestión del tiempo"]
    
    def _generate_personalized_insights(self, user_id: str, diagnostics: List[DiagnosticTest]) -> List[str]:
        """Generate personalized insights."""
        return ["Tu progreso es constante", "Excelente mejora en matemáticas"]
    
    # Export methods (simplified implementations)
    
    def _export_as_json(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Export report as JSON."""
        return report_data
    
    def _export_as_csv(self, report_data: Dict[str, Any]) -> str:
        """Export report as CSV."""
        return "CSV export not implemented"
    
    def _export_as_pdf(self, report_data: Dict[str, Any]) -> str:
        """Export report as PDF."""
        return "PDF export not implemented"
    
    def _export_as_excel(self, report_data: Dict[str, Any]) -> str:
        """Export report as Excel."""
        return "Excel export not implemented"
    
    def _get_stored_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get stored report by ID."""
        # In a real implementation, retrieve from database
        return None
    
    def _count_data_points(self, report_data: Dict[str, Any]) -> int:
        """Count data points in report."""
        return 100  # Placeholder
    
    # Additional calculation helpers
    
    def _calculate_time_efficiency_score(self, diagnostic: DiagnosticTest) -> float:
        """Calculate time efficiency score for a diagnostic."""
        if not diagnostic.time_spent_seconds or not diagnostic.questions_answered:
            return 0.5
        
        avg_time_per_question = diagnostic.time_spent_seconds / diagnostic.questions_answered
        # Assuming 90 seconds is optimal time per question
        efficiency = min(1.0, 90 / max(avg_time_per_question, 30))
        return efficiency
    
    def _calculate_difficulty_score(self, diagnostic: DiagnosticTest) -> float:
        """Calculate difficulty score for a diagnostic."""
        # This would require difficulty information for questions
        return 5.0  # Placeholder (scale 1-10)
    
    def _estimate_confidence_level(self, diagnostic: DiagnosticTest) -> float:
        """Estimate confidence level based on performance."""
        score = diagnostic.score_percentage
        if score >= 90:
            return 0.9
        elif score >= 70:
            return 0.7
        elif score >= 50:
            return 0.5
        else:
            return 0.3
    
    def _calculate_improvement_rate(self, diagnostics: List[DiagnosticTest], current_index: int) -> float:
        """Calculate improvement rate at a specific point."""
        if current_index == 0:
            return 0.0
        
        current_score = diagnostics[current_index].score_percentage
        previous_score = diagnostics[current_index - 1].score_percentage
        
        return current_score - previous_score
    
    # Simplified implementations for milestone analysis
    
    def _identify_achieved_milestones(self, diagnostics: List[DiagnosticTest]) -> List[Dict[str, Any]]:
        """Identify achieved milestones."""
        milestones = []
        
        for diagnostic in diagnostics:
            score = diagnostic.score_percentage
            if score >= 90:
                milestones.append({
                    "milestone": "Excelencia Académica",
                    "achieved_date": diagnostic.created_at,
                    "score": score,
                    "description": "Logró 90% o más en evaluación"
                })
            elif score >= 80:
                milestones.append({
                    "milestone": "Alto Rendimiento",
                    "achieved_date": diagnostic.created_at,
                    "score": score,
                    "description": "Logró 80% o más en evaluación"
                })
        
        return milestones
    
    def _calculate_upcoming_milestones(self, diagnostics: List[DiagnosticTest]) -> List[Dict[str, Any]]:
        """Calculate upcoming milestones."""
        if not diagnostics:
            return []
        
        current_score = diagnostics[-1].score_percentage
        upcoming = []
        
        if current_score < 70:
            upcoming.append({
                "milestone": "Competencia Satisfactoria",
                "target_score": 70,
                "current_score": current_score,
                "progress": current_score / 70,
                "estimated_assessments": max(1, int((70 - current_score) / 10))
            })
        
        if current_score < 80:
            upcoming.append({
                "milestone": "Alto Rendimiento",
                "target_score": 80,
                "current_score": current_score,
                "progress": current_score / 80,
                "estimated_assessments": max(1, int((80 - current_score) / 10))
            })
        
        return upcoming
    
    def _is_recent(self, date: datetime, days: int) -> bool:
        """Check if date is within recent days."""
        return (datetime.utcnow() - date).days <= days