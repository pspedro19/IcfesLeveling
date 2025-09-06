"""
Diagnostic Study Plan Integration Service
Integrates diagnostic test results with personalized study plan generation,
creating adaptive learning paths based on performance analysis
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import math
import json
from dataclasses import dataclass, asdict

from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.user import User
from ..models.question import Question, Topic
from ..models.subject import Subject

logger = logging.getLogger(__name__)

@dataclass
class StudyPlanModule:
    """Represents a study plan module"""
    module_id: str
    title: str
    description: str
    priority: str  # 'critical', 'high', 'medium', 'low'
    estimated_hours: int
    difficulty_level: str  # 'beginner', 'intermediate', 'advanced'
    topics: List[str]
    learning_objectives: List[str]
    resources: List[Dict[str, Any]]
    prerequisites: List[str]
    success_criteria: Dict[str, Any]
    gamification_rewards: Dict[str, Any]

@dataclass
class AdaptiveLearningPath:
    """Represents an adaptive learning path"""
    path_id: str
    user_id: str
    subject_id: str
    diagnostic_test_id: str
    total_estimated_hours: int
    target_score: int
    target_rank: str
    modules: List[StudyPlanModule]
    milestones: List[Dict[str, Any]]
    adaptive_parameters: Dict[str, Any]
    created_at: datetime
    last_updated: datetime

class DiagnosticStudyPlanIntegration:
    """
    Service to integrate diagnostic test results with personalized study plan generation
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logger
        
        # Study plan configuration
        self.RANK_TARGET_SCORES = {
            'E': {'min': 0, 'target': 35, 'study_intensity': 'intensive'},
            'D': {'min': 35, 'target': 50, 'study_intensity': 'high'},
            'C': {'min': 50, 'target': 65, 'study_intensity': 'moderate'},
            'B': {'min': 65, 'target': 80, 'study_intensity': 'focused'},
            'A': {'min': 80, 'target': 90, 'study_intensity': 'refinement'},
            'S': {'min': 90, 'target': 95, 'study_intensity': 'mastery'}
        }
        
        # Learning efficiency factors
        self.BASE_STUDY_HOURS_PER_POINT = 1.5
        self.DIFFICULTY_MULTIPLIERS = {
            'beginner': 2.0,
            'intermediate': 1.5,
            'advanced': 1.0
        }
        
        # Module categories and templates
        self.MODULE_TEMPLATES = {
            'concept_review': {
                'title_template': 'Conceptual Review: {}',
                'description_template': 'Master fundamental concepts in {}',
                'base_hours': 8,
                'difficulty_level': 'beginner'
            },
            'skill_building': {
                'title_template': 'Skill Building: {}',
                'description_template': 'Develop practical skills in {}',
                'base_hours': 12,
                'difficulty_level': 'intermediate'
            },
            'problem_solving': {
                'title_template': 'Problem Solving: {}',
                'description_template': 'Advanced problem-solving strategies for {}',
                'base_hours': 10,
                'difficulty_level': 'advanced'
            },
            'test_preparation': {
                'title_template': 'Test Prep: {}',
                'description_template': 'ICFES-specific test preparation for {}',
                'base_hours': 6,
                'difficulty_level': 'intermediate'
            }
        }

    def generate_study_plan_from_diagnostic(self, diagnostic_test_id: str, 
                                          target_rank: Optional[str] = None,
                                          time_constraint_weeks: Optional[int] = None) -> AdaptiveLearningPath:
        """
        Generate a comprehensive study plan based on diagnostic test results
        """
        # Get diagnostic test and results
        test = self.db.query(DiagnosticTest).filter(DiagnosticTest.id == diagnostic_test_id).first()
        if not test or test.status != "completed":
            raise ValueError("Diagnostic test not found or not completed")
        
        # Analyze diagnostic results
        diagnostic_analysis = self._analyze_diagnostic_results(test)
        
        # Determine target rank if not specified
        if not target_rank:
            target_rank = self._determine_optimal_target_rank(test.score_percentage, diagnostic_analysis)
        
        # Generate learning modules based on weaknesses and target
        learning_modules = self._generate_learning_modules(
            diagnostic_analysis, target_rank, test.subject_id
        )
        
        # Create adaptive learning path
        learning_path = self._create_adaptive_learning_path(
            test, learning_modules, target_rank, time_constraint_weeks
        )
        
        # Generate milestones and checkpoints
        learning_path.milestones = self._generate_learning_milestones(
            learning_path, diagnostic_analysis
        )
        
        # Set adaptive parameters for ongoing adjustment
        learning_path.adaptive_parameters = self._set_adaptive_parameters(
            diagnostic_analysis, target_rank
        )
        
        # Store study plan in database (would integrate with StudyPlan model)
        self._store_study_plan(learning_path)
        
        self.logger.info(f"Generated study plan {learning_path.path_id} for user {test.user_id}")
        return learning_path

    def update_study_plan_from_progress(self, path_id: str, progress_data: Dict[str, Any]) -> AdaptiveLearningPath:
        """
        Update study plan based on learning progress and new diagnostic results
        """
        # Get existing study plan
        learning_path = self._get_study_plan(path_id)
        if not learning_path:
            raise ValueError("Study plan not found")
        
        # Analyze progress data
        progress_analysis = self._analyze_learning_progress(learning_path, progress_data)
        
        # Adjust modules based on progress
        updated_modules = self._adjust_modules_based_on_progress(
            learning_path.modules, progress_analysis
        )
        
        # Update adaptive parameters
        learning_path.adaptive_parameters = self._update_adaptive_parameters(
            learning_path.adaptive_parameters, progress_analysis
        )
        
        # Recalculate timeline if needed
        if progress_analysis["pace_deviation"] > 0.3:  # Significant deviation
            learning_path = self._recalculate_timeline(learning_path, progress_analysis)
        
        learning_path.modules = updated_modules
        learning_path.last_updated = datetime.utcnow()
        
        # Update stored plan
        self._update_stored_study_plan(learning_path)
        
        self.logger.info(f"Updated study plan {path_id} based on progress")
        return learning_path

    def generate_daily_study_schedule(self, path_id: str, 
                                    available_hours_per_day: float = 2.0,
                                    preferred_study_times: List[str] = None) -> Dict[str, Any]:
        """
        Generate a detailed daily study schedule from the study plan
        """
        learning_path = self._get_study_plan(path_id)
        if not learning_path:
            raise ValueError("Study plan not found")
        
        # Calculate daily distribution
        total_hours = learning_path.total_estimated_hours
        estimated_days = int(total_hours / available_hours_per_day)
        
        # Generate daily schedule
        daily_schedule = []
        current_date = datetime.now().date()
        
        for day in range(estimated_days):
            study_date = current_date + timedelta(days=day)
            
            # Select modules for this day
            daily_modules = self._select_modules_for_day(
                learning_path.modules, day, available_hours_per_day
            )
            
            daily_schedule.append({
                "date": study_date.isoformat(),
                "day_number": day + 1,
                "total_hours": available_hours_per_day,
                "modules": daily_modules,
                "focus_areas": self._identify_daily_focus_areas(daily_modules),
                "gamification_goals": self._set_daily_gamification_goals(daily_modules),
                "adaptive_adjustments": self._get_daily_adaptive_adjustments(learning_path, day)
            })
        
        return {
            "schedule_id": f"{path_id}_daily_schedule",
            "total_days": estimated_days,
            "average_hours_per_day": available_hours_per_day,
            "daily_schedule": daily_schedule,
            "weekly_milestones": self._generate_weekly_milestones(daily_schedule),
            "completion_date": (current_date + timedelta(days=estimated_days)).isoformat()
        }

    def create_diagnostic_remediation_plan(self, diagnostic_test_id: str,
                                         specific_topics: List[str] = None) -> Dict[str, Any]:
        """
        Create a focused remediation plan for specific diagnostic weaknesses
        """
        test = self.db.query(DiagnosticTest).filter(DiagnosticTest.id == diagnostic_test_id).first()
        if not test:
            raise ValueError("Diagnostic test not found")
        
        # Analyze specific weaknesses
        weakness_analysis = self._analyze_specific_weaknesses(test, specific_topics)
        
        # Create targeted modules
        remediation_modules = []
        for weakness in weakness_analysis["critical_weaknesses"]:
            module = self._create_remediation_module(weakness, test.subject_id)
            remediation_modules.append(module)
        
        # Create quick-win modules for motivation
        for strength in weakness_analysis["near_strengths"][:2]:  # Top 2 near-strengths
            module = self._create_reinforcement_module(strength, test.subject_id)
            remediation_modules.append(module)
        
        # Calculate timeline
        total_hours = sum(module.estimated_hours for module in remediation_modules)
        estimated_weeks = math.ceil(total_hours / 10)  # Assuming 10 hours per week
        
        return {
            "plan_id": f"remediation_{diagnostic_test_id}",
            "user_id": str(test.user_id),
            "subject_id": str(test.subject_id),
            "focus_type": "remediation",
            "modules": [asdict(module) for module in remediation_modules],
            "total_estimated_hours": total_hours,
            "estimated_weeks": estimated_weeks,
            "success_criteria": {
                "target_improvement": 15,  # 15 point improvement
                "mastery_threshold": 70,   # 70% mastery in weak areas
                "consistency_target": 0.8  # 80% consistency across topics
            },
            "progress_checkpoints": self._create_remediation_checkpoints(remediation_modules)
        }

    def integrate_with_existing_study_plan(self, user_id: str, diagnostic_test_id: str,
                                         existing_plan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Integrate diagnostic results with an existing study plan
        """
        test = self.db.query(DiagnosticTest).filter(DiagnosticTest.id == diagnostic_test_id).first()
        if not test:
            raise ValueError("Diagnostic test not found")
        
        # Get existing plan or create new one
        if existing_plan_id:
            existing_path = self._get_study_plan(existing_plan_id)
            if not existing_path:
                raise ValueError("Existing study plan not found")
        else:
            # Look for most recent study plan for this subject
            existing_path = self._find_recent_study_plan(user_id, test.subject_id)
        
        # Analyze diagnostic insights
        diagnostic_insights = self._extract_diagnostic_insights(test)
        
        if existing_path:
            # Modify existing plan
            integration_result = self._modify_existing_plan(existing_path, diagnostic_insights)
            integration_type = "modification"
        else:
            # Create new plan
            integration_result = self.generate_study_plan_from_diagnostic(diagnostic_test_id)
            integration_type = "creation"
        
        return {
            "integration_type": integration_type,
            "study_plan": asdict(integration_result) if hasattr(integration_result, '__dict__') else integration_result,
            "diagnostic_insights": diagnostic_insights,
            "integration_summary": self._summarize_integration_changes(
                integration_type, diagnostic_insights, integration_result
            ),
            "recommended_next_steps": self._generate_integration_next_steps(
                diagnostic_insights, integration_result
            )
        }

    def calculate_study_plan_effectiveness(self, path_id: str) -> Dict[str, Any]:
        """
        Calculate the effectiveness of a study plan based on progress and outcomes
        """
        learning_path = self._get_study_plan(path_id)
        if not learning_path:
            raise ValueError("Study plan not found")
        
        # Get progress data (would come from user progress tracking)
        progress_data = self._get_study_plan_progress(path_id)
        
        # Calculate effectiveness metrics
        effectiveness_metrics = {
            "completion_rate": progress_data.get("completion_percentage", 0),
            "pace_adherence": progress_data.get("pace_score", 0),
            "learning_efficiency": self._calculate_learning_efficiency(learning_path, progress_data),
            "objective_achievement": self._assess_objective_achievement(learning_path, progress_data),
            "user_engagement": progress_data.get("engagement_score", 0),
            "predicted_success": self._predict_plan_success(learning_path, progress_data)
        }
        
        # Generate effectiveness insights
        insights = self._generate_effectiveness_insights(effectiveness_metrics)
        
        # Recommendations for improvement
        recommendations = self._generate_plan_improvement_recommendations(
            learning_path, effectiveness_metrics
        )
        
        return {
            "plan_id": path_id,
            "effectiveness_score": sum(effectiveness_metrics.values()) / len(effectiveness_metrics),
            "metrics": effectiveness_metrics,
            "insights": insights,
            "recommendations": recommendations,
            "benchmark_comparison": self._compare_to_benchmarks(effectiveness_metrics)
        }

    # Private helper methods
    
    def _analyze_diagnostic_results(self, test: DiagnosticTest) -> Dict[str, Any]:
        """Analyze diagnostic test results for study plan generation"""
        # Get test answers for detailed analysis
        answers = self.db.query(DiagnosticTestAnswer).filter(
            DiagnosticTestAnswer.diagnostic_test_id == test.id
        ).all()
        
        # Analyze by topic
        topic_analysis = defaultdict(lambda: {"correct": 0, "total": 0, "avg_time": 0})
        
        for answer in answers:
            topic_id = str(answer.topic_id) if answer.topic_id else "general"
            topic_analysis[topic_id]["total"] += 1
            topic_analysis[topic_id]["avg_time"] += answer.response_time_ms or 0
            if answer.is_correct:
                topic_analysis[topic_id]["correct"] += 1
        
        # Calculate topic scores
        topic_scores = {}
        for topic_id, data in topic_analysis.items():
            topic_scores[topic_id] = {
                "accuracy": data["correct"] / data["total"] if data["total"] > 0 else 0,
                "avg_time": data["avg_time"] / data["total"] if data["total"] > 0 else 0,
                "mastery_level": self._calculate_topic_mastery_level(
                    data["correct"] / data["total"] if data["total"] > 0 else 0
                )
            }
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for topic_id, scores in topic_scores.items():
            topic = self.db.query(Topic).filter(Topic.id == topic_id).first()
            topic_name = topic.name if topic else "General"
            
            if scores["accuracy"] >= 0.8:
                strengths.append({
                    "topic": topic_name,
                    "accuracy": scores["accuracy"],
                    "status": "mastered"
                })
            elif scores["accuracy"] < 0.5:
                weaknesses.append({
                    "topic": topic_name,
                    "accuracy": scores["accuracy"],
                    "priority": "high" if scores["accuracy"] < 0.3 else "medium",
                    "estimated_hours": self._estimate_topic_study_hours(scores["accuracy"])
                })
        
        return {
            "overall_score": test.score_percentage,
            "current_rank": self._calculate_current_rank(test.score_percentage),
            "topic_scores": topic_scores,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "learning_style_indicators": self._infer_learning_style(answers),
            "efficiency_metrics": self._calculate_efficiency_metrics(test, answers)
        }

    def _determine_optimal_target_rank(self, current_score: float, 
                                     analysis: Dict[str, Any]) -> str:
        """Determine optimal target rank based on current performance"""
        current_rank = analysis["current_rank"]
        
        # Suggest next achievable rank based on weaknesses
        major_weaknesses = len([w for w in analysis["weaknesses"] if w["priority"] == "high"])
        
        rank_progression = {"E": "D", "D": "C", "C": "B", "B": "A", "A": "S"}
        
        if major_weaknesses <= 2 and current_score >= 60:
            # Can aim for rank beyond next
            next_rank = rank_progression.get(current_rank, "S")
            return rank_progression.get(next_rank, "S")
        else:
            # Conservative target - next rank
            return rank_progression.get(current_rank, "S")

    def _generate_learning_modules(self, analysis: Dict[str, Any], 
                                 target_rank: str, subject_id: str) -> List[StudyPlanModule]:
        """Generate learning modules based on analysis"""
        modules = []
        
        # Create modules for each weakness
        for weakness in analysis["weaknesses"]:
            module_type = self._determine_module_type(weakness)
            template = self.MODULE_TEMPLATES[module_type]
            
            module = StudyPlanModule(
                module_id=f"module_{weakness['topic'].lower().replace(' ', '_')}_{module_type}",
                title=template["title_template"].format(weakness["topic"]),
                description=template["description_template"].format(weakness["topic"]),
                priority=weakness["priority"],
                estimated_hours=weakness["estimated_hours"],
                difficulty_level=template["difficulty_level"],
                topics=[weakness["topic"]],
                learning_objectives=self._generate_learning_objectives(weakness, module_type),
                resources=self._get_topic_resources(weakness["topic"], subject_id),
                prerequisites=self._identify_prerequisites(weakness["topic"]),
                success_criteria=self._define_success_criteria(weakness, target_rank),
                gamification_rewards=self._calculate_module_rewards(weakness["estimated_hours"])
            )
            modules.append(module)
        
        # Add reinforcement modules for near-strengths
        near_strengths = [s for s in analysis["strengths"] if 0.7 <= s["accuracy"] < 0.8]
        for strength in near_strengths:
            module = self._create_reinforcement_module(strength, subject_id)
            modules.append(module)
        
        # Add test preparation module
        test_prep_module = self._create_test_preparation_module(target_rank, subject_id)
        modules.append(test_prep_module)
        
        return modules

    def _create_adaptive_learning_path(self, test: DiagnosticTest, 
                                     modules: List[StudyPlanModule],
                                     target_rank: str,
                                     time_constraint_weeks: Optional[int]) -> AdaptiveLearningPath:
        """Create adaptive learning path from modules"""
        total_hours = sum(module.estimated_hours for module in modules)
        
        # Adjust for time constraints
        if time_constraint_weeks:
            max_hours = time_constraint_weeks * 15  # 15 hours per week max
            if total_hours > max_hours:
                modules = self._prioritize_modules_for_time_constraint(modules, max_hours)
                total_hours = sum(module.estimated_hours for module in modules)
        
        target_score = self.RANK_TARGET_SCORES[target_rank]["target"]
        
        return AdaptiveLearningPath(
            path_id=f"path_{test.user_id}_{test.subject_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_id=str(test.user_id),
            subject_id=str(test.subject_id),
            diagnostic_test_id=str(test.id),
            total_estimated_hours=total_hours,
            target_score=target_score,
            target_rank=target_rank,
            modules=modules,
            milestones=[],  # Will be populated by _generate_learning_milestones
            adaptive_parameters={},  # Will be populated by _set_adaptive_parameters
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )

    def _generate_learning_milestones(self, path: AdaptiveLearningPath, 
                                    analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate learning milestones for the study plan"""
        milestones = []
        
        # Weekly milestones
        weeks = math.ceil(path.total_estimated_hours / 15)  # 15 hours per week
        for week in range(1, weeks + 1):
            milestone = {
                "milestone_id": f"week_{week}",
                "week_number": week,
                "title": f"Week {week} Checkpoint",
                "target_completion": week / weeks,
                "success_criteria": {
                    "modules_completed": math.ceil(len(path.modules) * week / weeks),
                    "practice_score_target": analysis["overall_score"] + (week * 2),
                    "consistency_target": 0.7
                },
                "gamification_rewards": {
                    "xp": 100 * week,
                    "badge": f"Week {week} Warrior",
                    "crystals": 25 * week
                }
            }
            milestones.append(milestone)
        
        # Final milestone
        final_milestone = {
            "milestone_id": "final_assessment",
            "week_number": weeks + 1,
            "title": "Final Assessment Ready",
            "target_completion": 1.0,
            "success_criteria": {
                "target_score_achieved": path.target_score,
                "all_modules_completed": True,
                "consistency_maintained": True
            },
            "gamification_rewards": {
                "xp": 500,
                "badge": f"Study Plan Champion - {path.target_rank} Rank",
                "crystals": 100,
                "special_item": "Study Master Certificate"
            }
        }
        milestones.append(final_milestone)
        
        return milestones

    def _set_adaptive_parameters(self, analysis: Dict[str, Any], target_rank: str) -> Dict[str, Any]:
        """Set adaptive parameters for ongoing plan adjustment"""
        return {
            "adaptation_enabled": True,
            "adaptation_frequency": "weekly",
            "performance_threshold": 0.1,  # 10% deviation triggers adaptation
            "learning_style": analysis.get("learning_style_indicators", "mixed"),
            "difficulty_preference": "progressive",
            "time_management_style": analysis.get("efficiency_metrics", {}).get("time_style", "steady"),
            "motivation_factors": ["gamification", "progress_tracking", "social_features"],
            "adjustment_sensitivity": 0.3,  # How quickly to adapt to performance changes
            "fallback_strategies": ["reduce_difficulty", "increase_practice", "add_support_materials"]
        }

    # Additional helper methods (simplified for brevity)
    
    def _calculate_current_rank(self, score: float) -> str:
        """Calculate current rank from score"""
        if score >= 90: return "S"
        elif score >= 80: return "A"
        elif score >= 65: return "B"
        elif score >= 50: return "C"
        elif score >= 35: return "D"
        else: return "E"

    def _calculate_topic_mastery_level(self, accuracy: float) -> str:
        """Calculate mastery level for a topic"""
        if accuracy >= 0.9: return "mastered"
        elif accuracy >= 0.7: return "proficient"
        elif accuracy >= 0.5: return "developing"
        else: return "needs_work"

    def _estimate_topic_study_hours(self, accuracy: float) -> int:
        """Estimate study hours needed for a topic based on current accuracy"""
        if accuracy < 0.3: return 12
        elif accuracy < 0.5: return 8
        elif accuracy < 0.7: return 6
        else: return 4

    def _determine_module_type(self, weakness: Dict[str, Any]) -> str:
        """Determine the type of module needed for a weakness"""
        if weakness["accuracy"] < 0.3:
            return "concept_review"
        elif weakness["accuracy"] < 0.5:
            return "skill_building"
        else:
            return "problem_solving"

    def _generate_learning_objectives(self, weakness: Dict[str, Any], module_type: str) -> List[str]:
        """Generate learning objectives for a module"""
        topic = weakness["topic"]
        if module_type == "concept_review":
            return [
                f"Understand fundamental concepts of {topic}",
                f"Identify key principles and formulas in {topic}",
                f"Apply basic {topic} concepts to simple problems"
            ]
        elif module_type == "skill_building":
            return [
                f"Develop problem-solving skills in {topic}",
                f"Practice intermediate {topic} techniques",
                f"Build fluency in {topic} calculations"
            ]
        else:  # problem_solving
            return [
                f"Solve complex {topic} problems efficiently",
                f"Apply advanced {topic} strategies",
                f"Analyze and critique {topic} solutions"
            ]

    def _get_topic_resources(self, topic: str, subject_id: str) -> List[Dict[str, Any]]:
        """Get learning resources for a topic"""
        # This would query actual resource database
        return [
            {"type": "video", "title": f"{topic} Fundamentals", "duration_minutes": 15},
            {"type": "practice", "title": f"{topic} Practice Problems", "question_count": 20},
            {"type": "reading", "title": f"{topic} Study Guide", "page_count": 8}
        ]

    def _identify_prerequisites(self, topic: str) -> List[str]:
        """Identify prerequisites for a topic"""
        # Simplified mapping - would be more sophisticated in practice
        prerequisite_map = {
            "Algebra": ["Basic Arithmetic"],
            "Geometry": ["Basic Shapes", "Measurements"],
            "Calculus": ["Algebra", "Functions"]
        }
        return prerequisite_map.get(topic, [])

    def _define_success_criteria(self, weakness: Dict[str, Any], target_rank: str) -> Dict[str, Any]:
        """Define success criteria for a module"""
        target_accuracy = 0.8 if target_rank in ["A", "S"] else 0.7
        
        return {
            "accuracy_target": target_accuracy,
            "consistency_target": 0.75,
            "speed_target": "improve_by_20_percent",
            "practice_completion": 1.0,
            "assessment_score": target_accuracy * 100
        }

    def _calculate_module_rewards(self, estimated_hours: int) -> Dict[str, Any]:
        """Calculate gamification rewards for a module"""
        return {
            "xp": estimated_hours * 50,
            "crystals": estimated_hours * 5,
            "orbs": estimated_hours * 10,
            "badge": f"{estimated_hours}h Study Hero" if estimated_hours >= 10 else "Study Warrior"
        }

    def _create_reinforcement_module(self, strength: Dict[str, Any], subject_id: str) -> StudyPlanModule:
        """Create a reinforcement module for a near-strength"""
        return StudyPlanModule(
            module_id=f"reinforcement_{strength['topic'].lower().replace(' ', '_')}",
            title=f"Master {strength['topic']}",
            description=f"Achieve full mastery in {strength['topic']}",
            priority="medium",
            estimated_hours=4,
            difficulty_level="intermediate",
            topics=[strength["topic"]],
            learning_objectives=[f"Achieve 90%+ accuracy in {strength['topic']}"],
            resources=self._get_topic_resources(strength["topic"], subject_id),
            prerequisites=[],
            success_criteria={"accuracy_target": 0.9, "consistency_target": 0.85},
            gamification_rewards={"xp": 200, "crystals": 20, "badge": f"{strength['topic']} Master"}
        )

    def _create_test_preparation_module(self, target_rank: str, subject_id: str) -> StudyPlanModule:
        """Create a test preparation module"""
        return StudyPlanModule(
            module_id="test_preparation",
            title="ICFES Test Preparation",
            description="Comprehensive test-taking strategies and practice",
            priority="high",
            estimated_hours=8,
            difficulty_level="intermediate",
            topics=["Test Strategy", "Time Management", "Practice Tests"],
            learning_objectives=[
                "Master ICFES test format and structure",
                "Develop effective time management strategies",
                "Practice with full-length mock exams"
            ],
            resources=[
                {"type": "mock_test", "title": "Full Practice Exam", "duration_minutes": 180},
                {"type": "strategy", "title": "Test-Taking Strategies", "duration_minutes": 30}
            ],
            prerequisites=[],
            success_criteria={
                "mock_test_score": self.RANK_TARGET_SCORES[target_rank]["target"],
                "time_management": 0.9
            },
            gamification_rewards={
                "xp": 400,
                "crystals": 40,
                "badge": "Test Master",
                "special_item": "Strategic Edge"
            }
        )

    # Placeholder methods for complex operations
    def _store_study_plan(self, learning_path: AdaptiveLearningPath):
        """Store study plan in database"""
        # Would integrate with StudyPlan model
        self.logger.info(f"Stored study plan {learning_path.path_id}")

    def _get_study_plan(self, path_id: str) -> Optional[AdaptiveLearningPath]:
        """Get study plan from database"""
        # Would query from database
        return None

    def _update_stored_study_plan(self, learning_path: AdaptiveLearningPath):
        """Update stored study plan"""
        self.logger.info(f"Updated study plan {learning_path.path_id}")

    # Additional placeholder methods for full functionality...
    def _infer_learning_style(self, answers: List[DiagnosticTestAnswer]) -> str:
        """Infer learning style from response patterns"""
        return "mixed"

    def _calculate_efficiency_metrics(self, test: DiagnosticTest, answers: List[DiagnosticTestAnswer]) -> Dict[str, Any]:
        """Calculate learning efficiency metrics"""
        return {"time_style": "steady", "accuracy_pattern": "consistent"}

    def _prioritize_modules_for_time_constraint(self, modules: List[StudyPlanModule], max_hours: int) -> List[StudyPlanModule]:
        """Prioritize modules when time is constrained"""
        # Sort by priority and select within time limit
        sorted_modules = sorted(modules, key=lambda m: {"critical": 0, "high": 1, "medium": 2, "low": 3}[m.priority])
        
        selected_modules = []
        total_hours = 0
        
        for module in sorted_modules:
            if total_hours + module.estimated_hours <= max_hours:
                selected_modules.append(module)
                total_hours += module.estimated_hours
            else:
                # Try to fit a shorter version
                remaining_hours = max_hours - total_hours
                if remaining_hours >= 4:  # Minimum viable module
                    shortened_module = module
                    shortened_module.estimated_hours = remaining_hours
                    selected_modules.append(shortened_module)
                    break
        
        return selected_modules

    # Additional methods would be implemented for full functionality...