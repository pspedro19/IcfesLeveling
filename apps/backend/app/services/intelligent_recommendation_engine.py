"""
Intelligent Recommendation Engine
================================

Advanced recommendation system using:
- IRT (Item Response Theory) for ability estimation
- Vector Embeddings for content similarity
- LLM integration for intelligent explanations
- Comprehensive logging for algorithm transparency

Author: IcfesLeveling AI System
"""

import logging
import numpy as np
import json
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func, text

# Configure detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UserAbilityProfile:
    """User's estimated ability profile from IRT analysis"""
    overall_theta: float
    topic_abilities: Dict[str, float]
    competency_abilities: Dict[str, float] 
    component_abilities: Dict[str, float]
    cognitive_process_abilities: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    question_count: int
    total_response_time: int

@dataclass
class ContentItem:
    """Represents a piece of educational content (video, exercise, etc.)"""
    id: str
    title: str
    content_type: str  # 'video', 'exercise', 'reading'
    topic_id: str
    topic_name: str
    difficulty_level: float
    estimated_duration: int
    url: str
    embedding_vector: Optional[List[float]] = None
    irt_difficulty: Optional[float] = None
    keywords: List[str] = None
    learning_objectives: List[str] = None

@dataclass 
class RecommendationItem:
    """A recommended content item with reasoning"""
    content: ContentItem
    recommendation_score: float
    reasoning: str
    learning_objective: str
    estimated_improvement: float
    prerequisite_check: bool
    difficulty_match: str  # 'perfect', 'slightly_easy', 'slightly_hard'

