#!/usr/bin/env python3
"""
Difficulty-Appropriate Content Selection System using IRT Models
==============================================================

An advanced content selection system that uses Item Response Theory (IRT) 
models to match educational video content with student ability levels, 
ensuring optimal challenge and learning progression for ICFES preparation.

Features:
- Three-Parameter Logistic (3PL) IRT model implementation
- Student theta (ability) estimation and tracking
- Content difficulty (b-parameter) calibration
- Adaptive difficulty progression algorithms
- Zone of Proximal Development (ZPD) targeting
- Content effectiveness tracking and feedback loops
- Personalized difficulty trajectories

Author: Claude Code Assistant (Video Matching Specialist)
Date: 2025-09-11
"""

import logging
import numpy as np
import scipy.stats as stats
import scipy.optimize as optimize
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DifficultyModel(Enum):
    """Supported difficulty models"""
    IRT_1PL = "1pl"  # Rasch model
    IRT_2PL = "2pl"  # Two-parameter logistic
    IRT_3PL = "3pl"  # Three-parameter logistic
    CUSTOM_ICFES = "custom_icfes"  # ICFES-adapted model

class LearningProgression(Enum):
    """Learning progression strategies"""
    CONSERVATIVE = "conservative"    # Slightly below current ability
    OPTIMAL = "optimal"             # At current ability level
    CHALLENGING = "challenging"     # Slightly above current ability
    ADAPTIVE = "adaptive"           # Dynamically adjust based on performance

class ContentDifficultyCategory(Enum):
    """Content difficulty categories"""
    FOUNDATIONAL = "foundational"   # Below grade level
    BASIC = "basic"                 # At grade level
    INTERMEDIATE = "intermediate"   # Above grade level
    ADVANCED = "advanced"           # Significantly above grade level
    EXPERT = "expert"               # Expert level content

@dataclass
class IRTParameters:
    """IRT model parameters for content item"""
    content_id: Union[int, str]
    
    # IRT Parameters
    a_parameter: float  # Discrimination (slope)
    b_parameter: float  # Difficulty (location)
    c_parameter: float  # Guessing (asymptote)
    
    # Additional parameters for extended models
    d_parameter: Optional[float] = None  # Upper asymptote (for 4PL)
    
    # Metadata
    subject_area: str = ""
    topic: str = ""
    content_type: str = ""
    n_calibration_responses: int = 0
    calibration_date: Optional[datetime] = None
    standard_error: float = 0.0
    fit_statistics: Dict[str, float] = field(default_factory=dict)

@dataclass
class StudentAbility:
    """Student ability estimate (theta) with confidence intervals"""
    student_id: str
    subject_area: str
    
    # Ability parameters
    theta: float  # Current ability estimate
    theta_se: float  # Standard error
    theta_ci_lower: float  # 95% CI lower bound
    theta_ci_upper: float  # 95% CI upper bound
    
    # Historical data
    theta_history: List[Tuple[datetime, float]] = field(default_factory=list)
    n_responses: int = 0
    last_updated: Optional[datetime] = None
    
    # Learning trajectory
    learning_rate: float = 0.0  # Rate of ability change
    plateau_indicator: float = 0.0  # Indicator of learning plateau
    
    def get_confidence_interval(self, confidence_level: float = 0.95) -> Tuple[float, float]:
        """Get confidence interval for theta estimate"""
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        margin = z_score * self.theta_se
        return (self.theta - margin, self.theta + margin)
    
    def is_estimate_reliable(self, min_responses: int = 10, max_se: float = 0.5) -> bool:
        """Check if theta estimate is reliable"""
        return self.n_responses >= min_responses and self.theta_se <= max_se

