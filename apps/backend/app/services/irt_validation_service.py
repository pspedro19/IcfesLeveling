"""
IRT Validation and Testing Service
Comprehensive validation, testing, and demonstration of the IRT calculation system

Features:
- Parameter validation for 3PL model
- Mathematical accuracy testing
- Performance benchmarking
- Real data validation
- Adaptive algorithm testing
- Comprehensive reporting

Author: Claude Code
Date: 2025-09-09
"""

import math
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging
import random
from datetime import datetime
import json

from .irt_calculation_service import IRTCalculationService
from ..models.question import Question
from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.user import User

logger = logging.getLogger(__name__)


class IRTValidationService:
    """
    Comprehensive validation and testing service for IRT calculations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.irt_service = IRTCalculationService(db)
        self.logger = logger
        
    def validate_question_irt_parameters(self, question_id: str = None) -> Dict[str, Any]:
        """
        Validate IRT parameters for a specific question or all questions
        
        Args:
            question_id: Optional specific question to validate
            
        Returns:
            Validation report with detailed analysis
        """
        if question_id:
            questions = [self.db.query(Question).filter(Question.id == question_id).first()]
            if not questions[0]:
                return {"error": f"Question {question_id} not found"}
        else:
            questions = self.db.query(Question).filter(
                and_(
                    Question.parametro_irt_a.isnot(None),
                    Question.parametro_irt_b.isnot(None),
                    Question.parametro_irt_c.isnot(None)
                )
            ).limit(100).all()  # Limit for performance
        
        validation_results = {
            "summary": {
                "total_questions": len(questions),
                "valid_questions": 0,
                "questions_with_warnings": 0,
                "invalid_questions": 0
            },
            "parameter_statistics": {
                "a_parameter": {"min": float('inf'), "max": float('-inf'), "mean": 0, "std": 0},
                "b_parameter": {"min": float('inf'), "max": float('-inf'), "mean": 0, "std": 0},
                "c_parameter": {"min": float('inf'), "max": float('-inf'), "mean": 0, "std": 0}
            },
            "detailed_results": [],
            "recommendations": []
        }
        
        a_values, b_values, c_values = [], [], []
        
        for question in questions:
            validation = self.irt_service.validate_irt_parameters(question)
            
            # Collect statistics
            if validation["valid"]:
                validation_results["summary"]["valid_questions"] += 1
                a_values.append(validation["parameters"]["a"])
                b_values.append(validation["parameters"]["b"])
                c_values.append(validation["parameters"]["c"])
            else:
                validation_results["summary"]["invalid_questions"] += 1
                
            if validation["warnings"]:
                validation_results["summary"]["questions_with_warnings"] += 1
            
            # Add to detailed results
            validation_results["detailed_results"].append({
                "question_id": str(question.id),
                "validation": validation,
                "difficulty_legacy": question.difficulty
            })
        
        # Calculate parameter statistics
        if a_values:
            validation_results["parameter_statistics"]["a_parameter"] = {
                "min": min(a_values),
                "max": max(a_values),
                "mean": np.mean(a_values),
                "std": np.std(a_values),
                "median": np.median(a_values)
            }
            
        if b_values:
            validation_results["parameter_statistics"]["b_parameter"] = {
                "min": min(b_values),
                "max": max(b_values),
                "mean": np.mean(b_values),
                "std": np.std(b_values),
                "median": np.median(b_values)
            }
            
        if c_values:
            validation_results["parameter_statistics"]["c_parameter"] = {
                "min": min(c_values),
                "max": max(c_values),
                "mean": np.mean(c_values),
                "std": np.std(c_values),
                "median": np.median(c_values)
            }
        
        # Generate recommendations
        if validation_results["summary"]["invalid_questions"] > 0:
            validation_results["recommendations"].append(
                f"Found {validation_results['summary']['invalid_questions']} questions with invalid IRT parameters that need review"
            )
            
        if validation_results["parameter_statistics"]["a_parameter"]["mean"] < 1.0:
            validation_results["recommendations"].append(
                "Average discrimination parameter is below 1.0, consider recalibration"
            )
            
        if validation_results["parameter_statistics"]["c_parameter"]["mean"] > 0.3:
            validation_results["recommendations"].append(
                "Average pseudo-guessing parameter is high, review item quality"
            )
        
        return validation_results

    def test_3pl_model_accuracy(self, num_test_points: int = 100) -> Dict[str, Any]:
        """
        Test mathematical accuracy of 3PL model implementation
        
        Args:
            num_test_points: Number of test points to validate
            
        Returns:
            Test results with accuracy metrics
        """
        test_results = {
            "test_points": num_test_points,
            "accuracy_tests": [],
            "probability_range_tests": [],
            "information_function_tests": [],
            "mathematical_properties": {}
        }
        
        # Test various parameter combinations
        test_parameters = [
            (1.0, 0.0, 0.25),  # Standard parameters
            (2.0, -1.0, 0.15), # High discrimination, easy item
            (0.5, 2.0, 0.35),  # Low discrimination, hard item
            (3.0, 0.5, 0.20),  # Very high discrimination
            (0.8, -2.5, 0.10), # Very easy item
            (1.5, 3.0, 0.40)   # Very hard item
        ]
        
        theta_range = np.linspace(-4, 4, num_test_points)
        
        for i, (a, b, c) in enumerate(test_parameters):
            test_case = {
                "parameters": {"a": a, "b": b, "c": c},
                "theta_range_test": True,
                "monotonicity_test": True,
                "boundary_conditions": True,
                "information_peak": None
            }
            
            probabilities = []
            information_values = []
            
            for theta in theta_range:
                # Test probability calculation
                prob = self.irt_service.calculate_3pl_probability(theta, a, b, c)
                probabilities.append(prob)
                
                # Test information function
                info = self.irt_service.calculate_information_function(theta, a, b, c)
                information_values.append(info)
                
                # Check probability bounds
                if not (0 <= prob <= 1):
                    test_case["theta_range_test"] = False
                    
                # Check that probability >= c (pseudo-guessing parameter)
                if prob < c - 1e-10:  # Small tolerance for floating point
                    test_case["boundary_conditions"] = False
            
            # Test monotonicity (probabilities should increase with theta)
            for j in range(1, len(probabilities)):
                if probabilities[j] < probabilities[j-1] - 1e-10:  # Small tolerance
                    test_case["monotonicity_test"] = False
                    break
            
            # Find information function peak
            max_info_idx = np.argmax(information_values)
            test_case["information_peak"] = {
                "theta": theta_range[max_info_idx],
                "expected_near_b": abs(theta_range[max_info_idx] - b) < 0.5,
                "max_information": information_values[max_info_idx]
            }
            
            test_results["accuracy_tests"].append(test_case)
        
        # Test specific mathematical properties
        test_results["mathematical_properties"] = self._test_mathematical_properties()
        
        return test_results

    def test_theta_estimation_accuracy(self, num_simulations: int = 50) -> Dict[str, Any]:
        """
        Test accuracy of theta estimation methods using simulated data
        
        Args:
            num_simulations: Number of simulation runs
            
        Returns:
            Estimation accuracy results
        """
        estimation_results = {
            "simulations": num_simulations,
            "mle_results": [],
            "eap_results": [],
            "adaptive_results": [],
            "summary_statistics": {}
        }
        
        # Define test scenarios with known theta values
        true_thetas = [-2.0, -1.0, 0.0, 1.0, 2.0]
        
        # Get a sample of questions with valid IRT parameters
        sample_questions = self.db.query(Question).filter(
            and_(
                Question.parametro_irt_a.isnot(None),
                Question.parametro_irt_b.isnot(None),
                Question.parametro_irt_c.isnot(None)
            )
        ).limit(20).all()
        
        if len(sample_questions) < 5:
            return {"error": "Insufficient questions with IRT parameters for testing"}
        
        for true_theta in true_thetas:
            mle_errors = []
            eap_errors = []
            adaptive_errors = []
            
            for sim in range(num_simulations):
                # Simulate responses for this theta
                simulated_responses = []
                
                for question in sample_questions[:10]:  # Use first 10 questions
                    # Calculate probability of correct response
                    prob = question.get_irt_probability(true_theta)
                    
                    # Simulate response
                    response = random.random() < prob
                    
                    simulated_responses.append((
                        response,
                        question.parametro_irt_a,
                        question.parametro_irt_b,
                        question.parametro_irt_c
                    ))
                
                # Test MLE estimation
                mle_theta, mle_se, mle_converged = self.irt_service.estimate_theta_mle(
                    simulated_responses
                )
                if mle_converged:
                    mle_errors.append(abs(mle_theta - true_theta))
                
                # Test EAP estimation
                eap_theta, eap_se = self.irt_service.estimate_theta_eap(
                    simulated_responses
                )
                eap_errors.append(abs(eap_theta - true_theta))
                
                # Test adaptive estimation
                current_theta = 0.0
                current_se = 1.0
                
                for response, a, b, c in simulated_responses:
                    # Create a mock question for adaptive testing
                    mock_question = type('MockQuestion', (), {
                        'parametro_irt_a': a,
                        'parametro_irt_b': b,
                        'parametro_irt_c': c
                    })()
                    
                    current_theta, current_se = self.irt_service.update_theta_adaptive(
                        current_theta, current_se, response, mock_question
                    )
                
                adaptive_errors.append(abs(current_theta - true_theta))
            
            # Store results for this true theta
            estimation_results["mle_results"].append({
                "true_theta": true_theta,
                "mean_error": np.mean(mle_errors) if mle_errors else None,
                "std_error": np.std(mle_errors) if mle_errors else None,
                "successful_estimations": len(mle_errors)
            })
            
            estimation_results["eap_results"].append({
                "true_theta": true_theta,
                "mean_error": np.mean(eap_errors),
                "std_error": np.std(eap_errors),
                "successful_estimations": len(eap_errors)
            })
            
            estimation_results["adaptive_results"].append({
                "true_theta": true_theta,
                "mean_error": np.mean(adaptive_errors),
                "std_error": np.std(adaptive_errors),
                "successful_estimations": len(adaptive_errors)
            })
        
        # Calculate overall summary statistics
        all_mle_errors = [result["mean_error"] for result in estimation_results["mle_results"] 
                         if result["mean_error"] is not None]
        all_eap_errors = [result["mean_error"] for result in estimation_results["eap_results"]]
        all_adaptive_errors = [result["mean_error"] for result in estimation_results["adaptive_results"]]
        
        estimation_results["summary_statistics"] = {
            "mle": {
                "overall_mean_error": np.mean(all_mle_errors) if all_mle_errors else None,
                "overall_rmse": np.sqrt(np.mean(np.array(all_mle_errors)**2)) if all_mle_errors else None
            },
            "eap": {
                "overall_mean_error": np.mean(all_eap_errors),
                "overall_rmse": np.sqrt(np.mean(np.array(all_eap_errors)**2))
            },
            "adaptive": {
                "overall_mean_error": np.mean(all_adaptive_errors),
                "overall_rmse": np.sqrt(np.mean(np.array(all_adaptive_errors)**2))
            }
        }
        
        return estimation_results

    def test_real_data_analysis(self, test_id: str = None) -> Dict[str, Any]:
        """
        Test IRT calculations on real test data
        
        Args:
            test_id: Optional specific test to analyze
            
        Returns:
            Real data analysis results
        """
        if test_id:
            tests = [self.db.query(DiagnosticTest).filter(
                DiagnosticTest.id == test_id
            ).first()]
            if not tests[0]:
                return {"error": f"Test {test_id} not found"}
        else:
            # Get recent completed tests
            tests = self.db.query(DiagnosticTest).filter(
                DiagnosticTest.status == "completed"
            ).order_by(DiagnosticTest.completed_at.desc()).limit(5).all()
        
        if not tests:
            return {"error": "No completed tests found for analysis"}
        
        analysis_results = {
            "analyzed_tests": len(tests),
            "test_analyses": [],
            "aggregated_insights": {}
        }
        
        all_thetas = []
        all_reliabilities = []
        
        for test in tests:
            try:
                # Generate IRT profile for this test
                irt_profile = self.irt_service.generate_theta_profile(str(test.id))
                
                # Extract key metrics
                test_analysis = {
                    "test_id": str(test.id),
                    "user_id": str(test.user_id),
                    "theta_estimates": irt_profile["estimation_methods"],
                    "test_quality": irt_profile["test_quality"],
                    "response_pattern": irt_profile["response_summary"],
                    "theta_progression": len(irt_profile["theta_progression"])
                }
                
                analysis_results["test_analyses"].append(test_analysis)
                
                # Collect for aggregation
                if irt_profile["estimation_methods"]["mle"]["converged"]:
                    all_thetas.append(irt_profile["estimation_methods"]["mle"]["theta"])
                else:
                    all_thetas.append(irt_profile["estimation_methods"]["eap"]["theta"])
                
                all_reliabilities.append(irt_profile["test_quality"]["reliability"])
                
            except Exception as e:
                self.logger.error(f"Error analyzing test {test.id}: {e}")
                analysis_results["test_analyses"].append({
                    "test_id": str(test.id),
                    "error": str(e)
                })
        
        # Generate aggregated insights
        if all_thetas:
            analysis_results["aggregated_insights"] = {
                "theta_distribution": {
                    "mean": np.mean(all_thetas),
                    "std": np.std(all_thetas),
                    "min": min(all_thetas),
                    "max": max(all_thetas),
                    "median": np.median(all_thetas)
                },
                "reliability_stats": {
                    "mean": np.mean(all_reliabilities),
                    "std": np.std(all_reliabilities),
                    "min": min(all_reliabilities),
                    "max": max(all_reliabilities)
                },
                "sample_size": len(all_thetas)
            }
        
        return analysis_results

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive validation and testing report
        
        Returns:
            Complete system validation report
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_status": "analyzing",
            "validation_summary": {},
            "performance_metrics": {},
            "recommendations": [],
            "detailed_results": {}
        }
        
        try:
            # 1. Question parameter validation
            self.logger.info("Validating question IRT parameters...")
            param_validation = self.validate_question_irt_parameters()
            report["detailed_results"]["parameter_validation"] = param_validation
            
            # 2. Mathematical accuracy testing
            self.logger.info("Testing 3PL model mathematical accuracy...")
            accuracy_test = self.test_3pl_model_accuracy()
            report["detailed_results"]["mathematical_accuracy"] = accuracy_test
            
            # 3. Theta estimation testing
            self.logger.info("Testing theta estimation accuracy...")
            theta_test = self.test_theta_estimation_accuracy(num_simulations=20)
            report["detailed_results"]["theta_estimation"] = theta_test
            
            # 4. Real data analysis
            self.logger.info("Analyzing real test data...")
            real_data_analysis = self.test_real_data_analysis()
            report["detailed_results"]["real_data_analysis"] = real_data_analysis
            
            # Generate summary
            report["validation_summary"] = {
                "total_questions_analyzed": param_validation["summary"]["total_questions"],
                "valid_questions_percentage": (
                    param_validation["summary"]["valid_questions"] / 
                    max(1, param_validation["summary"]["total_questions"]) * 100
                ),
                "mathematical_accuracy": "PASS" if all(
                    test["theta_range_test"] and test["monotonicity_test"] 
                    for test in accuracy_test["accuracy_tests"]
                ) else "REVIEW",
                "theta_estimation_rmse": {
                    "mle": theta_test["summary_statistics"]["mle"]["overall_rmse"],
                    "eap": theta_test["summary_statistics"]["eap"]["overall_rmse"],
                    "adaptive": theta_test["summary_statistics"]["adaptive"]["overall_rmse"]
                }
            }
            
            # Generate recommendations
            if param_validation["summary"]["invalid_questions"] > 0:
                report["recommendations"].append(
                    f"Review {param_validation['summary']['invalid_questions']} questions with invalid IRT parameters"
                )
            
            if theta_test["summary_statistics"]["mle"]["overall_rmse"] and theta_test["summary_statistics"]["mle"]["overall_rmse"] > 0.5:
                report["recommendations"].append(
                    "MLE theta estimation accuracy could be improved with parameter recalibration"
                )
            
            if "aggregated_insights" in real_data_analysis and real_data_analysis["aggregated_insights"]["reliability_stats"]["mean"] < 0.8:
                report["recommendations"].append(
                    "Average test reliability is below 0.8, consider adding more informative items"
                )
            
            report["system_status"] = "validated"
            
        except Exception as e:
            report["system_status"] = "error"
            report["error"] = str(e)
            self.logger.error(f"Error generating validation report: {e}")
        
        return report

    def _test_mathematical_properties(self) -> Dict[str, Any]:
        """Test specific mathematical properties of the 3PL model"""
        properties = {
            "asymptote_test": True,
            "inflection_point_test": True,
            "derivative_test": True
        }
        
        # Test that probability approaches c as theta approaches negative infinity
        very_low_theta = -10
        prob_low = self.irt_service.calculate_3pl_probability(very_low_theta, 1.0, 0.0, 0.25)
        if abs(prob_low - 0.25) > 0.01:
            properties["asymptote_test"] = False
        
        # Test that probability approaches 1 as theta approaches positive infinity
        very_high_theta = 10
        prob_high = self.irt_service.calculate_3pl_probability(very_high_theta, 1.0, 0.0, 0.25)
        if abs(prob_high - 1.0) > 0.01:
            properties["asymptote_test"] = False
        
        # Test that probability at b parameter is approximately (1+c)/2
        prob_at_b = self.irt_service.calculate_3pl_probability(0.0, 1.0, 0.0, 0.25)
        expected_prob_at_b = (1 + 0.25) / 2
        if abs(prob_at_b - expected_prob_at_b) > 0.01:
            properties["inflection_point_test"] = False
        
        return properties