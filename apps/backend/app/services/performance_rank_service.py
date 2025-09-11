"""
Performance-based Rank Calculation Service

This service calculates user ranks (E-S) based on real diagnostic test performance data,
including theta scores from IRT analysis and actual XP earned from test completions.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import Dict, List, Optional, Tuple
import statistics
import logging

from ..models.user import User
from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestResult
from ..models.subject import Subject
from ..models.question import Question
from ..core.database import get_db

logger = logging.getLogger(__name__)

class PerformanceRankService:
    """
    Service to calculate user ranks based on real performance data from diagnostic tests.
    
    Ranking Criteria:
    - Theta scores across subjects (IRT ability estimation)
    - Test completion rate and consistency
    - XP earned from actual question performance
    - Cross-subject performance stability
    """
    
    # Rank thresholds based on average theta scores and performance metrics
    RANK_THRESHOLDS = {
        'SSS': {'min_theta': 2.5, 'min_tests': 5, 'min_stability': 0.8, 'min_xp_per_test': 150},
        'SS':  {'min_theta': 2.0, 'min_tests': 4, 'min_stability': 0.7, 'min_xp_per_test': 120},
        'S':   {'min_theta': 1.5, 'min_tests': 3, 'min_stability': 0.6, 'min_xp_per_test': 100},
        'A':   {'min_theta': 1.0, 'min_tests': 3, 'min_stability': 0.5, 'min_xp_per_test': 80},
        'B':   {'min_theta': 0.5, 'min_tests': 2, 'min_stability': 0.4, 'min_xp_per_test': 60},
        'C':   {'min_theta': 0.0, 'min_tests': 2, 'min_stability': 0.3, 'min_xp_per_test': 40},
        'D':   {'min_theta': -0.5, 'min_tests': 1, 'min_stability': 0.2, 'min_xp_per_test': 20},
        'E':   {'min_theta': -3.0, 'min_tests': 0, 'min_stability': 0.0, 'min_xp_per_test': 0}
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_user_rank(self, user_id: str) -> Dict:
        """
        Calculate user rank based on diagnostic test performance data.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Dict containing rank calculation details
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}
            
            # Get performance metrics
            performance_data = self._get_user_performance_data(user_id)
            
            if not performance_data['completed_tests']:
                return {
                    "user_id": user_id,
                    "current_rank": "E",
                    "new_rank": "E",
                    "reason": "No completed diagnostic tests",
                    "metrics": performance_data
                }
            
            # Calculate rank based on performance
            new_rank = self._determine_rank_from_metrics(performance_data)
            
            # Calculate level based on total XP
            new_level = self._calculate_level_from_xp(performance_data['total_xp_earned'])
            
            result = {
                "user_id": user_id,
                "current_rank": user.rank,
                "new_rank": new_rank,
                "current_level": user.level,
                "new_level": new_level,
                "rank_changed": user.rank != new_rank,
                "level_changed": user.level != new_level,
                "metrics": performance_data,
                "thresholds_met": self._get_threshold_analysis(performance_data, new_rank)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating rank for user {user_id}: {str(e)}")
            return {"error": f"Calculation error: {str(e)}"}
    
    def _get_user_performance_data(self, user_id: str) -> Dict:
        """
        Gather comprehensive performance data from diagnostic tests.
        
        Args:
            user_id: User UUID
            
        Returns:
            Dict with performance metrics
        """
        # Get completed diagnostic tests
        completed_tests = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.status == "completed"
            )
        ).all()
        
        # Get all individual question results with theta scores
        test_results = self.db.query(DiagnosticTestResult).filter(
            DiagnosticTestResult.user_id == user_id
        ).all()
        
        if not test_results:
            return {
                "completed_tests": 0,
                "total_questions_answered": 0,
                "total_correct_answers": 0,
                "average_theta": 0.0,
                "theta_stability": 0.0,
                "subject_performance": {},
                "total_xp_earned": 0,
                "average_xp_per_test": 0,
                "test_completion_rate": 0.0
            }
        
        # Calculate theta statistics
        valid_theta_scores = [r.theta_after for r in test_results if r.theta_after is not None]
        avg_theta = statistics.mean(valid_theta_scores) if valid_theta_scores else 0.0
        
        # Calculate theta stability (inverse of standard deviation)
        theta_stability = 0.0
        if len(valid_theta_scores) > 1:
            theta_std = statistics.stdev(valid_theta_scores)
            theta_stability = 1.0 / (1.0 + theta_std)  # Higher stability = lower variation
        
        # Calculate performance by subject
        subject_performance = self._calculate_subject_performance(test_results)
        
        # Calculate XP metrics
        total_xp = sum(r.puntos_xp_earned for r in test_results if r.puntos_xp_earned)
        avg_xp_per_test = total_xp / len(completed_tests) if completed_tests else 0
        
        # Calculate accuracy
        correct_answers = sum(1 for r in test_results if r.is_correct)
        accuracy_rate = correct_answers / len(test_results) if test_results else 0.0
        
        return {
            "completed_tests": len(completed_tests),
            "total_questions_answered": len(test_results),
            "total_correct_answers": correct_answers,
            "accuracy_rate": accuracy_rate,
            "average_theta": avg_theta,
            "theta_stability": theta_stability,
            "theta_scores": valid_theta_scores,
            "subject_performance": subject_performance,
            "total_xp_earned": total_xp,
            "average_xp_per_test": avg_xp_per_test,
            "test_completion_rate": 1.0 if completed_tests else 0.0  # Based on actual test completion
        }
    
    def _calculate_subject_performance(self, test_results: List[DiagnosticTestResult]) -> Dict:
        """
        Calculate performance metrics by subject.
        
        Args:
            test_results: List of test result records
            
        Returns:
            Dict with subject-specific performance data
        """
        subject_data = {}
        
        for result in test_results:
            if not result.subject_id:
                continue
                
            subject_id = str(result.subject_id)
            if subject_id not in subject_data:
                subject_data[subject_id] = {
                    "questions_answered": 0,
                    "correct_answers": 0,
                    "theta_scores": [],
                    "xp_earned": 0
                }
            
            subject_data[subject_id]["questions_answered"] += 1
            if result.is_correct:
                subject_data[subject_id]["correct_answers"] += 1
            
            if result.theta_after is not None:
                subject_data[subject_id]["theta_scores"].append(result.theta_after)
            
            if result.puntos_xp_earned:
                subject_data[subject_id]["xp_earned"] += result.puntos_xp_earned
        
        # Calculate aggregated metrics per subject
        for subject_id, data in subject_data.items():
            data["accuracy"] = data["correct_answers"] / data["questions_answered"] if data["questions_answered"] > 0 else 0
            data["average_theta"] = statistics.mean(data["theta_scores"]) if data["theta_scores"] else 0.0
            
            # Get subject name
            subject = self.db.query(Subject).filter(Subject.id == subject_id).first()
            data["subject_name"] = subject.name if subject else "Unknown"
        
        return subject_data
    
    def _determine_rank_from_metrics(self, performance_data: Dict) -> str:
        """
        Determine rank based on performance metrics.
        
        Args:
            performance_data: User performance metrics
            
        Returns:
            Rank string (E, D, C, B, A, S, SS, SSS)
        """
        avg_theta = performance_data['average_theta']
        completed_tests = performance_data['completed_tests']
        theta_stability = performance_data['theta_stability']
        avg_xp_per_test = performance_data['average_xp_per_test']
        
        # Check ranks from highest to lowest
        for rank in ['SSS', 'SS', 'S', 'A', 'B', 'C', 'D', 'E']:
            thresholds = self.RANK_THRESHOLDS[rank]
            
            if (avg_theta >= thresholds['min_theta'] and
                completed_tests >= thresholds['min_tests'] and
                theta_stability >= thresholds['min_stability'] and
                avg_xp_per_test >= thresholds['min_xp_per_test']):
                
                return rank
        
        return 'E'  # Default rank
    
    def _calculate_level_from_xp(self, total_xp: int) -> int:
        """
        Calculate user level based on total XP earned.
        Uses a more realistic progression curve.
        
        Args:
            total_xp: Total XP earned from tests
            
        Returns:
            User level (1-100+)
        """
        if total_xp <= 0:
            return 1
        
        # Progressive XP requirements: level = sqrt(total_xp / 50) + 1
        # This creates a curve where early levels are easier but higher levels require more XP
        import math
        level = int(math.sqrt(total_xp / 50)) + 1
        
        return max(1, min(level, 999))  # Cap at level 999
    
    def _get_threshold_analysis(self, performance_data: Dict, achieved_rank: str) -> Dict:
        """
        Analyze which thresholds were met for the achieved rank.
        
        Args:
            performance_data: User performance metrics
            achieved_rank: The rank that was calculated
            
        Returns:
            Dict showing threshold analysis
        """
        if achieved_rank not in self.RANK_THRESHOLDS:
            return {}
        
        thresholds = self.RANK_THRESHOLDS[achieved_rank]
        
        return {
            "theta_requirement": {
                "required": thresholds['min_theta'],
                "achieved": performance_data['average_theta'],
                "met": performance_data['average_theta'] >= thresholds['min_theta']
            },
            "tests_requirement": {
                "required": thresholds['min_tests'],
                "achieved": performance_data['completed_tests'],
                "met": performance_data['completed_tests'] >= thresholds['min_tests']
            },
            "stability_requirement": {
                "required": thresholds['min_stability'],
                "achieved": performance_data['theta_stability'],
                "met": performance_data['theta_stability'] >= thresholds['min_stability']
            },
            "xp_requirement": {
                "required": thresholds['min_xp_per_test'],
                "achieved": performance_data['average_xp_per_test'],
                "met": performance_data['average_xp_per_test'] >= thresholds['min_xp_per_test']
            }
        }
    
    def update_user_rank_and_level(self, user_id: str) -> Dict:
        """
        Update user's rank and level in the database based on performance.
        
        Args:
            user_id: User UUID
            
        Returns:
            Dict with update results
        """
        try:
            calculation_result = self.calculate_user_rank(user_id)
            
            if "error" in calculation_result:
                return calculation_result
            
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}
            
            # Update user if rank or level changed
            updates_made = []
            
            if calculation_result['rank_changed']:
                old_rank = user.rank
                user.rank = calculation_result['new_rank']
                updates_made.append(f"Rank: {old_rank} → {calculation_result['new_rank']}")
            
            if calculation_result['level_changed']:
                old_level = user.level
                user.level = calculation_result['new_level']
                updates_made.append(f"Level: {old_level} → {calculation_result['new_level']}")
            
            # Update experience to match calculated XP
            total_xp = calculation_result['metrics']['total_xp_earned']
            if user.experience != total_xp:
                old_exp = user.experience
                user.experience = total_xp
                updates_made.append(f"XP: {old_exp} → {total_xp}")
            
            if updates_made:
                self.db.commit()
                logger.info(f"Updated user {user_id}: {', '.join(updates_made)}")
            
            calculation_result['updates_made'] = updates_made
            calculation_result['database_updated'] = len(updates_made) > 0
            
            return calculation_result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user {user_id}: {str(e)}")
            return {"error": f"Update error: {str(e)}"}
    
    def bulk_update_all_user_ranks(self, limit: Optional[int] = None) -> Dict:
        """
        Update ranks for all users with diagnostic test data.
        
        Args:
            limit: Optional limit on number of users to process
            
        Returns:
            Dict with bulk update results
        """
        try:
            # Get users who have completed at least one diagnostic test
            query = self.db.query(User.id).join(
                DiagnosticTest,
                User.id == DiagnosticTest.user_id
            ).filter(
                DiagnosticTest.status == "completed"
            ).distinct()
            
            if limit:
                query = query.limit(limit)
            
            user_ids = [str(u.id) for u in query.all()]
            
            results = {
                "total_users_processed": 0,
                "users_updated": 0,
                "rank_changes": 0,
                "level_changes": 0,
                "errors": [],
                "processing_results": []
            }
            
            for user_id in user_ids:
                try:
                    update_result = self.update_user_rank_and_level(user_id)
                    results["total_users_processed"] += 1
                    
                    if "error" not in update_result:
                        if update_result.get('database_updated', False):
                            results["users_updated"] += 1
                        
                        if update_result.get('rank_changed', False):
                            results["rank_changes"] += 1
                        
                        if update_result.get('level_changed', False):
                            results["level_changes"] += 1
                        
                        results["processing_results"].append({
                            "user_id": user_id,
                            "new_rank": update_result.get('new_rank'),
                            "new_level": update_result.get('new_level'),
                            "updates": update_result.get('updates_made', [])
                        })
                    else:
                        results["errors"].append({
                            "user_id": user_id,
                            "error": update_result["error"]
                        })
                        
                except Exception as e:
                    results["errors"].append({
                        "user_id": user_id,
                        "error": str(e)
                    })
            
            logger.info(f"Bulk rank update completed: {results['users_updated']}/{results['total_users_processed']} users updated")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk rank update: {str(e)}")
            return {"error": f"Bulk update error: {str(e)}"}

def create_performance_rank_service() -> PerformanceRankService:
    """Factory function to create PerformanceRankService with database session."""
    db = next(get_db())
    try:
        return PerformanceRankService(db)
    finally:
        db.close()