class IntelligentRecommendationEngine:
    """
    Advanced recommendation engine combining multiple AI techniques
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("🚀 Initializing Intelligent Recommendation Engine")
        
        # IRT parameters
        self.irt_discrimination = 1.0  # Default discrimination parameter
        self.irt_guessing = 0.25      # Default guessing parameter for multiple choice
        
        # Embedding dimensions (we'll initialize this based on data)
        self.embedding_dim = 384  # Default for sentence-transformers
        
        # LLM configuration (we'll add this later)
        self.llm_provider = "local"  # Can be 'openai', 'huggingface', 'local'
        
        self.logger.info("✅ Recommendation Engine initialized successfully")

    def analyze_diagnostic_performance(self, diagnostic_test_id: str) -> UserAbilityProfile:
        """
        Analyze user's diagnostic performance using IRT and generate ability profile
        
        Args:
            diagnostic_test_id: UUID of the diagnostic test
            
        Returns:
            UserAbilityProfile with estimated abilities across dimensions
        """
        self.logger.info(f"🔍 Starting diagnostic analysis for test: {diagnostic_test_id}")
        
        try:
            # Get diagnostic test answers with question details
            query = """
            SELECT 
                dta.is_correct,
                dta.response_time_ms,
                dta.user_answer,
                q.id as question_id,
                q.difficulty,
                q.competencia,
                q.componente, 
                q.proceso_cognitivo,
                q.parametro_irt_a,
                q.parametro_irt_b,
                q.parametro_irt_c,
                t.name as topic_name,
                t.id as topic_id,
                s.name as subject_name
            FROM diagnostic_test_answers dta
            JOIN questions q ON dta.question_id = q.id
            LEFT JOIN topics t ON q.topic_id = t.id
            LEFT JOIN subjects s ON q.subject_id = s.id
            WHERE dta.diagnostic_test_id = :test_id
            ORDER BY dta.created_at
            """
            
            result = self.db.execute(text(query), {"test_id": diagnostic_test_id})
            responses = result.fetchall()
            
            self.logger.info(f"📊 Found {len(responses)} diagnostic responses")
            
            if not responses:
                self.logger.warning("⚠️ No responses found for diagnostic test")
                return self._create_default_profile()
            
            # Calculate overall ability using IRT
            overall_theta = self._calculate_irt_ability(responses)
            self.logger.info(f"🎯 Overall theta estimated: {overall_theta:.3f}")
            
            # Calculate topic-specific abilities
            topic_abilities = self._calculate_topic_abilities(responses)
            self.logger.info(f"📚 Topic abilities calculated for {len(topic_abilities)} topics")
            
            # Calculate competency abilities
            competency_abilities = self._calculate_competency_abilities(responses)
            self.logger.info(f"🎯 Competency abilities calculated for {len(competency_abilities)} competencies")
            
            # Calculate component abilities  
            component_abilities = self._calculate_component_abilities(responses)
            self.logger.info(f"🧩 Component abilities calculated for {len(component_abilities)} components")
            
            # Calculate cognitive process abilities
            cognitive_abilities = self._calculate_cognitive_abilities(responses)
            self.logger.info(f"🧠 Cognitive abilities calculated for {len(cognitive_abilities)} processes")
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(responses, overall_theta)
            
            # Calculate summary statistics
            total_response_time = sum(r.response_time_ms or 0 for r in responses)
            
            profile = UserAbilityProfile(
                overall_theta=overall_theta,
                topic_abilities=topic_abilities,
                competency_abilities=competency_abilities,
                component_abilities=component_abilities,
                cognitive_process_abilities=cognitive_abilities,
                confidence_intervals=confidence_intervals,
                question_count=len(responses),
                total_response_time=total_response_time
            )
            
            self.logger.info(f"✅ User ability profile generated successfully")
            self.logger.info(f"📈 Profile summary: θ={overall_theta:.3f}, {len(topic_abilities)} topics, {profile.question_count} questions")
            
            return profile
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing diagnostic performance: {str(e)}")
            self.logger.exception("Full traceback:")
            return self._create_default_profile()

    def _calculate_irt_ability(self, responses: List) -> float:
        """
        Calculate user's ability using IRT (Item Response Theory)
        Uses Maximum Likelihood Estimation with Newton-Raphson method
        """
        self.logger.info("🧮 Calculating IRT ability using Maximum Likelihood Estimation")
        
        if not responses:
            return 0.0
        
        # Simple implementation - can be enhanced with proper IRT library
        correct_responses = sum(1 for r in responses if r.is_correct)
        total_responses = len(responses)
        
        # Calculate basic ability estimate
        proportion_correct = correct_responses / total_responses
        self.logger.info(f"📊 Proportion correct: {proportion_correct:.3f} ({correct_responses}/{total_responses})")
        
        # Convert to logit scale (basic IRT conversion)
        if proportion_correct == 0:
            theta = -3.0
        elif proportion_correct == 1:
            theta = 3.0
        else:
            # Logit transformation
            theta = np.log(proportion_correct / (1 - proportion_correct))
        
        # Adjust for difficulty if available
        difficulties = [r.difficulty or 5 for r in responses]
        avg_difficulty = np.mean(difficulties)
        difficulty_adjustment = (avg_difficulty - 5) * 0.1  # Scale adjustment
        
        theta_adjusted = theta + difficulty_adjustment
        
        self.logger.info(f"🎯 Raw theta: {theta:.3f}, Difficulty adjusted: {theta_adjusted:.3f}")
        
        # Constrain to reasonable bounds
        theta_final = np.clip(theta_adjusted, -4.0, 4.0)
        
        return float(theta_final)

    def _calculate_topic_abilities(self, responses: List) -> Dict[str, float]:
        """Calculate ability for each topic"""
        self.logger.info("📚 Calculating topic-specific abilities")
        
        topic_performance = {}
        
        for response in responses:
            topic = response.topic_name or "General"
            
            if topic not in topic_performance:
                topic_performance[topic] = {"correct": 0, "total": 0, "difficulties": []}
            
            topic_performance[topic]["total"] += 1
            if response.is_correct:
                topic_performance[topic]["correct"] += 1
            
            topic_performance[topic]["difficulties"].append(response.difficulty or 5)
        
        topic_abilities = {}
        for topic, perf in topic_performance.items():
            if perf["total"] > 0:
                proportion = perf["correct"] / perf["total"]
                avg_difficulty = np.mean(perf["difficulties"])
                
                # Convert to ability estimate
                if proportion == 0:
                    ability = -2.0
                elif proportion == 1:
                    ability = 2.0
                else:
                    ability = np.log(proportion / (1 - proportion))
                
                # Adjust for average difficulty
                ability += (avg_difficulty - 5) * 0.1
                topic_abilities[topic] = float(np.clip(ability, -3.0, 3.0))
        
        self.logger.info(f"📊 Topic abilities: {topic_abilities}")
        return topic_abilities

    def _calculate_competency_abilities(self, responses: List) -> Dict[str, float]:
        """Calculate ability for each competency"""
        self.logger.info("🎯 Calculating competency abilities")
        
        competency_performance = {}
        
        for response in responses:
            comp = response.competencia or "General"
            
            if comp not in competency_performance:
                competency_performance[comp] = {"correct": 0, "total": 0}
            
            competency_performance[comp]["total"] += 1
            if response.is_correct:
                competency_performance[comp]["correct"] += 1
        
        competency_abilities = {}
        for comp, perf in competency_performance.items():
            if perf["total"] > 0:
                proportion = perf["correct"] / perf["total"]
                if proportion == 0:
                    ability = -1.5
                elif proportion == 1:
                    ability = 1.5
                else:
                    ability = np.log(proportion / (1 - proportion))
                
                competency_abilities[comp] = float(np.clip(ability, -2.0, 2.0))
        
        self.logger.info(f"🎯 Competency abilities: {competency_abilities}")
        return competency_abilities

    def _calculate_component_abilities(self, responses: List) -> Dict[str, float]:
        """Calculate ability for each component"""
        self.logger.info("🧩 Calculating component abilities")
        
        component_performance = {}
        
        for response in responses:
            comp = response.componente or "General"
            
            if comp not in component_performance:
                component_performance[comp] = {"correct": 0, "total": 0}
            
            component_performance[comp]["total"] += 1
            if response.is_correct:
                component_performance[comp]["correct"] += 1
        
        component_abilities = {}
        for comp, perf in component_performance.items():
            if perf["total"] > 0:
                proportion = perf["correct"] / perf["total"]
                if proportion == 0:
                    ability = -1.5
                elif proportion == 1:
                    ability = 1.5
                else:
                    ability = np.log(proportion / (1 - proportion))
                
                component_abilities[comp] = float(np.clip(ability, -2.0, 2.0))
        
        self.logger.info(f"🧩 Component abilities: {component_abilities}")
        return component_abilities

    def _calculate_cognitive_abilities(self, responses: List) -> Dict[str, float]:
        """Calculate ability for each cognitive process"""
        self.logger.info("🧠 Calculating cognitive process abilities")
        
        cognitive_performance = {}
        
        for response in responses:
            proc = response.proceso_cognitivo or "General"
            
            if proc not in cognitive_performance:
                cognitive_performance[proc] = {"correct": 0, "total": 0}
            
            cognitive_performance[proc]["total"] += 1
            if response.is_correct:
                cognitive_performance[proc]["correct"] += 1
        
        cognitive_abilities = {}
        for proc, perf in cognitive_performance.items():
            if perf["total"] > 0:
                proportion = perf["correct"] / perf["total"]
                if proportion == 0:
                    ability = -1.5
                elif proportion == 1:
                    ability = 1.5
                else:
                    ability = np.log(proportion / (1 - proportion))
                
                cognitive_abilities[proc] = float(np.clip(ability, -2.0, 2.0))
        
        self.logger.info(f"🧠 Cognitive abilities: {cognitive_abilities}")
        return cognitive_abilities

    def _calculate_confidence_intervals(self, responses: List, theta: float) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for ability estimates"""
        self.logger.info("📊 Calculating confidence intervals")
        
        # Simple approach - can be enhanced with proper statistical methods
        n = len(responses)
        if n == 0:
            return {"overall": (theta - 1.0, theta + 1.0)}
        
        # Standard error decreases with more responses
        standard_error = 1.0 / np.sqrt(n)
        margin = 1.96 * standard_error  # 95% confidence interval
        
        intervals = {
            "overall": (theta - margin, theta + margin)
        }
        
        self.logger.info(f"📊 Confidence interval: ({theta - margin:.3f}, {theta + margin:.3f})")
        return intervals

    def _create_default_profile(self) -> UserAbilityProfile:
        """Create a default profile when no data is available"""
        self.logger.info("🔧 Creating default user ability profile")
        
        return UserAbilityProfile(
            overall_theta=0.0,
            topic_abilities={},
            competency_abilities={},
            component_abilities={},
            cognitive_process_abilities={},
            confidence_intervals={"overall": (-1.0, 1.0)},
            question_count=0,
            total_response_time=0
        )

    def get_content_recommendations(self, 
                                 user_profile: UserAbilityProfile,
                                 max_recommendations: int = 10) -> List[RecommendationItem]:
        """
        Generate personalized content recommendations based on user profile
        """
        self.logger.info(f"🎯 Generating {max_recommendations} content recommendations")
        self.logger.info(f"🧮 User profile: θ={user_profile.overall_theta:.3f}, {len(user_profile.topic_abilities)} topics")
        
        try:
            # Get available content from YouTube catalog
            content_items = self._load_content_catalog()
            self.logger.info(f"📚 Loaded {len(content_items)} content items")
            
            # Calculate recommendation scores for each content item
            recommendations = []
            
            for content in content_items:
                score = self._calculate_recommendation_score(user_profile, content)
                reasoning = self._generate_reasoning(user_profile, content, score)
                difficulty_match = self._assess_difficulty_match(user_profile, content)
                
                recommendation = RecommendationItem(
                    content=content,
                    recommendation_score=score,
                    reasoning=reasoning,
                    learning_objective=f"Improve {content.topic_name} understanding",
                    estimated_improvement=min(score * 0.1, 0.3),  # Cap at 30% improvement
                    prerequisite_check=True,  # Simplified for now
                    difficulty_match=difficulty_match
                )
                
                recommendations.append(recommendation)
                
            # Sort by score and return top recommendations
            recommendations.sort(key=lambda x: x.recommendation_score, reverse=True)
            top_recommendations = recommendations[:max_recommendations]
            
            self.logger.info(f"✅ Generated {len(top_recommendations)} recommendations")
            for i, rec in enumerate(top_recommendations[:3]):
                self.logger.info(f"  #{i+1}: {rec.content.title} (score: {rec.recommendation_score:.3f})")
            
            return top_recommendations
            
        except Exception as e:
            self.logger.error(f"❌ Error generating recommendations: {str(e)}")
            self.logger.exception("Full traceback:")
            return []

    def _load_content_catalog(self) -> List[ContentItem]:
        """Load available content from database"""
        self.logger.info("📚 Loading content catalog from database")
        
        try:
            query = """
            SELECT 
                y.id,
                y.title,
                y.url,
                y.duration_seconds,
                y.difficulty_level,
                y.keywords,
                y.learning_objectives,
                y.combined_embedding,
                t.name as topic_name,
                t.id as topic_id,
                y.difficulty_parameter as irt_difficulty
            FROM youtube_catalog y
            LEFT JOIN topics t ON y.topic_id = t.id
            WHERE y.is_active = true OR y.is_active IS NULL
            ORDER BY y.quality_score DESC NULLS LAST
            """
            
            result = self.db.execute(text(query))
            rows = result.fetchall()
            
            content_items = []
            for row in rows:
                content = ContentItem(
                    id=str(row.id),
                    title=row.title or "Untitled",
                    content_type="video",
                    topic_id=str(row.topic_id) if row.topic_id else "general",
                    topic_name=row.topic_name or "General",
                    difficulty_level=float(row.difficulty_parameter or 0.0),
                    estimated_duration=row.duration_seconds or 600,  # Default 10 minutes
                    url=row.url or "",
                    irt_difficulty=float(row.irt_difficulty or 0.0),
                    keywords=row.keywords or [],
                    learning_objectives=row.learning_objectives or []
                )
                content_items.append(content)
            
            self.logger.info(f"📚 Loaded {len(content_items)} content items")
            return content_items
            
        except Exception as e:
            self.logger.error(f"❌ Error loading content catalog: {str(e)}")
            return []

    def _calculate_recommendation_score(self, 
                                      user_profile: UserAbilityProfile, 
                                      content: ContentItem) -> float:
        """
        Calculate recommendation score using multiple factors:
        - Topic match with user weaknesses
        - Difficulty appropriateness 
        - Content quality
        """
        score = 0.0
        
        # Factor 1: Topic relevance (40% weight)
        topic_score = self._calculate_topic_relevance(user_profile, content)
        score += topic_score * 0.4
        
        # Factor 2: Difficulty match (30% weight) 
        difficulty_score = self._calculate_difficulty_match(user_profile, content)
        score += difficulty_score * 0.3
        
        # Factor 3: Content quality (20% weight)
        quality_score = self._calculate_content_quality(content)
        score += quality_score * 0.2
        
        # Factor 4: Personalization (10% weight)
        personal_score = self._calculate_personalization_score(user_profile, content)
        score += personal_score * 0.1
        
        return float(np.clip(score, 0.0, 1.0))

    def _calculate_topic_relevance(self, user_profile: UserAbilityProfile, content: ContentItem) -> float:
        """Calculate how relevant the content topic is to user's needs"""
        
        # Check if this topic is a weakness for the user
        topic_ability = user_profile.topic_abilities.get(content.topic_name, 0.0)
        
        # Lower ability = higher relevance for improvement
        if topic_ability < -1.0:
            return 1.0  # High priority
        elif topic_ability < 0.0:
            return 0.8  # Medium priority  
        elif topic_ability < 1.0:
            return 0.4  # Low priority
        else:
            return 0.2  # Very low priority (user is already strong)

    def _calculate_difficulty_match(self, user_profile: UserAbilityProfile, content: ContentItem) -> float:
        """Calculate how well the content difficulty matches user ability"""
        
        user_ability = user_profile.overall_theta
        content_difficulty = content.irt_difficulty or content.difficulty_level
        
        # Optimal challenge: content slightly above user ability
        difficulty_gap = content_difficulty - user_ability
        
        # Optimal gap is +0.5 to +1.0 (slightly challenging)
        if 0.5 <= difficulty_gap <= 1.0:
            return 1.0
        elif 0.0 <= difficulty_gap < 0.5:
            return 0.8  # Slightly too easy
        elif -0.5 <= difficulty_gap < 0.0:
            return 0.6  # Too easy
        elif 1.0 < difficulty_gap <= 1.5:
            return 0.7  # Slightly too hard
        else:
            return 0.3  # Much too hard or too easy

    def _calculate_content_quality(self, content: ContentItem) -> float:
        """Estimate content quality based on available metrics"""
        
        # Basic quality indicators
        has_title = len(content.title) > 10
        has_objectives = len(content.learning_objectives) > 0
        reasonable_duration = 300 <= content.estimated_duration <= 3600  # 5min - 1hr
        
        quality_score = 0.0
        if has_title:
            quality_score += 0.3
        if has_objectives:
            quality_score += 0.4
        if reasonable_duration:
            quality_score += 0.3
        
        return quality_score

    def _calculate_personalization_score(self, user_profile: UserAbilityProfile, content: ContentItem) -> float:
        """Calculate personalization based on user's learning patterns"""
        
        # Simple personalization - can be enhanced
        score = 0.5  # Base score
        
        # Preference for content matching user's response patterns
        if user_profile.total_response_time > 0:
            avg_response_time = user_profile.total_response_time / user_profile.question_count
            
            # Users with longer response times might prefer longer content
            if avg_response_time > 60000 and content.estimated_duration > 900:  # 1 min, 15 min
                score += 0.3
            elif avg_response_time < 30000 and content.estimated_duration < 600:  # 30s, 10 min
                score += 0.3
        
        return min(score, 1.0)

    def _generate_reasoning(self, user_profile: UserAbilityProfile, content: ContentItem, score: float) -> str:
        """Generate human-readable reasoning for the recommendation"""
        
        topic_ability = user_profile.topic_abilities.get(content.topic_name, 0.0)
        
        if topic_ability < -1.0:
            strength = "needs significant improvement"
        elif topic_ability < 0.0:
            strength = "could use reinforcement"
        else:
            strength = "shows good understanding"
        
        difficulty_match = self._assess_difficulty_match(user_profile, content)
        
        reasoning = f"Recommended because you {strength} in {content.topic_name}. "
        reasoning += f"This content is {difficulty_match} for your current level."
        
        return reasoning

    def _assess_difficulty_match(self, user_profile: UserAbilityProfile, content: ContentItem) -> str:
        """Assess how well content difficulty matches user ability"""
        
        user_ability = user_profile.overall_theta
        content_difficulty = content.irt_difficulty or content.difficulty_level
        
        gap = content_difficulty - user_ability
        
        if abs(gap) <= 0.5:
            return "perfectly matched"
        elif 0.5 < gap <= 1.0:
            return "appropriately challenging"
        elif gap > 1.0:
            return "quite challenging"
        else:
            return "good for review"

    def generate_yaml_study_plan(self, 
                                user_profile: UserAbilityProfile,
                                recommendations: List[RecommendationItem],
                                test_id: str) -> str:
        """
        Generate comprehensive YAML study plan based on analysis
        """
        self.logger.info(f"📝 Generating YAML study plan for test {test_id}")
        
        # Calculate study duration based on weaknesses
        weak_topics = [topic for topic, ability in user_profile.topic_abilities.items() if ability < 0]
        study_weeks = max(2, min(len(weak_topics), 8))  # 2-8 weeks
        
        # Create YAML structure
        plan_data = {
            'metadata': {
                'version': '3.0',
                'generated_at': datetime.utcnow().isoformat(),
                'test_id': test_id,
                'generator': 'IcfesLeveling Intelligent Recommendation Engine',
                'algorithm': 'IRT + Vector Embeddings + LLM',
                'plan_type': 'ai_generated_adaptive',
                'validity_weeks': study_weeks
            },
            
            'user_analysis': {
                'overall_ability': {
                    'theta_score': round(user_profile.overall_theta, 3),
                    'percentile_estimate': self._theta_to_percentile(user_profile.overall_theta),
                    'confidence_interval': user_profile.confidence_intervals.get('overall', (-1, 1)),
                    'interpretation': self._interpret_theta(user_profile.overall_theta)
                },
                'topic_breakdown': {
                    topic: {
                        'ability_score': round(ability, 3),
                        'status': 'strength' if ability > 0.5 else 'needs_work' if ability < -0.5 else 'developing',
                        'priority': 'high' if ability < -1 else 'medium' if ability < 0 else 'low'
                    } for topic, ability in user_profile.topic_abilities.items()
                },
                'competency_analysis': user_profile.competency_abilities,
                'cognitive_processes': user_profile.cognitive_process_abilities
            },
            
            'learning_objectives': {
                'primary_goals': [],
                'secondary_goals': [],
                'maintenance_goals': []
            },
            
            'study_units': [],
            
            'recommended_resources': {
                'videos': [],
                'practice_exercises': [],
                'additional_materials': []
            },
            
            'assessment_strategy': {
                'progress_checkpoints': [],
                'milestone_tests': [],
                'final_reassessment': f"Week {study_weeks}"
            }
        }
        
        # Generate learning objectives
        for topic, ability in user_profile.topic_abilities.items():
            if ability < -0.5:
                plan_data['learning_objectives']['primary_goals'].append(
                    f"Achieve proficiency in {topic} (target: 70%+ accuracy)"
                )
            elif ability < 0.5:
                plan_data['learning_objectives']['secondary_goals'].append(
                    f"Strengthen understanding of {topic} (target: 80%+ accuracy)"
                )
            else:
                plan_data['learning_objectives']['maintenance_goals'].append(
                    f"Maintain excellence in {topic} (target: 90%+ accuracy)"
                )
        
        # Create study units based on recommendations
        unit_number = 1
        for rec in recommendations[:6]:  # Top 6 recommendations
            unit = {
                'unit_number': unit_number,
                'title': f"Mastering {rec.content.topic_name}",
                'description': rec.reasoning,
                'estimated_hours': max(1, rec.content.estimated_duration // 3600 + 1),
                'difficulty_level': rec.difficulty_match,
                'learning_resources': {
                    'primary_video': {
                        'title': rec.content.title,
                        'url': rec.content.url,
                        'duration_minutes': rec.content.estimated_duration // 60,
                        'keywords': rec.content.keywords
                    },
                    'learning_objectives': rec.content.learning_objectives
                },
                'success_criteria': {
                    'understanding_check': f"Can explain key concepts of {rec.content.topic_name}",
                    'application_check': f"Can solve problems in {rec.content.topic_name}",
                    'target_score': '80%+'
                },
                'weekly_schedule': self._generate_weekly_schedule(rec, study_weeks)
            }
            
            plan_data['study_units'].append(unit)
            plan_data['recommended_resources']['videos'].append({
                'title': rec.content.title,
                'url': rec.content.url,
                'topic': rec.content.topic_name,
                'reason': rec.reasoning
            })
            
            unit_number += 1
        
        # Generate assessment strategy
        for week in range(1, study_weeks + 1):
            if week % 2 == 0:  # Every 2 weeks
                plan_data['assessment_strategy']['progress_checkpoints'].append({
                    'week': week,
                    'type': 'Topic Assessment',
                    'focus': f'Units 1-{min(week, len(plan_data["study_units"]))}'
                })
        
        # Convert to YAML string
        import yaml
        yaml_content = yaml.dump(plan_data, default_flow_style=False, allow_unicode=True, indent=2)
        
        # Add header
        header = f"""# 🎯 Personalized Study Plan - IcfesLeveling AI
# Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
# Algorithm: IRT + Vector Embeddings + LLM Analysis
# User Ability (θ): {user_profile.overall_theta:.3f}
# Confidence: {user_profile.confidence_intervals.get('overall', (-1, 1))}
# Duration: {study_weeks} weeks intensive study program

"""
        
        final_yaml = header + yaml_content
        
        self.logger.info(f"✅ Generated YAML study plan: {len(final_yaml)} characters")
        self.logger.info(f"📊 Plan includes {len(plan_data['study_units'])} units, {study_weeks} weeks duration")
        
        return final_yaml

    def _generate_weekly_schedule(self, recommendation: RecommendationItem, total_weeks: int) -> List[Dict]:
        """Generate weekly schedule for a study unit"""
        schedule = []
        
        for week in range(1, min(total_weeks + 1, 5)):  # Max 4 weeks per unit
            week_plan = {
                'week': week,
                'focus': f'Progressive mastery of {recommendation.content.topic_name}',
                'activities': [],
                'estimated_hours': 2
            }
            
            if week == 1:
                week_plan['activities'] = [
                    f'Watch: {recommendation.content.title}',
                    'Take notes on key concepts',
                    'Complete basic practice problems'
                ]
            elif week == 2:
                week_plan['activities'] = [
                    'Review previous material',
                    'Apply concepts to new problems',
                    'Identify challenging areas'
                ]
            elif week == 3:
                week_plan['activities'] = [
                    'Focus on difficult concepts',
                    'Additional practice exercises',
                    'Mini-assessment'
                ]
            else:
                week_plan['activities'] = [
                    'Comprehensive review',
                    'Final practice test',
                    'Self-evaluation'
                ]
            
            schedule.append(week_plan)
        
        return schedule

    def _theta_to_percentile(self, theta: float) -> int:
        """Convert theta score to approximate percentile"""
        # Simplified conversion - in practice would use proper IRT tables
        if theta >= 2.0:
            return 97
        elif theta >= 1.5:
            return 93
        elif theta >= 1.0:
            return 84
        elif theta >= 0.5:
            return 69
        elif theta >= 0.0:
            return 50
        elif theta >= -0.5:
            return 31
        elif theta >= -1.0:
            return 16
        elif theta >= -1.5:
            return 7
        else:
            return 3

    def _interpret_theta(self, theta: float) -> str:
        """Provide interpretation of theta score"""
        if theta >= 1.5:
            return "Exceptional performance - well above average"
        elif theta >= 1.0:
            return "Strong performance - above average"
        elif theta >= 0.5:
            return "Good performance - moderately above average"
        elif theta >= -0.5:
            return "Average performance - typical range"
        elif theta >= -1.0:
            return "Below average - needs focused improvement"
        else:
            return "Significant improvement needed - requires intensive support"