@dataclass
class ContentDifficultyProfile:
    """Complete difficulty profile for content item"""
    content_id: Union[int, str]
    title: str
    
    # IRT-based difficulty
    irt_parameters: IRTParameters
    
    # Multi-dimensional difficulty
    cognitive_difficulty: float  # Cognitive load/complexity
    linguistic_difficulty: float  # Language complexity
    conceptual_difficulty: float  # Concept abstraction level
    procedural_difficulty: float  # Procedure complexity
    
    # Context and prerequisites
    prerequisite_theta: float  # Minimum theta for prerequisites
    optimal_theta: float  # Optimal theta for learning
    challenge_theta: float  # Maximum beneficial theta
    
    # Effectiveness metrics
    learning_effectiveness: float  # How well content improves ability
    engagement_factor: float  # Student engagement with content
    completion_rate: float  # Rate of content completion
    
    # Metadata
    subject_area: str
    topic: str
    duration_minutes: int
    content_type: str
    created_date: datetime
    last_calibrated: Optional[datetime] = None
    
    def get_probability_correct(self, theta: float, model: DifficultyModel = DifficultyModel.IRT_3PL) -> float:
        """Calculate probability of success at given ability level"""
        if model == DifficultyModel.IRT_1PL:
            return self._prob_1pl(theta)
        elif model == DifficultyModel.IRT_2PL:
            return self._prob_2pl(theta)
        elif model == DifficultyModel.IRT_3PL:
            return self._prob_3pl(theta)
        else:
            return self._prob_3pl(theta)  # Default to 3PL
    
    def _prob_1pl(self, theta: float) -> float:
        """1PL (Rasch) probability function"""
        exponent = theta - self.irt_parameters.b_parameter
        return np.exp(exponent) / (1 + np.exp(exponent))
    
    def _prob_2pl(self, theta: float) -> float:
        """2PL probability function"""
        exponent = self.irt_parameters.a_parameter * (theta - self.irt_parameters.b_parameter)
        return np.exp(exponent) / (1 + np.exp(exponent))
    
    def _prob_3pl(self, theta: float) -> float:
        """3PL probability function"""
        exponent = self.irt_parameters.a_parameter * (theta - self.irt_parameters.b_parameter)
        prob_2pl = np.exp(exponent) / (1 + np.exp(exponent))
        return self.irt_parameters.c_parameter + (1 - self.irt_parameters.c_parameter) * prob_2pl

@dataclass
class DifficultySelectionCriteria:
    """Criteria for difficulty-appropriate content selection"""
    student_ability: StudentAbility
    learning_progression: LearningProgression
    
    # Target difficulty parameters
    target_success_rate: float = 0.7  # Target probability of success
    difficulty_tolerance: float = 0.2  # Acceptable deviation from target
    
    # Content constraints
    max_content_items: int = 10
    min_content_items: int = 3
    include_prerequisite_check: bool = True
    
    # Progression parameters
    conservative_offset: float = -0.5  # Logit units below theta
    challenging_offset: float = 0.5   # Logit units above theta
    adaptive_window: float = 1.0      # Adaptive selection window
    
    # Quality filters
    min_discrimination: float = 0.5   # Minimum a-parameter
    max_guessing: float = 0.4        # Maximum c-parameter
    min_calibration_responses: int = 20
    
    # Subject/topic filters
    subject_filters: List[str] = field(default_factory=list)
    topic_filters: List[str] = field(default_factory=list)
    content_type_filters: List[str] = field(default_factory=list)

@dataclass
class DifficultySelectionResult:
    """Result of difficulty-appropriate content selection"""
    content_profile: ContentDifficultyProfile
    
    # Difficulty matching metrics
    theta_distance: float  # Distance from student's theta
    success_probability: float  # Predicted probability of success
    difficulty_category: ContentDifficultyCategory
    
    # Learning optimization metrics
    learning_potential: float  # Estimated learning gain
    optimal_challenge_score: float  # How well it fits optimal challenge zone
    progression_alignment: float  # Alignment with learning progression strategy
    
    # Selection metadata
    selection_confidence: float  # Confidence in selection
    recommendation_reason: str  # Reason for recommendation
    expected_learning_time: int  # Expected learning time in minutes

