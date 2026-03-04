"""
Performance-based Rank Calculation Service

This service calculates user ranks (E-S) based on PERCENTILE comparison among all users,
using theta scores from IRT analysis and performance metrics.

Rank System (per README_NEGOCIO.md spec):
- E: Bottom 20% of users
- D: 20-40 percentile
- C: 40-60 percentile
- B: 60-80 percentile
- A: 80-95 percentile
- S: Top 5% of users (elite)

IMPORTANT: Ranks are calculated weekly by comparing users against each other.
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
    Service to calculate user ranks based on PERCENTILE comparison among all users.

    Ranking is comparative - a user's rank depends on how they perform relative to others.
    Uses a composite score based on:
    - Average theta score (IRT ability)
    - Accuracy rate
    - Consistency (stability of performance)
    """

    # Percentile-based rank thresholds (per spec)
    # Ranks: E → D → C → B → A → S (no SS or SSS)
    RANK_PERCENTILES = {
        'S': 95,   # Top 5%
        'A': 80,   # Top 20% (80-95 percentile)
        'B': 60,   # Top 40% (60-80 percentile)
        'C': 40,   # Middle (40-60 percentile)
        'D': 20,   # Lower middle (20-40 percentile)
        'E': 0     # Bottom 20%
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_user_rank(self, user_id: str) -> Dict:
        """
        Calculate user rank based on PERCENTILE comparison among all users.

        Rank is determined by comparing the user's composite score against all other users.
        This implements the spec requirement for comparative ranking.

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
                    "percentile": 0.0,
                    "reason": "No completed diagnostic tests",
                    "metrics": performance_data
                }

            # Get all user scores for percentile calculation
            all_user_scores = self._get_all_user_scores()

            # Calculate composite score for this user
            composite_score = self._calculate_composite_score(performance_data)

            # Determine rank based on percentile
            new_rank, percentile = self._determine_rank_from_percentile(user_id, all_user_scores)

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
                "composite_score": composite_score,
                "percentile": round(percentile, 2),
                "total_ranked_users": len(all_user_scores),
                "metrics": performance_data,
                "ranking_method": "percentile_based"
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
    
    def _calculate_composite_score(self, performance_data: Dict) -> float:
        """
        Calculate a composite score for percentile ranking.

        Composite score combines:
        - Theta score (50% weight) - normalized to 0-100 scale
        - Accuracy rate (30% weight) - already 0-1, scale to 0-100
        - Consistency (20% weight) - theta stability, scale to 0-100

        Args:
            performance_data: User performance metrics

        Returns:
            Composite score (0-100)
        """
        # Normalize theta from [-3, 3] to [0, 100]
        theta = performance_data.get('average_theta', 0.0)
        theta_normalized = ((theta + 3) / 6) * 100
        theta_normalized = max(0, min(100, theta_normalized))

        # Accuracy is already 0-1, convert to 0-100
        accuracy = performance_data.get('accuracy_rate', 0.0) * 100

        # Stability is 0-1, convert to 0-100
        stability = performance_data.get('theta_stability', 0.0) * 100

        # Weighted composite
        composite = (theta_normalized * 0.50) + (accuracy * 0.30) + (stability * 0.20)

        return round(composite, 2)

    def _get_all_user_scores(self) -> List[Tuple[str, float]]:
        """
        Get composite scores for all users with completed tests.

        Returns:
            List of (user_id, composite_score) tuples, sorted by score descending
        """
        # Get all users with completed diagnostic tests
        users_with_tests = self.db.query(User.id).join(
            DiagnosticTest,
            User.id == DiagnosticTest.user_id
        ).filter(
            DiagnosticTest.status == "completed"
        ).distinct().all()

        user_scores = []
        for (user_id,) in users_with_tests:
            performance = self._get_user_performance_data(str(user_id))
            if performance['completed_tests'] > 0:
                score = self._calculate_composite_score(performance)
                user_scores.append((str(user_id), score))

        # Sort by score descending (highest first)
        user_scores.sort(key=lambda x: x[1], reverse=True)
        return user_scores

    def _determine_rank_from_percentile(self, user_id: str, user_scores: List[Tuple[str, float]]) -> Tuple[str, float]:
        """
        Determine rank based on percentile among all users.

        Args:
            user_id: User ID to find rank for
            user_scores: List of (user_id, score) sorted by score descending

        Returns:
            Tuple of (rank, percentile)
        """
        if not user_scores:
            return 'E', 0.0

        total_users = len(user_scores)
        user_position = None

        for idx, (uid, score) in enumerate(user_scores):
            if uid == user_id:
                user_position = idx
                break

        if user_position is None:
            return 'E', 0.0

        # Calculate percentile (higher is better)
        # Position 0 = top, so percentile = (total - position - 1) / (total - 1) * 100
        if total_users == 1:
            percentile = 50.0  # Only user, give middle rank
        else:
            percentile = ((total_users - user_position - 1) / (total_users - 1)) * 100

        # Determine rank from percentile
        if percentile >= self.RANK_PERCENTILES['S']:
            return 'S', percentile
        elif percentile >= self.RANK_PERCENTILES['A']:
            return 'A', percentile
        elif percentile >= self.RANK_PERCENTILES['B']:
            return 'B', percentile
        elif percentile >= self.RANK_PERCENTILES['C']:
            return 'C', percentile
        elif percentile >= self.RANK_PERCENTILES['D']:
            return 'D', percentile
        else:
            return 'E', percentile
    
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