"""
Advanced IRT (Item Response Theory) Calculation Service
Implementation of complete 3PL model with adaptive theta estimation for diagnostic tests

Features:
- Complete 3PL model implementation: P(θ) = c + (1-c) / (1 + e^(-a(θ-b)))
- Maximum Likelihood Estimation (MLE) for theta calculation
- Expected A Posteriori (EAP) estimation with Bayesian priors
- Information function calculations for optimal question selection
- Real-time adaptive theta updates during test taking
- Comprehensive validation and error handling

Author: Claude Code
Date: 2025-09-09
"""

import math
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime
import logging
from scipy import optimize
from collections import defaultdict

from ..models.question import Question
from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.user import User

logger = logging.getLogger(__name__)


class IRTCalculationService:
    """
    Comprehensive IRT calculation service implementing 3PL model with adaptive capabilities
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logger
        
        # IRT Model Parameters
        self.DEFAULT_PRIOR_MEAN = 0.0      # Prior theta mean
        self.DEFAULT_PRIOR_SD = 1.0        # Prior theta standard deviation
        self.THETA_MIN = -5.0              # Minimum theta value
        self.THETA_MAX = 5.0               # Maximum theta value
        self.CONVERGENCE_TOLERANCE = 1e-6  # MLE convergence tolerance
        self.MAX_ITERATIONS = 100          # Maximum iterations for MLE
        
        # Question selection parameters
        self.INFORMATION_THRESHOLD = 0.1   # Minimum information for question selection
        self.CONTENT_BALANCING_WEIGHT = 0.3  # Weight for content balancing
        
    def calculate_3pl_probability(self, theta: float, a: float, b: float, c: float) -> float:
        """
        Calculate probability of correct response using 3PL IRT model
        
        Args:
            theta: Ability parameter (logit scale)
            a: Discrimination parameter
            b: Difficulty parameter 
            c: Pseudo-guessing parameter
            
        Returns:
            Probability of correct response (0-1)
        """
        try:
            # Validate parameters
            a = max(0.1, min(10.0, a))
            b = max(-5.0, min(5.0, b))
            c = max(0.0, min(1.0, c))
            theta = max(self.THETA_MIN, min(self.THETA_MAX, theta))
            
            # Calculate 3PL probability: P(θ) = c + (1-c)/(1+e^(-a(θ-b)))
            exponent = -a * (theta - b)
            exponent = max(-50, min(50, exponent))  # Prevent overflow
            
            exp_val = math.exp(exponent)
            probability = c + (1 - c) / (1 + exp_val)
            
            return max(0.001, min(0.999, probability))
            
        except (OverflowError, ValueError, ZeroDivisionError):
            return 0.5

    def calculate_information_function(self, theta: float, a: float, b: float, c: float) -> float:
        """
        Calculate Fisher information function for question at given theta
        
        Args:
            theta: Ability parameter
            a: Discrimination parameter
            b: Difficulty parameter
            c: Pseudo-guessing parameter
            
        Returns:
            Information value at theta
        """
        try:
            # Calculate probability and its complement
            p = self.calculate_3pl_probability(theta, a, b, c)
            q = 1 - p
            
            # Calculate first derivative of P with respect to theta
            exponent = -a * (theta - b)
            exponent = max(-50, min(50, exponent))
            exp_val = math.exp(exponent)
            
            # dP/dθ = a(1-c)e^(-a(θ-b)) / (1+e^(-a(θ-b)))²
            dp_dtheta = a * (1 - c) * exp_val / ((1 + exp_val) ** 2)
            
            # Information function: I(θ) = [P'(θ)]² / [P(θ)(1-P(θ))]
            if p * q > 0:
                information = (dp_dtheta ** 2) / (p * q)
            else:
                information = 0.0
                
            return max(0.0, information)
            
        except (OverflowError, ValueError, ZeroDivisionError):
            return 0.0

    def estimate_theta_mle(self, responses: List[Tuple[bool, float, float, float]], 
                          initial_theta: float = 0.0) -> Tuple[float, float, bool]:
        """
        Estimate theta using Maximum Likelihood Estimation
        
        Args:
            responses: List of (response, a, b, c) tuples
            initial_theta: Starting value for optimization
            
        Returns:
            Tuple of (estimated_theta, standard_error, converged)
        """
        if not responses:
            return initial_theta, 1.0, False
            
        def log_likelihood(theta):
            """Calculate negative log-likelihood for optimization"""
            ll = 0.0
            for response, a, b, c in responses:
                p = self.calculate_3pl_probability(theta, a, b, c)
                if response:
                    ll += math.log(max(1e-10, p))
                else:
                    ll += math.log(max(1e-10, 1 - p))
            return -ll  # Negative for minimization
        
        try:
            # Use scipy optimization for MLE
            result = optimize.minimize_scalar(
                log_likelihood,
                bounds=(self.THETA_MIN, self.THETA_MAX),
                method='bounded',
                options={'xatol': self.CONVERGENCE_TOLERANCE}
            )
            
            estimated_theta = result.x
            converged = result.success
            
            # Calculate standard error using Fisher information
            total_information = sum(
                self.calculate_information_function(estimated_theta, a, b, c)
                for _, a, b, c in responses
            )
            
            standard_error = 1.0 / math.sqrt(max(0.1, total_information))
            
            return estimated_theta, standard_error, converged
            
        except Exception as e:
            self.logger.warning(f"MLE estimation failed: {e}")
            return initial_theta, 1.0, False

    def estimate_theta_eap(self, responses: List[Tuple[bool, float, float, float]],
                          prior_mean: float = 0.0, prior_sd: float = 1.0) -> Tuple[float, float]:
        """
        Estimate theta using Expected A Posteriori (EAP) method with Bayesian prior
        
        Args:
            responses: List of (response, a, b, c) tuples
            prior_mean: Prior distribution mean
            prior_sd: Prior distribution standard deviation
            
        Returns:
            Tuple of (estimated_theta, posterior_sd)
        """
        if not responses:
            return prior_mean, prior_sd
            
        # Create quadrature points for numerical integration
        n_points = 41
        theta_points = np.linspace(self.THETA_MIN, self.THETA_MAX, n_points)
        
        # Calculate posterior distribution
        posterior_weights = []
        
        for theta in theta_points:
            # Prior density (normal distribution)
            prior_density = math.exp(-0.5 * ((theta - prior_mean) / prior_sd) ** 2)
            prior_density /= (prior_sd * math.sqrt(2 * math.pi))
            
            # Likelihood
            likelihood = 1.0
            for response, a, b, c in responses:
                p = self.calculate_3pl_probability(theta, a, b, c)
                if response:
                    likelihood *= p
                else:
                    likelihood *= (1 - p)
            
            # Posterior (unnormalized)
            posterior_weights.append(prior_density * likelihood)
        
        # Normalize posterior
        total_weight = sum(posterior_weights)
        if total_weight > 0:
            posterior_weights = [w / total_weight for w in posterior_weights]
        else:
            # Fallback to uniform weights
            posterior_weights = [1.0 / n_points] * n_points
        
        # Calculate EAP estimate (expected value)
        eap_theta = sum(theta * weight for theta, weight in zip(theta_points, posterior_weights))
        
        # Calculate posterior standard deviation
        posterior_variance = sum(
            ((theta - eap_theta) ** 2) * weight 
            for theta, weight in zip(theta_points, posterior_weights)
        )
        posterior_sd = math.sqrt(posterior_variance)
        
        return eap_theta, posterior_sd

    def update_theta_adaptive(self, current_theta: float, current_se: float,
                            new_response: bool, question: Question) -> Tuple[float, float]:
        """
        Update theta estimate incrementally with new response (for real-time adaptation)
        
        Args:
            current_theta: Current theta estimate
            current_se: Current standard error
            new_response: True if correct, False if incorrect
            question: Question object with IRT parameters
            
        Returns:
            Tuple of (new_theta, new_se)
        """
        # Get question parameters
        a = question.parametro_irt_a or 1.0
        b = question.parametro_irt_b or 0.0
        c = question.parametro_irt_c or 0.25
        
        # Calculate information for this question
        information = self.calculate_information_function(current_theta, a, b, c)
        
        if information < self.INFORMATION_THRESHOLD:
            # Low information, minimal update
            return current_theta, current_se
        
        # Calculate expected response probability
        expected_prob = self.calculate_3pl_probability(current_theta, a, b, c)
        
        # Actual response (1 for correct, 0 for incorrect)
        actual_response = 1.0 if new_response else 0.0
        
        # Calculate residual
        residual = actual_response - expected_prob
        
        # Newton-Raphson style update
        # Δθ = residual / information
        theta_adjustment = residual / information
        
        # Apply conservative adjustment factor
        adjustment_factor = min(1.0, information / 2.0)
        theta_adjustment *= adjustment_factor
        
        # Update theta
        new_theta = current_theta + theta_adjustment
        new_theta = max(self.THETA_MIN, min(self.THETA_MAX, new_theta))
        
        # Update standard error using information accumulation
        current_information = 1.0 / (current_se ** 2)
        new_information = current_information + information
        new_se = 1.0 / math.sqrt(max(0.1, new_information))
        
        return new_theta, new_se

    def select_optimal_next_question(self, current_theta: float, 
                                   answered_questions: List[str],
                                   subject_id: str,
                                   content_constraints: Optional[Dict] = None) -> Optional[Question]:
        """
        Select the most informative next question for adaptive testing
        
        Args:
            current_theta: Current ability estimate
            answered_questions: List of already answered question IDs
            subject_id: Subject ID for question pool
            content_constraints: Optional content balancing constraints
            
        Returns:
            Selected question or None if no suitable questions available
        """
        # Get available questions
        query = self.db.query(Question).filter(
            and_(
                Question.subject_id == subject_id,
                ~Question.id.in_(answered_questions),
                Question.parametro_irt_a.isnot(None),
                Question.parametro_irt_b.isnot(None),
                Question.parametro_irt_c.isnot(None)
            )
        )
        
        available_questions = query.all()
        
        if not available_questions:
            return None
        
        # Calculate information value for each question
        question_scores = []
        
        for question in available_questions:
            a = question.parametro_irt_a
            b = question.parametro_irt_b  
            c = question.parametro_irt_c
            
            # Calculate Fisher information at current theta
            information = self.calculate_information_function(current_theta, a, b, c)
            
            # Apply content balancing if specified
            if content_constraints:
                content_weight = self._calculate_content_weight(question, content_constraints)
                information *= content_weight
            
            question_scores.append((question, information))
        
        # Select question with highest information
        if question_scores:
            best_question, best_info = max(question_scores, key=lambda x: x[1])
            
            self.logger.info(f"Selected question {best_question.id} with information {best_info:.4f}")
            return best_question
        
        return None

    def calculate_test_information(self, theta: float, questions: List[Question]) -> float:
        """
        Calculate total test information at given theta level
        
        Args:
            theta: Ability level
            questions: List of questions in test
            
        Returns:
            Total information value
        """
        total_information = 0.0
        
        for question in questions:
            if all(param is not None for param in 
                  [question.parametro_irt_a, question.parametro_irt_b, question.parametro_irt_c]):
                info = self.calculate_information_function(
                    theta, 
                    question.parametro_irt_a,
                    question.parametro_irt_b, 
                    question.parametro_irt_c
                )
                total_information += info
        
        return total_information

    def estimate_test_reliability(self, questions: List[Question], 
                                theta_range: Tuple[float, float] = (-2.0, 2.0)) -> float:
        """
        Estimate test reliability using information function
        
        Args:
            questions: List of questions in test
            theta_range: Range of theta values to consider
            
        Returns:
            Estimated reliability coefficient
        """
        # Sample theta points across range
        theta_points = np.linspace(theta_range[0], theta_range[1], 21)
        
        # Calculate average information across theta range
        avg_information = 0.0
        for theta in theta_points:
            info = self.calculate_test_information(theta, questions)
            avg_information += info
        
        avg_information /= len(theta_points)
        
        # Convert information to reliability: r = I/(1+I)
        if avg_information > 0:
            reliability = avg_information / (1 + avg_information)
        else:
            reliability = 0.0
        
        return min(1.0, max(0.0, reliability))

    def generate_theta_profile(self, test_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive theta estimation profile for completed test
        
        Args:
            test_id: Diagnostic test ID
            
        Returns:
            Dictionary with theta profile and analysis
        """
        # Get test and answers
        test = self.db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        answers = self.db.query(DiagnosticTestAnswer).filter(
            DiagnosticTestAnswer.diagnostic_test_id == test_id
        ).order_by(DiagnosticTestAnswer.created_at).all()
        
        if not answers:
            raise ValueError("No answers found for test")
        
        # Prepare response data with IRT parameters
        responses = []
        questions_data = []
        
        for answer in answers:
            question = self.db.query(Question).filter(Question.id == answer.question_id).first()
            if question and all(param is not None for param in 
                              [question.parametro_irt_a, question.parametro_irt_b, question.parametro_irt_c]):
                responses.append((
                    answer.is_correct,
                    question.parametro_irt_a,
                    question.parametro_irt_b,
                    question.parametro_irt_c
                ))
                questions_data.append(question)
        
        if not responses:
            raise ValueError("No questions with valid IRT parameters found")
        
        # Calculate theta estimates using different methods
        mle_theta, mle_se, mle_converged = self.estimate_theta_mle(responses)
        eap_theta, eap_se = self.estimate_theta_eap(responses)
        
        # Calculate test information and reliability
        test_info = self.calculate_test_information(mle_theta, questions_data)
        test_reliability = self.estimate_test_reliability(questions_data)
        
        # Generate theta progression over test
        theta_progression = self._calculate_theta_progression(answers, questions_data)
        
        # Calculate confidence intervals
        mle_ci_lower = mle_theta - 1.96 * mle_se
        mle_ci_upper = mle_theta + 1.96 * mle_se
        eap_ci_lower = eap_theta - 1.96 * eap_se
        eap_ci_upper = eap_theta + 1.96 * eap_se
        
        return {
            "test_id": str(test_id),
            "estimation_methods": {
                "mle": {
                    "theta": mle_theta,
                    "standard_error": mle_se,
                    "converged": mle_converged,
                    "confidence_interval": [mle_ci_lower, mle_ci_upper]
                },
                "eap": {
                    "theta": eap_theta,
                    "standard_error": eap_se,
                    "confidence_interval": [eap_ci_lower, eap_ci_upper]
                }
            },
            "test_quality": {
                "total_information": test_info,
                "reliability": test_reliability,
                "measurement_precision": 1.0 / math.sqrt(max(0.1, test_info))
            },
            "theta_progression": theta_progression,
            "response_summary": {
                "total_items": len(responses),
                "correct_responses": sum(1 for r, _, _, _ in responses if r),
                "accuracy_rate": sum(1 for r, _, _, _ in responses if r) / len(responses)
            },
            "recommended_theta": mle_theta if mle_converged else eap_theta,
            "final_standard_error": mle_se if mle_converged else eap_se
        }

    def _calculate_content_weight(self, question: Question, content_constraints: Dict) -> float:
        """Calculate content balancing weight for question selection"""
        # Simple implementation - can be enhanced based on specific requirements
        if not content_constraints:
            return 1.0
        
        # Weight based on topic coverage needs
        topic_id = str(question.topic_id)
        if topic_id in content_constraints.get('topic_weights', {}):
            return content_constraints['topic_weights'][topic_id]
        
        return 1.0

    def _calculate_theta_progression(self, answers: List[DiagnosticTestAnswer], 
                                   questions: List[Question]) -> List[Dict]:
        """Calculate how theta estimate evolved during the test"""
        progression = []
        current_theta = 0.0
        current_se = 1.0
        
        for i, (answer, question) in enumerate(zip(answers, questions)):
            if all(param is not None for param in 
                  [question.parametro_irt_a, question.parametro_irt_b, question.parametro_irt_c]):
                
                # Update theta with this response
                current_theta, current_se = self.update_theta_adaptive(
                    current_theta, current_se, answer.is_correct, question
                )
                
                progression.append({
                    "item_number": i + 1,
                    "question_id": str(question.id),
                    "response": answer.is_correct,
                    "theta_estimate": current_theta,
                    "standard_error": current_se,
                    "question_difficulty": question.parametro_irt_b,
                    "question_discrimination": question.parametro_irt_a
                })
        
        return progression

    def validate_irt_parameters(self, question: Question) -> Dict[str, Any]:
        """
        Validate IRT parameters for a question
        
        Args:
            question: Question object to validate
            
        Returns:
            Validation results with warnings and errors
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "parameters": {}
        }
        
        # Check if parameters exist
        a = question.parametro_irt_a
        b = question.parametro_irt_b
        c = question.parametro_irt_c
        
        if a is None:
            validation["errors"].append("Missing discrimination parameter (a)")
            validation["valid"] = False
        else:
            validation["parameters"]["a"] = a
            if a <= 0:
                validation["errors"].append("Discrimination parameter must be positive")
                validation["valid"] = False
            elif a < 0.5:
                validation["warnings"].append("Low discrimination parameter may reduce measurement precision")
            elif a > 5.0:
                validation["warnings"].append("Very high discrimination parameter may indicate model misfit")
        
        if b is None:
            validation["errors"].append("Missing difficulty parameter (b)")
            validation["valid"] = False
        else:
            validation["parameters"]["b"] = b
            if abs(b) > 4:
                validation["warnings"].append("Extreme difficulty parameter may affect model stability")
        
        if c is None:
            validation["errors"].append("Missing pseudo-guessing parameter (c)")
            validation["valid"] = False
        else:
            validation["parameters"]["c"] = c
            if c < 0 or c >= 1:
                validation["errors"].append("Pseudo-guessing parameter must be between 0 and 1")
                validation["valid"] = False
            elif c > 0.5:
                validation["warnings"].append("High pseudo-guessing parameter may indicate poor item quality")
        
        # Additional checks if all parameters are present
        if validation["valid"]:
            # Check if parameters are reasonable for 3PL model
            prob_at_b = self.calculate_3pl_probability(b, a, b, c)
            expected_prob = c + (1 - c) / 2  # Should be around (c + 1)/2
            
            if abs(prob_at_b - expected_prob) > 0.1:
                validation["warnings"].append("Parameter combination may not follow expected 3PL behavior")
        
        return validation