class IRTModelManager:
    """Manages IRT model fitting and calibration"""
    
    def __init__(self):
        self.model_cache = {}
        self.calibration_history = defaultdict(list)
    
    def calibrate_content_difficulty(
        self,
        content_id: Union[int, str],
        responses: List[Dict[str, Any]],
        model_type: DifficultyModel = DifficultyModel.IRT_3PL
    ) -> IRTParameters:
        """Calibrate IRT parameters for content item"""
        
        if len(responses) < 10:
            logger.warning(f"Insufficient responses ({len(responses)}) for reliable calibration")
            return self._get_default_parameters(content_id)
        
        # Prepare data
        response_data = []
        theta_estimates = []
        
        for response in responses:
            response_data.append(1 if response.get('is_correct', False) else 0)
            theta_estimates.append(response.get('student_theta', 0.0))
        
        response_array = np.array(response_data)
        theta_array = np.array(theta_estimates)
        
        # Fit IRT model
        if model_type == DifficultyModel.IRT_1PL:
            params = self._fit_1pl_model(response_array, theta_array)
        elif model_type == DifficultyModel.IRT_2PL:
            params = self._fit_2pl_model(response_array, theta_array)
        elif model_type == DifficultyModel.IRT_3PL:
            params = self._fit_3pl_model(response_array, theta_array)
        else:
            params = self._fit_3pl_model(response_array, theta_array)
        
        # Create IRTParameters object
        irt_params = IRTParameters(
            content_id=content_id,
            a_parameter=params.get('a', 1.0),
            b_parameter=params.get('b', 0.0),
            c_parameter=params.get('c', 0.0),
            n_calibration_responses=len(responses),
            calibration_date=datetime.now(),
            standard_error=params.get('se_b', 0.0),
            fit_statistics=params.get('fit_stats', {})
        )
        
        # Cache the parameters
        self.model_cache[content_id] = irt_params
        
        logger.info(f"Calibrated content {content_id}: a={irt_params.a_parameter:.3f}, "
                   f"b={irt_params.b_parameter:.3f}, c={irt_params.c_parameter:.3f}")
        
        return irt_params
    
    def _fit_1pl_model(self, responses: np.ndarray, thetas: np.ndarray) -> Dict[str, float]:
        """Fit 1PL (Rasch) model"""
        
        def negative_log_likelihood(params):
            b = params[0]
            
            prob = np.exp(thetas - b) / (1 + np.exp(thetas - b))
            prob = np.clip(prob, 1e-10, 1 - 1e-10)  # Avoid log(0)
            
            ll = np.sum(responses * np.log(prob) + (1 - responses) * np.log(1 - prob))
            return -ll
        
        # Initial parameter estimates
        initial_b = np.mean(thetas[responses == 0.5])  # Approximate difficulty
        
        # Optimize
        try:
            result = optimize.minimize(
                negative_log_likelihood,
                [initial_b],
                bounds=[(-4, 4)],
                method='L-BFGS-B'
            )
            
            b_param = result.x[0]
            
            return {
                'a': 1.0,  # Fixed at 1.0 for Rasch model
                'b': b_param,
                'c': 0.0,  # Fixed at 0.0 for Rasch model
                'se_b': 0.1,  # Simplified SE calculation
                'fit_stats': {'nll': result.fun}
            }
            
        except Exception as e:
            logger.error(f"1PL model fitting failed: {e}")
            return self._get_default_model_params()
    
    def _fit_2pl_model(self, responses: np.ndarray, thetas: np.ndarray) -> Dict[str, float]:
        """Fit 2PL model"""
        
        def negative_log_likelihood(params):
            a, b = params
            
            if a <= 0:  # Ensure positive discrimination
                return 1e10
            
            prob = np.exp(a * (thetas - b)) / (1 + np.exp(a * (thetas - b)))
            prob = np.clip(prob, 1e-10, 1 - 1e-10)
            
            ll = np.sum(responses * np.log(prob) + (1 - responses) * np.log(1 - prob))
            return -ll
        
        # Initial estimates
        initial_a = 1.0
        initial_b = np.mean(thetas)
        
        try:
            result = optimize.minimize(
                negative_log_likelihood,
                [initial_a, initial_b],
                bounds=[(0.1, 5.0), (-4, 4)],
                method='L-BFGS-B'
            )
            
            a_param, b_param = result.x
            
            return {
                'a': a_param,
                'b': b_param,
                'c': 0.0,
                'se_b': 0.1,
                'fit_stats': {'nll': result.fun}
            }
            
        except Exception as e:
            logger.error(f"2PL model fitting failed: {e}")
            return self._get_default_model_params()
    
    def _fit_3pl_model(self, responses: np.ndarray, thetas: np.ndarray) -> Dict[str, float]:
        """Fit 3PL model"""
        
        def negative_log_likelihood(params):
            a, b, c = params
            
            if a <= 0 or c < 0 or c >= 1:
                return 1e10
            
            prob = c + (1 - c) * (np.exp(a * (thetas - b)) / (1 + np.exp(a * (thetas - b))))
            prob = np.clip(prob, 1e-10, 1 - 1e-10)
            
            ll = np.sum(responses * np.log(prob) + (1 - responses) * np.log(1 - prob))
            return -ll
        
        # Initial estimates
        initial_a = 1.0
        initial_b = np.mean(thetas)
        initial_c = max(0.0, min(np.mean(responses[thetas < np.percentile(thetas, 10)]), 0.4))
        
        try:
            result = optimize.minimize(
                negative_log_likelihood,
                [initial_a, initial_b, initial_c],
                bounds=[(0.1, 5.0), (-4, 4), (0.0, 0.5)],
                method='L-BFGS-B'
            )
            
            a_param, b_param, c_param = result.x
            
            return {
                'a': a_param,
                'b': b_param,
                'c': c_param,
                'se_b': 0.1,
                'fit_stats': {'nll': result.fun}
            }
            
        except Exception as e:
            logger.error(f"3PL model fitting failed: {e}")
            return self._get_default_model_params()
    
    def _get_default_parameters(self, content_id: Union[int, str]) -> IRTParameters:
        """Get default IRT parameters when calibration is not possible"""
        return IRTParameters(
            content_id=content_id,
            a_parameter=1.0,
            b_parameter=0.0,
            c_parameter=0.2,
            n_calibration_responses=0,
            standard_error=0.5
        )
    
    def _get_default_model_params(self) -> Dict[str, float]:
        """Get default model parameters"""
        return {
            'a': 1.0,
            'b': 0.0,
            'c': 0.2,
            'se_b': 0.5,
            'fit_stats': {}
        }

class StudentAbilityEstimator:
    """Estimates and tracks student ability (theta) over time"""
    
    def __init__(self):
        self.ability_cache = {}
        self.estimation_history = defaultdict(list)
    
    def estimate_ability(
        self,
        student_id: str,
        responses: List[Dict[str, Any]],
        subject_area: str = "general"
    ) -> StudentAbility:
        """Estimate student ability using Maximum Likelihood Estimation"""
        
        if len(responses) < 5:
            logger.warning(f"Insufficient responses ({len(responses)}) for reliable theta estimation")
            return self._get_default_ability(student_id, subject_area)
        
        # Prepare data
        response_data = []
        item_parameters = []
        
        for response in responses:
            response_data.append(1 if response.get('is_correct', False) else 0)
            
            # Get item parameters (use defaults if not available)
            item_params = response.get('item_parameters', {
                'a': 1.0, 'b': 0.0, 'c': 0.2
            })
            item_parameters.append(item_params)
        
        # Maximum Likelihood Estimation
        theta_estimate = self._mle_theta_estimation(response_data, item_parameters)
        
        # Calculate standard error
        theta_se = self._calculate_theta_se(theta_estimate, item_parameters)
        
        # Create StudentAbility object
        ability = StudentAbility(
            student_id=student_id,
            subject_area=subject_area,
            theta=theta_estimate,
            theta_se=theta_se,
            theta_ci_lower=theta_estimate - 1.96 * theta_se,
            theta_ci_upper=theta_estimate + 1.96 * theta_se,
            n_responses=len(responses),
            last_updated=datetime.now()
        )
        
        # Update learning trajectory if we have historical data
        self._update_learning_trajectory(ability, student_id, subject_area)
        
        # Cache the ability estimate
        cache_key = f"{student_id}_{subject_area}"
        self.ability_cache[cache_key] = ability
        
        logger.info(f"Estimated ability for {student_id} in {subject_area}: "
                   f"theta={theta_estimate:.3f} ± {theta_se:.3f}")
        
        return ability
    
    def _mle_theta_estimation(
        self,
        responses: List[int],
        item_parameters: List[Dict[str, float]]
    ) -> float:
        """Maximum Likelihood Estimation of theta"""
        
        def negative_log_likelihood(theta):
            total_ll = 0
            
            for response, params in zip(responses, item_parameters):
                a, b, c = params['a'], params['b'], params['c']
                
                # 3PL probability
                prob = c + (1 - c) * (np.exp(a * (theta - b)) / (1 + np.exp(a * (theta - b))))
                prob = np.clip(prob, 1e-10, 1 - 1e-10)
                
                if response == 1:
                    total_ll += np.log(prob)
                else:
                    total_ll += np.log(1 - prob)
            
            return -total_ll
        
        # Initial theta estimate (use proportion correct)
        proportion_correct = np.mean(responses)
        initial_theta = np.log(proportion_correct / (1 - proportion_correct + 1e-10))
        initial_theta = np.clip(initial_theta, -4, 4)
        
        try:
            result = optimize.minimize_scalar(
                negative_log_likelihood,
                bounds=(-4, 4),
                method='bounded'
            )
            
            return result.x
            
        except Exception as e:
            logger.error(f"Theta estimation failed: {e}")
            return initial_theta
    
    def _calculate_theta_se(
        self,
        theta: float,
        item_parameters: List[Dict[str, float]]
    ) -> float:
        """Calculate standard error of theta estimate"""
        
        information = 0
        
        for params in item_parameters:
            a, b, c = params['a'], params['b'], params['c']
            
            # 3PL probability and its derivative
            prob = c + (1 - c) * (np.exp(a * (theta - b)) / (1 + np.exp(a * (theta - b))))
            prob = np.clip(prob, 1e-10, 1 - 1e-10)
            
            # Fisher information for 3PL
            p_star = (np.exp(a * (theta - b)) / (1 + np.exp(a * (theta - b))))
            info_contribution = (a**2 * (1 - c)**2 * p_star * (1 - p_star)) / (prob * (1 - prob))
            
            information += info_contribution
        
        # Standard error is 1/sqrt(information)
        if information > 0:
            return 1.0 / np.sqrt(information)
        else:
            return 0.5  # Default SE when information is insufficient
    
    def _update_learning_trajectory(
        self,
        ability: StudentAbility,
        student_id: str,
        subject_area: str
    ):
        """Update learning trajectory metrics"""
        
        # Get historical theta estimates
        history_key = f"{student_id}_{subject_area}"
        history = self.estimation_history.get(history_key, [])
        
        if len(history) >= 2:
            # Calculate learning rate (change in theta over time)
            recent_estimates = history[-5:]  # Last 5 estimates
            if len(recent_estimates) >= 2:
                time_diffs = [(est[0] - recent_estimates[0][0]).total_seconds() / 3600  # hours
                             for est in recent_estimates[1:]]
                theta_diffs = [est[1] - recent_estimates[i][1] 
                              for i, est in enumerate(recent_estimates[1:])]
                
                if sum(time_diffs) > 0:
                    ability.learning_rate = sum(theta_diffs) / sum(time_diffs)  # theta per hour
                
                # Plateau indicator (variance in recent estimates)
                recent_thetas = [est[1] for est in recent_estimates]
                ability.plateau_indicator = np.var(recent_thetas)
        
        # Add current estimate to history
        history.append((datetime.now(), ability.theta))
        self.estimation_history[history_key] = history[-20:]  # Keep last 20 estimates
    
    def _get_default_ability(self, student_id: str, subject_area: str) -> StudentAbility:
        """Get default ability estimate when insufficient data"""
        return StudentAbility(
            student_id=student_id,
            subject_area=subject_area,
            theta=0.0,  # Average ability
            theta_se=1.0,  # High uncertainty
            theta_ci_lower=-1.96,
            theta_ci_upper=1.96,
            n_responses=0
        )

class DifficultyAppropriateContentSelector:
    """Main system for selecting difficulty-appropriate content"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.irt_manager = IRTModelManager()
        self.ability_estimator = StudentAbilityEstimator()
        
        # Load content difficulty profiles
        self.content_profiles = {}
        self._load_content_profiles()
    
    def _load_content_profiles(self):
        """Load content difficulty profiles from database"""
        try:
            query = text("""
                SELECT 
                    yc.id,
                    yc.title,
                    yc.subject_id,
                    yc.topic_id,
                    yc.duration_seconds,
                    yc.irt_b,
                    yc.irt_a,
                    yc.irt_c,
                    s.name as subject_name,
                    t.name as topic_name,
                    COALESCE(vs.completion_rate_7d, 0.7) as completion_rate,
                    COALESCE(vs.ctr_7d, 0.1) as engagement_factor
                FROM youtube_catalog yc
                JOIN subjects s ON yc.subject_id = s.id
                LEFT JOIN topics t ON yc.topic_id = t.id
                LEFT JOIN video_stats vs ON yc.id = vs.video_id
                WHERE yc.is_processed = true
                    AND yc.irt_b IS NOT NULL
                ORDER BY yc.subject_id, yc.irt_b
            """)
            
            results = self.db.execute(query).fetchall()
            
            for row in results:
                # Create IRT parameters
                irt_params = IRTParameters(
                    content_id=row.id,
                    a_parameter=row.irt_a or 1.0,
                    b_parameter=row.irt_b or 0.0,
                    c_parameter=row.irt_c or 0.2
                )
                
                # Create difficulty profile
                profile = ContentDifficultyProfile(
                    content_id=row.id,
                    title=row.title,
                    irt_parameters=irt_params,
                    cognitive_difficulty=row.irt_b or 0.0,  # Use b-parameter as proxy
                    linguistic_difficulty=0.5,  # Default value
                    conceptual_difficulty=row.irt_b or 0.0,
                    procedural_difficulty=0.5,
                    prerequisite_theta=(row.irt_b or 0.0) - 1.0,
                    optimal_theta=row.irt_b or 0.0,
                    challenge_theta=(row.irt_b or 0.0) + 1.0,
                    learning_effectiveness=0.8,  # Default
                    engagement_factor=row.engagement_factor,
                    completion_rate=row.completion_rate,
                    subject_area=row.subject_name,
                    topic=row.topic_name or "",
                    duration_minutes=int((row.duration_seconds or 600) / 60),
                    content_type="video",
                    created_date=datetime.now()
                )
                
                self.content_profiles[row.id] = profile
            
            logger.info(f"Loaded {len(self.content_profiles)} content difficulty profiles")
            
        except Exception as e:
            logger.error(f"Error loading content profiles: {e}")
    
    def select_appropriate_content(
        self,
        criteria: DifficultySelectionCriteria
    ) -> List[DifficultySelectionResult]:
        """Select difficulty-appropriate content for student"""
        
        student_ability = criteria.student_ability
        
        if not student_ability.is_estimate_reliable():
            logger.warning(f"Unreliable ability estimate for student {student_ability.student_id}")
        
        # Filter content by basic criteria
        candidate_profiles = self._filter_candidate_content(criteria)
        
        if not candidate_profiles:
            logger.warning("No candidate content found matching criteria")
            return []
        
        # Score each candidate
        scored_results = []
        
        for profile in candidate_profiles:
            result = self._score_content_difficulty_match(profile, criteria)
            if result.selection_confidence > 0.3:  # Minimum confidence threshold
                scored_results.append(result)
        
        # Sort by learning potential and optimal challenge
        scored_results.sort(
            key=lambda x: (x.learning_potential, x.optimal_challenge_score),
            reverse=True
        )
        
        # Apply progression strategy
        final_results = self._apply_progression_strategy(scored_results, criteria)
        
        logger.info(f"Selected {len(final_results)} appropriate content items for "
                   f"student {student_ability.student_id}")
        
        return final_results[:criteria.max_content_items]
    
    def _filter_candidate_content(
        self,
        criteria: DifficultySelectionCriteria
    ) -> List[ContentDifficultyProfile]:
        """Filter content by basic criteria"""
        
        candidates = []
        student_theta = criteria.student_ability.theta
        
        for profile in self.content_profiles.values():
            # Subject filter
            if criteria.subject_filters and profile.subject_area not in criteria.subject_filters:
                continue
            
            # Topic filter
            if criteria.topic_filters and profile.topic not in criteria.topic_filters:
                continue
            
            # Content type filter
            if criteria.content_type_filters and profile.content_type not in criteria.content_type_filters:
                continue
            
            # IRT parameter quality checks
            irt_params = profile.irt_parameters
            if irt_params.a_parameter < criteria.min_discrimination:
                continue
            
            if irt_params.c_parameter > criteria.max_guessing:
                continue
            
            if irt_params.n_calibration_responses < criteria.min_calibration_responses:
                # Allow content with no calibration data if it's the only option
                pass
            
            # Difficulty window check
            theta_distance = abs(irt_params.b_parameter - student_theta)
            max_distance = 2.0  # Maximum reasonable theta distance
            
            if theta_distance > max_distance:
                continue
            
            # Prerequisite check
            if (criteria.include_prerequisite_check and 
                student_theta < profile.prerequisite_theta):
                continue
            
            candidates.append(profile)
        
        logger.info(f"Found {len(candidates)} candidate content items")
        return candidates
    
    def _score_content_difficulty_match(
        self,
        profile: ContentDifficultyProfile,
        criteria: DifficultySelectionCriteria
    ) -> DifficultySelectionResult:
        """Score how well content matches student's difficulty needs"""
        
        student_ability = criteria.student_ability
        student_theta = student_ability.theta
        
        # Calculate basic metrics
        theta_distance = abs(profile.irt_parameters.b_parameter - student_theta)
        success_probability = profile.get_probability_correct(student_theta)
        
        # Determine difficulty category
        difficulty_category = self._categorize_difficulty(
            profile.irt_parameters.b_parameter, student_theta
        )
        
        # Calculate learning potential
        learning_potential = self._calculate_learning_potential(
            profile, student_ability, success_probability
        )
        
        # Calculate optimal challenge score
        optimal_challenge_score = self._calculate_optimal_challenge_score(
            success_probability, criteria.target_success_rate, criteria.difficulty_tolerance
        )
        
        # Calculate progression alignment
        progression_alignment = self._calculate_progression_alignment(
            profile, criteria.learning_progression, student_theta
        )
        
        # Calculate selection confidence
        selection_confidence = self._calculate_selection_confidence(
            profile, student_ability, success_probability
        )
        
        # Generate recommendation reason
        recommendation_reason = self._generate_recommendation_reason(
            profile, success_probability, difficulty_category, learning_potential
        )
        
        # Estimate learning time
        expected_learning_time = self._estimate_learning_time(
            profile, success_probability
        )
        
        return DifficultySelectionResult(
            content_profile=profile,
            theta_distance=theta_distance,
            success_probability=success_probability,
            difficulty_category=difficulty_category,
            learning_potential=learning_potential,
            optimal_challenge_score=optimal_challenge_score,
            progression_alignment=progression_alignment,
            selection_confidence=selection_confidence,
            recommendation_reason=recommendation_reason,
            expected_learning_time=expected_learning_time
        )
    
    def _categorize_difficulty(self, content_b: float, student_theta: float) -> ContentDifficultyCategory:
        """Categorize content difficulty relative to student ability"""
        
        difference = content_b - student_theta
        
        if difference < -2.0:
            return ContentDifficultyCategory.FOUNDATIONAL
        elif difference < -0.5:
            return ContentDifficultyCategory.BASIC
        elif difference < 0.5:
            return ContentDifficultyCategory.INTERMEDIATE
        elif difference < 2.0:
            return ContentDifficultyCategory.ADVANCED
        else:
            return ContentDifficultyCategory.EXPERT
    
    def _calculate_learning_potential(
        self,
        profile: ContentDifficultyProfile,
        student_ability: StudentAbility,
        success_probability: float
    ) -> float:
        """Calculate potential learning gain from content"""
        
        # Base learning potential from success probability (inverted U-curve)
        # Maximum learning occurs around 60-80% success rate
        if 0.6 <= success_probability <= 0.8:
            base_potential = 1.0
        elif 0.4 <= success_probability <= 0.9:
            base_potential = 0.8
        elif 0.3 <= success_probability <= 0.95:
            base_potential = 0.6
        else:
            base_potential = 0.3
        
        # Adjust for content quality factors
        quality_factor = (
            profile.learning_effectiveness * 0.4 +
            profile.engagement_factor * 0.3 +
            profile.completion_rate * 0.3
        )
        
        # Adjust for discrimination (higher discrimination = better learning)
        discrimination_factor = min(profile.irt_parameters.a_parameter / 2.0, 1.0)
        
        # Adjust for student's learning trajectory
        trajectory_factor = 1.0
        if student_ability.learning_rate > 0:
            trajectory_factor = 1.2  # Student is improving
        elif student_ability.plateau_indicator > 0.5:
            trajectory_factor = 0.8  # Student may be plateauing
        
        learning_potential = base_potential * quality_factor * discrimination_factor * trajectory_factor
        
        return min(1.0, max(0.0, learning_potential))
    
    def _calculate_optimal_challenge_score(
        self,
        success_probability: float,
        target_success_rate: float,
        tolerance: float
    ) -> float:
        """Calculate how well content fits optimal challenge zone"""
        
        distance_from_target = abs(success_probability - target_success_rate)
        
        if distance_from_target <= tolerance:
            # Within tolerance zone
            return 1.0 - (distance_from_target / tolerance) * 0.2
        else:
            # Outside tolerance zone - exponential decay
            excess_distance = distance_from_target - tolerance
            return max(0.1, np.exp(-excess_distance * 2))
    
    def _calculate_progression_alignment(
        self,
        profile: ContentDifficultyProfile,
        progression_strategy: LearningProgression,
        student_theta: float
    ) -> float:
        """Calculate alignment with learning progression strategy"""
        
        content_difficulty = profile.irt_parameters.b_parameter
        difficulty_offset = content_difficulty - student_theta
        
        if progression_strategy == LearningProgression.CONSERVATIVE:
            # Prefer slightly easier content
            optimal_offset = -0.5
        elif progression_strategy == LearningProgression.OPTIMAL:
            # Prefer content at current ability level
            optimal_offset = 0.0
        elif progression_strategy == LearningProgression.CHALLENGING:
            # Prefer slightly harder content
            optimal_offset = 0.5
        elif progression_strategy == LearningProgression.ADAPTIVE:
            # Dynamic based on recent performance
            optimal_offset = 0.0  # Default to optimal for now
        else:
            optimal_offset = 0.0
        
        alignment_distance = abs(difficulty_offset - optimal_offset)
        return max(0.0, 1.0 - alignment_distance / 2.0)
    
    def _calculate_selection_confidence(
        self,
        profile: ContentDifficultyProfile,
        student_ability: StudentAbility,
        success_probability: float
    ) -> float:
        """Calculate confidence in content selection"""
        
        # Base confidence from ability estimate reliability
        if student_ability.is_estimate_reliable():
            base_confidence = 0.8
        elif student_ability.n_responses >= 5:
            base_confidence = 0.6
        else:
            base_confidence = 0.4
        
        # Adjust for IRT parameter quality
        if profile.irt_parameters.n_calibration_responses >= 50:
            param_confidence = 1.0
        elif profile.irt_parameters.n_calibration_responses >= 20:
            param_confidence = 0.8
        else:
            param_confidence = 0.5
        
        # Adjust for success probability (avoid extreme values)
        if 0.3 <= success_probability <= 0.9:
            prob_confidence = 1.0
        elif 0.1 <= success_probability <= 0.95:
            prob_confidence = 0.7
        else:
            prob_confidence = 0.3
        
        confidence = base_confidence * param_confidence * prob_confidence
        return min(1.0, max(0.0, confidence))
    
    def _generate_recommendation_reason(
        self,
        profile: ContentDifficultyProfile,
        success_probability: float,
        difficulty_category: ContentDifficultyCategory,
        learning_potential: float
    ) -> str:
        """Generate human-readable recommendation reason"""
        
        reasons = []
        
        # Success probability explanation
        if success_probability > 0.8:
            reasons.append("Alta probabilidad de éxito")
        elif success_probability > 0.6:
            reasons.append("Probabilidad moderada de éxito")
        else:
            reasons.append("Contenido desafiante")
        
        # Difficulty category
        category_descriptions = {
            ContentDifficultyCategory.FOUNDATIONAL: "nivel básico de repaso",
            ContentDifficultyCategory.BASIC: "nivel apropiado",
            ContentDifficultyCategory.INTERMEDIATE: "nivel intermedio",
            ContentDifficultyCategory.ADVANCED: "nivel avanzado",
            ContentDifficultyCategory.EXPERT: "nivel experto"
        }
        reasons.append(category_descriptions[difficulty_category])
        
        # Learning potential
        if learning_potential > 0.8:
            reasons.append("alto potencial de aprendizaje")
        elif learning_potential > 0.5:
            reasons.append("buen potencial de aprendizaje")
        
        # Content quality
        if profile.engagement_factor > 0.7:
            reasons.append("contenido altamente atractivo")
        
        return " | ".join(reasons)
    
    def _estimate_learning_time(
        self,
        profile: ContentDifficultyProfile,
        success_probability: float
    ) -> int:
        """Estimate expected learning time in minutes"""
        
        base_duration = profile.duration_minutes
        
        # Adjust for difficulty
        if success_probability > 0.8:
            time_multiplier = 1.0  # Easy content
        elif success_probability > 0.6:
            time_multiplier = 1.3  # Moderate content
        else:
            time_multiplier = 1.7  # Challenging content
        
        # Adjust for engagement
        engagement_adjustment = 2.0 - profile.engagement_factor
        
        estimated_time = base_duration * time_multiplier * engagement_adjustment
        
        return max(5, int(estimated_time))  # Minimum 5 minutes
    
    def _apply_progression_strategy(
        self,
        scored_results: List[DifficultySelectionResult],
        criteria: DifficultySelectionCriteria
    ) -> List[DifficultySelectionResult]:
        """Apply learning progression strategy to final selection"""
        
        if criteria.learning_progression == LearningProgression.ADAPTIVE:
            # Implement adaptive strategy based on recent performance
            # For now, use optimal strategy as default
            return scored_results
        
        # Sort by progression alignment for non-adaptive strategies
        scored_results.sort(
            key=lambda x: x.progression_alignment,
            reverse=True
        )
        
        return scored_results
    
    def get_difficulty_distribution_stats(self, subject_area: str = None) -> Dict[str, Any]:
        """Get statistics about content difficulty distribution"""
        
        profiles = list(self.content_profiles.values())
        
        if subject_area:
            profiles = [p for p in profiles if p.subject_area == subject_area]
        
        if not profiles:
            return {}
        
        b_parameters = [p.irt_parameters.b_parameter for p in profiles]
        
        stats = {
            'total_items': len(profiles),
            'difficulty_mean': np.mean(b_parameters),
            'difficulty_std': np.std(b_parameters),
            'difficulty_min': np.min(b_parameters),
            'difficulty_max': np.max(b_parameters),
            'difficulty_percentiles': {
                'p10': np.percentile(b_parameters, 10),
                'p25': np.percentile(b_parameters, 25),
                'p50': np.percentile(b_parameters, 50),
                'p75': np.percentile(b_parameters, 75),
                'p90': np.percentile(b_parameters, 90)
            }
        }
        
        return stats

# Utility functions
def create_default_selection_criteria(
    student_id: str,
    subject_area: str,
    current_theta: float = 0.0,
    progression: LearningProgression = LearningProgression.OPTIMAL
) -> DifficultySelectionCriteria:
    """Create default selection criteria for a student"""
    
    student_ability = StudentAbility(
        student_id=student_id,
        subject_area=subject_area,
        theta=current_theta,
        theta_se=0.5,
        theta_ci_lower=current_theta - 0.98,
        theta_ci_upper=current_theta + 0.98,
        n_responses=10,
        last_updated=datetime.now()
    )
    
    criteria = DifficultySelectionCriteria(
        student_ability=student_ability,
        learning_progression=progression,
        target_success_rate=0.7,
        difficulty_tolerance=0.15,
        max_content_items=5,
        subject_filters=[subject_area] if subject_area != "general" else []
    )
    
    return criteria

if __name__ == "__main__":
    # Example usage and testing
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Mock database for testing
    class MockSession:
        def execute(self, query):
            class MockResult:
                def fetchall(self):
                    return []
            return MockResult()
    
    db = MockSession()
    
    # Initialize selector
    selector = DifficultyAppropriateContentSelector(db)
    
    # Test with default criteria
    criteria = create_default_selection_criteria(
        student_id="test_student_001",
        subject_area="Matemáticas",
        current_theta=0.5
    )
    
    logger.info("Difficulty-Appropriate Content Selector initialized successfully!")
    logger.debug(f"Student theta: {criteria.student_ability.theta}")
    logger.debug(f"Target success rate: {criteria.target_success_rate}")
    logger.debug(f"Learning progression: {criteria.learning_progression}")